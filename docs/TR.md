# Technical Requirements (TR)

Last reviewed: 2026-10-12 (Asia/Calcutta)

Status values: **ready** = implementable with current information; **blocked** = needs data, labels, or hardware; **proposed** = needs design or evidence review; **done** = implemented and verified.

## Current requirements

| ID | Status | Requirement and acceptance evidence |
| --- | --- | --- |
| TR-001 | Ready | Define a versioned paired-frame record: RGB array, thermal temperature array, units, capture timestamps, sensor/subject/session IDs, calibration metadata, orientation, and validity masks. Reject missing or contradictory units. |
| TR-002 | Ready | Implement a recorded-data loader and deterministic pairing rule with a maximum permitted timestamp difference; report rejected or unmatched frames. Do not assume matching filenames prove synchronization. |
| TR-003 | Proposed | Define multimodal registration interfaces and a calibration-point format. Evaluate a geometric/homography baseline with robust fitting; keep feature-based or learned registration replaceable. Record coordinate conventions, transform provenance, and held-out alignment error. |
| TR-004 | Proposed | Map thermal temperature and validity masks into the RGB/anatomical frame, using RGB-guided ROI cues where appropriate. Report held-out landmark/ROI error and valid overlap; flag failed registration. Test whether a homography is adequate for knee pilot poses and distances. |
| TR-005 | Proposed | Define anatomical ROI and reference-mask protocols adaptable to the body region; specify knee view, posture, distance, side identity, and named ROIs for the first application. Store masks independently of any pose model. |
| TR-006 | Ready | Compute explicit radiometric ROI biomarkers: mean, min, max, spread, gradients, reference-relative difference, and knee left-minus-right asymmetry where applicable. Include units, valid-pixel fraction, and sign convention. The calculation can be verified with synthetic temperature maps; physical validity still requires paired sensor data and reference masks. |
| TR-007 | Blocked | Produce a session report containing RGB/thermal overlays, anatomical masks, temperature evidence, registration quality, classification result, and abnormality spatial output when those models are validated. Export versioned machine-readable provenance and quality flags. |
| TR-008 | Blocked | Run the PDF's six controlled comparisons on the same subject-level partitions: RGB-only, thermal-only, early fusion, dual-stream, cross-attention, and cross-attention plus explicit thermal features. Report class counts, uncertainty, and whether fusion improves over each single modality. Requires sufficient paired labels. |
| TR-009 | Blocked | Treat abnormality localization as a core output alongside classification. Train and evaluate it only with independent spatial annotations; keep localization metrics separate from classification and do not substitute an attention map for a validated abnormality mask. |
| TR-010 | Blocked | Add live camera adapters without changing downstream record contracts after actual sensor output formats, synchronization, and calibration are characterized. |
| TR-011 | Ready | Define separate RGB and thermal preprocessing with transformations and raw-value provenance preserved. RGB enhancement and thermal denoising must not silently alter radiometric units or invalidate temperature measurements. |
| TR-012 | Proposed | Support RGB-guided anatomical ROI detection and anatomical segmentation, then compare with multimodal segmentation where paired reference masks exist. Evaluate segmentation by Dice/IoU and boundary error where suitable. |
| TR-013 | Blocked | Build modality-specific RGB and thermal feature paths, an explicit thermal-biomarker branch, and an adaptive fusion interface. Cross-modal attention is the target research comparison; each branch and fused output must be traceable. Requires suitable paired training data. |
| TR-014 | Proposed | Define task-specific evaluation before training: registration error and overlap; ROI segmentation; temperature MAE/RMSE or repeatability; classification sensitivity, specificity, F1, ROC-AUC/PR-AUC and balanced accuracy; spatial localization IoU/Dice and pixel sensitivity. Use only metrics supported by available ground truth. |

## Open technical decisions

- Which rights-cleared paired fixture and radiometric file format will be used first?
- What knee view and anatomical ROI protocol will be used for the first application?
- Which calibration target and held-out acceptance threshold suit the intended camera geometry?
- Which independent classification and spatial-localization labels, if any, will support the PDF's two target outputs?

## Current implementation status

- No application code, dependency manifest, test fixture, dataset, sample pair, calibration correspondence, or outcome label has been added to this repository.
- The repository currently contains `AGENTS.md` and the documentation under `docs/`, including `docs/RGB_Thermal_Architecture.md`. There is no application code.
- Stage 0 is next: define the paired-frame contract and construct a clearly marked synthetic fixture with known geometry and synthetic temperature units. Stage 1 is the recorded-pair loader and preprocessing. RGB-guided ROI, registration, anatomical segmentation, thermal biomarkers, and a measured overlay come next. Model comparisons and abnormality localization follow their label and validation gates.
- The key technical data gap is a paired **radiometric RGB/thermal knee** sample with known units, sensor metadata, and permission to use it. Independent class and spatial annotations are additional gaps. General RGB-thermal image datasets can help with image handling but cannot by themselves validate knee temperature biomarkers or physiological abnormality localization.

## PDF-to-architecture reconciliation

| Topic | Older knee architecture | PDF-led requirement |
| --- | --- | --- |
| Project goal | Knee injury/inflammation classification and severity | General physiological abnormality **detection and spatial localization**; knee is the first application |
| Registration | Fixed homography treated as sufficient | Multimodal registration is required; geometric, feature-based, calibration-assisted, and learned approaches are candidates; validate rather than assume homography |
| Anatomical processing | Knee landmark ROIs after registration | RGB-guided anatomical ROI and segmentation are central; ROI cues may guide registration; multimodal segmentation is a comparison |
| Thermal representation | Hand-crafted knee statistics | Explicit quantitative biomarkers **and** a learned thermal feature path |
| Fusion | Feature concatenation primary; deep fusion optional | Separate modality encoders and adaptive cross-modal fusion are the target research architecture; concatenation and early fusion are baselines |
| Output | Class/severity and knee overlay | Classification **plus localized abnormality output** with anatomical and thermal evidence |
| Evaluation | A few registration/classification measures | Six ablations and distinct registration, segmentation, temperature, classification, and localization evaluations |

The older architecture remains useful for recorded acquisition, knee pilot details, and module boundaries where it does not conflict with the PDF. The PDF's broad examples and cited performance are research context, not proof that the proposed integrated system will work on knees.

## Change history (append new entries; do not erase old ones)

### 2026-10-12 — Initial register

- **Changed:** Created TR-001 through TR-010 and staged implementation from data contract to measured ROI output, then prediction.
- **Reason/evidence:** Compared the knee architecture with the RGB–thermal review and current repository. Homography, radiometric measurements, and clinical labels need explicit validation.
- **Files affected:** `AGENTS.md`, `PROJECT_CONTEXT.md`, `TR.md`, `NTR.md`.
- **Verification:** Read the supplied architecture, the review, the committed architecture, and `git status`; confirmed the repository has no implementation files.
- **Remaining risk/next step:** Obtain or construct a clearly marked paired fixture and settle the first data format before Stage 0 coding.

### 2026-10-12 — Documentation structure corrected

- **Changed:** Moved this register into `docs/`; placed all implementation status and next-stage information here instead of in project context. Requirement IDs and statuses are unchanged.
- **Reason/evidence:** User specified that project context must contain enduring A-to-Z project details, while TR/NTR hold where the project stands and all updates.
- **Files affected:** `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Checked document paths, current repository state, and consistency of cross-references; the architecture file now matches its committed content.
- **Remaining risk/next step:** Choose the first data format and fixture before Stage 0 implementation.

### 2026-10-12 — Implementation readiness reviewed

- **Changed:** Corrected current repository paths and recorded the recommended immediate work: Stage 0 data contract and synthetic fixture, followed by Stage 1 recorded-pair loading. TR-001 and TR-002 remain ready; later requirements retain their existing status.
- **Reason/evidence:** The repository contains documentation only. A synthetic fixture can validate software contracts without claiming radiometric or clinical validity; real paired knee data is still missing.
- **Files affected:** `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Inspected tracked files, current repository status, and requirement register.
- **Remaining risk/next step:** Establish a real paired radiometric knee dataset or collection route, plus a calibration/ROI protocol, before interpreting physical measurements.

### 2026-10-12 — README added

- **Changed:** Added a root README linking to the project documents and intended development path. Reviewed technical requirements; no status changed.
- **Reason/evidence:** User requested a README for repository navigation.
- **Files affected:** `README.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Confirmed the linked documentation files exist in `docs/`.
- **Remaining risk/next step:** Complete Stage 0 data contract and synthetic fixture.

### 2026-10-12 — PDF designated as controlling architecture

- **Changed:** Revised TR-003 through TR-009; added TR-011 through TR-014; recorded a topic-by-topic reconciliation. Spatial localization, segmentation, explicit thermal biomarkers, separate modality paths, adaptive fusion, and six ablations are now target requirements. Homography and classical feature fusion are baselines. Knee remains the first application by user decision.
- **Reason/evidence:** The user's instruction gives the review PDF precedence over the older knee architecture. The PDF's Sections II-III, X-XVI, XVIII, XXIII-XXVII, and XXIX define the broader objective and proposed framework.
- **Files affected:** `AGENTS.md`, `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`, `docs/RGB_Thermal_Systematic_Review_IEEE.pdf`.
- **Verification:** Compared the complete architecture with the PDF's objectives, registration, ROI/segmentation, feature/fusion, output, and evaluation sections; checked current repository files and verified the repository PDF copy against the supplied file by SHA-256.
- **Remaining risk/next step:** Implement the data contract and synthetic fixture first; obtain paired radiometric knee data, anatomical and abnormality masks, and independent outcome labels before testing the full model.
