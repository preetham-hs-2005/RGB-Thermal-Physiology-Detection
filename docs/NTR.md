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
| NTR-005 | Proposed | Make reports interpretable to a researcher: show knee side, ROI, temperature units, bilateral comparison, registration quality, missing data, and uncertainty or limitations. |
| NTR-006 | Blocked | Confirm dataset availability, usage rights, representativeness, and a plan for independent ground truth before making performance or generalization claims. |
| NTR-007 | Blocked | Assess performance and ROI detection across relevant skin tones, body shapes, camera setups, and acquisition settings when a suitable validation cohort exists. |
| NTR-008 | Ready | Keep project decisions and progress discoverable: every work session updates both `docs/TR.md` and `docs/NTR.md` change histories. Update `docs/PROJECT_CONTEXT.md` only when enduring project details change. |

## Open project decisions

- Who is the intended first user of the prototype: researcher, clinician, or coach?
- What data-use permission and consent apply to the initial paired images?
- What is the intended outcome definition: thermal asymmetry, inflammation assessment, injury detection, or longitudinal monitoring? These need different evidence.
- What review or ethics process applies before collecting patient images or sharing results externally?

## Current evidence and project status

- The supplied knee architecture and the repository's committed architecture are identical. They describe a research direction, not a validated diagnostic product.
- Dataset availability and rights for the named knee sources in the architecture have not been established. Do not claim an eligible paired radiometric dataset or clinical ground truth until confirmed.
- The review's PRISMA numbers can reconcile if 19 citation records enter after database screening: 470 screened minus 431 excluded leaves 39; plus 19 gives 58 full texts; minus 38 gives 20 included. That route is not documented, and Section VII says the flow needs reconstruction while Table V labels counts verified. The quality scores are near-uniformly high without a stated scoring process. Treat its synthesis as a literature map until checked against primary studies.
- Intended first user, permitted dataset, and first outcome definition remain open decisions. Clinical use and generalization claims are blocked by those decisions and later validation.

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
