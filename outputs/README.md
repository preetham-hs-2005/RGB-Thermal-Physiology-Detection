# Local model outputs

Generated checkpoints and metrics stay out of Git. The Caltech smoke-test checkpoints and JSON report are in `caltech_rgbt_runs/`; their setup, split limits, and interpretation are recorded in `docs/DATASET_RESEARCH.md` and `docs/PROCESS_MODEL_DESIGN.md`.

The trained LUTSeg RGB wound-tissue transformer checkpoint and `training_report.json` are in `lutseg_transformer_baseline/`. Launch the desktop inference viewer from the repository root with `python scripts/run_lutseg_baseline.py`. It includes a separate TRICVI-C RGB/thermal/Celsius viewer; that dataset is not used by the wound model. See `docs/BASELINE_MODEL.md` for metrics, training details, and limits.
