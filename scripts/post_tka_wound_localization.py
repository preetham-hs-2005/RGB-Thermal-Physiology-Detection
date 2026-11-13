"""Paired RGB/radiometric-thermal wound mask training scaffold.

This is a research pipeline, not a diagnostic tool. The clinical dataset is
restricted and has not been acquired; training must wait until a rights-cleared
manifest and real annotation files are available. No synthetic data are
silently treated as clinical samples.

The fusion model uses pretrained DINOv2 modality encoders and a query-mask
transformer decoder (Mask2Former-style mask classification). The decoder is
task-specific and is initialized from scratch. The thermal encoder starts from
the same published DINOv2 weights, then is fine-tuned independently.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path(__file__).resolve().parents[1]
CLASS_NAMES = (
    "background",
    "open_wound",
    "granulation",
    "infection_associated_exudate",
    "necrosis",
)
IGNORE_INDEX = 255
RGB_MEAN = torch.tensor((0.485, 0.456, 0.406)).view(3, 1, 1)
RGB_STD = torch.tensor((0.229, 0.224, 0.225)).view(3, 1, 1)


@dataclass(frozen=True)
class Record:
    record_id: str
    pairing_id: str
    pairing_basis: str
    timestamp_delta_ms: float | None
    subject_id: str
    split: str
    rgb_path: Path
    thermal_path: Path
    mask_path: Path
    thermal_to_rgb: np.ndarray
    thermal_unit: str
    thermal_conversion_method: str
    thermal_scale_to_c: float
    thermal_offset_c: float
    invalid_value: float | None
    landmarks: tuple[dict[str, Any], ...]


def _resolved(root: Path, value: str, field: str) -> Path:
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"{field} must stay inside the dataset root: {value}")
    return path


def load_manifest(path: Path, require_access: bool = False) -> tuple[list[Record], dict[str, int]]:
    """Load/validate a JSON manifest with dataset-level mask IDs.

    Required top-level keys: ``dataset_id``, ``class_ids`` and ``records``.
    Every sample has split, subject_id, RGB/mask paths, a radiometric thermal
    path and a 3x3 thermal-to-RGB homography. Held-out registration landmarks
    are optional in the file but required for a registration-quality claim.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if require_access and (
        data.get("access_status") != "approved_for_research"
        or not str(data.get("access_terms_ref", "")).strip()
    ):
        raise PermissionError("training blocked until manifest records approved_for_research and the applicable license/DUA reference")
    root = path.parent.resolve()
    class_ids = {str(k): int(v) for k, v in data["class_ids"].items()}
    expected = {name: idx for idx, name in enumerate(CLASS_NAMES)}
    if class_ids != expected:
        raise ValueError(f"class_ids must exactly match {expected}; found {class_ids}")
    records: list[Record] = []
    seen_ids: set[str] = set()
    seen_pairing_ids: set[str] = set()
    split_subjects: dict[str, set[str]] = {s: set() for s in ("train", "val", "test")}
    for raw in data["records"]:
        record_id = str(raw["record_id"])
        pairing_id = str(raw.get("pairing_id", "")).strip()
        pairing_basis = str(raw.get("pairing_basis", "")).strip()
        subject_id = str(raw["subject_id"])
        split = str(raw["split"])
        if not record_id or record_id in seen_ids:
            raise ValueError(f"record_id must be nonempty and unique: {record_id!r}")
        if not pairing_id or pairing_id in seen_pairing_ids or not pairing_basis:
            raise ValueError(f"{record_id}: require a unique pairing_id and documented pairing_basis")
        if split not in split_subjects:
            raise ValueError(f"{record_id}: split must be train, val, or test")
        seen_ids.add(record_id)
        seen_pairing_ids.add(pairing_id)
        split_subjects[split].add(subject_id)
        timestamp_delta = raw.get("timestamp_delta_ms")
        if timestamp_delta is not None:
            timestamp_delta = float(timestamp_delta)
            max_delta = data.get("max_pair_delta_ms")
            if max_delta is None:
                raise ValueError(f"{record_id}: set dataset-level max_pair_delta_ms when timestamp_delta_ms is supplied")
            if abs(timestamp_delta) > float(max_delta):
                raise ValueError(f"{record_id}: paired timestamp difference exceeds max_pair_delta_ms")
        unit = str(raw["thermal_unit"]).strip().lower()
        if unit not in {"degc", "celsius", "°c"}:
            raise ValueError(f"{record_id}: thermal values must have documented Celsius units")
        conversion_method = str(raw.get("thermal_conversion_method", "")).strip()
        if not conversion_method:
            raise ValueError(f"{record_id}: thermal_conversion_method/source provenance is required")
        matrix = np.asarray(raw["thermal_to_rgb"], dtype=np.float64)
        if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-10:
            raise ValueError(f"{record_id}: thermal_to_rgb must be a finite invertible 3x3 matrix")
        if str(raw.get("mask_frame", "rgb")) != "rgb":
            raise ValueError(f"{record_id}: masks must be in RGB coordinates before training")
        records.append(Record(
            record_id=record_id,
            pairing_id=pairing_id,
            pairing_basis=pairing_basis,
            timestamp_delta_ms=timestamp_delta,
            subject_id=subject_id,
            split=split,
            rgb_path=_resolved(root, raw["rgb_path"], "rgb_path"),
            thermal_path=_resolved(root, raw["thermal_path"], "thermal_path"),
            mask_path=_resolved(root, raw["mask_path"], "mask_path"),
            thermal_to_rgb=matrix,
            thermal_unit=unit,
            thermal_conversion_method=conversion_method,
            thermal_scale_to_c=float(raw.get("thermal_scale_to_c", 1.0)),
            thermal_offset_c=float(raw.get("thermal_offset_c", 0.0)),
            invalid_value=None if raw.get("invalid_value") is None else float(raw["invalid_value"]),
            landmarks=tuple(raw.get("heldout_landmarks", ())),
        ))
    for split, ids in split_subjects.items():
        if not ids:
            raise ValueError(f"manifest has no {split} records")
    for left, right in (("train", "val"), ("train", "test"), ("val", "test")):
        overlap = split_subjects[left] & split_subjects[right]
        if overlap:
            raise ValueError(f"patient leakage between {left} and {right}: {sorted(overlap)[:5]}")
    missing = [str(p) for r in records for p in (r.rgb_path, r.thermal_path, r.mask_path) if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"manifest references missing files (first 5): {missing[:5]}")
    return records, class_ids


def read_thermal(path: Path) -> np.ndarray:
    """Read raw numeric thermal data; reject color-mapped display images."""
    if path.suffix.lower() == ".npy":
        array = np.load(path, allow_pickle=False)
    elif path.suffix.lower() in {".tif", ".tiff"}:
        try:
            import tifffile
        except ImportError as exc:
            raise RuntimeError("Install requirements-medical.txt to read radiometric TIFF files") from exc
        array = tifffile.imread(path)
    else:
        raise ValueError(f"{path}: thermal files must be raw .npy or .tif/.tiff arrays")
    array = np.asarray(array)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.number):
        raise ValueError(f"{path}: expected a single-channel numeric thermal array")
    return array.astype(np.float32, copy=False)


def _warp_thermal_to_rgb(thermal: torch.Tensor, valid: torch.Tensor, matrix: np.ndarray, height: int, width: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Project a thermal image into RGB coordinates via H(thermal -> RGB)."""
    device = thermal.device
    inverse = torch.as_tensor(np.linalg.inv(matrix), dtype=torch.float64, device=device)
    yy, xx = torch.meshgrid(
        torch.arange(height, dtype=torch.float64, device=device),
        torch.arange(width, dtype=torch.float64, device=device),
        indexing="ij",
    )
    rgb_points = torch.stack((xx, yy, torch.ones_like(xx)), dim=-1)
    thermal_points = rgb_points @ inverse.T
    denom = thermal_points[..., 2]
    x = thermal_points[..., 0] / denom.clamp(min=1e-12)
    y = thermal_points[..., 1] / denom.clamp(min=1e-12)
    source_h, source_w = thermal.shape[-2:]
    grid = torch.stack((2 * x / max(source_w - 1, 1) - 1, 2 * y / max(source_h - 1, 1) - 1), dim=-1)
    grid = grid.to(dtype=thermal.dtype).unsqueeze(0)
    warped = F.grid_sample(thermal[None, None], grid, mode="bilinear", padding_mode="zeros", align_corners=True)[0, 0]
    warped_valid = F.grid_sample(valid[None, None].float(), grid, mode="nearest", padding_mode="zeros", align_corners=True)[0, 0] > 0.5
    inside = (x >= 0) & (x <= source_w - 1) & (y >= 0) & (y <= source_h - 1) & (denom > 0)
    warped_valid &= inside
    warped = torch.where(warped_valid, warped, torch.zeros_like(warped))
    return warped, warped_valid


def heldout_tre_px(record: Record) -> float | None:
    """Mean target-registration error over held-out point pairs, in RGB px."""
    points = [p for p in record.landmarks if p.get("split") == "held_out"]
    if not points:
        return None
    errors = []
    for point in points:
        thermal_xy = np.asarray(point["thermal_xy"], dtype=np.float64)
        rgb_xy = np.asarray(point["rgb_xy"], dtype=np.float64)
        mapped = record.thermal_to_rgb @ np.array([thermal_xy[0], thermal_xy[1], 1.0])
        mapped = mapped[:2] / mapped[2]
        errors.append(float(np.linalg.norm(mapped - rgb_xy)))
    return float(np.mean(errors))


class WoundPairs(Dataset):
    def __init__(self, records: list[Record], image_size: int, min_thermal_coverage: float):
        self.records = records
        self.image_size = image_size
        self.min_thermal_coverage = min_thermal_coverage
        if image_size % 14:
            raise ValueError("image_size must be divisible by 14 for DINOv2 patch embedding")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        rec = self.records[index]
        rgb_img = Image.open(rec.rgb_path).convert("RGB")
        mask_img = Image.open(rec.mask_path).convert("L")
        if mask_img.size != rgb_img.size:
            raise ValueError(f"{rec.record_id}: mask and RGB dimensions differ; map mask to RGB frame first")
        src_w, src_h = rgb_img.size
        scale = self.image_size / max(src_w, src_h)
        fit_w = max(1, round(src_w * scale))
        fit_h = max(1, round(src_h * scale))
        left = (self.image_size - fit_w) // 2
        top = (self.image_size - fit_h) // 2
        rgb_fit = rgb_img.resize((fit_w, fit_h), Image.Resampling.BILINEAR)
        rgb_canvas = Image.new("RGB", (self.image_size, self.image_size), (0, 0, 0))
        rgb_canvas.paste(rgb_fit, (left, top))
        rgb = np.asarray(rgb_canvas, dtype=np.float32) / 255.0
        mask_fit = mask_img.resize((fit_w, fit_h), Image.Resampling.NEAREST)
        mask_canvas = Image.new("L", (self.image_size, self.image_size), IGNORE_INDEX)
        mask_canvas.paste(mask_fit, (left, top))
        labels = np.asarray(mask_canvas, dtype=np.uint8)
        allowed = set(range(len(CLASS_NAMES))) | {IGNORE_INDEX}
        found = set(np.unique(labels).tolist())
        if not found <= allowed:
            raise ValueError(f"{rec.record_id}: unknown mask IDs {sorted(found - allowed)}")

        raw = read_thermal(rec.thermal_path)
        valid_np = np.isfinite(raw)
        if rec.invalid_value is not None:
            valid_np &= raw != rec.invalid_value
        celsius = raw * rec.thermal_scale_to_c + rec.thermal_offset_c
        valid_np &= np.isfinite(celsius)
        thermal = torch.from_numpy(np.where(valid_np, celsius, 0).astype(np.float32))
        valid = torch.from_numpy(valid_np.astype(np.float32))
        thermal, valid = _warp_thermal_to_rgb(thermal, valid, rec.thermal_to_rgb, src_h, src_w)
        thermal_fit = F.interpolate(thermal[None, None], size=(fit_h, fit_w), mode="bilinear", align_corners=False)[0, 0]
        valid_fit = F.interpolate(valid[None, None].float(), size=(fit_h, fit_w), mode="nearest")[0, 0] > 0.5
        thermal = torch.zeros((self.image_size, self.image_size), dtype=torch.float32)
        valid = torch.zeros((self.image_size, self.image_size), dtype=torch.bool)
        thermal[top:top + fit_h, left:left + fit_w] = thermal_fit
        valid[top:top + fit_h, left:left + fit_w] = valid_fit
        coverage = float(valid.float().mean().item())
        if coverage < self.min_thermal_coverage:
            raise ValueError(f"{rec.record_id}: mapped valid thermal coverage {coverage:.3f} is below threshold")

        vals = thermal[valid]
        if vals.numel() == 0:
            raise ValueError(f"{rec.record_id}: no valid radiometric pixels remain after registration")
        median = vals.median()
        q25 = torch.quantile(vals, 0.25)
        q75 = torch.quantile(vals, 0.75)
        iqr = (q75 - q25).clamp_min(0.25)
        absolute_temp = ((thermal - 25.0) / 15.0).clamp(0, 1)
        relative_temp = (((thermal - median) / iqr).clamp(-5, 5) + 5) / 10
        gx = F.pad(thermal[:, 1:] - thermal[:, :-1], (0, 1, 0, 0))
        gy = F.pad(thermal[1:, :] - thermal[:-1, :], (0, 0, 0, 1))
        grad = torch.sqrt(gx.square() + gy.square())
        grad_scale = torch.quantile(grad[valid], 0.95).clamp_min(0.25)
        grad = (grad / grad_scale).clamp(0, 1)
        thermal_features = torch.stack((absolute_temp, relative_temp, grad), dim=0)
        thermal_features = (thermal_features - RGB_MEAN) / RGB_STD

        rgb_tensor = torch.from_numpy(rgb.transpose(2, 0, 1))
        rgb_tensor = (rgb_tensor - RGB_MEAN) / RGB_STD
        return {
            "rgb": rgb_tensor,
            "thermal": thermal_features,
            "thermal_valid": valid,
            "mask": torch.from_numpy(labels.astype(np.int64)),
            "subject_id": rec.subject_id,
            "record_id": rec.record_id,
            "thermal_coverage": coverage,
            "temperature_median_c": float(median.item()),
            "temperature_iqr_c": float(iqr.item()),
            "heldout_tre_px": heldout_tre_px(rec),
        }


class BidirectionalGatedFusion(nn.Module):
    def __init__(self, hidden_size: int, heads: int = 12):
        super().__init__()
        self.rgb_to_thermal = nn.MultiheadAttention(hidden_size, heads, batch_first=True)
        self.thermal_to_rgb = nn.MultiheadAttention(hidden_size, heads, batch_first=True)
        self.gate = nn.Linear(hidden_size * 2, hidden_size)
        self.norm = nn.LayerNorm(hidden_size)

    def forward(self, rgb: torch.Tensor, thermal: torch.Tensor, invalid_thermal: torch.Tensor) -> torch.Tensor:
        rgb_context, _ = self.rgb_to_thermal(rgb, thermal, thermal, key_padding_mask=invalid_thermal, need_weights=False)
        thermal_context, _ = self.thermal_to_rgb(thermal, rgb, rgb, need_weights=False)
        thermal_context = thermal_context.masked_fill(invalid_thermal.unsqueeze(-1), 0)
        thermal = thermal.masked_fill(invalid_thermal.unsqueeze(-1), 0)
        gate = torch.sigmoid(self.gate(torch.cat((rgb, thermal), dim=-1)))
        gate = torch.where(invalid_thermal.unsqueeze(-1), torch.ones_like(gate), gate)
        mixed = gate * rgb_context + (1 - gate) * thermal_context
        return self.norm(gate * rgb + (1 - gate) * thermal + mixed)


class QueryMaskDecoder(nn.Module):
    """Fixed tissue queries with Mask2Former-style query-mask predictions."""
    def __init__(self, hidden_size: int, num_tissues: int = 4, decoder_dim: int = 256, layers: int = 4, heads: int = 8):
        super().__init__()
        self.feature = nn.Linear(hidden_size, decoder_dim)
        self.queries = nn.Parameter(torch.randn(num_tissues, decoder_dim) * 0.02)
        block = nn.TransformerDecoderLayer(decoder_dim, heads, decoder_dim * 4, batch_first=True, norm_first=True)
        self.decoder = nn.TransformerDecoder(block, layers, norm=nn.LayerNorm(decoder_dim))
        self.mask_embed = nn.Sequential(nn.Linear(decoder_dim, decoder_dim), nn.GELU(), nn.Linear(decoder_dim, decoder_dim))
        self.background = nn.Linear(decoder_dim, 1)
        self.num_tissues = num_tissues

    def forward(self, tokens: torch.Tensor, grid_h: int, grid_w: int, output_size: tuple[int, int], memory_padding_mask: torch.Tensor | None = None) -> torch.Tensor:
        memory = self.feature(tokens)
        query = self.queries.unsqueeze(0).expand(tokens.shape[0], -1, -1)
        query = self.decoder(query, memory, memory_key_padding_mask=memory_padding_mask)
        mask_vectors = self.mask_embed(query)
        masks = torch.einsum("bqd,bnd->bqn", mask_vectors, memory) / math.sqrt(memory.shape[-1])
        masks = masks.transpose(1, 2).reshape(tokens.shape[0], self.num_tissues, grid_h, grid_w)
        bg = self.background(memory).transpose(1, 2).reshape(tokens.shape[0], 1, grid_h, grid_w)
        logits = torch.cat((bg, masks), dim=1)
        return F.interpolate(logits, size=output_size, mode="bilinear", align_corners=False)


class DualStreamMask2Former(nn.Module):
    """DINOv2 dual-encoder + gated cross-attention + query-mask decoder.

    This is a project-specific Mask2Former-style adaptation, not the official
    single-stream Mask2Former checkpoint. Pretrained image encoders are used;
    fusion and tissue-query decoder weights are task-specific.
    """
    def __init__(self, backbone: str = "facebook/dinov2-base", mode: str = "fusion", local_files_only: bool = False):
        super().__init__()
        if mode not in {"rgb", "thermal", "fusion"}:
            raise ValueError("mode must be rgb, thermal, or fusion")
        try:
            from transformers import AutoModel
        except ImportError as exc:
            raise RuntimeError("Install requirements-medical.txt to load pretrained DINOv2 encoders") from exc
        self.rgb_encoder = AutoModel.from_pretrained(backbone, local_files_only=local_files_only)
        self.thermal_encoder = AutoModel.from_pretrained(backbone, local_files_only=local_files_only)
        self.hidden_size = int(self.rgb_encoder.config.hidden_size)
        self.patch_size = int(self.rgb_encoder.config.patch_size)
        if self.hidden_size % 12:
            raise ValueError("DINOv2 hidden size must be divisible by 12 for fusion attention")
        self.fusion = BidirectionalGatedFusion(self.hidden_size)
        self.decoder = QueryMaskDecoder(self.hidden_size)
        self.mode = mode

    def _encode(self, encoder: nn.Module, x: torch.Tensor) -> tuple[torch.Tensor, int, int]:
        out = encoder(pixel_values=x, return_dict=True)
        tokens = out.last_hidden_state
        patch_tokens = tokens[:, 1:, :]  # drop CLS; base DINOv2 has no register tokens
        gh, gw = x.shape[-2] // self.patch_size, x.shape[-1] // self.patch_size
        if patch_tokens.shape[1] != gh * gw:
            raise ValueError("DINOv2 token count does not match input patch grid")
        return patch_tokens, gh, gw

    def forward(self, rgb: torch.Tensor, thermal: torch.Tensor, thermal_valid: torch.Tensor) -> torch.Tensor:
        memory_padding_mask = None
        if self.mode == "rgb":
            fused, gh, gw = self._encode(self.rgb_encoder, rgb)
        elif self.mode == "thermal":
            fused, gh, gw = self._encode(self.thermal_encoder, thermal)
            patch_valid = F.adaptive_avg_pool2d(thermal_valid[:, None].float(), (gh, gw)).flatten(1) > 0.5
            memory_padding_mask = ~patch_valid
            if memory_padding_mask.all(dim=1).any():
                raise ValueError("thermal branch has no valid patches for at least one sample")
        else:
            rgb_tokens, gh, gw = self._encode(self.rgb_encoder, rgb)
            thermal_tokens, th, tw = self._encode(self.thermal_encoder, thermal)
            if (gh, gw) != (th, tw):
                raise ValueError("RGB and thermal encoders must use the same patch grid")
            patch_valid = F.adaptive_avg_pool2d(thermal_valid[:, None].float(), (gh, gw)).flatten(1) > 0.5
            invalid = ~patch_valid
            if invalid.all(dim=1).any():
                raise ValueError("thermal branch has no valid patches for at least one sample")
            fused = self.fusion(rgb_tokens, thermal_tokens, invalid)
        return self.decoder(fused, gh, gw, (rgb.shape[-2], rgb.shape[-1]), memory_padding_mask)


def dice_loss(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    probs = logits.softmax(1)
    valid = target != IGNORE_INDEX
    safe = target.masked_fill(~valid, 0)
    onehot = F.one_hot(safe, num_classes=len(CLASS_NAMES)).permute(0, 3, 1, 2).float()
    mask = valid[:, None].float()
    probs = probs * mask
    onehot = onehot * mask
    intersection = (probs[:, 1:] * onehot[:, 1:]).sum((0, 2, 3))
    denominator = probs[:, 1:].sum((0, 2, 3)) + onehot[:, 1:].sum((0, 2, 3))
    present = onehot[:, 1:].sum((0, 2, 3)) > 0
    if not present.any():
        return logits.new_tensor(0.0)
    score = (2 * intersection + 1e-6) / (denominator + 1e-6)
    return 1 - score[present].mean()


def batch_loss(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return F.cross_entropy(logits, target, ignore_index=IGNORE_INDEX) + dice_loss(logits, target)


def counts_per_image(logits: torch.Tensor, targets: torch.Tensor) -> np.ndarray:
    """Return per-image/per-class TP, FP, FN counts (keeps bootstrap patient-level)."""
    predictions = logits.argmax(1)
    counts = np.zeros((targets.shape[0], len(CLASS_NAMES) - 1, 3), dtype=np.int64)
    for image_i in range(targets.shape[0]):
        target = targets[image_i]
        pred_map = predictions[image_i]
        valid = target != IGNORE_INDEX
        for out_i, class_id in enumerate(range(1, len(CLASS_NAMES))):
            pred = (pred_map == class_id) & valid
            truth = (target == class_id) & valid
            counts[image_i, out_i] = (
                int((pred & truth).sum().item()),
                int((pred & ~truth & valid).sum().item()),
                int((~pred & truth & valid).sum().item()),
            )
    return counts


def metrics_from_counts(counts: np.ndarray) -> dict[str, Any]:
    total = counts.sum(axis=0)
    result: dict[str, Any] = {}
    dice_values = []
    for out_i, name in enumerate(CLASS_NAMES[1:]):
        tp, fp, fn = (int(v) for v in total[out_i])
        denom = 2 * tp + fp + fn
        dice = 2 * tp / denom if denom else None
        result[name] = {
            "dice": dice,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "support_pixels": tp + fn,
        }
        if dice is not None:
            dice_values.append(dice)
    result["macro_dice_present_classes"] = float(np.mean(dice_values)) if dice_values else None
    return result


def bootstrap_subject_ci(subject_counts: dict[str, list[np.ndarray]], seed: int, replicates: int = 1000) -> dict[str, Any]:
    """Cluster bootstrap subjects, preserving repeated scans within a person."""
    subjects = sorted(subject_counts)
    if len(subjects) < 2:
        return {"replicates": replicates, "subjects": len(subjects), "intervals": None}
    rng = np.random.default_rng(seed)
    by_subject = {sid: np.stack(rows).sum(axis=0) for sid, rows in subject_counts.items()}
    samples: dict[str, list[float]] = {name: [] for name in (*CLASS_NAMES[1:], "macro_dice_present_classes")}
    for _ in range(replicates):
        draw = rng.choice(subjects, size=len(subjects), replace=True)
        counts = np.stack([by_subject[str(sid)] for sid in draw]).sum(axis=0)
        metrics = metrics_from_counts(counts[None, ...])
        for name in samples:
            value = metrics[name]["dice"] if name in CLASS_NAMES[1:] else metrics[name]
            if value is not None:
                samples[name].append(float(value))
    intervals = {
        name: [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))] if values else None
        for name, values in samples.items()
    }
    return {"replicates": replicates, "subjects": len(subjects), "intervals_95_percent": intervals}


def add_counts_by_subject(target: dict[str, list[np.ndarray]], subject_ids: list[str], counts: np.ndarray) -> None:
    for subject_id, image_counts in zip(subject_ids, counts, strict=True):
        target.setdefault(subject_id, []).append(image_counts)


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    result = {key: torch.stack([sample[key] for sample in batch]) for key in ("rgb", "thermal", "thermal_valid", "mask")}
    for key in ("subject_id", "record_id", "thermal_coverage", "temperature_median_c", "temperature_iqr_c", "heldout_tre_px"):
        result[key] = [sample[key] for sample in batch]
    return result


def run_training(args: argparse.Namespace) -> Path:
    records, _ = load_manifest(args.manifest, require_access=True)
    manifest_metadata = json.loads(args.manifest.read_text(encoding="utf-8"))
    by_split = {split: [r for r in records if r.split == split] for split in ("train", "val", "test")}
    test_tre = [heldout_tre_px(r) for r in by_split["test"]]
    test_tre = [value for value in test_tre if value is not None]
    if not test_tre:
        raise ValueError("training blocked: test split needs held-out RGB/thermal landmarks to verify registration")
    mean_tre = float(np.mean(test_tre))
    if args.max_heldout_tre_px is not None and mean_tre > args.max_heldout_tre_px:
        raise ValueError(f"training blocked: mean held-out TRE {mean_tre:.3f}px exceeds limit {args.max_heldout_tre_px:.3f}px")
    datasets = {split: WoundPairs(rows, args.image_size, args.min_thermal_coverage) for split, rows in by_split.items()}
    loaders = {
        split: DataLoader(ds, batch_size=args.batch_size, shuffle=(split == "train"), num_workers=args.workers, collate_fn=collate)
        for split, ds in datasets.items()
    }
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    results: dict[str, Any] = {
        "dataset_id": args.dataset_id,
        "dataset_source": manifest_metadata.get("source"),
        "access_terms_ref": manifest_metadata.get("access_terms_ref"),
        "thermal_conversion_methods": sorted({r.thermal_conversion_method for r in records}),
        "pairing_bases": sorted({r.pairing_basis for r in records}),
        "model": "DualStreamMask2Former(DINOv2-base, gated bidirectional cross-attention, 4 tissue queries)",
        "pretrained_backbone": args.backbone,
        "mode": args.mode,
        "test_mean_heldout_tre_px": mean_tre,
        "class_names": CLASS_NAMES,
        "split_subject_counts": {s: len({r.subject_id for r in by_split[s]}) for s in by_split},
        "image_size": args.image_size,
        "seed": args.seed,
        "device": str(device),
        "runs": [],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model = DualStreamMask2Former(args.backbone, args.mode, args.local_files_only).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.05)
    best_val = -1.0
    best_path = args.output_dir / f"post_tka_{args.mode}_best.pt"
    history = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for batch in loaders["train"]:
            rgb, thermal = batch["rgb"].to(device), batch["thermal"].to(device)
            valid, mask = batch["thermal_valid"].to(device), batch["mask"].to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(rgb, thermal, valid)
            loss = batch_loss(logits, mask)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss.detach().item()))
        model.eval()
        val_subject_counts: dict[str, list[np.ndarray]] = {}
        with torch.inference_mode():
            for batch in loaders["val"]:
                logits = model(batch["rgb"].to(device), batch["thermal"].to(device), batch["thermal_valid"].to(device)).cpu()
                add_counts_by_subject(val_subject_counts, batch["subject_id"], counts_per_image(logits, batch["mask"]))
        metrics = metrics_from_counts(np.stack([np.stack(rows).sum(axis=0) for rows in val_subject_counts.values()]))
        score = metrics["macro_dice_present_classes"]
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "validation": metrics})
        print(f"{args.mode} epoch {epoch}/{args.epochs}: loss={np.mean(losses):.4f}, val_macro_dice={score}", flush=True)
        if score is not None and score > best_val:
            best_val = score
            torch.save({
                "state_dict": model.state_dict(),
                "model": "DualStreamMask2Former",
                "backbone": args.backbone,
                "mode": args.mode,
                "image_size": args.image_size,
                "class_names": list(CLASS_NAMES),
            }, best_path)
    if best_val < 0:
        raise RuntimeError("validation split contained no positive tissue pixels; checkpoint not selected")

    model.load_state_dict(torch.load(best_path, map_location=device, weights_only=True)["state_dict"])
    model.eval()
    test_subject_counts: dict[str, list[np.ndarray]] = {}
    with torch.inference_mode():
        for batch in loaders["test"]:
            logits = model(batch["rgb"].to(device), batch["thermal"].to(device), batch["thermal_valid"].to(device)).cpu()
            add_counts_by_subject(test_subject_counts, batch["subject_id"], counts_per_image(logits, batch["mask"]))
    aggregate_test_counts = np.stack([np.stack(rows).sum(axis=0) for rows in test_subject_counts.values()])
    results["history"] = history
    results["selected_validation_macro_dice"] = best_val
    results["test_metrics"] = metrics_from_counts(aggregate_test_counts)
    results["test_patient_bootstrap_ci"] = bootstrap_subject_ci(test_subject_counts, args.seed + 1)
    tre_values = [heldout_tre_px(r) for r in by_split["test"]]
    tre_values = [value for value in tre_values if value is not None]
    results["registration_test_summary_px"] = {
        "records_with_heldout_landmarks": len(tre_values),
        "mean": float(np.mean(tre_values)),
        "median": float(np.median(tre_values)),
        "p95": float(np.quantile(tre_values, 0.95)),
    }
    results["clinical_interpretation"] = "Research localization only; no diagnostic or clinical-use claim."
    results_path = args.output_dir / f"post_tka_{args.mode}_metrics.json"
    results_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    return results_path


def validate_manifest(args: argparse.Namespace) -> int:
    records, class_ids = load_manifest(args.manifest)
    sizes = {split: sum(r.split == split for r in records) for split in ("train", "val", "test")}
    tre = [heldout_tre_px(r) for r in records]
    sample_set = WoundPairs(records, args.image_size, args.min_thermal_coverage)
    coverage: list[float] = []
    class_pixels = np.zeros(len(CLASS_NAMES), dtype=np.int64)
    for index in range(len(sample_set)):
        sample = sample_set[index]
        coverage.append(sample["thermal_coverage"])
        ids, counts = np.unique(sample["mask"].numpy(), return_counts=True)
        for label_id, count in zip(ids.tolist(), counts.tolist(), strict=True):
            if label_id != IGNORE_INDEX:
                class_pixels[label_id] += count
    payload = {
        "dataset_id": args.dataset_id,
        "records": len(records),
        "split_record_counts": sizes,
        "split_subject_counts": {s: len({r.subject_id for r in records if r.split == s}) for s in sizes},
        "class_ids": class_ids,
        "heldout_landmark_record_count": sum(v is not None for v in tre),
        "mean_heldout_tre_px": float(np.mean([v for v in tre if v is not None])) if any(v is not None for v in tre) else None,
        "mean_mapped_thermal_coverage": float(np.mean(coverage)),
        "mask_pixel_counts": {name: int(class_pixels[idx]) for idx, name in enumerate(CLASS_NAMES)},
        "status": "files, mask IDs and registered thermal coverage inspected; clinical labels and access terms still require human review",
    }
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="dataset manifest JSON; data files stay outside Git")
    parser.add_argument("--dataset-id", default="post_tka_wound_masks")
    parser.add_argument("--validate-only", action="store_true", help="validate files, pairing geometry and patient-disjoint splits")
    parser.add_argument("--mode", choices=("all", "rgb", "thermal", "fusion"), default="all")
    parser.add_argument("--backbone", default="facebook/dinov2-base", help="pretrained vision encoder checkpoint")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--image-size", type=int, default=518)
    parser.add_argument("--min-thermal-coverage", type=float, default=0.10)
    parser.add_argument("--max-heldout-tre-px", type=float, default=None, help="optional maximum mean TRE on held-out RGB landmarks")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--seed", type=int, default=20261113)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "post_tka_wound")
    parser.add_argument("--cpu", action="store_true", help="force CPU; full training is not recommended on CPU")
    args = parser.parse_args()
    if not 0 <= args.min_thermal_coverage <= 1:
        parser.error("--min-thermal-coverage must be in [0, 1]")
    if args.validate_only:
        return validate_manifest(args)
    modes = ("rgb", "thermal", "fusion") if args.mode == "all" else (args.mode,)
    for mode in modes:
        args.mode = mode
        path = run_training(args)
        print(f"Metrics written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
