# Multi-domain RGB–thermal process and model design

**Status:** recommended implementation architecture; dataset-level training choice remains empirical.
**Updated:** 2026-11-13 (Asia/Calcutta)
**Scope:** multiple human body regions and nonclinical RGB–thermal tasks. No single anatomy or clinical label is assumed.

## Decision in one paragraph

Build one reusable data, calibration, registration, quality-control, and evaluation core, with explicit dataset adapters and task-specific model heads. Do **not** train one universal classifier from mixed datasets whose labels mean different things. For each dataset, establish its own paired frames, transform provenance, anatomy/classes, split unit, and valid metric. Compare RGB-only, thermal-only, and fusion using identical subject-level partitions. The earlier small U-Net remains only a nonclinical Caltech pipeline smoke test; it is not the model for medical wound localization. Keep absolute temperature as a separate calibrated sensor input and biomarker branch; never infer °C from a false-color or auto-gain image.

### Access-gated clinical lead: post-TKA wound tissue localization

The project has no knee-first default. Use the 2026 post-TKA cohort only if written data access is approved and the clinical cohort actually includes paired RGB/EO images, raw radiometric arrays, patient-disjoint identifiers, and the four claimed tissue masks. The paper's larger wound-segmentation corpus also incorporated public images; do not assume those annotations are all from the paired clinical cohort. The source is proprietary and release is subject to a DUA and sponsor approval: [primary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13691468/). It remains a possible future task-specific adapter.

The initial output is a task-specific mask with background plus open wound, granulation, infection-associated exudate, and necrosis. It does not predict infection or diagnose a patient. Train RGB-only, thermal-only, and fused arms on the same approved patient-disjoint partitions.

**Model choice:** two DINOv2-base transformer encoders initialized from the same pretrained image checkpoint, with separate modality paths, bidirectional gated cross-attention, and a four-query mask decoder following Mask2Former's query-mask pattern. This is a project-specific dual-stream adaptation, not the official single-stream Mask2Former checkpoint. The Hugging Face model card lists DINOv2-base as Apache-2.0 and its config defines 768-dimensional, patch-14 features ([checkpoint](https://huggingface.co/facebook/dinov2-base)). Fusion and tissue decoder weights are task-specific; keep encoders partially frozen initially and unfreeze progressively only if data volume and validation support it. Record checkpoint revision and license in each run.

The thermal encoder receives normalized absolute Celsius, robust per-image relative temperature, and local gradient channels; the validity map remains a separate attention/quality mask. Preserve raw temperature arrays and Celsius conversion metadata. Use the provider's EO-to-IR mapping with explicit thermal-to-RGB direction and check target-registration error on held-out landmarks before training. The implementation blocks model training until the manifest records approved access and a test-split held-out landmark set.

Report per-class Dice, precision, recall, and 95% subject-cluster bootstrap intervals on the held-out test set. Include poor overlap, invalid thermal coverage, bandages, motion, and rare/missing tissue classes as failure cases. Fusion is not presumed superior. No small U-Net fallback is used for this clinical task.

## Target use cases and what each dataset can teach

| Use case | Example source/task | Valid question | Cannot claim |
| --- | --- | --- | --- |
| Body-part anatomy | StereoThermoLegs posterior legs; segmentation of left/right leg regions | Can RGB, thermal, or fusion identify the provided anatomy masks across held-out people? | Clinical abnormality, precise radiometry, all-body generalization |
| Scene perception | Caltech aerial RGB-T; 10 terrain/object semantic classes | Does thermal add semantic-segmentation value over RGB in its scene and time/geography split? | Human physiology or medical usefulness |
| Temperature metrology | FDA facial and oral temperature tables; where raw pixels are not present, reference temperature regression only | How do provided facial-site measurements relate to oral references and recorded environment/device fields? | Pixel-level alignment or image fusion from CSV-only files |
| Low-light human detection (possible later dataset) | LLVIP visible/IR detection | Does IR improve person detection in low light, and how robust is alignment? | Surface-temperature biomarkers or clinical diagnosis |
| Clinical localization (selected; access-gated) | Post-TKA wound tissue classes on paired RGB and radiometric thermal data | Can the three modality arms localize the four annotated tissue classes on patient-disjoint data? | Infection diagnosis, other body regions, or external-site performance |

Tasks with different class ontologies stay in separate heads and evaluations. A shared backbone may be studied later with balanced sampling and explicit domain/task conditioning, but dataset names, camera, body site, task label map, and missing modalities must stay available to the model.

## End-to-end process

1. **Dataset intake:** record source DOI, version, license/DUA, permitted use, modalities, participant/scene IDs, timestamps, sensor metadata, label definitions, split unit, and known exclusions. Inspect actual file examples and checksums.
2. **Canonical record:** each observation points to untouched source files and contains RGB, thermal raw array (or explicitly marked display-only image), units/conversion, validity mask, capture times, source identifiers, body/site or scene, device, and label references. A missing modality remains missing; it is not fabricated.
3. **Pairing and synchronization:** use common capture IDs/timestamps or documented co-capture. Enforce a task-specific maximum timestamp delta for moving scenes. Record unmatched frames and reject duplicate/cross-subject pairing.
4. **Calibration and registration:** preserve each modality's native frame. Estimate or load a transform, carry the transform direction and coordinate conventions, map thermal values and validity mask with the same geometry, and measure alignment on held-out landmarks or masks. Never silently stretch one modality until it looks aligned.
5. **Quality gate:** flag saturation, missing/invalid thermal pixels, motion, occlusion, poor overlap, lens/camera changes, and time mismatch. Report exclusions and failure rates by dataset/device/domain.
6. **Task adapter:** transform source annotation into a versioned task label map without losing original labels. Anatomy masks, environmental segmentation, temperature reference, disease label, and abnormality mask are separate targets.
7. **Controlled experiments:** use subject/scene/trajectory-disjoint splits. Fit normalization only on training data. Run one modality at a time first; then fusion on the exact same paired split. Report per-class metrics and uncertainty.
8. **Cross-domain evaluation:** hold out a site, camera, body region, or geography only when semantics are comparable. If label meanings differ, evaluate separately; do not average incompatible mIoU/AUROC scores.
9. **Report:** produce overlays, original and aligned coordinate frames, transform quality, temperature units/provenance, per-task metrics, dataset version/license, model/config hashes, and limitations.

## RGB-to-thermal alignment strategy

### Tier 1: sensor-provided mapping / shared optics

Use vendor calibration or known registration from the data provider. Confirm it on examples and held-out landmarks because dual sensors can still have different fields of view, pixel pitch, and parallax. Carry a pixel-validity mask; cropping, rotation, rectification, and any resizing must update the transform metadata.

### Tier 2: calibrated cameras

Calibrate RGB and thermal intrinsics/distortion independently, then estimate their extrinsic relation using a target visible to both sensors (heated checkerboard, heated circular grid, or equivalent). If scene depth is available, back-project thermal pixels to 3D and project into RGB; this handles parallax and occlusion better than a single homography. For static planar distant scenes, a homography may be an adequate baseline. For curved bodies or close cameras, validate a local/nonrigid residual only if the acquisition is synchronized and reference points support it.

### Tier 3: no calibration / legacy data

Use cross-modal structure: edges/gradients, thermal boundaries, mutual-information objectives, or modality-invariant learned descriptors. Fit affine/homography candidates with robust RANSAC and reject degenerate or low-inlier mappings. A learned matcher (for example LoFTR-style or cross-modal feature matching) is a later candidate, not the first dependency. Dense optical flow is only a refinement after coarse geometric alignment and should be tested carefully under modality appearance changes.

### Registration evaluation

- Estimate transforms on a calibration subset; reserve independent landmarks for target-registration error (TRE) in pixels and, with depth/scale, physical units.
- Report the fraction of the RGB region with valid mapped thermal coverage, mask overlap, reprojection residuals, and error by scene/body pose/distance.
- For moving captures, report timestamp offset and test motion-induced correspondence error.
- Use overlays for review, not as a numeric metric. RGB/thermal PSNR or SSIM alone is not a sufficient alignment metric because the modalities have different appearance.
- On aligned masks, report Dice/IoU between mapped anatomical masks and independent references when available.
- Apply one geometric resampling to raw thermal values where possible; propagate validity masks with nearest-neighbour interpolation and do not treat padded/occluded pixels as temperatures.

## Model architecture

### Shared system components

- Per-source loaders and schema adapters.
- RGB encoder and thermal encoder with independent normalization and checkpoints.
- Thermal input carries (a) raw/display intensity, (b) calibrated °C when actually present, and (c) quality/validity channels. Temperature normalization is learned from training subjects only; preserve physical units as a separate ROI feature vector.
- Optional metadata embedding for device, site/body region, view, and task. Do not let identity or split leakage enter features.
- Fusion interfaces: early channel stacking (baseline), late feature concatenation, gated/adaptive fusion, then cross-attention as a data-demanding comparison.
- Separate decoder/head per task: segmentation, object detection, scalar temperature regression, classification, or abnormality localization. Abnormality localization requires its own independent spatial labels.
- Missing-modality path with explicit mask/dropout; do not represent missing thermal as an all-zero real temperature.

### Model size and training order

1. **Clinical wound task:** perform access/label preflight, verify transform direction and held-out error, then train the pretrained dual-stream query-mask transformer in RGB-only, thermal-only, and gated-fusion modes on identical patient-disjoint partitions.
2. **Quality-controlled fusion:** preserve raw radiometry, temperature units, validity masks, and mapping provenance. Apply the same augmentation, optimization budget, and validation rule across all three arms.
3. **Task/domain expansion:** keep each dataset's label map and head separate. Compare other model families only on tasks those datasets support; the Caltech U-Net smoke test remains nonclinical and is not a medical baseline.

Do not choose a single “best” fusion model before the controlled baselines. If fusion does not beat the best single modality with uncertainty intervals on a subject/scene-disjoint test, retain the simpler model.

## Current implementation and future training sequence

The Caltech U-Net run has already served as a nonclinical pipeline smoke test; it is not the medical training model. Its terrain labels support only environmental perception. For the first future wound segmentation run, LUTSeg provides an accessible RGB-only tissue-mask task with patient-level train/validation splits; the baseline should be a pretrained transformer segmentation model or query-mask decoder, with the RGB DINOv2/query-mask scaffold as the current candidate. Do not synthesize thermal input or report RGB-only results as multimodal.

TRICVI-C separately provides paired clinical RGB, display thermal views, numeric per-pixel Celsius CSVs, and a workbook with CEAP labels for 71 volunteers. It could support a separate venous-disease classification task after a verified mapping from volunteer IDs to FLIR frame groups and a patient-level split are recovered. Its class counts are imbalanced (C0–C6: 21/4/21/16/4/2/3); report per-class metrics and do not overclaim rare-class performance. CEAP is not pixel-level wound tissue annotation. The two datasets must not be cross-paired. A later multimodal wound model requires one approved cohort containing paired RGB, calibrated thermal and independently reviewed wound masks. Use StereoThermoLegs separately for anatomy masks; use FDA CSV tables only for temperature-reference analysis because they contain no paired image pixels.

Training report should include: archive checksum/version/license; numbers of unique scenes/people and frames; split manifest; image sizes and RGB/IR channel treatment; label IDs and ignored classes; GPU/software versions; seed; train/validation curves; mIoU, Dice and per-class IoU; RGB/thermal/fusion comparison; and alignment/quality summary. The result cannot be described as clinical or general all-body performance.

### First pipeline smoke test — 2026-10-31

Implemented in `scripts/train_caltech_segmentation.py` and run on an NVIDIA RTX 3050 Laptop GPU. The model is a compact U-Net with 3-channel RGB, 1-channel thermal16 intensity, or 4-channel early fusion. All three arms used the same 256 training samples, 64 validation samples, and 64 test samples from the creator-provided train/validation/test lists; one epoch at 128x128; seed 20261031. Mask IDs 0 and 1 were ignored; mIoU averages classes 2–11 that occur in each evaluated slice. Test mIoU: RGB 0.0990, thermal 0.0627, fusion 0.1004. Validation mIoU: RGB 0.1068, thermal 0.0789, fusion 0.1050. The training slice came from the start of the ordered train list, so this is an order-sensitive loader/training smoke test, not a fair final comparison. Fusion is essentially tied with RGB here; no superiority claim follows. Caltech thermal16 is treated as sensor intensity, not calibrated temperature. JSON metrics and model weights are under `outputs/caltech_rgbt_runs/` (ignored by Git).

The experiment confirms that all three input branches can load, train, evaluate, and save weights on the current machine. Next, implement reproducible split selection and a versioned data adapter, train longer on the full creator split, and add repeated seeds/uncertainty and per-class reporting. For StereoThermoLegs, confirm calibration transform direction/units against creator documentation, implement depth-aware RGB-to-IRT mapping, measure held-out alignment error, then run a separate held-out-participant anatomy task. This Caltech pilot does not implement registration, calibration, clinical abnormality classification, or abnormality localization.

## Acceptance gates before clinical claims

1. Rights-cleared paired radiometric human dataset with identifiable participant split keys.
2. Sensor conversion/calibration and environmental metadata sufficient to interpret °C.
3. One precisely specified clinical outcome and an independent reference standard.
4. Independent anatomical masks for anatomy metrics and independent abnormality masks for localization metrics.
5. Subject-disjoint development plus external-site validation, appropriate event counts, and a preregistered primary metric.

Until those gates are met, the model is a research/engineering prototype. A successful terrain or anatomy segmentation run only demonstrates that the pipeline trains on that dataset's labels.
