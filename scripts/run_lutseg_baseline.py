"""Desktop inference viewer for the trained LUTSeg RGB wound baseline."""
from __future__ import annotations

import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageTk
import torch
from transformers import Dinov2Config, Dinov2Model

from train_lutseg_transformer import (CLASSES, DATA, DINOv2DenseSegmenter,
                                      MEAN, STD, letterbox, read_split)
from build_review_demo import read_temp_csv, temp_heatmap

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/"outputs"/"lutseg_transformer_baseline"
CKPT=RUN/"best_model.pt"
REPORT=RUN/"training_report.json"
COLORS=[(25,30,38),(41,220,170),(255,190,65),(80,200,255),(245,95,120),(195,145,255)]


def colorize(labels: Image.Image) -> Image.Image:
    values=np.asarray(labels,dtype=np.uint8)
    out=np.zeros((*values.shape,3),dtype=np.uint8)
    for i,c in enumerate(COLORS): out[values==i]=c
    out[values==255]=(60,60,60)
    return Image.fromarray(out,"RGB")


class Viewer:
    def __init__(self, root, model, device, report):
        self.root,self.model,self.device,self.report=root,model,device,report
        self.items=read_split(DATA/"val.txt")
        self.root.title("LUTSeg Wound Tissue Baseline · RGB-only")
        self.root.geometry("1420x790")
        self.root.configure(bg="#101827")
        header=tk.Frame(root,bg="#101827");header.pack(fill="x",padx=18,pady=(15,8))
        tk.Label(header,text="Wound tissue segmentation baseline",font=("Segoe UI",22,"bold"),fg="#eef4ff",bg="#101827").pack(anchor="w")
        tk.Label(header,text="RGB-only · pretrained DINOv2-small + dense Transformer decoder · LUTSeg",font=("Segoe UI",11),fg="#a8bad1",bg="#101827").pack(anchor="w",pady=3)
        bar=tk.Frame(root,bg="#101827");bar.pack(fill="x",padx=18,pady=7)
        self.choice=tk.StringVar()
        self.combo=ttk.Combobox(bar,textvariable=self.choice,state="readonly",width=48,values=[a for a,_ in self.items])
        self.combo.pack(side="left",padx=(0,8)); self.combo.bind("<<ComboboxSelected>>",self.on_select)
        ttk.Button(bar,text="Load selected validation sample",command=self.load_selected).pack(side="left",padx=5)
        ttk.Button(bar,text="Open an RGB wound image…",command=self.open_image).pack(side="left",padx=5)
        ttk.Button(bar,text="Show paired RGB–thermal sample…",command=self.open_thermal).pack(side="left",padx=5)
        self.status=tk.Label(bar,text=f"Best validation mIoU: {report['best_validation_metrics']['mean_iou_present_classes']:.3f} · best epoch {report['best_epoch']}",font=("Segoe UI",10,"bold"),fg="#7ee3bd",bg="#101827")
        self.status.pack(side="right")
        panels=tk.Frame(root,bg="#101827");panels.pack(fill="both",expand=True,padx=18,pady=10)
        self.labels=["RGB input","Model prediction","Clinician mask (reference)"]
        self.images=[]
        for i,title in enumerate(self.labels):
            card=tk.Frame(panels,bg="#19263a",highlightbackground="#344761",highlightthickness=1)
            card.grid(row=0,column=i,sticky="nsew",padx=6)
            panels.grid_columnconfigure(i,weight=1);panels.grid_rowconfigure(0,weight=1)
            tk.Label(card,text=title,font=("Segoe UI",14,"bold"),fg="#eff5ff",bg="#19263a").pack(pady=10)
            holder=tk.Label(card,bg="#0b111b");holder.pack(fill="both",expand=True,padx=8,pady=6)
            self.images.append(holder)
        footer=tk.Frame(root,bg="#101827");footer.pack(fill="x",padx=18,pady=(0,14))
        self.metrics=tk.Label(footer,text="Choose an official validation image or open an image for prediction.",justify="left",wraplength=1300,font=("Segoe UI",10),fg="#cfdaea",bg="#101827")
        self.metrics.pack(anchor="w")
        legend=tk.Label(footer,text="Classes: 1 epithelial · 2 slough · 3 granulation · 4 necrotic · 5 other. Predictions are research outputs, not diagnoses.",font=("Segoe UI",9),fg="#a8bad1",bg="#101827")
        legend.pack(anchor="w",pady=(8,0))
        if self.items:
            self.combo.current(0);self.load_selected()

    def on_select(self,_): self.load_selected()

    def load_selected(self):
        idx=self.combo.current()
        if idx<0:return
        image_path,mask_path=self.items[idx]
        self.run_image(DATA/image_path,DATA/mask_path)

    def open_image(self):
        path=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.tif *.tiff")])
        if path:self.run_image(Path(path),None)

    def open_thermal(self):
        manifest=json.loads((ROOT/"datasets"/"tricvi_c"/"manifest.json").read_text(encoding="utf-8"))
        grouped={}
        import re
        for item in manifest["files"]:
            match=re.search(r"FLIR\d+",item["filename"])
            if match: grouped.setdefault(match.group(),[]).append(item)
        sample=next((items for items in grouped.values()
                     if sum(x["filename"].lower().endswith(".jpg") for x in items)==2
                     and sum(x["filename"].lower().endswith(".csv") for x in items)==1),None)
        if not sample:
            messagebox.showerror("Dataset unavailable","No RGB/thermal/Celsius sample triplet was found.");return
        from PIL import Image as PILImage
        imgs=[(x,PILImage.open(ROOT/"datasets"/"tricvi_c"/x["path"]).convert("RGB"))
              for x in sample if x["filename"].lower().endswith(".jpg")]
        rgb_item,rgb=max(imgs,key=lambda pair:pair[1].width*pair[1].height)
        ir_item,ir=min(imgs,key=lambda pair:pair[1].width*pair[1].height)
        csv_item=next(x for x in sample if x["filename"].lower().endswith(".csv"))
        grid=read_temp_csv(ROOT/"datasets"/"tricvi_c"/csv_item["path"]);heat,stats=temp_heatmap(grid)
        overlay=PILImage.blend(rgb,heat.resize(rgb.size,PILImage.Resampling.BILINEAR),0.43)
        window=tk.Toplevel(self.root);window.title("TRICVI-C · paired RGB / thermal / Celsius");window.geometry("1320x720");window.configure(bg="#101827")
        tk.Label(window,text=f"TRICVI-C · capture {rgb_item['filename']} · source-linked modalities",font=("Segoe UI",18,"bold"),fg="#eef4ff",bg="#101827").pack(anchor="w",padx=18,pady=12)
        row=tk.Frame(window,bg="#101827");row.pack(fill="both",expand=True,padx=12)
        self.thermal_photos=[]
        for title,img in [("RGB",rgb),("Thermal camera display",ir),("Celsius grid",heat),("Scale-only overlay",overlay)]:
            card=tk.Frame(row,bg="#19263a",highlightbackground="#344761",highlightthickness=1);card.pack(side="left",fill="both",expand=True,padx=5)
            tk.Label(card,text=title,font=("Segoe UI",12,"bold"),fg="#eff5ff",bg="#19263a").pack(pady=8)
            img=img.copy();img.thumbnail((300,490),PILImage.Resampling.LANCZOS);photo=ImageTk.PhotoImage(img);self.thermal_photos.append(photo)
            tk.Label(card,image=photo,bg="#0b111b").pack(fill="both",expand=True,padx=6,pady=6)
        text=(f"Temperature: min {stats['min']:.2f} °C · mean {stats['mean']:.2f} °C · max {stats['max']:.2f} °C · grid {len(grid[0])}×{len(grid)}.  "
              "RGB/thermal records share the FLIR capture ID. The overlay is resized for display only; landmark-based registration is not validated. This dataset has no wound masks, and it is not paired with LUTSeg.")
        tk.Label(window,text=text,wraplength=1270,justify="left",font=("Segoe UI",10),fg="#ffd596",bg="#101827").pack(anchor="w",padx=18,pady=12)

    @torch.inference_mode()
    def run_image(self,image_path,mask_path):
        try:
            raw=ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
            boxed,_,(left,top,nw,nh)=letterbox(raw,Image.new("L",raw.size,0),self.report["image_size"])
            x=torch.from_numpy(np.asarray(boxed,dtype=np.float32).copy()).permute(2,0,1)/255.0
            x=((x-MEAN)/STD).unsqueeze(0).to(self.device)
            logits=self.model(x)[0].cpu()
            pred=logits.argmax(0).numpy().astype(np.uint8)
            pred_img=Image.fromarray(pred).crop((left,top,left+nw,top+nh)).resize(raw.size,Image.Resampling.NEAREST)
            mask_img=None
            if mask_path and Path(mask_path).is_file(): mask_img=Image.open(mask_path).convert("L").resize(raw.size,Image.Resampling.NEAREST)
            overlay=Image.blend(raw,colorize(pred_img),0.48)
            views=[raw,overlay,colorize(mask_img) if mask_img else Image.new("RGB",raw.size,(25,30,38))]
            if mask_img:
                rows=[]
                p=np.asarray(pred_img);g=np.asarray(mask_img)
                valid=g!=255
                for cid in range(1,len(CLASSES)):
                    a=(p==cid)&valid;b=(g==cid)&valid
                    union=np.logical_or(a,b).sum()
                    if b.sum(): rows.append(f"{CLASSES[cid]} Dice {2*np.logical_and(a,b).sum()/(a.sum()+b.sum()+1e-9):.2f}")
                self.metrics.config(text="Sample-level comparison against this clinician mask: " + (" · ".join(rows) if rows else "no foreground class in reference"))
            else:
                self.metrics.config(text="No reference mask supplied for this image. Showing model prediction only; no accuracy score is available for it.")
            for slot,im in zip(self.images,views):
                im.thumbnail((390,440),Image.Resampling.LANCZOS)
                photo=ImageTk.PhotoImage(im.copy());slot.config(image=photo);slot.image=photo
            self.status.config(text=f"Image {raw.width}×{raw.height} · RGB-only prediction")
        except Exception as exc:
            messagebox.showerror("Inference failed",str(exc))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint",type=Path,default=CKPT)
    args=parser.parse_args()
    if not args.checkpoint.exists(): raise SystemExit(f"Checkpoint not found: {args.checkpoint}. Train first with scripts/train_lutseg_transformer.py")
    checkpoint=torch.load(args.checkpoint,map_location="cpu",weights_only=False)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    backbone=Dinov2Model(Dinov2Config.from_dict(checkpoint["backbone_config"]))
    model=DINOv2DenseSegmenter(backbone);model.load_state_dict(checkpoint["state_dict"]);model.to(device).eval()
    report=json.loads(REPORT.read_text(encoding="utf-8"))
    root=tk.Tk();Viewer(root,model,device,report);root.mainloop()


if __name__=="__main__":main()
