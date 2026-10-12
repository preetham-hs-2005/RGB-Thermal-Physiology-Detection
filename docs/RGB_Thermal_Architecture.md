# RGB–Thermal Physiology Detection System
## Architecture Document — Musculoskeletal Knee Joint Injury Detection

---

## 1. Project Overview

**Objective:** Detect and characterize musculoskeletal injury / inflammation signatures at the knee joint by fusing RGB (visual) and thermal (infrared) imaging, using a homography-based geometric registration between the two modalities.

**Scope of this phase:** Software-only. The camera hardware (RGB + thermal sensor pair) is treated as an abstracted data source; the pipeline is designed so real sensors can be plugged in later without re-architecting anything.

**Core clinical rationale:** Musculoskeletal inflammation (osteoarthritis, rheumatoid arthritis, ligament/tendon injury, post-exercise strain) produces localized skin-surface temperature elevation and left–right thermal asymmetry around the joint. RGB imaging supplies structural/pose context (where the knee and its sub-regions are); thermal imaging supplies the physiological signal (how hot those regions are). Homography registration is what allows a thermal pixel to be correctly mapped onto the anatomical region it belongs to.

---

## 2. High-Level Architecture

The system is organized into seven layers. Each layer has a defined input/output contract so it can be developed, tested, and swapped independently.

```
┌─────────────────────────────────────────────────────────────────┐
│ L1: Acquisition Layer          (RGB frame, Thermal frame, ts)    │
├─────────────────────────────────────────────────────────────────┤
│ L2: Calibration & Registration  (Homography matrix H, warp)     │
├─────────────────────────────────────────────────────────────────┤
│ L3: Preprocessing                (denoise, normalize, sync)     │
├─────────────────────────────────────────────────────────────────┤
│ L4: Anatomical ROI Localization  (knee landmarks, ROI masks)     │
├─────────────────────────────────────────────────────────────────┤
│ L5: Feature Extraction & Fusion  (thermal + visual features)    │
├─────────────────────────────────────────────────────────────────┤
│ L6: Classification / Detection   (injury / no-injury, severity) │
├─────────────────────────────────────────────────────────────────┤
│ L7: Output, Visualization & Reporting                            │
└─────────────────────────────────────────────────────────────────┘
```

Data flows strictly downward; each layer only depends on the layer directly above it, which keeps the system testable in isolation (e.g., L5–L6 can be developed against pre-recorded aligned data while L1–L2 is still being built against real hardware).

---

## 3. Layer-by-Layer Specification

### 3.1 Layer 1 — Acquisition Layer

**Purpose:** Provide synchronized RGB and thermal frames to the rest of the pipeline, regardless of whether the source is a live camera pair or recorded/simulated data.

**Interface contract:**
- Input: none (data source configuration — live device IDs or file paths)
- Output: a stream of tuples `(rgb_frame, thermal_frame, timestamp)`

**Design decisions:**
- Define an abstract `CameraSource` interface with two concrete implementations:
  - `LiveCameraSource` — for real hardware later (RGB webcam/industrial camera + thermal sensor, e.g. FLIR-class device)
  - `RecordedDatasetSource` — reads paired RGB/thermal images or videos from disk for development and evaluation
- Frame synchronization: since RGB and thermal sensors often run at different frame rates, this layer is responsible for time-aligning frames (nearest-timestamp match or frame-index mapping for pre-paired datasets).
- Resolution/format normalization happens here at the raw level (e.g., thermal radiometric data converted to a consistent temperature-per-pixel array, not just a false-color image).

---

### 3.2 Layer 2 — Calibration & Homography Registration

**Purpose:** Establish a consistent geometric mapping between the thermal and RGB pixel grids so that a temperature value can be correctly assigned to an anatomical location seen in the RGB frame.

**Why homography specifically:** RGB and thermal sensors are mounted at slightly different positions/angles and have different fields of view and resolutions. Because the knee surface being imaged is approximately planar (or treated as such at the working distance used), a single planar homography `H` (3×3 projective transform) is sufficient to map thermal-image coordinates to RGB-image coordinates, rather than requiring a full 3D stereo calibration.

**Sub-modules:**

1. **Calibration target design**
   - A checkerboard/pattern visible in *both* modalities is required. Plain printed checkerboards are often invisible in thermal, so the target should use materials with contrasting emissivity (e.g., aluminum tape squares on cardboard) or embedded low-power heating elements at known grid points.

2. **Correspondence detection**
   - Detect calibration corner points independently in the RGB frame and the thermal frame (standard corner detection on RGB; thresholded/contrast-based detection on thermal).

3. **Homography estimation**
   - Compute `H` using a robust estimator (RANSAC-based least squares) from the matched point sets. Since the camera rig is physically fixed, `H` is computed once during a calibration step and reused for all subsequent frames — it does not need to be recomputed per frame unless the physical rig configuration changes.

4. **Frame warping**
   - Apply `H` to warp the thermal frame into the RGB frame's coordinate space (or vice versa, depending on which resolution is treated as the reference plane — typically the higher-resolution RGB frame is the reference).
   - Output: a thermal map that is pixel-aligned with the RGB frame, i.e., `aligned_thermal[y, x]` corresponds to the same physical point as `rgb_frame[y, x]`.

5. **Calibration validation**
   - Reprojection error check: verify that known calibration points map within an acceptable pixel-error tolerance after warping.
   - Periodic re-calibration trigger: if the rig can be bumped/adjusted, define a re-calibration procedure rather than assuming permanence.

**Interface contract:**
- Input: `rgb_frame`, `thermal_frame` (raw, synchronized)
- Output: `rgb_frame` (unchanged), `aligned_thermal_map` (same pixel dimensions as `rgb_frame`, each pixel holding a temperature value)

---

### 3.3 Layer 3 — Preprocessing

**Purpose:** Clean and normalize both modalities before anatomical analysis.

**RGB preprocessing:**
- Illumination normalization (histogram equalization / CLAHE)
- Denoising
- Resizing/cropping to a standard working resolution

**Thermal preprocessing:**
- Radiometric calibration check (ensure pixel values represent actual temperature, not just relative intensity)
- Ambient temperature compensation (skin temperature readings drift with room/environmental temperature; this should be logged and optionally normalized against a reference object in-frame)
- Noise reduction (thermal sensors are typically noisier than RGB — median or bilateral filtering is appropriate since it preserves edges)

**Interface contract:**
- Input: `rgb_frame`, `aligned_thermal_map`
- Output: `clean_rgb`, `clean_thermal_map`

---

### 3.4 Layer 4 — Anatomical ROI Localization

**Purpose:** Identify the knee joint location and its clinically relevant sub-regions in the RGB frame, then project those regions onto the aligned thermal map.

**Sub-modules:**

1. **Pose/landmark detection (RGB)**
   - General-purpose pose estimation (e.g., a pretrained human pose model) to localize the knee joint region at a coarse level.
   - Fine-grained landmark detection (a custom-trained model, e.g., DeepLabCut-style) for precise sub-regions: medial condyle, lateral condyle, patella (superior/inferior), suprapatellar pouch. These specific ROIs are the standard regions used in clinical knee thermography protocols.

2. **ROI mask generation**
   - Convert landmark points into region masks (e.g., small polygons/circles around each landmark, or a segmentation mask for the whole joint region).

3. **Cross-modal ROI projection**
   - Since RGB and thermal are already pixel-aligned (Layer 2), the same ROI masks apply directly to `clean_thermal_map` without additional transformation.

4. **Bilateral handling**
   - If both knees are visible in-frame (or captured in separate sessions), maintain left/right labeling so asymmetry comparisons can be computed later.

**Interface contract:**
- Input: `clean_rgb`, `clean_thermal_map`
- Output: a set of named ROI masks (e.g., `medial`, `lateral`, `patella`, `suprapatellar`) applicable to both modalities, plus left/right labeling

---

### 3.5 Layer 5 — Feature Extraction & Fusion

**Purpose:** Convert the ROI-masked RGB and thermal data into a structured feature representation suitable for classification.

**Thermal features (per ROI):**
- Mean, min, max, and standard deviation of temperature
- Temperature gradient across the ROI
- Left–right contralateral asymmetry (difference between corresponding ROIs on each knee — a well-established inflammation marker)
- Texture descriptors (e.g., GLCM-based) on the thermal ROI to capture heat-distribution patterns, not just averages

**Visual features (per ROI):**
- Local swelling/contour irregularity (edge and shape descriptors)
- Skin discoloration/redness indicators
- Structural landmark displacement (useful for detecting swelling-driven anatomical distortion)

**Fusion strategy:**
- **Feature-level fusion (primary approach):** concatenate thermal and visual feature vectors per ROI into a single structured feature vector. This is the more data-efficient approach and works well with smaller clinical-style datasets.
- **Data-level fusion (optional, for larger datasets):** stack aligned RGB channels and the thermal channel into a 4-channel image tensor for direct CNN input, if sufficient labeled image data becomes available.

**Interface contract:**
- Input: ROI-masked `clean_rgb`, `clean_thermal_map`
- Output: a structured feature vector (or fused image tensor) per subject/session, with ROI-level granularity preserved

---

### 3.6 Layer 6 — Classification / Detection

**Purpose:** Produce an injury/inflammation determination from the fused features.

**Model tiers (choose based on available data volume):**
- **Tier 1 — Classical ML (recommended starting point):** SVM, Random Forest, or Gradient Boosting on the structured feature vector. Appropriate given that most available knee-thermal datasets are small (tens to low hundreds of subjects).
- **Tier 2 — Deep learning (if data volume permits):** CNN on the fused 4-channel image tensor, or a two-branch network (one branch per modality) with a late-fusion classification head.

**Output categories (configurable to project goals):**
- Binary: injury/inflammation present vs. not present
- Multi-class: injury type or condition category (e.g., OA, RA, acute strain/ligament injury, healthy)
- Regression/severity score: continuous estimate of inflammation severity, useful for tracking progression over time

**Interface contract:**
- Input: fused feature vector or fused image tensor
- Output: classification label(s) with confidence score, and/or severity estimate

---

### 3.7 Layer 7 — Output, Visualization & Reporting

**Purpose:** Present results in a form usable by a clinician, coach, or researcher.

**Components:**
- Overlay visualization: RGB frame with thermal heatmap overlaid on the ROI regions, annotated with landmark points
- Asymmetry report: side-by-side left/right knee temperature comparison with flagged deviations
- Session/trend report: temperature and classification history over multiple sessions (useful for monitoring recovery or progression)
- Exportable structured output (e.g., JSON/CSV record per session) for downstream storage or integration with a clinical record system

---

## 4. End-to-End Data Flow Summary

```
Camera Pair / Recorded Data
        │
        ▼
[L1] Synchronized RGB + Thermal frames
        │
        ▼
[L2] Homography-based registration → pixel-aligned thermal map
        │
        ▼
[L3] Preprocessing (denoise, normalize, ambient-temp compensation)
        │
        ▼
[L4] Knee landmark detection → anatomical ROI masks (applied to both modalities)
        │
        ▼
[L5] Feature extraction (thermal stats + asymmetry + visual features) → fused feature vector
        │
        ▼
[L6] Classification / severity estimation
        │
        ▼
[L7] Visualization, asymmetry report, trend tracking
```

---

## 5. Dataset Strategy

Knee-specific RGB-thermal datasets are limited and mostly not openly downloadable, so the dataset strategy is deliberately layered across three purposes:

### 5.1 Domain-specific (knee/thermal) datasets — for validation and clinical grounding
- **OSTHERSIT dataset** — a thermal knee image dataset (75 images) built specifically for osteoarthritis analysis; small but directly relevant.
- **"Infrared Knee Joint Dataset"** (Majumdar, Das, Bhowmik et al.) — a purpose-built dataset with healthy and multiple arthritis-affected knee thermograms, built with a standardized acquisition protocol. Not always openly hosted; typically requires contacting the authors.
- Published clinical thermography studies (FLIR-based OA and RA studies) — while not always distributable as raw datasets, they provide critical reference values: expected knee temperature ranges, correlation with clinical severity scores, and ROI definitions (medial/lateral/patellar/suprapatellar) that this architecture directly adopts.

### 5.2 General-purpose RGB-Thermal datasets — for building and testing the registration/fusion pipeline
Since domain-specific paired RGB-thermal knee data is scarce, the homography and fusion pipeline (Layers 2–5) should first be built and validated against general RGB-thermal datasets that provide real, synchronized image pairs:
- **KAIST Multispectral Pedestrian dataset**
- **RGBT234** (RGB-Thermal tracking benchmark)

These are not medical datasets, but they are ideal for de-risking the registration pipeline before applying it to scarce medical data.

### 5.3 Supporting datasets — for anatomical localization and severity correlation
- **COCO-Keypoints / MPII** — for pretraining general human pose/landmark detection, later fine-tuned on a small custom-labeled knee image set.
- **Knee X-ray severity-grading datasets** (e.g., publicly available knee OA X-ray grading sets) — useful as an independent severity reference to validate whether thermal-asymmetry-based predictions correlate with structural severity, even though the imaging modality differs.

### 5.4 Custom data collection (post-hardware)
Once the real RGB+thermal camera rig is available, the calibration protocol and ROI definitions established in this architecture should be used to collect a project-specific labeled dataset (healthy vs. injured/inflamed knees, ideally with clinical ground truth), which then plugs directly into the same L1–L7 pipeline without modification.

---

## 6. Technology Stack (Recommended)

| Component | Recommended Tools |
|---|---|
| Image processing / homography | OpenCV |
| Pose/landmark detection | Pretrained pose model + custom fine-tuned landmark model |
| Classical ML | scikit-learn |
| Deep learning (if needed) | PyTorch |
| Data handling | NumPy, pandas |
| Visualization / reporting | Matplotlib / a lightweight dashboard layer |

---

## 7. Evaluation Metrics

- **Registration accuracy:** reprojection error (pixels) on calibration validation points
- **Classification performance:** accuracy, precision, recall, F1-score, ROC-AUC (given class imbalance is likely in clinical data)
- **Severity estimation:** correlation coefficient against clinical reference scores (e.g., ultrasound-based inflammation scores or OA severity grades)
- **Asymmetry detection reliability:** intra-observer/session reproducibility (repeat-session variance)

---

## 8. Risks & Limitations

- **Dataset scarcity:** knee-specific RGB-thermal datasets are small; classical ML with careful feature engineering is more realistic than deep learning until more data is collected.
- **Ambient temperature sensitivity:** thermal readings are highly sensitive to room conditions; the acquisition protocol must standardize or log ambient temperature and acclimatization time.
- **Calibration drift:** if the camera rig is not perfectly rigid, periodic re-calibration of the homography matrix is required.
- **Generalization across skin tones/body types:** ROI localization models should be validated across diverse subjects to avoid bias in landmark detection.

---

## 9. Future Hardware Integration Path

Because Layer 1 is abstracted behind a `CameraSource` interface, integrating the real RGB+thermal camera pair later only requires implementing a `LiveCameraSource` that feeds synchronized frames into the existing pipeline — no changes needed to Layers 2–7. The calibration protocol (Section 3.2.1) should be executed once physically with the real rig to obtain the production homography matrix.
