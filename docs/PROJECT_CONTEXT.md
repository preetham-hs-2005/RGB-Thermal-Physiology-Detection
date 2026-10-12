# RGB-Thermal Knee Physiology Detection: Project Context

## Purpose

Develop a research system that combines visible-light RGB and radiometric thermal images to locate knee anatomy, measure skin-surface temperature patterns, compare corresponding left/right regions, and investigate whether those measurements help characterize physiological abnormality. RGB supplies visible anatomical context; thermal supplies estimated surface temperature. Injury, inflammation, disease, or severity prediction is a separate capability requiring suitable reference labels and validation.

The initial system accepts recorded image pairs. Live camera adapters should later use the same data contract. This document describes the enduring project from acquisition through evaluation and use. Current requirements, progress, decisions, and work history belong in [TR.md](TR.md) and [NTR.md](NTR.md).

## Intended users and scope

- Researchers and developers inspect images, calibration, ROI masks, measurements, and model experiments.
- Clinical collaborators, if engaged, review acquisition, anatomical definitions, outcome labels, and interpretation.
- Future end users are considered only after the use case and validation are defined. The research prototype does not issue a diagnosis.

The system covers image ingestion, synchronization, calibration, registration, quality checks, knee ROI definition, thermal feature calculation, optional feature fusion and predictive models, visualization, structured export, and evaluation. It supports single-session bilateral comparison and repeated-session trends when data permit.

Thermal images estimate skin-surface temperature under sensor calibration and emissivity assumptions. Measurements can vary with room conditions, airflow, clothing, distance, motion, and physiology unrelated to knee injury. Neither temperature nor RGB appearance alone establishes a specific condition.

## End-to-end workflow

1. **Acquire or load:** Read RGB pixels and thermal temperature values with timestamps, units, sensor metadata, orientation, and subject/session IDs. Record the pairing rule and time difference.
2. **Check quality:** Validate dimensions, temperature units, valid pixels, exposure or saturation, and required metadata. Preserve raw inputs and provenance.
3. **Calibrate and register:** Estimate thermal-to-RGB geometry from a target or known correspondences. Warp temperature and validity masks into RGB space. Evaluate alignment using points or regions not used for fitting.
4. **Preprocess:** Apply documented modality-specific processing while retaining raw data, units, masks, transforms, and processing history. A false-color thermal view is for display, not temperature calculation.
5. **Locate anatomy:** Determine view and left/right identity, knee landmarks, and named ROI masks. Reference annotations define the regions against which automation is evaluated.
6. **Measure:** Compute temperature statistics, reference-relative values, spatial patterns, bilateral asymmetry, and quality indicators for each valid ROI. Keep RGB-derived features identifiable.
7. **Model, if labels permit:** Compare RGB-only, thermal-only, simple fusion, and more complex multimodal models on the same subject-level partitions with independently defined targets.
8. **Report:** Show RGB and aligned thermal overlays, ROI boundaries, measurements and units, quality flags, and any appropriately validated model result. Export a versioned session record.
9. **Evaluate:** Test alignment, ROI consistency, temperature repeatability, classification, and localization as separate outcomes. Document failures.

## Seven-layer architecture

| Layer | Responsibility | Principal output |
| --- | --- | --- |
| L1 Acquisition | Recorded/live sources and frame pairing | Paired RGB and radiometric thermal observation |
| L2 Calibration and registration | Thermal-to-RGB transform and independent quality check | Transform, aligned temperature map, valid mask, errors |
| L3 Preprocessing | Documented corrections and normalization | Processed views with raw references |
| L4 Anatomical ROI | Knee side, view, landmarks, and named masks | ROI masks and annotation provenance |
| L5 Feature extraction and fusion | Thermal biomarkers, RGB features, optional fusion | ROI-level features with units and missingness |
| L6 Detection or estimation | Baselines and later task-specific models | Research prediction and model metadata |
| L7 Visualization and reporting | Overlays, tables, trends, exports | Human and machine-readable session report |

Every layer retains source, capture times, coordinate frames, transforms, sensor details, valid-pixel masks, ROI definitions, processing versions, and quality flags as applicable. Downstream steps may need earlier metadata, not only the immediately preceding layer's output.

## Calibration and anatomy

Homography is the proposed starting transform, not a guarantee of pixel correspondence. A knee is curved and camera separation creates parallax. Validate alignment across the intended poses and distances; flag failed mapping. Invalid pixels created by warping remain invalid for temperature calculations. A fixed rig may reuse geometry while its relative camera positions remain fixed; sensor temperature calibration is a separate concern. Calibration records include target design, correspondences, transform direction, fit method, residuals, and recalibration conditions.

Define imaging view, posture, knee exposure, camera distance and angle, left/right orientation, room conditions, and acclimatization. Named ROI boundaries need operational definitions and versions. The architecture suggests medial, lateral, patellar, and suprapatellar regions; a clinical collaborator should review exact boundaries before medical interpretation. Manual ROI masks can serve as reference data before automating pose or segmentation.

For each ROI, preserve valid-pixel count and fraction, central temperature, spread, useful extremes, and reference-relative or contralateral differences. Define the subtraction order for asymmetry. Report acquisition and registration quality beside measurements. Thermal texture from a non-radiometric image is not a temperature biomarker.

## Data and annotation strategy

- **Synthetic pairs with known geometry** test contracts, registration, masks, and failures. They cannot validate physiology.
- **General RGB-thermal pairs** can exercise image handling and some alignment methods. They do not establish knee anatomy, radiometric biomarkers, or clinical outcomes unless those properties are present.
- **Unpaired knee RGB or thermal data** may inform anatomy or exploratory thermal work but cannot validate the complete paired pipeline.
- **Paired knee RGB and radiometric thermal observations** support end-to-end measurement evaluation when sensor details, permission, and acquisition protocol are documented.
- **Independent expert or clinical labels** are needed for ROI accuracy, abnormality localization, disease classification, or severity evaluation, depending on the task.

Avoid placing images from one person in both training and test partitions. Record class counts, missing data, and acquisition differences. “One knee is warmer” is a measured comparison; “ligament injury” requires independent clinical evidence. X-ray severity may be examined as an association but is not a substitute for paired-image localization ground truth.

## Model and evaluation strategy

Start with interpretable ROI features and simple single-modality baselines. Feature-level fusion is a candidate for small labeled datasets. Four-channel early fusion, dual-stream networks, cross-modal attention, and Transformers are optional comparisons justified by suitable data and demonstrated improvement. Any fusion model must explicitly include both RGB and thermal paths.

Classification, severity estimation, and spatial localization are different tasks. A classifier attention map is not automatically a validated abnormality map. Each needs its own target and assessment:

| Question | Evidence |
| --- | --- |
| Alignment | Held-out landmark error, ROI overlap, valid coverage, results by pose/distance |
| ROI consistency | Protocol or expert reference masks, overlap/boundary error, reviewer agreement |
| Temperature reliability | Units, sensor calibration, reference measurement when available, repeat-session variance, environment sensitivity |
| Benefit of fusion | Same-data RGB-only/thermal-only comparisons, subject-level splits, ablations, uncertainty |
| Outcome prediction | Independent outcome labels, class counts, sensitivity/specificity, precision/recall, PR-AUC when appropriate, external validation |
| Abnormality localization | Spatial reference annotations and pixel/region metrics distinct from classification |

Count and report failures such as misregistration, missing knee, occlusion, inadequate valid thermal area, sensor drift, and missing metadata rather than silently removing them from performance figures.

## Responsible use and records

Use data with a documented permission and consent basis. Minimize personal identifiers and keep identifiable medical images out of the repository unless an approved handling plan exists. Preserve reproducibility through source data, code/config, annotation versions, and experiment records. Research reports distinguish measurement, inference, and clinically established findings.

[TR.md](TR.md) and [NTR.md](NTR.md) are the living records for requirements, status, decisions, open questions, and dated updates. Root [AGENTS.md](../AGENTS.md) tells future workers how to maintain them. Change this context document only when the enduring objective, scope, workflow, or system design changes.

## Reference documents

- [Architecture](../RGB_Thermal_Architecture.md): original seven-layer proposal. Supplied copy: `C:/Users/preet/Downloads/RGB_Thermal_Architecture (1).md`.
- Systematic review: `C:/Users/preet/Downloads/Mobile Devices/RGB-Thermal_Systematic_Review_IEEE.pdf`. It maps relevant methods; check consequential claims in primary studies before using them as implementation or clinical evidence.
