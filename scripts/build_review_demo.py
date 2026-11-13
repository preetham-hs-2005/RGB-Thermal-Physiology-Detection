"""Build an offline, evidence-labelled review demo from local research data.

The page intentionally distinguishes measured/annotated source data from model
predictions. It embeds only one sample from each source and writes to outputs/.
"""
from __future__ import annotations

import base64
import csv
import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "baseline_review_demo"
TRICVI = ROOT / "datasets" / "tricvi_c"
LUTSEG = ROOT / "datasets" / "lutseg"


def b64_image(image: Image.Image, fmt: str = "PNG") -> str:
    from io import BytesIO
    stream = BytesIO()
    image.save(stream, format=fmt, optimize=True)
    return "data:image/" + fmt.lower() + ";base64," + base64.b64encode(stream.getvalue()).decode("ascii")


def read_temp_csv(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        for row in csv.reader(f):
            vals = []
            for cell in row:
                try:
                    vals.append(float(cell.strip().replace(",", ".")))
                except (ValueError, AttributeError):
                    continue
            if len(vals) >= 100:
                rows.append(vals)
    if not rows:
        raise ValueError(f"No numeric temperature grid found in {path}")
    width = min(map(len, rows))
    grid = [r[:width] for r in rows]
    if len(grid) < 100 or width < 100:
        raise ValueError(f"Unexpected temperature grid shape {len(grid)}x{width}")
    return grid


def temp_heatmap(grid: list[list[float]]) -> tuple[Image.Image, dict[str, float]]:
    flat = [v for row in grid for v in row]
    lo, hi = min(flat), max(flat)
    w, h = len(grid[0]), len(grid)
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            t = 0.0 if hi == lo else (value - lo) / (hi - lo)
            # Compact blue-cyan-yellow-red palette for temperature display.
            r = max(0, min(255, int(255 * max(0.0, min(1.0, 1.5 * t - 0.25)))))
            g = max(0, min(255, int(255 * max(0.0, 1.0 - abs(2.0 * t - 1.0)))))
            b = max(0, min(255, int(255 * max(0.0, min(1.0, 1.0 - 1.5 * t)))))
            px[x, y] = (r, g, b)
    return im, {"min": lo, "max": hi, "mean": sum(flat) / len(flat), "pixels": float(len(flat))}


def lutseg_sample() -> tuple[Image.Image, Image.Image, Image.Image, str]:
    # Choose the first image/mask pair listed in the publisher's validation split.
    names = (LUTSEG / "val.txt").read_text(encoding="utf-8").splitlines()
    image_path = None
    for line in names:
        candidate = line.strip().split()[0] if line.strip() else ""
        if candidate:
            p = LUTSEG / candidate
            if p.is_file() and "Images" in p.parts:
                image_path = p
                break
            # Some releases list the patient-relative image name only.
            matches = list((LUTSEG / "Images").rglob(Path(candidate).name))
            if matches:
                image_path = matches[0]
                break
    if image_path is None:
        image_path = sorted((LUTSEG / "Images").rglob("*.jpg"))[0]
    rel = image_path.relative_to(LUTSEG / "Images")
    mask_path = LUTSEG / "Masks" / rel.with_suffix(".png")
    if not mask_path.is_file():
        mask_path = next((LUTSEG / "Masks").rglob(rel.stem + ".png"), None)
    if mask_path is None or not mask_path.is_file():
        raise FileNotFoundError(f"No source tissue mask for {image_path}")
    rgb = Image.open(image_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")
    mask = mask.resize(rgb.size, Image.Resampling.NEAREST)
    colors = {1: (42, 220, 170), 2: (255, 190, 65), 3: (80, 200, 255), 4: (245, 95, 120), 5: (195, 145, 255)}
    overlay = rgb.copy()
    over_px, mask_px = overlay.load(), mask.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            color = colors.get(mask_px[x, y])
            if color:
                original = over_px[x, y]
                over_px[x, y] = tuple(int(0.58 * a + 0.42 * b) for a, b in zip(original, color))
    return rgb, mask, overlay, str(rel).replace("\\", "/")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((TRICVI / "manifest.json").read_text(encoding="utf-8"))
    by_id: dict[str, list[dict]] = {}
    for item in manifest["files"]:
        match = re.search(r"FLIR\d+", item["filename"])
        if match:
            by_id.setdefault(match.group(), []).append(item)
    sample_id = next((k for k, group in by_id.items()
                      if len([x for x in group if x["filename"].lower().endswith(".jpg")]) == 2
                      and len([x for x in group if x["filename"].lower().endswith(".csv")]) == 1), None)
    if not sample_id:
        raise RuntimeError("No complete RGB/thermal/CSV triplet found in verified TRICVI-C manifest")
    group = by_id[sample_id]
    jpgs = [x for x in group if x["filename"].lower().endswith(".jpg")]
    csv_item = next(x for x in group if x["filename"].lower().endswith(".csv"))
    source_images = [(x, Image.open(TRICVI / x["path"]).convert("RGB")) for x in jpgs]
    rgb_item, rgb = max(source_images, key=lambda pair: pair[1].width * pair[1].height)
    thermal_item, thermal_display = min(source_images, key=lambda pair: pair[1].width * pair[1].height)
    grid = read_temp_csv(TRICVI / csv_item["path"])
    heat, stats = temp_heatmap(grid)
    # Resize the display and numeric grids to the RGB size for a review overlay.
    heat_rgbsize = heat.resize(rgb.size, Image.Resampling.BILINEAR)
    overlay = Image.blend(rgb, heat_rgbsize, 0.43)
    lrgb, lmask, loverlay, lut_name = lutseg_sample()
    lut_rgb64 = b64_image(lrgb)
    lut_mask64 = b64_image(lmask)
    lut_overlay64 = b64_image(loverlay)
    values = {
        "id": sample_id,
        "rgb": b64_image(rgb),
        "thermal": b64_image(thermal_display),
        "heat": b64_image(heat),
        "overlay": b64_image(overlay),
        "source_rgb_shape": f"{rgb.width} × {rgb.height}",
        "source_thermal_shape": f"{thermal_display.width} × {thermal_display.height}",
        "grid_shape": f"{len(grid[0])} × {len(grid)}",
        "stats": stats,
        "rgb_name": rgb_item["filename"],
        "thermal_name": thermal_item["filename"],
        "temp_name": csv_item["filename"],
        "lut_image": lut_rgb64,
        "lut_mask": lut_mask64,
        "lut_overlay": lut_overlay64,
        "lut_name": lut_name,
    }
    data = json.dumps(values, separators=(",", ":"))
    page = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RGB–Thermal Physiology | Baseline Demonstrator</title>
<style>
:root{--bg:#0b1220;--panel:#121d30;--panel2:#17253a;--line:#2b3a52;--text:#eff5ff;--muted:#9aabc2;--cyan:#52d6e8;--green:#59d6a7;--amber:#ffbf69;--pink:#fa8b99}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% -20%,#1c4560 0,transparent 42%),var(--bg);color:var(--text);font:15px/1.48 Segoe UI,Inter,system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:34px 28px 58px}.eyebrow{letter-spacing:.14em;text-transform:uppercase;color:var(--cyan);font-size:12px;font-weight:700}.hero{display:grid;grid-template-columns:1.5fr .8fr;gap:28px;align-items:center;margin:12px 0 24px}h1{font-size:clamp(34px,5vw,58px);letter-spacing:-.04em;line-height:1.02;margin:12px 0}h2{margin:0;font-size:21px;letter-spacing:-.02em}h3{font-size:15px;margin:0 0 10px}.sub{max-width:750px;color:var(--muted);font-size:17px}.badge{display:inline-flex;align-items:center;gap:8px;padding:9px 12px;border:1px solid #6c4e20;background:#332a1c;border-radius:999px;color:#ffd596;font-weight:700}.dot{width:8px;height:8px;border-radius:50%;background:var(--amber)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.stat,.card,.callout,.arch{background:linear-gradient(145deg,var(--panel),#0f1929);border:1px solid var(--line);border-radius:16px}.stat{padding:16px}.stat strong{display:block;font-size:24px}.stat span{font-size:12px;color:var(--muted)}.section{margin-top:30px}.section-head{display:flex;align-items:end;justify-content:space-between;gap:15px;margin-bottom:14px}.section-head p{color:var(--muted);margin:5px 0 0}.tag{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--cyan);font-weight:700}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}.card{padding:15px;min-width:0}.imgbox{height:280px;background:#080d16;border:1px solid #28354a;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden}.imgbox img{max-width:100%;max-height:100%;object-fit:contain}.label{display:flex;justify-content:space-between;gap:9px;margin:11px 0 5px;font-weight:700}.meta{color:var(--muted);font-size:12px}.controls{display:flex;gap:8px;margin:10px 0}.controls button{background:#1d2e44;color:var(--text);border:1px solid #3a4d66;padding:8px 11px;border-radius:8px;cursor:pointer}.controls button.active{border-color:var(--cyan);color:var(--cyan)}.callout{padding:14px 16px;margin-top:13px;color:var(--muted)}.callout strong{color:var(--text)}.callout.warn{border-color:#654d26;background:#282316}.callout.good{border-color:#285943;background:#13291f}.pill{display:inline-block;border:1px solid #3a4d66;color:#c4d3e7;padding:3px 8px;border-radius:999px;font-size:11px;margin-right:5px}.table{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}.table div{background:var(--panel2);padding:11px;border-radius:9px}.table b{display:block;font-size:19px}.table small{color:var(--muted)}.arch{padding:20px}.flow{display:flex;align-items:stretch;gap:8px;margin:18px 0;flex-wrap:wrap}.node{flex:1;min-width:130px;padding:14px 12px;border-radius:11px;background:#192a40;border:1px solid #3a4c65;text-align:center}.node b{display:block;margin-bottom:5px}.node small{color:var(--muted)}.arrow{align-self:center;color:var(--cyan);font-size:22px}.foot{color:var(--muted);font-size:12px;margin-top:24px;border-top:1px solid var(--line);padding-top:16px}a{color:var(--cyan)}@media(max-width:850px){.hero{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.imgbox{height:340px}.table{grid-template-columns:repeat(2,1fr)}main{padding:22px 14px}}
</style></head><body><main><div class="eyebrow">Research prototype · review build · November 2026</div><div class="hero"><div><h1>RGB + thermal,<br>made inspectable.</h1><p class="sub">A working data demonstrator for paired visible and thermal imaging, numeric Celsius evidence, registration review, and clinically annotated wound tissue.</p></div><div><span class="badge"><i class="dot"></i> Data and visualization baseline · not a trained predictor</span><div class="stats"><div class="stat"><strong>1,284</strong><span>TRICVI-C source files verified</span></div><div class="stat"><strong>141</strong><span>LUTSeg wound images</span></div><div class="stat"><strong>39</strong><span>pseudonymized patients</span></div></div></div></div>
<section class="section"><div class="section-head"><div><div class="tag">01 · paired clinical thermography</div><h2>Visible image, thermal view, temperature map</h2><p>TRICVI-C · chronic venous insufficiency · one co-indexed acquisition</p></div><span class="pill">CC BY 4.0</span></div><div class="grid"><article class="card"><div class="imgbox"><img id="rgb"></div><div class="label"><span>RGB image</span><span class="pill">source</span></div><div class="meta" id="rgbmeta"></div></article><article class="card"><div class="imgbox"><img id="thermal"></div><div class="label"><span>Thermal camera view</span><span class="pill">display JPEG</span></div><div class="meta" id="thermalmeta"></div></article><article class="card"><div class="imgbox"><img id="temp"></div><div class="label"><span>Radiometric temperature grid</span><span class="pill">°C CSV</span></div><div class="meta" id="tempmeta"></div></article></div><div class="card" style="margin-top:13px"><div class="section-head"><div><h3>Registration preview</h3><div class="meta">Overlay visualization with opacity control</div></div><span class="pill">scale-only mapping</span></div><div class="controls"><button id="btnOverlay" class="active">RGB + thermal overlay</button><button id="btnRGB">RGB reference</button><button id="btnHeat">Temperature heatmap</button><input id="alpha" aria-label="Overlay opacity" type="range" min="10" max="80" value="43"></div><div class="imgbox" style="height:390px"><img id="aligned"></div><div class="callout warn"><strong>Alignment status: provisional.</strong> The records share the FLIR frame identifier; thermal is 320×240 and RGB is 640×480. This display scales the temperature grid to the RGB size. No independent landmarks, camera intrinsics/extrinsics, or held-out registration error have been verified, so the overlay is for inspection and is not a validated pixel mapping.</div></div><div class="table"><div><b id="tmin"></b><small>Minimum recorded temperature</small></div><div><b id="tmean"></b><small>Mean recorded temperature</small></div><div><b id="tmax"></b><small>Maximum recorded temperature</small></div><div><b id="gridshape"></b><small>Temperature grid size</small></div></div><div class="callout good"><strong>What this source supports:</strong> paired clinical thermography, explicit Celsius data, acquisition metadata, and a clinical workbook listing CEAP classes for 71 volunteers (C0-C6 counts: 21 / 4 / 21 / 16 / 4 / 2 / 3). The current file manifest does not yet provide a verified mapping from those volunteer codes to the FLIR frame groups, so the class labels are not ready for training or splitting. The dataset does not provide wound tissue masks; CEAP describes venous disease class, not pixel-level wound tissue.</div></section>
<section class="section"><div class="section-head"><div><div class="tag">02 · clinical wound tissue annotations</div><h2>Real wound image with clinician-labelled tissue</h2><p>LUTSeg · longitudinal leprosy-related ulcers · RGB-only</p></div><span class="pill">CC BY 4.0</span></div><div class="grid"><article class="card"><div class="imgbox"><img id="wound"></div><div class="label"><span>Wound RGB image</span><span class="pill">source</span></div><div class="meta" id="woundmeta"></div></article><article class="card"><div class="imgbox"><img id="mask"></div><div class="label"><span>Ground-truth tissue mask</span><span class="pill">annotation</span></div><div class="meta">Original label IDs retained (not a model prediction)</div></article><article class="card"><div class="imgbox"><img id="woundoverlay"></div><div class="label"><span>Ground-truth overlay</span><span class="pill">visual check</span></div><div class="meta">Color overlay generated from the source categorical mask</div></article></div><div class="callout"><strong>Mask classes:</strong> 1 epithelial, 2 slough, 3 granulation, 4 necrotic, 5 other. The dataset provides 141 images from 39 pseudonymized patients, a patient-level train/validation split, and a multi-expert reference subset. It contains no thermal images or Celsius measurements. RGB and thermal examples on this page come from different datasets and are never paired across sources.</div></section>
<section class="section"><div class="section-head"><div><div class="tag">03 · implementation baseline</div><h2>Model design we can build and validate</h2><p>One shared measurement and registration core, task-specific outputs, modality ablations.</p></div></div><div class="arch"><div class="flow"><div class="node"><b>RGB encoder</b><small>pretrained transformer features</small></div><div class="node"><b>Thermal encoder</b><small>thermal appearance + valid-pixel mask</small></div><div class="node"><b>°C feature branch</b><small>ROI statistics, gradients, asymmetry</small></div><div class="arrow">›</div><div class="node"><b>Gated cross-modal fusion</b><small>modality-aware feature exchange</small></div><div class="arrow">›</div><div class="node"><b>Task-specific heads</b><small>tissue masks · anatomy · class / score</small></div></div><div class="callout"><strong>Baseline status:</strong> the repository contains a dual-encoder transformer/query-mask wound-task scaffold. It has not been trained on either newly acquired dataset. The outputs above are source measurements and published human annotations, not model outputs. The first legitimate training experiment can use LUTSeg for RGB-only wound tissue segmentation; TRICVI-C can exercise RGB/thermal/Celsius ingestion and registration tooling. There is currently no open dataset in hand that supplies the same patients with all three: RGB + calibrated thermal + clinician wound-tissue masks.</div><div class="callout warn"><strong>Before fusion training:</strong> confirm exact RGB↔thermal pairing and transform, measure held-out landmark error, preserve patient-disjoint partitions, and reconcile task labels. Celsius arrays support temperature-map display; they do not automatically support thermal tissue labels.</div></div></section>
<div class="foot">Data sources: <a href="https://data.mendeley.com/datasets/rf5m97cmm3/2">TRICVI-C (Mendeley Data, DOI 10.17632/rf5m97cmm3.2)</a> and <a href="https://huggingface.co/datasets/ksanchez84/LUTSeg">LUTSeg (Hugging Face, CC BY 4.0)</a>. Source images remain local in the project workspace; the HTML embeds one review sample from each. For research review only. Not a diagnostic tool.</div></main>
<script>const D=__DATA__;const $=id=>document.getElementById(id);$('rgb').src=D.rgb;$('thermal').src=D.thermal;$('temp').src=D.heat;$('rgbmeta').textContent=D.rgb_name+' · '+D.source_rgb_shape;$('thermalmeta').textContent=D.thermal_name+' · '+D.source_thermal_shape;$('tempmeta').textContent=D.temp_name+' · '+D.grid_shape+' samples';$('tmin').textContent=D.stats.min.toFixed(1)+' °C';$('tmean').textContent=D.stats.mean.toFixed(1)+' °C';$('tmax').textContent=D.stats.max.toFixed(1)+' °C';$('gridshape').textContent=D.grid_shape;$('wound').src=D.lut_image;$('mask').src=D.lut_mask;$('woundoverlay').src=D.lut_overlay;$('woundmeta').textContent=D.lut_name+' · LUTSeg validation sample';let view='overlay';function paint(){const im=$('aligned');if(view==='rgb')im.src=D.rgb;else if(view==='heat')im.src=D.heat;else {const c=document.createElement('canvas'),a=new Image(),b=new Image();a.src=D.rgb;b.src=D.heat;Promise.all([a.decode(),b.decode()]).then(()=>{c.width=a.width;c.height=a.height;let x=c.getContext('2d');x.drawImage(a,0,0);x.globalAlpha=Number($('alpha').value)/100;x.drawImage(b,0,0,c.width,c.height);im.src=c.toDataURL('image/png')})}}[['btnOverlay','overlay'],['btnRGB','rgb'],['btnHeat','heat']].forEach(([id,v])=>$(id).onclick=()=>{view=v;document.querySelectorAll('.controls button').forEach(b=>b.classList.remove('active'));$(id).classList.add('active');paint()});$('alpha').oninput=paint;paint();</script></body></html>'''.replace("__DATA__", data)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"Built {OUT / 'index.html'} ({(OUT / 'index.html').stat().st_size:,} bytes)")
    print(f"TRICVI-C {sample_id}: RGB {rgb.size}, display thermal {thermal_display.size}, CSV grid {len(grid[0])}x{len(grid)}")
    print(f"temperature min/mean/max: {stats['min']:.2f}/{stats['mean']:.2f}/{stats['max']:.2f} C")
    print(f"LUTSeg wound sample: {lut_name}")


if __name__ == "__main__":
    main()
