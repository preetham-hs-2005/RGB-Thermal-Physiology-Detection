"""Controlled RGB / thermal / fused semantic-segmentation pilot on Caltech RGB-T.

The source thermal16 values are treated as sensor intensities, not degrees C.
The three arms share the creator-provided split, mask, resize, optimizer and
training budget. Output is a research/engineering benchmark, not a health claim.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import time
import zipfile
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "datasets" / "caltech_aerial_rgbt" / "labeled_rgbt_pairs.zip"
SPLIT_DIR = ROOT / "datasets" / "caltech_aerial_rgbt" / "official_splits"
OUT_DIR = ROOT / "outputs" / "caltech_rgbt_runs"
ARCHIVE_ROOT = "labeled_rgbt_pairs/"
IGNORE_INDEX = 255
NUM_CLASSES = 12
EVALUATED_CLASSES = list(range(2, 12))  # creator convention: ignore unknown/background


def read_split(modality: str, split: str) -> list[tuple[str, str]]:
    path = SPLIT_DIR / f"{modality}_{split}.txt"
    with path.open("r", newline="", encoding="utf-8") as stream:
        rows = [(a.strip(), b.strip()) for a, b in csv.reader(stream) if len((a, b)) == 2]
    return rows


def paired_rows(split: str) -> list[tuple[str, str, str]]:
    rgb = read_split("rgb", split)
    thermal = read_split("thermal16", split)
    if len(rgb) != len(thermal):
        raise ValueError(f"{split}: RGB/thermal split counts differ")
    paired: list[tuple[str, str, str]] = []
    for (rgb_path, rgb_mask), (thermal_path, thermal_mask) in zip(rgb, thermal):
        if rgb_mask != thermal_mask:
            raise ValueError(f"{split}: RGB/thermal mask mismatch: {rgb_mask} != {thermal_mask}")
        paired.append((ARCHIVE_ROOT + rgb_path, ARCHIVE_ROOT + thermal_path, ARCHIVE_ROOT + rgb_mask))
    return paired


class CaltechPairs(Dataset):
    def __init__(self, rows: list[tuple[str, str, str]], mode: str, size: int, augment: bool):
        self.rows = rows
        self.mode = mode
        self.size = size
        self.augment = augment
        self._zip: zipfile.ZipFile | None = None

    def __len__(self) -> int:
        return len(self.rows)

    def _read(self, member: str) -> Image.Image:
        if self._zip is None:
            self._zip = zipfile.ZipFile(ZIP_PATH, "r")
        return Image.open(io.BytesIO(self._zip.read(member)))

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        rgb_path, thermal_path, mask_path = self.rows[index]
        rgb = self._read(rgb_path).convert("RGB").resize((self.size, self.size), Image.Resampling.BILINEAR)
        thermal = self._read(thermal_path).convert("I;16").resize((self.size, self.size), Image.Resampling.BILINEAR)
        mask = self._read(mask_path).convert("L").resize((self.size, self.size), Image.Resampling.NEAREST)

        rgb_np = np.asarray(rgb, dtype=np.float32) / 255.0
        thermal_np = np.asarray(thermal, dtype=np.float32)
        # Fixed, explicit scale for this 16-bit sensor representation. It is not °C.
        thermal_np = np.clip((thermal_np - 32768.0) / 16384.0, -2.0, 2.0)
        mask_np = np.asarray(mask, dtype=np.int64).copy()
        mask_np[(mask_np == 0) | (mask_np == 1)] = IGNORE_INDEX

        if self.augment and random.random() < 0.5:
            rgb_np = np.fliplr(rgb_np).copy()
            thermal_np = np.fliplr(thermal_np).copy()
            mask_np = np.fliplr(mask_np).copy()

        rgb_tensor = torch.from_numpy(rgb_np.transpose(2, 0, 1))
        thermal_tensor = torch.from_numpy(thermal_np[None, ...])
        if self.mode == "rgb":
            inputs = rgb_tensor
        elif self.mode == "thermal":
            inputs = thermal_tensor
        elif self.mode == "fusion":
            inputs = torch.cat((rgb_tensor, thermal_tensor), dim=0)
        else:
            raise ValueError(f"unknown mode: {self.mode}")
        return inputs, torch.from_numpy(mask_np)


class DoubleConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class SmallUNet(nn.Module):
    def __init__(self, in_ch: int, classes: int = NUM_CLASSES, base: int = 16):
        super().__init__()
        self.enc1 = DoubleConv(in_ch, base)
        self.enc2 = DoubleConv(base, base * 2)
        self.enc3 = DoubleConv(base * 2, base * 4)
        self.bottleneck = DoubleConv(base * 4, base * 8)
        self.pool = nn.MaxPool2d(2)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.dec3 = DoubleConv(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = DoubleConv(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = DoubleConv(base * 2, base)
        self.head = nn.Conv2d(base, classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        b = self.bottleneck(self.pool(e3))
        d3 = self.dec3(torch.cat((self.up3(b), e3), dim=1))
        d2 = self.dec2(torch.cat((self.up2(d3), e2), dim=1))
        d1 = self.dec1(torch.cat((self.up1(d2), e1), dim=1))
        return self.head(d1)


def make_loader(rows: list[tuple[str, str, str]], mode: str, args: argparse.Namespace, train: bool) -> DataLoader:
    if train and args.limit_train:
        rows = rows[: args.limit_train]
    if not train and args.limit_eval:
        rows = rows[: args.limit_eval]
    ds = CaltechPairs(rows, mode, args.size, augment=train)
    generator = torch.Generator().manual_seed(args.seed)
    return DataLoader(ds, batch_size=args.batch_size, shuffle=train, num_workers=0, pin_memory=True, generator=generator)


def confusion_update(matrix: torch.Tensor, prediction: torch.Tensor, target: torch.Tensor) -> None:
    valid = target != IGNORE_INDEX
    encoded = target[valid] * NUM_CLASSES + prediction[valid]
    matrix += torch.bincount(encoded, minlength=NUM_CLASSES * NUM_CLASSES).reshape(NUM_CLASSES, NUM_CLASSES)


def metrics_from_confusion(matrix: torch.Tensor) -> dict[str, object]:
    m = matrix.float()
    tp = torch.diag(m)
    denom = m.sum(0) + m.sum(1) - tp
    iou = tp / denom.clamp_min(1)
    present = [c for c in EVALUATED_CLASSES if denom[c] > 0]
    return {
        "mIoU_classes_2_to_11": float(iou[present].mean().item()) if present else None,
        "per_class_iou": {str(c): float(iou[c].item()) if denom[c] > 0 else None for c in EVALUATED_CLASSES},
        "evaluated_class_ids": present,
        "valid_pixels": int(m.sum().item()),
    }


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, object]:
    model.eval()
    confusion = torch.zeros((NUM_CLASSES, NUM_CLASSES), dtype=torch.int64, device=device)
    with torch.inference_mode():
        for inputs, targets in loader:
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            logits = model(inputs)
            confusion_update(confusion, logits.argmax(1), targets)
    return metrics_from_confusion(confusion.cpu())


def train_one(mode: str, args: argparse.Namespace, train_rows: list[tuple[str, str, str]], val_rows: list[tuple[str, str, str]], test_rows: list[tuple[str, str, str]], device: torch.device) -> dict[str, object]:
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    channels = {"rgb": 3, "thermal": 1, "fusion": 4}[mode]
    model = SmallUNet(channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss(ignore_index=IGNORE_INDEX)
    train_loader = make_loader(train_rows, mode, args, train=True)
    val_loader = make_loader(val_rows, mode, args, train=False)
    test_loader = make_loader(test_rows, mode, args, train=False)
    history = []
    started = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum = 0.0
        batches = 0
        for inputs, targets in train_loader:
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            loss = loss_fn(logits, targets)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach().item())
            batches += 1
        val_metrics = evaluate(model, val_loader, device)
        record = {"epoch": epoch, "train_loss": loss_sum / max(batches, 1), "validation": val_metrics}
        history.append(record)
        print(f"{mode} epoch {epoch}/{args.epochs}: loss={record['train_loss']:.4f} val_mIoU={val_metrics['mIoU_classes_2_to_11']}", flush=True)

    test_metrics = evaluate(model, test_loader, device)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = OUT_DIR / f"caltech_{mode}_unet_seed{args.seed}.pt"
    torch.save({"state_dict": model.state_dict(), "mode": mode, "size": args.size, "classes": NUM_CLASSES, "seed": args.seed}, checkpoint)
    return {
        "mode": mode,
        "architecture": "SmallUNet(base_channels=16)",
        "input_channels": channels,
        "epochs": args.epochs,
        "train_samples": min(len(train_rows), args.limit_train) if args.limit_train else len(train_rows),
        "val_samples": min(len(val_rows), args.limit_eval) if args.limit_eval else len(val_rows),
        "test_samples": min(len(test_rows), args.limit_eval) if args.limit_eval else len(test_rows),
        "history": history,
        "test": test_metrics,
        "checkpoint": str(checkpoint.relative_to(ROOT)),
        "elapsed_seconds": round(time.time() - started, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modes", nargs="+", choices=("rgb", "thermal", "fusion"), default=("rgb", "thermal", "fusion"))
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--limit-train", type=int, default=0, help="0 uses the full official train split")
    parser.add_argument("--limit-eval", type=int, default=0, help="0 uses the full official validation/test splits")
    args = parser.parse_args()
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(f"dataset archive is missing: {ZIP_PATH}")
    for required in ("rgb_train.txt", "rgb_val.txt", "rgb_test.txt", "thermal16_train.txt", "thermal16_val.txt", "thermal16_test.txt"):
        if not (SPLIT_DIR / required).is_file():
            raise FileNotFoundError(f"creator-provided split file is missing: {SPLIT_DIR / required}")

    train_rows = paired_rows("train")
    val_rows = paired_rows("val")
    test_rows = paired_rows("test")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
        print(f"Training on {torch.cuda.get_device_name(0)}; thermal16 values treated as non-radiometric intensities", flush=True)
    else:
        print("CUDA unavailable; training on CPU", flush=True)

    results = {
        "dataset": "Caltech Aerial RGB-T labeled pairs",
        "dataset_license_note": "CaltechDATA record says CC BY-NC 4.0; creator README says CC BY-SA 4.0; retain noncommercial use and resolve discrepancy before redistribution",
        "split_source": "creator-provided rgbt_splits",
        "split_counts": {"train": len(train_rows), "val": len(val_rows), "test": len(test_rows)},
        "seed": args.seed,
        "device": str(device),
        "thermal_semantics": "16-bit thermal sensor values; units not established as Celsius",
        "resize": [args.size, args.size],
        "ignored_mask_ids": [0, 1],
        "runs": [],
    }
    for mode in args.modes:
        results["runs"].append(train_one(mode, args, train_rows, val_rows, test_rows, device))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUT_DIR / "caltech_rgbt_baseline_metrics.json"
    metrics_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"metrics saved to {metrics_path.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
