# Non-Technical Requirements (NTR)

Last reviewed: 2026-11-13 (Asia/Calcutta)

Status values: **ready** = applies now; **blocked** = depends on external decisions or resources; **proposed** = needs agreement; **done** = demonstrated.

## Current requirements

| ID | Status | Requirement and acceptance evidence |
| --- | --- | --- |
| NTR-001 | Ready | Present the project as a research prototype. Reports must distinguish measured surface temperature, research predictions, and clinically validated conclusions. No diagnostic or severity claim without appropriate validation. |
| NTR-002 | Ready | Preserve a reproducible record of source dataset, rights/consent basis, subject/session split, sensor and environment metadata, code/config version, and processing decisions for each result. |
| NTR-003 | Ready | Protect participant privacy: minimize identifiers in datasets and exports; do not commit identifiable images or medical records without an approved handling plan. |
| NTR-004 | Proposed | Define acquisition conditions and document deviations: room conditions, acclimatization, camera distance, pose, exposed skin, and factors that can alter surface temperature. |
| NTR-005 | Proposed | Make reports interpretable to a researcher: show dataset/task label definitions, anatomy and ROI, temperature units and reference difference when valid, registration quality, missing data, and limitations beside classification and spatial-localization outputs. Show side/bilateral comparison only when relevant. |
| NTR-006 | Blocked | Confirm dataset availability, usage rights, representativeness, and a plan for independent ground truth before making performance or generalization claims. |
| NTR-007 | Blocked | Assess performance and ROI detection across relevant skin tones, body shapes, camera setups, and acquisition settings when a suitable validation cohort exists. |
| NTR-008 | Ready | Keep project decisions and progress discoverable: every work session updates both `docs/TR.md` and `docs/NTR.md` change histories. Update `docs/PROJECT_CONTEXT.md` only when enduring project details change. |
| NTR-009 | Ready | Apply the user's source priority: the review PDF controls project scope and target capabilities over the older knee architecture. Treat study performance and clinical claims within the review as evidence to verify, not guaranteed properties of the system. |
| NTR-010 | Ready | Design for multiple body regions and nonclinical RGB–thermal tasks using dataset-specific label maps, task heads, and evaluations. Do not claim one task/domain validates another. |
| NTR-011 | Ready | Before using a third-party dataset, document its owner, exact file/license or DUA terms, allowed research and derivative use, access method, privacy basis, and any restrictions on publication or redistribution. A paper's data-availability statement is an access lead, not permission or proof of local access. |
| NTR-012 | Ready | Do not train on or stage post-TKA participant files until written research access, sponsor approval, the applicable DUA, storage/security rules, and permitted derivative/publication terms are recorded. Keep clinical data and identifiers out of Git. |
| NTR-013 | Done | A review demonstrator must label source measurements and clinician annotations as such, state when alignment is provisional, distinguish ground truth from model predictions, and keep data from different cohorts separate. |
| NTR-014 | Done | Show the trained wound model as a research output, report validation split and per-class results with small-data limits, and state prominently that it is RGB-only and not for diagnosis or treatment decisions. |

## Open project decisions

- Can the study authors and sponsor provide rights-cleared paired clinical images and tissue masks under a DUA?
- What data storage, institutional review, derivative-mask, and publication conditions will the DUA require?
- Are the four tissue categories independently annotated in the clinical paired cohort, and what clinical annotation/consent scope applies? Temperature asymmetry remains a measurement, not a diagnosis.
- Can the dataset owner provide a verified mapping between TRICVI-C workbook volunteer codes and the image-folder/FLIR capture IDs? Do not infer it from ordering or image appearance.
- What review or ethics process applies before collecting patient images or sharing results externally?

## Current evidence and project status

- The review PDF controls technical capabilities. The reusable pipeline remains multi-domain with separate task/dataset schemas and no assumed cross-domain generalization. The older knee architecture is one historical adapter proposal; the user’s current direction is not knee-first. The initial demonstrator uses separate clinical datasets for RGB-thermal/Celsius handling and RGB wound-mask visualization.
- Multi-domain dataset research and local acquisition status are recorded in [DATASET_RESEARCH.md](DATASET_RESEARCH.md). Alongside Caltech aerial RGB-T, StereoThermoLegs and FDA/PhysioNet tables, TRICVI-C v2 is locally downloaded and SHA-256 verified (paired clinical RGB, thermal display images, and per-pixel Celsius CSVs; no tissue masks). LUTSeg is locally downloaded under CC BY 4.0 (RGB chronic-ulcer photos with clinician tissue masks; no thermal data). These datasets support separate tasks and must not be cross-paired.
- TRICVI-C also includes a clinical workbook with per-volunteer records and aggregate CEAP counts for 71 volunteers. The volunteer-code-to-FLIR-frame mapping is not yet verified; do not expose individual workbook details in the review demo or treat class labels as assigned to images until that linkage is recovered.
- Additional nonclinical candidates were screened: PST900, LLVIP, FLIR ADAS, KAIST, MFNet, Freiburg Thermal, and LasHeR. They can extend calibration, segmentation, detection, or tracking work, but their access terms and labels vary; none supplies the required paired clinical outcome and independently marked abnormality regions. These candidates were not acquired in this review.
- The post-TKA wound cohort is a restricted access lead, not the project's selected first task. Its mask provenance, radiometric conversion, registration, patient-key availability and terms remain unverified until the owner shares an approved data manifest. LUTSeg provides a rights-cleared RGB-only tissue-mask task, while TRICVI-C separately provides paired RGB-thermal measurements; neither alone supports clinical RGB-thermal wound localization.
- Dataset licenses include noncommercial research restrictions and a Caltech record/repository license description discrepancy (the repository describes CC BY-SA, while the CaltechDATA record API says CC BY-NC). Check full terms with the dataset owner before public redistribution or reuse beyond research.
- The review's PRISMA numbers can reconcile if 19 citation records enter after database screening: 470 screened minus 431 excluded leaves 39; plus 19 gives 58 full texts; minus 38 gives 20 included. That route is not documented, and Section VII says the flow needs reconstruction while Table V labels counts verified. The quality scores are near-uniformly high without a stated scoring process. Treat its synthesis as a literature map until checked against primary studies.
- A named clinical reviewer and external validation remain open. The LUTSeg RGB-only baseline is trained and shown in a desktop inference app; it is a small-data research result, not validated clinical performance. The dual-stream thermal wound scaffold remains untrained. Clinical use and generalization claims are blocked pending larger independent validation.
- The [KSCST SPP 2026–27 proposal](KSCST_SPP_50th_Proposal_2026-27_Filled.docx) is an applicant-review draft. The guide, coordinator, team-leader and student contact fields, signatures, payment details, and confirmation of facilities and degree/semester entries remain with the applicants; no institutional endorsement or fee payment has been asserted.

## Change history (append new entries; do not erase old ones)

### 2026-10-12 — Initial register

- **Changed:** Created NTR-001 through NTR-008 and established the required dual-log update process.
- **Reason/evidence:** The architecture proposes clinical-facing outputs, while the review and repository do not yet establish paired knee data, diagnostic labels, or external validation.
- **Files affected:** `AGENTS.md`, `PROJECT_CONTEXT.md`, `TR.md`, `NTR.md`.
- **Verification:** Read the supplied architecture and review and checked the repository's current state.
- **Remaining risk/next step:** Confirm intended user, permissible dataset, and first outcome definition before claiming clinical utility.

### 2026-10-12 — Documentation structure corrected

- **Changed:** Moved this register into `docs/`; moved current evidence status, open decisions, and review caveats here from project context. Updated NTR-008 to keep progress and history in TR/NTR.
- **Reason/evidence:** User clarified that project context should describe the overall project from A to Z without a "where we stand" section.
- **Files affected:** `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Checked document paths, current repository state, and consistency of cross-references.
- **Remaining risk/next step:** Confirm dataset rights, intended user, and first outcome definition.

### 2026-10-12 — Implementation readiness reviewed

- **Changed:** Reviewed; no NTR requirement change. The project remains a research prototype and the dataset, intended user, and outcome definition remain open.
- **Reason/evidence:** Found documentation only in the repository. Synthetic fixtures support software development but do not establish data rights, clinical utility, or generalization.
- **Files affected:** `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Inspected current repository files and the NTR register.
- **Remaining risk/next step:** Confirm who the first researcher/user is, what paired data may be used, and which outcome will eventually be evaluated.

### 2026-10-12 — README added

- **Changed:** Reviewed non-technical requirements; no status changed. The new README describes the research scope and links to the authoritative documents.
- **Reason/evidence:** User requested a repository README.
- **Files affected:** `README.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Confirmed the README identifies the project as a research effort and links to the current requirement registers.
- **Remaining risk/next step:** Confirm dataset rights, intended user, and first outcome definition.

### 2026-10-12 — PDF designated as controlling project direction

- **Changed:** Updated NTR-005 and open decisions; added NTR-009 and NTR-010. Recorded that knee is the first application while the system objective is physiological abnormality detection and spatial localization across adaptable anatomy.
- **Reason/evidence:** The user explicitly gave the review PDF precedence over the older knee architecture and chose knee as the first application. The PDF proposes registration, segmentation, explicit thermal biomarkers, adaptive fusion, and localization, and warns that fusion may not improve every task.
- **Files affected:** `AGENTS.md`, `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/TR.md`, `docs/NTR.md`, `docs/RGB_Thermal_Systematic_Review_IEEE.pdf`.
- **Verification:** Compared the architecture and PDF's project objective, framework, experimental design, and limitations; checked the current documentation and verified the repository PDF copy against the supplied file by SHA-256.
- **Remaining risk/next step:** Confirm permissions for paired radiometric knee data, the first independently labelled outcome, and a spatial annotation protocol. The review's methodological claims still need primary-source checks before clinical claims.

### 2026-10-12 — Dataset rights and clinical evidence reviewed

- **Changed:** Added NTR-011 and a sourced dataset access assessment. NTR-006 remains blocked: no rights-cleared, file-inspected paired radiometric clinical knee cohort is available in the repository. Recorded that distinct knee disease targets cannot share an undefined “abnormal” label.
- **Reason/evidence:** Dataset-owner pages and original studies linked in `docs/DATASET_RESEARCH.md` distinguish open engineering data from restricted knee clinical data. The post-TKA study explicitly requires a DUA and sponsor approval for potential deidentified access.
- **Files affected:** `docs/DATASET_RESEARCH.md`, `docs/TR.md`, `docs/NTR.md`, `AGENTS.md`, `README.md`.
- **Verification:** Compared source-level pairing, temperature, outcome, spatial-annotation and rights statements; checked that no dataset has been added to the repository.
- **Remaining risk/next step:** Choose one clinically defined knee target with a collaborator, verify licenses and file contents for initial engineering sources, and pursue restricted data access or an approved local pilot. No access messages were sent.

### 2026-10-27 — KSCST proposal drafted

- **Changed:** Reviewed NTR-001–NTR-011; no non-technical requirement or status changed. Recorded the applicant-review state of the funding form and fields that must be supplied or verified by the team.
- **Reason/evidence:** The user asked for an accurate, moderately sized application and chose to complete guide-related details personally. The form's project content therefore presents a research prototype and makes dataset-dependent clinical evaluation conditional.
- **Files affected:** `docs/KSCST_SPP_50th_Proposal_2026-27_Filled.docx`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Checked the completed Word file and 11-page rendering; cross-checked the official KSCST theme and institution address, preserved supplied names/identifiers, and left unverified contact, approval, signature, and payment fields blank.
- **Remaining risk/next step:** Applicants must check all identifiers and inferred student course/semester details, provide real facility and budget evidence, review the proposal for originality and accuracy, obtain required signatures, and submit the fee and application through the official process.

### 2026-10-31 — Dataset use and pilot limitations recorded

- **Changed:** Updated the current evidence status to distinguish acquired engineering datasets and the FDA measurement tables from inaccessible image data and clinical validation. Reviewed NTR-001–NTR-011; no non-technical requirement changed.
- **Reason/evidence:** The local StereoThermoLegs subset is CC BY-NC and contains propagated anatomy labels rather than disease labels. Caltech license metadata conflict between CaltechDATA and creator README. FDA/PhysioNet download has derived CSV tables only. The Caltech training result is a small engineering smoke test, not clinical evidence or proof of fusion superiority.
- **Files affected:** `.gitignore`, `docs/NTR.md`, `docs/TR.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `datasets/README.md`, `outputs/README.md`, local ignored datasets, calibration files, and model outputs.
- **Verification:** Reviewed dataset license/readme files and official source records; checked downloaded file types, all 400 StereoThermoLegs manifest hashes, and calibration-file checksums; inspected pilot metrics and confirmed these acquired assets provide no disease outcome or abnormality-mask labels.
- **Remaining risk/next step:** Keep downloaded data local and use only within verified license terms. Resolve Caltech license conflict before redistribution. Clinical use, outcome performance, broad demographic representation, and external generalization remain blocked pending permissions and suitable independently labeled data.

### 2026-11-13 — Additional dataset access and scope reviewed

- **Changed:** Reviewed NTR-001–NTR-011; no non-technical requirement changed. Added access and license caveats for candidate RGB-thermal engineering datasets to the research register; recorded that none changes the clinical evidence gap.
- **Reason/evidence:** LLVIP requires agreement to noncommercial terms and form-based access; KAIST states a default CC BY-NC-SA 4.0 license with code exceptions; FLIR uses an owner download form; PST900's README does not clearly specify dataset terms; Freiburg Thermal's official project page timed out during this review; tracking dataset terms need confirmation. No candidate contains clinical abnormality labels.
- **Files affected:** `docs/DATASET_RESEARCH.md`, `docs/TR.md`, `docs/NTR.md`.
- **Verification:** Checked current owner/creator pages and primary dataset descriptions; confirmed that no candidate files or licenses were added to the local dataset folders. No external contact or access request was sent.
- **Remaining risk/next step:** Confirm permitted research, derivative, and publication use before downloading or training on any new source. Clinical performance and localization remain blocked until suitable rights-cleared paired clinical images and labels are obtained.

### 2026-11-13 — Post-TKA access and research-use safeguards

- **Changed:** Added NTR-012 and updated status to record postoperative wound localization as the selected clinical adapter. Added a local draft access request; no message was sent. The existing `NTR-001` research-only and `NTR-011` dataset-rights requirements remain active.
- **Reason/evidence:** The primary study states the data are not publicly available and any deidentified sharing is subject to reasonable request, DUA, and sponsor approval. It reports an expanded segmentation development set incorporating public images, so provenance of the selected four-class masks requires confirmation before use.
- **Files affected:** `docs/NTR.md`, `docs/TR.md`, `docs/PROJECT_CONTEXT.md`, `docs/DATASET_RESEARCH.md`, `docs/POST_TKA_DATA_ACCESS_REQUEST.md`, `docs/PROCESS_MODEL_DESIGN.md`, `datasets/post_tka_wound/README.md`.
- **Verification:** Checked primary study data-availability statement and annotation sections; confirmed the access-request document is marked draft and no external contact was made.
- **Remaining risk/next step:** Obtain written approval and DUA, determine institutional storage/ethics requirements, and confirm the dataset labels, masks, and deidentification scope before accepting files.

### 2026-11-13 — Clinical model scaffold safeguards

- **Changed:** Reviewed NTR-001–NTR-012; no non-technical status change. Added access-status enforcement and dataset privacy/handling notes around the model scaffold.
- **Reason/evidence:** Manifest access cannot stand in for permission; the training entry point must refuse to run until the approved research status and terms reference are recorded. No clinical dataset is currently local.
- **Files affected:** `scripts/post_tka_wound_localization.py`, `datasets/post_tka_wound/manifest.template.json`, `datasets/post_tka_wound/README.md`, `.gitignore`, `docs/NTR.md`, `docs/TR.md`.
- **Verification:** Synthetic fixture confirmed `pending` access blocks training; `.gitignore` check confirmed project docs/template are tracked while a mock patient-data file remains ignored. No protected data were added.
- **Remaining risk/next step:** Confirm that actual institutional terms permit this processing and the intended model derivatives; keep training blocked until then.

### 2026-11-13 — Public clinical datasets and review demonstrator

- **Changed:** Reviewed NTR-001–NTR-013. Added NTR-013 and marked it done for a self-contained offline review page that distinguishes source °C measurements, clinician ground-truth masks, provisional registration and untrained model status. Updated current evidence to record acquisition of TRICVI-C and LUTSeg and to remove post-TKA as the selected first task.
- **Reason/evidence:** TRICVI-C v2 is CC BY 4.0 and contains co-indexed clinical RGB images, thermal display views and numeric Celsius grids but no wound tissue masks. LUTSeg is CC BY 4.0 and contains clinician wound tissue masks for RGB photos but no thermal data. They are different cohorts and cannot validate RGB-thermal wound fusion together.
- **Files affected:** `README.md`, `docs/NTR.md`, `docs/TR.md`, `docs/PROJECT_CONTEXT.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `docs/BASELINE_DEMO.md`, `datasets/README.md`, `scripts/build_review_demo.py`, local ignored datasets and generated demo.
- **Verification:** Reviewed owner dataset records and terms; checked TRICVI per-file publisher SHA-256 for all 1,284 files; checked LUTSeg publisher checksums (1,028 exact, 21 match after CRLF normalization, one README discrepancy); inspected the RGB/thermal/Celsius sample and LUTSeg mask label IDs. Checked the generated page's provenance text and JavaScript syntax and checked the source pair dimensions from local files.
- **Remaining risk/next step:** Measure held-out RGB/thermal registration error and resolve LUTSeg's README checksum discrepancy; obtain a single approved cohort with paired RGB, calibrated thermal and wound labels if the eventual target requires fused wound segmentation. Do not present the offline demo as a trained model or a clinical result.


### 2026-11-13 — Trained research baseline

- **Changed:** Reviewed NTR-001–NTR-014. Added NTR-014 and updated current status for a trained RGB-only LUTSeg segmentation model and desktop inference screen; kept the model explicitly research-only and the clinical data samples separate.
- **Reason/evidence:** The model runs on RGB wound photos and compares predictions with clinician masks. LUTSeg does not contain thermal images; TRICVI-C has RGB/thermal/Celsius but no wound masks. Validation mIoU is 0.331 including background (foreground macro 0.216) on only 30 patient-disjoint validation images, used for checkpoint selection, with no independent test set.
- **Files affected:** `README.md`, `docs/NTR.md`, `docs/TR.md`, `docs/DATASET_RESEARCH.md`, `docs/PROCESS_MODEL_DESIGN.md`, `docs/BASELINE_MODEL.md`, `requirements-medical.txt`, `outputs/README.md`, `scripts/train_lutseg_transformer.py`, `scripts/run_lutseg_baseline.py`, local ignored weights/report.
- **Verification:** Inspected the running desktop window showing actual model prediction, clinician mask, and sample Dice. Verified training report, validation split, per-class scores, and model checkpoint; confirmed clinical workbook data are not exposed in the inference view. No clinical claim or RGB/thermal wound performance is made.
- **Remaining risk/next step:** The validation estimate is optimistic because the same split chose the checkpoint, and rare-class performance is weak. Obtain an independent test cohort and more annotated wound images; paired thermal wound masks are still missing. The model must not guide diagnosis or treatment.
