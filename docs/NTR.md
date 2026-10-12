# Non-Technical Requirements (NTR)

Last reviewed: 2026-10-12 (Asia/Calcutta)

Status values: **ready** = applies now; **blocked** = depends on external decisions or resources; **proposed** = needs agreement; **done** = demonstrated.

## Current requirements

| ID | Status | Requirement and acceptance evidence |
| --- | --- | --- |
| NTR-001 | Ready | Present the project as a research prototype. Reports must distinguish measured surface temperature, research predictions, and clinically validated conclusions. No diagnostic or severity claim without appropriate validation. |
| NTR-002 | Ready | Preserve a reproducible record of source dataset, rights/consent basis, subject/session split, sensor and environment metadata, code/config version, and processing decisions for each result. |
| NTR-003 | Ready | Protect participant privacy: minimize identifiers in datasets and exports; do not commit identifiable images or medical records without an approved handling plan. |
| NTR-004 | Proposed | Define acquisition conditions and document deviations: room conditions, acclimatization, camera distance, pose, exposed skin, and factors that can alter surface temperature. |
| NTR-005 | Proposed | Make reports interpretable to a researcher: show anatomy and ROI, temperature units and reference difference, registration quality, missing data, and limitations beside classification and spatial-localization outputs. Show knee side and bilateral comparison for the first application. |
| NTR-006 | Blocked | Confirm dataset availability, usage rights, representativeness, and a plan for independent ground truth before making performance or generalization claims. |
| NTR-007 | Blocked | Assess performance and ROI detection across relevant skin tones, body shapes, camera setups, and acquisition settings when a suitable validation cohort exists. |
| NTR-008 | Ready | Keep project decisions and progress discoverable: every work session updates both `docs/TR.md` and `docs/NTR.md` change histories. Update `docs/PROJECT_CONTEXT.md` only when enduring project details change. |
| NTR-009 | Ready | Apply the user's source priority: the review PDF controls project scope and target capabilities over the older knee architecture. Treat study performance and clinical claims within the review as evidence to verify, not guaranteed properties of the system. |
| NTR-010 | Ready | Use the knee as the first application while designing reusable anatomical and modality interfaces. Do not present knee-only data as validation for other body regions or conditions. |

## Open project decisions

- Which researcher or clinical collaborator will review the first knee protocol and outputs?
- What data-use permission and consent apply to the initial paired images?
- What exact independently labelled knee outcome and abnormality-region annotation will support classification and spatial localization? Thermal asymmetry is a measurement, not an injury label.
- What review or ethics process applies before collecting patient images or sharing results externally?

## Current evidence and project status

- The review PDF is the controlling project direction. The older knee architecture is a pilot implementation proposal and conflicts with the PDF on scope, homography being assumed sufficient, fusion priority, and the centrality of spatial localization. Knee is the first application, not the system's only possible anatomy.
- Dataset availability and rights for the named knee sources in the architecture have not been established. Do not claim an eligible paired radiometric dataset or clinical ground truth until confirmed.
- The review's PRISMA numbers can reconcile if 19 citation records enter after database screening: 470 screened minus 431 excluded leaves 39; plus 19 gives 58 full texts; minus 38 gives 20 included. That route is not documented, and Section VII says the flow needs reconstruction while Table V labels counts verified. The quality scores are near-uniformly high without a stated scoring process. Treat its synthesis as a literature map until checked against primary studies.
- The specific reviewer, permitted dataset, and first independently labelled outcome remain open decisions. Clinical use and generalization claims are blocked by those decisions and later validation.

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
