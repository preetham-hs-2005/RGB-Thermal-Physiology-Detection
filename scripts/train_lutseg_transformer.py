"""Train a patient-split RGB wound tissue transformer baseline on LUTSeg.

Uses the Apache-2.0 DINOv2-small visual encoder as a frozen feature extractor
and trains a dense transformer segmentation decoder on LUTSeg masks. This is an
RGB-only baseline; it does not use TRICVI-C or claim thermal fusion.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import Dinov2Model

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "lutseg"
OUTPUT = ROOT / "outputs" / "lutseg_transformer_baseline"
SIZE = 224
MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
CLASSES = ["Background", "Epithelial", "Slough", "Granulation", "Necrotic", "Other"]


def read_split(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        a, b = line.split()
        rows.append((a, b))
    return rows


def letterbox(image: Image.Image, mask: Image.Image, size: int) -> tuple[Image.Image, Image.Image, tuple[int,int,int,int]]:
    image = ImageOps.exif_transpose(image).convert("RGB")
    mask = mask.convert("L")
    scale = min(size / image.width, size / image.height)
    nw, nh = max(1, round(image.width * scale)), max(1, round(image.height * scale))
    image = image.resize((nw, nh), Image.Resampling.BILINEAR)
    mask = mask.resize((nw, nh), Image.Resampling.NEAREST)
    left, top = (size - nw) // 2, (size - nh) // 2
    canvas = Image.new("RGB", (size, size), (0, 0, 0))
    labels = Image.new("L", (size, size), 255)
    canvas.paste(image, (left, top))
    labels.paste(mask, (left, top))
    return canvas, labels, (left, top, nw, nh)


class LUTSegDataset(Dataset):
    def __init__(self, rows: list[tuple[str,str]], train: bool):
        self.rows, self.train = rows, train

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        ip, mp = (DATA / p for p in self.rows[index])
        image, mask, _ = letterbox(Image.open(ip), Image.open(mp), SIZE)
        if self.train and random.random() < 0.5:
            image, mask = ImageOps.mirror(image), ImageOps.mirror(mask)
        if self.train:
            image = ImageEnhance.Brightness(image).enhance(random.uniform(0.9, 1.1))
            image = ImageEnhance.Contrast(image).enhance(random.uniform(0.9, 1.1))
        x = torch.from_numpy(np.asarray(image, dtype=np.float32).copy()).permute(2,0,1) / 255.0
        x = (x - MEAN) / STD
        y = torch.from_numpy(np.asarray(mask, dtype=np.uint8).copy()).long()
        return x, y


class DINOv2DenseSegmenter(nn.Module):
    def __init__(self, backbone: Dinov2Model, hidden: int = 192):
        super().__init__()
        self.backbone = backbone
        self.project = nn.Linear(backbone.config.hidden_size, hidden)
        layer = nn.TransformerEncoderLayer(d_model=hidden, nhead=6, dim_feedforward=hidden*4,
                                           dropout=0.1, batch_first=True, norm_first=True,
                                           activation="gelu")
        self.decoder = nn.TransformerEncoder(layer, num_layers=2, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(hidden)
        self.classifier = nn.Linear(hidden, len(CLASSES))
        for parameter in self.backbone.parameters():
            parameter.requires_grad = False

    def forward(self, x):
        with torch.no_grad():
            features = self.backbone(pixel_values=x, interpolate_pos_encoding=True).last_hidden_state[:, 1:]
        b, n, _ = features.shape
        side = int(n ** 0.5)
        features = self.project(features)
        # DINOv2 supplies patch tokens; the Transformer decoder models their
        # spatial context before dense tissue classification.
        features = self.decoder(features)
        logits = self.classifier(self.norm(features)).transpose(1,2).reshape(b, len(CLASSES), side, side)
        return F.interpolate(logits, size=x.shape[-2:], mode="bilinear", align_corners=False)


def class_weights(rows):
    counts = np.zeros(len(CLASSES), dtype=np.int64)
    for _, mp in rows:
        mask = Image.open(DATA / mp).convert("L")
        arr = np.asarray(mask)
        for cid in range(len(CLASSES)):
            counts[cid] += int((arr == cid).sum())
    freq = counts / max(1, counts.sum())
    weights = np.where(freq > 0, 1.0 / np.sqrt(np.maximum(freq, 1e-8)), 0)
    weights = weights / max(weights[freq > 0].mean(), 1e-8)
    weights = np.clip(weights, 0.5, 4.0)
    return torch.tensor(weights, dtype=torch.float32), counts.tolist()


def loss_fn(logits, target, weights):
    ce = F.cross_entropy(logits, target, weight=weights, ignore_index=255)
    probs = logits.softmax(1)
    valid = target != 255
    onehot = F.one_hot(target.clamp(0, len(CLASSES)-1), len(CLASSES)).permute(0,3,1,2).float()
    onehot *= valid.unsqueeze(1)
    probs = probs * valid.unsqueeze(1)
    dims = (0,2,3)
    intersection = (probs * onehot).sum(dims)
    denom = probs.sum(dims) + onehot.sum(dims)
    present = onehot.sum(dims) > 0
    dice = 1 - ((2 * intersection + 1) / (denom + 1))[present].mean()
    return ce + 0.5 * dice


@torch.no_grad()
def evaluate(model, loader, device):
    confusion = torch.zeros((len(CLASSES),len(CLASSES)),dtype=torch.int64)
    model.eval()
    for x,y in loader:
        pred=model(x.to(device)).argmax(1).cpu()
        valid=y != 255
        encoded=y[valid]*len(CLASSES)+pred[valid]
        confusion += torch.bincount(encoded,minlength=len(CLASSES)**2).reshape(len(CLASSES),len(CLASSES))
    diag=confusion.diag().double(); union=confusion.sum(0)+confusion.sum(1)-diag
    iou=(diag/union.clamp_min(1)).tolist(); dice=(2*diag/(confusion.sum(0)+confusion.sum(1)).clamp_min(1)).tolist()
    present=[i for i in range(len(CLASSES)) if confusion[i].sum()>0 or confusion[:,i].sum()>0]
    return {"per_class_iou":dict(zip(CLASSES,iou)),"per_class_dice":dict(zip(CLASSES,dice)),
            "mean_iou_present_classes":float(np.mean([iou[i] for i in present])),
            "mean_dice_present_classes":float(np.mean([dice[i] for i in present])),
            "confusion_matrix":confusion.tolist(),"evaluated_classes":[CLASSES[i] for i in present]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs",type=int,default=8)
    parser.add_argument("--batch-size",type=int,default=4)
    parser.add_argument("--image-size",type=int,default=224)
    parser.add_argument("--seed",type=int,default=20261113)
    parser.add_argument("--threads",type=int,default=4)
    parser.add_argument("--backbone",default="facebook/dinov2-small")
    args=parser.parse_args()
    global SIZE
    if args.image_size % 14: parser.error("--image-size must be divisible by DINOv2's patch size (14)")
    SIZE=args.image_size
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_rows=read_split(DATA/"train.txt"); val_rows=read_split(DATA/"val.txt")
    backbone=Dinov2Model.from_pretrained(args.backbone)
    model=DINOv2DenseSegmenter(backbone).to(device)
    train_ds=LUTSegDataset(train_rows,True); val_ds=LUTSegDataset(val_rows,False)
    generator=torch.Generator().manual_seed(args.seed)
    train_loader=DataLoader(train_ds,batch_size=args.batch_size,shuffle=True,num_workers=0,generator=generator)
    val_loader=DataLoader(val_ds,batch_size=args.batch_size,shuffle=False,num_workers=0)
    weights,counts=class_weights(train_rows); weights=weights.to(device)
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=3e-4,weight_decay=0.02)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    best=-1; history=[]; start=time.time()
    for epoch in range(1,args.epochs+1):
        model.train(); running=0.0
        for x,y in train_loader:
            x=x.to(device); y=y.to(device); optimizer.zero_grad(set_to_none=True)
            logits=model(x); loss=loss_fn(logits,y,weights); loss.backward()
            nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
            optimizer.step(); running+=float(loss.detach())
        metrics=evaluate(model,val_loader,device)
        record={"epoch":epoch,"train_loss":running/max(1,len(train_loader)),**metrics}
        history.append(record)
        print(json.dumps({"epoch":epoch,"train_loss":record['train_loss'],"val_mIoU":metrics['mean_iou_present_classes'],"val_mDice":metrics['mean_dice_present_classes']}),flush=True)
        if metrics["mean_iou_present_classes"]>best:
            best=metrics["mean_iou_present_classes"]
            torch.save({"state_dict":model.state_dict(),"backbone":args.backbone,
                        "backbone_config":model.backbone.config.to_dict(),"classes":CLASSES,
                        "image_size":SIZE,"patch_size":14,"hidden_dim":192,"seed":args.seed,
                        "epoch":epoch,"val_metrics":metrics},OUTPUT/"best_model.pt")
    report={"task":"RGB-only LUTSeg six-class wound tissue segmentation","architecture":"frozen pretrained DINOv2-small + 2-layer dense Transformer decoder + per-patch tissue classifier",
            "backbone":args.backbone,"backbone_license":"Apache-2.0 per model card","dataset":"LUTSeg, CC BY 4.0",
            "split":{"train_images":len(train_rows),"validation_images":len(val_rows),"patient_disjoint":True,"test_split":"not provided by dataset"},
            "epochs":args.epochs,"seed":args.seed,"image_size":SIZE,"device":str(device),"class_pixel_counts_train":dict(zip(CLASSES,counts)),
            "best_epoch":max(history,key=lambda x:x['mean_iou_present_classes'])['epoch'],"best_validation_metrics":max(history,key=lambda x:x['mean_iou_present_classes']),
            "history":history,"elapsed_seconds":round(time.time()-start,1),
            "limitations":["Validation set was used for checkpoint selection; results are not an independent test estimate.","No thermal modality is present in LUTSeg.","Dataset is small and domain-specific; do not infer clinical utility or generalization."]}
    (OUTPUT/"training_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"Saved {OUTPUT/'best_model.pt'} and {OUTPUT/'training_report.json'}",flush=True)


if __name__=="__main__": main()
