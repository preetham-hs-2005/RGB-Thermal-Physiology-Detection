# Technical Requirements (TR)

Last reviewed: 2026-11-13 (Asia/Calcutta)

Status values: **ready** = implementable with current information; **blocked** = needs data, labels, or hardware; **proposed** = needs design or evidence review; **done** = implemented and verified.

## Current requirements

| ID | Status | Requirement and acceptance evidence |
| --- | --- | --- |
| TR-001 | Ready | Define a versioned paired-frame record: RGB array, thermal temperature array, units, capture timestamps, sensor/subject/session IDs, calibration metadata, orientation, and validity masks. Reject missing or contradictory units. |
| TR-002 | Ready | Implement a recorded-data loader and deterministic pairing rule with a maximum permitted timestamp difference; report rejected or unmatched frames. Do not assume matching filenames prove synchronization. |
| TR-003 | Proposed | Define multimodal registration interfaces and a calibration-point format. Evaluate a geometric/homography baseline with robust fitting; keep feature-based or learned registration replaceable. Record coordinate conventions, transform provenance, and held-out alignment error. |
| TR-004 | Proposed | Map thermal measurements and validity masks into the RGB/task frame. Prefer calibrated sensor geometry and depth when available; compare geometric and learned fallbacks. Report held-out landmark/ROI error and valid overlap; flag failed registration. Do not assume a homography handles parallax or curved surfaces. |
| TR-005 | Proposed | Define versioned, dataset/task-specific anatomy and ROI schemas with view, pose, distance, orientation, and side metadata where applicable. Preserve independent reference masks and source label maps. |
| TR-006 | Ready | Compute explicit radiometric ROI biomarkers when calibrated per-pixel temperature is available: mean, min, max, spread, gradients, reference-relative difference, and bilateral asymmetry where applicable. Include units, valid-pixel fraction, and sign convention. Intensity-only/AGC imagery must not be reported as absolute temperature. |
| TR-007 | Blocked | Produce a session report containing RGB/thermal overlays, anatomical masks, temperature evidence, registration quality, classification result, and abnormality spatial output when those models are validated. Export versioned machine-readable provenance and quality flags. |
| TR-008 | Blocked | Run the PDF's six controlled comparisons on the same subject-level partitions: RGB-only, thermal-only, early fusion, dual-stream, cross-attention, and cross-attention plus explicit thermal features. Report class counts, uncertainty, and whether fusion improves over each single modality. Requires sufficient paired labels. |
| TR-009 | Blocked | Treat abnormality localization as a core output alongside classification. Train and evaluate it only with independent spatial annotations; keep localization metrics separate from classification and do not substitute an attention map for a validated abnormality mask. |
| TR-010 | Blocked | Add live camera adapters without changing downstream record contracts after actual sensor output formats, synchronization, and calibration are characterized. |
| TR-011 | Ready | Define separate RGB and thermal preprocessing with transformations and raw-value provenance preserved. RGB enhancement and thermal denoising must not silently alter radiometric units or invalidate temperature measurements. |
| TR-012 | Proposed | Support RGB-guided anatomical ROI detection and anatomical segmentation, then compare with multimodal segmentation where paired reference masks exist. Evaluate segmentation by Dice/IoU and boundary error where suitable. |
| TR-013 | Blocked | Build modality-specific RGB and thermal feature paths, an explicit thermal-biomarker branch, and an adaptive fusion interface. Cross-modal attention is the target research comparison; each branch and fused output must be traceable. Requires suitable paired training data. |
| TR-014 | Proposed | Define task-specific evaluation before training: registration error and overlap; ROI segmentation; temperature MAE/RMSE or repeatability; classification sensitivity, specificity, F1, ROC-AUC/PR-AUC and balanced accuracy; spatial localization IoU/Dice and pixel sensitivity. Use only metrics supported by available ground truth. |
| TR-015 | Ready | Maintain a dataset manifest per source and inspected sample: pair/subject/session keys, timestamps, thermal encoding and °C conversion, geometry, clinical and spatial-label provenance, rights, and allowed use. Mark unsupported fields unknown; qualify each dataset for only the tasks it can support. |
| TR-016 | Ready | Implement controlled same-split task baselines for RGB-only, thermal-only, and RGB+thermal fusion. Preserve separate dataset label maps and task heads; report modality and per-domain metrics. |
| TR-017 | Proposed | Add multiple registration strategies behind a common interface: vendor mapping, calibrated intrinsics/extrinsics and depth projection, planar homography baseline, and cross-modal feature/mutual-information fallback. Store transform source, direction, confidence, and held-out alignment evidence. |
| TR-018 | Ready | Add a post-TKA wound-mask dataset adapter that requires RGB, raw numeric radiometric thermal, unique documented pair IDs/basis, RGB-frame mask IDs (0 background, 1 open wound, 2 granulation, 3 infection-associated exudate, 4 necrosis, 255 ignore), a thermal-to-RGB transform, Celsius conversion metadata, and participant-disjoint train/validation/test groups. Validate file inventory, mask IDs, mapped thermal coverage, and held-out registration landmarks before model training. |
| TR-019 | Blocked | Train the task-specific dual-stream pretrained transformer/query-mask model in RGB-only, thermal-only, and gated-fusion modes; report per-class Dice/precision/recall and subject-cluster bootstrap intervals. Requires an approved data-use agreement, paired clinical files, verified mask provenance, and held-out registration points. |
| TR-020 | Done | Provide an offline review demonstrator that displays a verified paired RGB/thermal/Celsius sample, a clearly qualified registration overlay, and an independently sourced clinician wound-mask overlay. It must identify source, task, label provenance, and clearly distinguish ground truth from model predictions. |

## Open technical decisions

- Can the study authors and sponsor approve a deidentified post-TKA subset, including paired RGB/IR files and tissue masks?
- Are the four tissue masks attached to the paired clinical cohort or only to the broader corpus that also used public images?
- What EO-to-IR mapping, Celsius conversion, invalid-pixel codes, and patient keys will be shared for independent registration checks and patient-disjoint splits?
- Can TRICVI-C's original folder/volunteer-code mapping be recovered from the owner or a hierarchy-preserving archive so workbook CEAP labels can be linked to FLIR capture groups without guessing?

## Current implementation status

- Downloaded TRICVI-C v2 (DOI 10.17632/rf5m97cmm3.2): all 1,284 files / 318,816,132 bytes passed publisher per-file SHA-256 verification. Inspected example FLIR1753: paired by shared FLIR frame ID, 640x480 RGB, 320x240 thermal display JPEG, and numeric 320x240 CSV grid with °C values; sample range 21.73–33.43°C, mean 24.00°C. The workbook has CEAP labels for 71 volunteers, but a verified volunteer-code ↔ FLIR-frame mapping is not yet available; do not use these class labels for training or patient splitting until recovered. No tissue masks are provided. Exact geometric registration and held-out landmark error remain unverified.
- Downloaded LUTSeg at Hugging Face commit `e5115d4b2e5ecfc727f530deca9f3b0d032fb4bb`: 141 RGB wound images / 39 pseudonymized patients, patient-disjoint official train/validation split, six-class tissue masks and 46-image five-clinician gold-standard subset. License: CC BY 4.0 per the dataset card. RGB-only; no thermal or Celsius data. Publisher checksum list: 1,028 files match exact bytes, 21 text files match after CRLF normalization, and README.md differs from the listed hash and must be treated as a source integrity discrepancy. Images/masks inspected locally.
- Built an offline review page at `outputs/baseline_review_demo/index.html` from one local sample of each dataset. It shows RGB, thermal display, a parsed °C heatmap and interactive scale-only overlay, plus a source ground-truth tissue-mask overlay. This is a data/measurement demonstrator, not trained inference; its two clinical examples are from different datasets and are not fused together.
- A single dataset providing paired clinical RGB + radiometric thermal + wound-tissue masks has not been acquired. Post-TKA remains access-gated. TR-020 is done for the offline demonstrator; TR-003/004 alignment validation, TR-008 controlled modality experiments, TR-009 abnormality localization, TR-013 fusion evidence, and TR-019 training remain proposed/blocked as listed.
- No production application exists. Public clinical datasets TRICVI-C and LUTSeg have been acquired, but neither is the complete RGB+thermal+wound-label cohort. The post-TKA adapter/model-training scaffold remains access-gated; its registration transforms, label provenance, DUA, and patient-level data are unverified.
- Acquired locally: Caltech labeled RGB-T archive with creator split lists; FDA/PhysioNet CSV tables; and a manifest-backed StereoThermoLegs sample of 20 paired frames from each of four train participants and one held-out test participant. The FDA GitHub data have no image pixels. Dataset tasks and labels remain distinct; see [dataset research and acquisition plan](DATASET_RESEARCH.md).
- A compact U-Net segmentation script and checkpoints implement a one-epoch Caltech pilot comparing RGB, thermal16 intensity, and early channel fusion. On 256 train / 64 validation / 64 test samples at 128x128, test mIoU (classes 2–11) was 0.099 RGB, 0.063 thermal, 0.100 fusion. This is a smoke test using a small, order-selected subset, not a reliable performance comparison or clinical result. The thermal16 values were not verified as Celsius.
- Immediate next: show the offline review page; implement a LUTSeg RGB-only dataset adapter; implement TRICVI-C grid parsing, capture grouping, and measured registration checks; then select the exact first training task. A multimodal wound model remains blocked until one source contains approved paired RGB, calibrated thermal, and independently reviewed wound masks. Do not train on or cross-pair the current separate cohorts.
- No acquired source establishes one all-domain model or clinical abnormality performance. A clinical outcome requires separately rights-cleared paired radiometric data with independent outcome and spatial labels. See [process and model design](PROCESS_MODEL_DESIGN.md).
- A [KSCST SPP 2026–27 proposal draft](KSCST_SPP_50th_Proposal_2026-27_Filled.docx) now describes the staged engineering prototype. It does not establish dataset access, clinical labels, hardware availability, or implemented model performance.

## PDF-to-architecture reconciliation

| Topic | Older knee architecture | PDF-led requirement |
| --- | --- | --- |
| Project goal | Knee injury/inflammation classification and severity | General physiological abnormality **detection and spatial localization**; post-TKA wound tissue localization is the first selected clinical adapter, conditional on access |
| Registration | Fixed homography treated as sufficient | Multimodal registration is required; geometric, feature-based, calibration-assisted, and learned approaches are candidates; validate rather than assume homography |
| Anatomical processing | Knee landmark ROIs after registration | RGB-guided anatomical ROI and segmentation are central; ROI cues may guide registration; multimodal segmentation is a comparison |
| Thermal representation | Hand-crafted knee statistics | Explicit quantitative biomarkers **and** a learned thermal feature path |
| Fusion | Feature concatenation primary; deep fusion optional | Separate modality encoders and adaptive cross-modal fusion are the target research architecture; concatenation and early fusion are baselines |
| Output | Class/severity and knee overlay | Classification **plus localized abnormality output** with anatomical and thermal evidence |
| Evaluation | A few registration/classification measures | Six ablations and distinct registration, segmentation, temperature, classification, and localization evaluations |

The older architecture remains a historical knee-specific proposal and can inform only a later knee adapter. The PDF's proposed framework and cited performance are research context, not proof that an integrated model will generalize across body regions or tasks.

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

### 2026-10-12 — Dataset evidence and staged acquisition

- **Changed:** Added TR-015 and identified separate engineering datasets for knee anatomy/registration and absolute-temperature parsing. The paired radiometric clinical knee cohort and independent abnormality labels remain blocked requirements; no dataset has been acquired or validated locally.
- **Reason/evidence:** Direct Zenodo, dataset-owner, creator, and primary-paper sources in `docs/DATASET_RESEARCH.md` show that promising sources cover different subsets of the four required data properties. StereoThermoLegs supplies paired posterior-leg images, knee masks and calibration but 8-bit mapped thermal values; SGRT-140 supplies raw radiometric pairs in nonclinical scenes.
- **Files affected:** `docs/DATASET_RESEARCH.md`, `docs/TR.md`, `docs/NTR.md`, `AGENTS.md`, `README.md`.
- **Verification:** Checked primary source pages, dataset access statements, repository status and documentation links; no file-level dataset inspection was possible because no candidate has been downloaded.
- **Remaining risk/next step:** Implement the synthetic contract and manifest, inspect a small licensed sample from each engineering source, and obtain rights-cleared paired radiometric knee data before clinical model claims.

### 2026-10-27 — KSCST proposal drafted

- **Changed:** Reviewed TR-001–TR-015; no technical requirement or status changed. Added the funding proposal draft to current project status. Its proposed work follows the staged data, registration, ROI, radiometric measurement, and conditional model path in TR-001–TR-015.
- **Reason/evidence:** The user requested a concise application using the PDF-led project and existing form. The proposal describes future deliverables without presenting missing data or unvalidated predictions as completed results.
- **Files affected:** `docs/KSCST_SPP_50th_Proposal_2026-27_Filled.docx`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Opened the edited Word document, exported and visually checked its 11 pages, and checked the project scope, references, work plan, and budget against the form and current requirements.
- **Remaining risk/next step:** Confirm real data access, camera/compute facilities, and any independent labels before those proposal activities are claimed as achievable or completed.

### 2026-10-31 — Multi-domain data acquired and baseline pilot trained

- **Changed:** Recorded local acquisition of Caltech RGB-T labeled pairs and official splits, FDA/PhysioNet tables, and a 100-pair StereoThermoLegs subset spanning four train participants and one held-out participant. Added scripts for a Caltech RGB/thermal/fusion segmentation pilot and selective StereoThermoLegs acquisition. TR-016 remains ready rather than done because this is a small smoke test, not the required fair, sufficiently trained evaluation.
- **Reason/evidence:** Local file inspection confirmed Caltech RGB, thermal16, and mask files share 960x600 dimensions and official split counts (1,731/272/279); Caltech images are already rectified. Stereo manifest records 400 files/100 pairs with source members and SHA-256. FDA repository files are six derived CSV tables and no image pixels. The pilot trained on RTX 3050 GPU for one epoch, 256 train and 64 validation/test samples at 128x128; test mIoU was RGB 0.099, thermal 0.063, early fusion 0.100.
- **Files affected:** `.gitignore`, `docs/TR.md`, `docs/NTR.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `datasets/README.md`, `outputs/README.md`, `scripts/fetch_stereothermolegs_subset.py`, `scripts/train_caltech_segmentation.py`, local ignored dataset/output files.
- **Verification:** Verified the Caltech archive MD5 against publisher value; inspected sample image modes, dimensions, mask IDs, and official pair/split counts; downloaded all three publisher StereoThermoLegs calibration YAMLs and matched their MD5 values to Zenodo; inspected RGB/IRT and mask dimensions plus label IDs; checked SHA-256 for all 400 StereoThermoLegs files against the manifest with zero mismatches; cleaned unmanifested interrupted-download files; trained all three model arms and saved JSON metrics/checkpoints; checked `git status` and whitespace diff.
- **Remaining risk/next step:** Caltech sample uses an order-selected subset and one epoch, so results do not establish a fusion benefit. Resolve Caltech license discrepancy before redistribution; confirm thermal16 units; verify StereoThermoLegs transform direction/units, implement depth-aware alignment, and measure held-out registration error before the anatomy pilot. Clinical outcome/localization data and approval remain unavailable.

### 2026-11-13 — Additional RGB-thermal datasets screened

- **Changed:** Reviewed TR-001–TR-017; no requirement wording or status changed. Added a sourced shortlist of additional engineering datasets and ranked PST900 as the next acquisition candidate, subject to license confirmation (TR-015). Recorded that the new sources do not meet the clinical outcome/localization requirements.
- **Reason/evidence:** Primary owner/creator pages and dataset papers report complementary uses: PST900 has aligned RGB-T, depth, raw-encoded thermal, and pixel labels; LLVIP supports aligned low-light detection; FLIR ADAS provides multi-class detection and pre-AGC frames; KAIST provides a large pedestrian benchmark. Tracking and larger day/night scene candidates are optional. Access terms, annotation coverage, and task fit differ.
- **Files affected:** `docs/DATASET_RESEARCH.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Rechecked owner/creator access pages and primary dataset descriptions for scale, modalities, labels, calibration/alignment, and stated access terms; checked current repository status before editing. No additional archive was downloaded or used.
- **Remaining risk/next step:** Confirm PST900 dataset rights, file availability, and thermal conversion metadata before acquisition; retain the current data-contract and StereoThermoLegs alignment work as the immediate implementation tasks. No new candidate supports clinical abnormality claims.

### 2026-11-13 — Post-TKA wound localization implementation scaffold

- **Changed:** Selected post-TKA wound-tissue pixel localization as the first clinical task-specific adapter while preserving the multi-domain project scope. Added TR-018 for the approved-data manifest/preflight contract and TR-019 for the blocked RGB-only, thermal-only, and fused model evaluation. Implemented a raw-radiometry dataset loader, thermal-to-RGB homography warp, manifest/subject-split/access gates, DINOv2 dual encoders with gated bidirectional fusion and query-mask decoder, per-class metrics, and patient-cluster bootstrap intervals. Added a manifest template, handling note, optional dependency list, and unsent access-request draft.
- **Reason/evidence:** The primary post-TKA study reports RGB/EO and radiometric IR processing plus wound tissue labels, but states source data are not public and can be considered only through reasonable request, DUA, and sponsor approval. Its wound-segmentation development set includes public imagery; mask provenance in the paired clinical subset must be confirmed before training. The DINOv2 base checkpoint is available under the model card's stated Apache-2.0 license; the query-mask decoder and cross-modal fusion are project-specific.
- **Files affected:** `.gitignore`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `docs/POST_TKA_DATA_ACCESS_REQUEST.md`, `datasets/README.md`, `datasets/post_tka_wound/README.md`, `datasets/post_tka_wound/manifest.template.json`, `requirements-medical.txt`, `scripts/post_tka_wound_localization.py`.
- **Verification:** CLI help, syntax compilation, and `git diff --check` passed (Git only reports pre-existing line-ending normalization warnings). Synthetic-only fixtures passed patient-disjoint manifest validation, identity thermal-to-RGB projection, aspect-preserving paired loading, access-status blocking, metrics/bootstrap calculations, and forward/backward training/checkpoint reload for RGB-only, thermal-only, and fusion modes. No clinical training was run because the source dataset is not acquired; the local environment has CPU-only PyTorch and no Transformers install.
- **Remaining risk/next step:** Obtain written data permission and approved storage; verify the actual clinical masks, RGB/IR pairing, °C semantics, transform direction, held-out landmark accuracy, and patient IDs. Current model outputs and metrics will remain research-only and cannot establish diagnostic utility.

### 2026-11-13 — Clinical data demonstrator and dataset acquisition

- **Changed:** Added TR-020 and marked it done for an offline review demonstrator. Downloaded TRICVI-C v2 (1,284 files) and LUTSeg (141 RGB wound images); updated implementation status to separate measured thermal data from wound annotation. The user’s broader multi-domain direction supersedes post-TKA as the default first clinical task; preserved post-TKA as an access-gated future adapter.
- **Reason/evidence:** TRICVI-C provides co-indexed RGB, thermal display imagery and raw numeric Celsius maps, but no tissue masks. LUTSeg provides patient-level split files and clinician-labelled tissue masks, but no thermal input. They are separate tasks, not a single paired training set.
- **Files affected:** `README.md`, `docs/TR.md`, `docs/NTR.md`, `docs/PROJECT_CONTEXT.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `docs/BASELINE_DEMO.md`, `datasets/README.md`, `scripts/download_mendeley_public_dataset.py`, `scripts/build_review_demo.py`, local ignored dataset files and generated review page.
- **Verification:** Verified all 1,284 TRICVI-C files against publisher SHA-256 hashes. Checked LUTSeg's publisher `checksums.sha256`: 1,028 exact matches, 21 text files match when normalized from Windows CRLF, one README hash discrepancy remains. Inspected sample RGB 640x480 / thermal 320x240 / temperature grid 320x240, sample Celsius range 21.73–33.43°C, and LUTSeg image/mask dimensions and label IDs. Confirmed 427 TRICVI-C frame IDs have RGB/thermal/CSV triplets; verified LUTSeg split counts and no patient overlap; checked the generated page's key provenance text and JavaScript syntax. Built the self-contained review HTML.
- **Remaining risk/next step:** Validate registration using independent landmarks; resolve the LUTSeg README checksum discrepancy; add a dataset adapter for LUTSeg before training; train only after selecting the exact task. No training was run; the review output is not a model prediction. A single clinical dataset with paired RGB, radiometric thermal, and wound tissue masks remains unavailable.
