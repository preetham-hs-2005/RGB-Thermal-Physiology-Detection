# Post-TKA wound localization data

No clinical images are included in this repository. The cohort described by the
study is proprietary and can be shared only by the owners under a data-use
agreement and sponsor approval. Do not download, stage, or commit patient
images until written terms and approved storage are in place.

The model loader expects a dataset-local `manifest.json`. Copy
[`manifest.template.json`](manifest.template.json), fill it only from the
approved file manifest, and keep source images and radiometric files outside
Git. Training is blocked unless the manifest says `access_status` is
`approved_for_research` and cites the applicable license/DUA in
`access_terms_ref`.

Each record must also include a unique `pairing_id`, a documented
`pairing_basis`, and (when the source provides timestamps) a
`timestamp_delta_ms` checked against top-level `max_pair_delta_ms`. Include
`thermal_conversion_method` for every thermal array, even when the provider
already exported the values in Celsius. Store `thermal_to_rgb` as a 3x3
matrix mapping thermal pixel coordinates into RGB pixel coordinates and keep
held-out landmark pairs separate from calibration points. The loader uses
aspect-preserving resize and ignore-pads masks rather than stretching images.

Expected mask IDs are: 0 background, 1 open wound, 2 granulation, 3
infection-associated exudate, 4 necrosis, and 255 ignore/unknown. Confirm that
these annotations are present on the approved paired clinical cohort; the
published paper's wound-segmentation development set also incorporated
public images.

Run `python scripts/post_tka_wound_localization.py --manifest datasets/post_tka_wound/manifest.json --validate-only`
before training. It checks subject-disjoint splits, file formats, label IDs,
thermal coverage after projection, and held-out registration landmarks. It
does not verify the clinical meaning of annotations or grant data rights.

When approved files are available, run the three controlled arms on the same
manifest and splits with `--mode all`. The script uses pretrained DINOv2
encoders with a project-specific query-mask transformer decoder. The thermal
branch receives normalized Celsius, relative temperature, and gradient
channels; validity remains a separate quality/attention mask. Keep the
original radiometric arrays and conversion metadata unchanged.
