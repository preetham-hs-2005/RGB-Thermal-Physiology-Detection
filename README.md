# RGB-Thermal Physiological Abnormality Detection and Localization

A multi-domain research project to combine RGB and thermal images for registration, task-specific anatomy/scene segmentation, quantitative temperature biomarkers when radiometric inputs exist, multimodal feature fusion, and task-specific classification or localization. Body regions and nonclinical perception tasks are handled with dataset-specific labels and evaluations. The project is not a clinical diagnostic tool.

## Documentation

- [Project context](docs/PROJECT_CONTEXT.md) — the overall purpose, workflow, architecture, data strategy, and evaluation approach.
- [Systematic review PDF](docs/RGB_Thermal_Systematic_Review_IEEE.pdf) — controlling project direction.
- [Technical requirements](docs/TR.md) — technical requirements, implementation status, open decisions, and change history.
- [Non-technical requirements](docs/NTR.md) — data permissions, privacy, responsible use, evidence status, and change history.
- [Dataset research and acquisition plan](docs/DATASET_RESEARCH.md) — sourced candidate matrix, gaps, access questions, and staged data plan.
- [Process and model design](docs/PROCESS_MODEL_DESIGN.md) — multi-domain data flow, alignment tiers, model comparisons, and training gates.
- [Baseline review demo guide](docs/BASELINE_DEMO.md) — how to open and present the current offline data/model demonstrator.
- [Architecture proposal](docs/RGB_Thermal_Architecture.md) — the older knee-specific design; consult the PDF-led requirements where they differ.
- [Agent working agreement](AGENTS.md) — reading order and documentation update rules.

## Intended development path

1. Define a paired RGB/thermal record with timestamps, temperature units, calibration metadata, and valid-pixel masks.
2. Load recorded pairs and check synchronization and data quality.
3. Calibrate or estimate thermal-to-RGB registration, validate it with held-out landmarks/masks, and preserve dataset-specific anatomical schemas.
4. Calculate interpretable ROI temperature biomarkers and produce a measured overlay.
5. With independent class and spatial labels, compare RGB-only, thermal-only, early-fusion, dual-stream, cross-attention, and attention-plus-biomarker models; evaluate classification and localization separately.

For what has actually been implemented and what remains blocked, read [TR.md](docs/TR.md) and [NTR.md](docs/NTR.md). A false-color thermal image is not a temperature measurement, and a research model output is not a diagnosis.
