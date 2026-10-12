# Technical Requirements (TR)

Last reviewed: 2026-10-12 (Asia/Calcutta)

Status values: **ready** = implementable with current information; **blocked** = needs data, labels, or hardware; **proposed** = needs design or evidence review; **done** = implemented and verified.

## Current requirements

| ID | Status | Requirement and acceptance evidence |
| --- | --- | --- |
| TR-001 | Ready | Define a versioned paired-frame record: RGB array, thermal temperature array, units, capture timestamps, sensor/subject/session IDs, calibration metadata, orientation, and validity masks. Reject missing or contradictory units. |
| TR-002 | Ready | Implement a recorded-data loader and deterministic pairing rule with a maximum permitted timestamp difference; report rejected or unmatched frames. Do not assume matching filenames prove synchronization. |
| TR-003 | Proposed | Define a calibration-point format and estimate a thermal-to-RGB transform with robust fitting. Keep source/destination coordinate conventions explicit and preserve transform provenance. |
| TR-004 | Proposed | Warp measured temperature values with a separate valid-pixel mask. Report held-out reprojection error and ROI overlap; flag failed registration rather than producing unqualified measurements. Test whether a homography is adequate for the chosen knee poses and distances. |
| TR-005 | Proposed | Specify acquisition view, posture, distance, left/right orientation, and named knee ROI annotation rules. Store masks and annotations independently of any pose model. |
| TR-006 | Blocked | Compute ROI thermal statistics, reference-relative values, and bilateral differences from radiometric input; include valid-pixel fraction and an explicit sign convention. Requires paired temperature data and ROI masks for meaningful validation. |
| TR-007 | Blocked | Produce an RGB overlay and machine-readable per-session report that includes units, quality flags, transform ID, ROI definitions, and provenance. Requires upstream data contracts and quality measures. |
| TR-008 | Blocked | Train and compare RGB-only, thermal-only, and simple fused feature baselines using subject-level held-out splits, class counts, and uncertainty. Requires sufficient paired data and independent outcome labels. |
| TR-009 | Blocked | Add a spatial abnormality model only with reference localization annotations; evaluate its pixel/region localization separately from classification. |
| TR-010 | Blocked | Add live camera adapters without changing downstream record contracts after actual sensor output formats, synchronization, and calibration are characterized. |

## Open technical decisions

- Which rights-cleared paired fixture and radiometric file format will be used first?
- What is the initial image view and anatomical ROI protocol?
- Which calibration target and held-out acceptance threshold suit the intended camera geometry?
- What independent clinical or expert reference labels, if any, will support prediction?

## Current implementation status

- No application code, dependency manifest, test fixture, dataset, sample pair, calibration correspondence, or outcome label has been added to this repository.
- `RGB_Thermal_Architecture.md` currently contains the committed architecture content. It was empty when the initial documentation was written and was restored outside this work during this session. `README.md` remains deleted in the working tree and has been preserved as found.
- Stage 0 is next: define the paired-frame contract and obtain or construct a clearly marked fixture. Stage 1 is the recorded-pair loader. Registration, ROI measurement, and prediction follow their data and validation gates.
- The key technical data gap is a paired **radiometric RGB/thermal knee** sample with known units, sensor metadata, and permission to use it. General RGB-thermal image datasets can help with image handling but cannot by themselves validate knee temperature biomarkers.

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
