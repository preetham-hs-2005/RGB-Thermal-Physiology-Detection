# RGB-Thermal Physiological Abnormality Detection and Localization

A research project to combine RGB and radiometric thermal images for anatomical registration and segmentation, quantitative temperature biomarkers, multimodal feature fusion, physiological abnormality classification, and spatial localization. **The knee is the first application.** The systematic review PDF controls the project direction over the older knee architecture. The project is not a clinical diagnostic tool.

## Documentation

- [Project context](docs/PROJECT_CONTEXT.md) — the overall purpose, workflow, architecture, data strategy, and evaluation approach.
- [Systematic review PDF](docs/RGB_Thermal_Systematic_Review_IEEE.pdf) — controlling project direction.
- [Technical requirements](docs/TR.md) — technical requirements, implementation status, open decisions, and change history.
- [Non-technical requirements](docs/NTR.md) — data permissions, privacy, responsible use, evidence status, and change history.
- [Architecture proposal](docs/RGB_Thermal_Architecture.md) — the older knee-specific design; consult the PDF-led requirements where they differ.
- [Agent working agreement](AGENTS.md) — reading order and documentation update rules.

## Intended development path

1. Define a paired RGB/thermal record with timestamps, temperature units, calibration metadata, and valid-pixel masks.
2. Load recorded pairs and check synchronization and data quality.
3. Use RGB anatomical cues and validate thermal-to-RGB registration and segmentation for the knee pilot.
4. Calculate interpretable ROI temperature biomarkers and produce a measured overlay.
5. With independent class and spatial labels, compare RGB-only, thermal-only, early-fusion, dual-stream, cross-attention, and attention-plus-biomarker models; evaluate classification and localization separately.

For what has actually been implemented and what remains blocked, read [TR.md](docs/TR.md) and [NTR.md](docs/NTR.md). A false-color thermal image is not a temperature measurement, and a research model output is not a diagnosis.
