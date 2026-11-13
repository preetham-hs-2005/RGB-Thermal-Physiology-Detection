# Baseline review demo

## Open it

Open `outputs/baseline_review_demo/index.html` in a browser. The page is self-contained and works offline. Rebuild it after refreshing the downloaded examples with:

```powershell
python scripts/build_review_demo.py
```

The downloaded source images stay in the ignored `datasets/` directory. The page embeds only one local example from each dataset and is intended for a research review, not public release or clinical use.

## What to show

1. **TRICVI-C:** switch between RGB, thermal-camera view, and the numeric °C grid. Explain that this proves actual RGB/thermal/Celsius ingestion from a shared capture ID. The example has a 640×480 RGB frame, a 320×240 thermal display, and a 320×240 temperature grid. Its sampled values span 21.73–33.43°C; the overlay currently scales the temperature image and has not passed landmark-based registration evaluation. The workbook lists 71 volunteers with CEAP labels, but their class codes have not yet been mapped to the downloaded FLIR frame groups, so we are not showing a CEAP prediction.
2. **LUTSeg:** show the RGB wound image, categorical mask, and overlay. The mask is a published clinician annotation with tissue classes; it is ground truth for the dataset, not a prediction from our model.
3. **Architecture:** explain the planned separate RGB and thermal encoders, explicit Celsius feature path, quality masks, gated cross-modal fusion and task-specific output head. For wound segmentation, the available LUTSeg path is RGB-only. The existing DINOv2/query-mask implementation is a model scaffold, not a trained inference result.

## Suggested explanation

> “We have a working multimodal data demonstrator and have acquired two public clinical datasets. One shows paired clinical visible and thermal imaging with numeric Celsius maps; the other provides clinician-labelled wound tissue masks. They are different cohorts, so we do not pretend we have a fused wound model yet. The current baseline makes the data, temperature evidence, annotations, and alignment status visible. The next engineering steps are the dataset adapters and a measured registration check; training can follow once the task and data split are set.”

## What it demonstrates—and what it does not

- Demonstrates local acquisition and inspection of public clinical images, numeric Celsius grid parsing, image-level capture-ID association, wound mask loading, and source-ground-truth visualization.
- Demonstrates a reviewable candidate model design, not trained weights or clinical inference.
- Does not show validated RGB-to-thermal registration; the current preview uses a 2× scale only and has no held-out landmark error.
- Does not show RGB+thermal wound segmentation: TRICVI-C has no tissue masks and LUTSeg has no thermal images.
- Does not make a diagnosis, establish model accuracy, or show generalization to other wounds, hospitals, or body regions.

## Acquired sources

- TRICVI-C v2: [Mendeley Data, DOI 10.17632/rf5m97cmm3.2](https://data.mendeley.com/datasets/rf5m97cmm3/2), CC BY 4.0.
- LUTSeg: [Hugging Face dataset card](https://huggingface.co/datasets/ksanchez84/LUTSeg), CC BY 4.0. Follow attribution and citation requirements.

See [TR.md](TR.md), [NTR.md](NTR.md), [DATASET_RESEARCH.md](DATASET_RESEARCH.md), and [PROCESS_MODEL_DESIGN.md](PROCESS_MODEL_DESIGN.md) for the live project status and architecture.
