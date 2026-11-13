# Running wound segmentation baseline

## What runs

The current medical model is an **RGB-only wound-tissue segmenter** trained on LUTSeg. It uses a pretrained [DINOv2-small](https://huggingface.co/facebook/dinov2-small) visual encoder (Apache-2.0) with a learned two-layer dense Transformer decoder and six tissue classes. The DINOv2 encoder is frozen; the Transformer decoder and class head were trained on LUTSeg. It is not a U-Net, and it does not consume thermal data.

Launch the desktop application from the repository root:

```powershell
python scripts/run_lutseg_baseline.py
```

The app opens a patient-disjoint LUTSeg validation example and displays RGB input, model prediction, and clinician mask. It can also run inference on another RGB image. The paired RGB–thermal button opens a separate TRICVI-C example with Celsius grid and provisional scale-only overlay; no wound mask is attached to that pair.

## Training record

- Dataset: LUTSeg, 111 official train images / 30 patient-disjoint validation images from 39 pseudonymized patients.
- Labels: background, epithelial, slough, granulation, necrotic, other; ignore value 255.
- Initialization: `facebook/dinov2-small`, Apache-2.0 model card; DINOv2-small features are pretrained, the task decoder is trained here.
- Run: 8 epochs, image size 224, batch size 4, CPU, seed 20261113. Best checkpoint selected by validation mIoU at epoch 7.
- Best validation mIoU: **0.331** over six present classes including background; foreground-only macro mIoU: **0.216**. Foreground-only macro Dice: **0.325**.
- Per-class validation IoU: epithelial 0.102, slough 0.181, granulation 0.459, necrotic 0.338, other 0.000. The rare “other” class was not successfully learned.
- Dataset has no independent test split. The 30-image validation set was used for checkpoint selection, so these numbers are model-selection metrics, not an unbiased final test estimate.

Weights and the full run history are local and ignored by Git:

- `outputs/lutseg_transformer_baseline/best_model.pt`
- `outputs/lutseg_transformer_baseline/training_report.json`

Retrain with:

```powershell
python -m pip install -r requirements-medical.txt
python scripts/train_lutseg_transformer.py --epochs 8 --batch-size 4 --image-size 224
```

The pretrained DINOv2 checkpoint must be available from Hugging Face on first training. The saved trained checkpoint includes the encoder and decoder weights for subsequent local inference.

## Paired thermal data boundary

TRICVI-C provides paired clinical RGB/thermal frames and numeric Celsius grids. Its wound labels are not pixel masks, and its volunteer-code to FLIR-frame mapping remains unverified. The desktop thermal view is therefore an input/measurement display, not thermal wound inference. Do not describe the current application as an RGB–thermal wound model. The RGB-only model can be retrained and evaluated when additional wound image/mask datasets are acquired, while true wound fusion requires same-capture RGB, calibrated thermal, and independent wound masks.

This is a research baseline, not a diagnostic system. Do not use its predictions for treatment decisions.
