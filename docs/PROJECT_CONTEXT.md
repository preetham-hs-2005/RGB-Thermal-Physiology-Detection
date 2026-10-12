# RGB-Thermal Physiological Abnormality Detection and Localization: Project Context

## Purpose

Develop a research system that combines visible-light RGB and radiometric thermal images to **detect and spatially localize physiological abnormalities** with interpretable anatomical and temperature evidence. RGB supplies visible anatomical context; thermal supplies estimated surface temperature and quantitative biomarkers. The system integrates multimodal registration, anatomical ROI segmentation, modality-specific feature extraction, adaptive fusion, classification, and abnormality localization. These are the target capabilities described in the review PDF, which the user designated as authoritative over the older architecture.

The **knee is the first application and validation domain**. Its left/right comparison and named regions provide a concrete pilot, while the data contracts, registration, feature interfaces, and evaluation design remain adaptable to other anatomical applications. A knee-specific injury or disease claim still requires a separately defined clinical target and reference labels.

The initial system accepts recorded image pairs. Live camera adapters should later use the same data contract. This document describes the enduring PDF-led project from acquisition through evaluation and use. Current requirements, progress, decisions, and work history belong in [TR.md](TR.md) and [NTR.md](NTR.md).

## Intended users and scope

- Researchers and developers inspect images, calibration, ROI masks, measurements, and model experiments.
- Clinical collaborators, if engaged, review acquisition, anatomical definitions, outcome labels, and interpretation.
- Future end users are considered only after the use case and validation are defined. The research prototype does not issue a diagnosis.

The system covers image ingestion, synchronization, RGB and thermal preprocessing, calibration, registration, quality checks, anatomical ROI localization and segmentation, explicit thermal biomarker calculation, separate RGB and thermal feature learning, adaptive cross-modal fusion, abnormality classification and localization, visualization, structured export, and evaluation. Bilateral comparison and repeated-session trends are knee-pilot measurements when data permit.

Thermal images estimate skin-surface temperature under sensor calibration and emissivity assumptions. Measurements can vary with room conditions, airflow, clothing, distance, motion, and physiology unrelated to knee injury. Neither temperature nor RGB appearance alone establishes a specific condition.

## End-to-end workflow

1. **Acquire or load:** Read RGB pixels and thermal temperature values with timestamps, units, sensor metadata, orientation, and subject/session IDs. Record the pairing rule and time difference.
2. **Check quality:** Validate dimensions, temperature units, valid pixels, exposure or saturation, and required metadata. Preserve raw inputs and provenance.
3. **Find coarse RGB anatomy and register:** RGB preprocessing and coarse anatomical cues can guide thermal-to-RGB registration. Estimate geometry from a target or multimodal correspondences, warp temperature and validity masks, and evaluate alignment using points or regions not used for fitting.
4. **Preprocess:** Apply documented modality-specific processing while retaining raw data, units, masks, transforms, and processing history. A false-color thermal view is for display, not temperature calculation.
5. **Finalize anatomical ROIs and segment:** Refine named RGB and thermal ROIs after alignment; evaluate multimodal segmentation when labels permit. For the knee pilot, preserve view and left/right identity. Reference annotations define the regions against which automation is evaluated.
6. **Measure and learn features:** Compute temperature statistics, reference-relative values, gradients, bilateral asymmetry where appropriate, and quality indicators. Extract RGB and thermal features through identifiable modality-specific paths.
7. **Fuse and predict, if labels permit:** Compare RGB-only, thermal-only, early fusion, dual-stream, cross-modal attention, and attention plus explicit thermal features on the same subject-level partitions. Produce classification and a spatial abnormality output with separate ground truths.
8. **Report:** Show RGB and aligned thermal overlays, ROI boundaries, temperature evidence, quality flags, and evaluated classification/localization outputs. Export a versioned session record.
9. **Evaluate:** Test alignment, anatomical segmentation, temperature repeatability, classification, localization, and the contribution of each fusion component as separate outcomes. Document failures.

## Seven-layer architecture

These are functional components, not a rigid execution order. A coarse RGB ROI may guide registration; registration and final segmentation may then be refined together. The PDF describes both ROI-guided and registration-first approaches.

| Layer | Responsibility | Principal output |
| --- | --- | --- |
| L1 Acquisition | Recorded/live sources and frame pairing | Paired RGB and radiometric thermal observation |
| L2 Preprocessing | Documented RGB/thermal corrections and normalization | Processed views with raw references |
| L3 RGB anatomy | Coarse RGB-guided anatomical localization; knee side/view for the pilot | Initial ROI cues and annotation provenance |
| L4 Registration and segmentation | Thermal-to-RGB transform, thermal ROI mapping, final anatomical masks, independent quality checks | Aligned temperature map, valid mask, ROI masks, errors |
| L5 Feature extraction and fusion | Explicit thermal biomarkers, separate RGB/thermal encoders, and adaptive cross-modal fusion | ROI-level and spatial features with units and missingness |
| L6 Detection and localization | Baselines, classification, and abnormality-region prediction | Class result, spatial output, and model metadata |
| L7 Visualization and reporting | Overlays, thermal evidence, spatial results, trends, exports | Human and machine-readable session report |

Every layer retains source, capture times, coordinate frames, transforms, sensor details, valid-pixel masks, ROI definitions, processing versions, and quality flags as applicable. Downstream steps may need earlier metadata, not only the immediately preceding layer's output.

## Calibration and anatomy

Multimodal registration is required; homography is one geometric baseline, not a mandated final method or a guarantee of pixel correspondence. Compare geometric/calibration-assisted approaches with feature-based or learned registration when data and reference correspondences permit. A knee is curved and camera separation creates parallax. Validate alignment across the intended poses and distances; flag failed mapping. Invalid pixels created by warping remain invalid for temperature calculations. Calibration records include target design, correspondences, transform direction, fit method, residuals, and recalibration conditions.

Define imaging view, posture, exposed anatomy, camera distance and angle, orientation, room conditions, and acclimatization for each application. Named ROI boundaries need operational definitions and versions. For the knee pilot, the older architecture suggests medial, lateral, patellar, and suprapatellar regions; a clinical collaborator should review exact boundaries before medical interpretation. Manual ROI masks can serve as reference data before automating pose or segmentation.

For each ROI, preserve valid-pixel count and fraction, central temperature, spread, useful extremes, and reference-relative or contralateral differences. Define the subtraction order for asymmetry. Report acquisition and registration quality beside measurements. Thermal texture from a non-radiometric image is not a temperature biomarker.

## Data and annotation strategy

- **Synthetic pairs with known geometry** test contracts, registration, masks, and failures. They cannot validate physiology.
- **General RGB-thermal pairs** can exercise image handling and some alignment methods. They do not establish knee anatomy, radiometric biomarkers, or clinical outcomes unless those properties are present.
- **Unpaired knee RGB or thermal data** may inform anatomy or exploratory thermal work but cannot validate the complete paired pipeline.
- **Paired knee RGB and radiometric thermal observations** support end-to-end measurement evaluation when sensor details, permission, and acquisition protocol are documented.
- **Independent expert or clinical labels** are needed for ROI accuracy, abnormality localization, disease classification, or severity evaluation, depending on the task.

Avoid placing images from one person in both training and test partitions. Record class counts, missing data, and acquisition differences. “One knee is warmer” is a measured comparison; “ligament injury” requires independent clinical evidence. X-ray severity may be examined as an association but is not a substitute for paired-image localization ground truth.

## Model and evaluation strategy

Start with interpretable ROI features and single-modality baselines. The target research architecture has separate RGB and thermal feature paths, an explicit thermal-biomarker branch, adaptive cross-modal fusion, classification, and spatial localization. Compare it with early fusion and simpler feature-level methods rather than assuming the complex model is superior. Cross-modal attention and a CNN/Transformer branch are research candidates that require suitable data and ablation evidence. Any fusion model must explicitly include both RGB and thermal paths.

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

- [Systematic review PDF](RGB_Thermal_Systematic_Review_IEEE.pdf) (controlling project direction): its proposed framework and research objective take precedence over the older architecture; check consequential empirical claims in primary studies. This repository copy matches the user-supplied file from `C:/Users/preet/Downloads/Mobile Devices/`.
- [Architecture](RGB_Thermal_Architecture.md): older knee-specific seven-layer proposal. Supplied copy: `C:/Users/preet/Downloads/RGB_Thermal_Architecture (1).md`. Its implementation choices remain candidates only where they agree with the PDF-led direction.
