"""Fetch a reproducible small subject subset from the public Zenodo ZIP files.

The source archives are several GB each. HTTP Range downloads let this script
fetch selected image/mask records without saving every frame. Source data are
CC BY-NC per Zenodo record; keep them local and do not redistribute.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from remotezip import RemoteZip


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "stereothermolegs" / "pilot_split"
BASE = "https://zenodo.org/api/records/8289870/files/{archive}/content"
SAMPLE_PER_PERSON = 20
SEED = 20261031
PEOPLE = {
    "train": ["train_02.zip", "train_03.zip", "train_04.zip", "train_05.zip"],
    "test": ["test_01.zip"],
}
SUFFIXES = ("__rgb.png", "__irt.png", "__labels_rgbd.png", "__labels_irt.png")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    rng = random.Random(SEED)
    receipt: dict[str, object] = {
        "source": "https://zenodo.org/records/8289870",
        "doi": "10.5281/zenodo.8289870",
        "license": "CC BY-NC 4.0 (Zenodo record license; verify before reuse)",
        "split_unit": "participant archive",
        "sample_per_person": SAMPLE_PER_PERSON,
        "seed": SEED,
        "files": [],
    }
    total_bytes = 0

    for split, archives in PEOPLE.items():
        for archive in archives:
            person = archive.removesuffix(".zip").replace("_", "-")
            url = BASE.format(archive=archive)
            with RemoteZip(url) as zf:
                names = zf.namelist()
                by_stem: dict[str, set[str]] = {}
                for name in names:
                    if name.endswith(SUFFIXES):
                        stem = name.rsplit("__", 1)[0]
                        by_stem.setdefault(stem, set()).add("__" + name.rsplit("__", 1)[1])
                required = set(SUFFIXES)
                eligible = sorted(
                    stem for stem, types in by_stem.items() if types == required
                )
                if len(eligible) < SAMPLE_PER_PERSON:
                    raise RuntimeError(f"{archive}: only {len(eligible)} complete pairs")
                selected = sorted(rng.sample(eligible, SAMPLE_PER_PERSON))
                for stem in selected:
                    for suffix in SUFFIXES:
                        member = f"{stem}{suffix}"
                        data = zf.read(member)
                        relative = Path(split) / person / Path(member).name
                        target = OUT / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(data)
                        total_bytes += len(data)
                        receipt["files"].append(
                            {
                                "path": relative.as_posix(),
                                "source_archive": archive,
                                "source_member": member,
                                "bytes": len(data),
                                "sha256": sha256(data),
                            }
                        )
                print(f"{archive}: {len(selected)} paired samples -> {split}/{person}")

    receipt["total_bytes"] = total_bytes
    receipt["sample_count"] = len(receipt["files"]) // len(SUFFIXES)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"saved {receipt['sample_count']} paired samples; {total_bytes / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
