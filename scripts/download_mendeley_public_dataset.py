"""Download a public Mendeley dataset with per-file SHA-256 verification.

The script is intentionally limited to the public Mendeley API and stores
files by source folder ID, so repeated filenames cannot overwrite each other.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "RGB-Thermal-Physiology-Research/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download_one(item: dict[str, Any], root: Path) -> dict[str, Any]:
    folder_id = item.get("folder_id") or "root"
    filename = Path(item["filename"]).name
    target_dir = (root / "files" / folder_id).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = (target_dir / filename).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        raise ValueError(f"dataset path escapes output directory: {filename}")

    expected_size = int(item.get("size") or item["content_details"]["size"])
    expected_sha = item["content_details"].get("sha256_hash")
    if target.is_file() and target.stat().st_size == expected_size:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if expected_sha and digest == expected_sha:
            return {"id": item["id"], "folder_id": folder_id, "filename": filename, "path": target.relative_to(root).as_posix(), "bytes": expected_size, "sha256": digest, "verified": True, "skipped_existing": True}

    url = item["content_details"]["download_url"]
    request = urllib.request.Request(url, headers={"User-Agent": "RGB-Thermal-Physiology-Research/1.0"})
    digest = hashlib.sha256()
    size = 0
    fd, temp_name = tempfile.mkstemp(prefix=".mendeley-", suffix=".partial", dir=target_dir)
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(request, timeout=120) as response:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
                digest.update(block)
                size += len(block)
        actual_sha = digest.hexdigest()
        if size != expected_size:
            raise IOError(f"{filename}: expected {expected_size} bytes, downloaded {size}")
        if expected_sha and actual_sha != expected_sha:
            raise IOError(f"{filename}: SHA-256 mismatch ({actual_sha} != {expected_sha})")
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return {"id": item["id"], "folder_id": folder_id, "filename": filename, "path": target.relative_to(root).as_posix(), "bytes": size, "sha256": actual_sha, "verified": True, "skipped_existing": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_id", help="Public Mendeley dataset ID, e.g. rf5m97cmm3")
    parser.add_argument("--version", type=int, default=None, help="defaults to the API's latest version")
    parser.add_argument("--out", type=Path, required=True, help="local destination, excluded from Git by default")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 16:
        parser.error("--workers must be between 1 and 16")

    metadata = fetch_json(f"https://data.mendeley.com/public-api/datasets/{args.dataset_id}")
    if args.version is not None and int(metadata["version"]) != args.version:
        raise SystemExit(f"API latest version is {metadata['version']}; use that version explicitly before downloading")
    if not metadata.get("available") or not metadata.get("files"):
        raise SystemExit("dataset is not publicly available or has no files")
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, item, root): item for item in metadata["files"]}
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            item = futures[future]
            try:
                entries.append(future.result())
            except Exception as exc:
                failures.append(f"{item.get('filename')}: {exc}")
            if index % 50 == 0 or index == len(futures):
                print(f"processed {index}/{len(futures)} files; errors={len(failures)}", flush=True)

    receipt = {
        "dataset_id": metadata["id"],
        "title": metadata.get("name"),
        "doi": metadata.get("doi", {}).get("id"),
        "version": metadata.get("version"),
        "source": f"https://data.mendeley.com/datasets/{metadata['id']}/{metadata.get('version')}",
        "license": metadata.get("data_licence", {}).get("short_name"),
        "license_url": metadata.get("data_licence", {}).get("url"),
        "published_total_bytes": metadata.get("size"),
        "retrieved_file_count": len(entries),
        "retrieved_bytes": sum(e["bytes"] for e in entries),
        "files": sorted(entries, key=lambda e: (e["folder_id"], e["filename"], e["id"])),
        "errors": failures,
    }
    (root / "manifest.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    (root / "dataset_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if failures:
        raise SystemExit(f"download incomplete: {len(failures)} errors; details saved in {root / 'manifest.json'}")
    print(f"verified {len(entries)} files ({sum(e['bytes'] for e in entries):,} bytes) into {root}")


if __name__ == "__main__":
    main()
