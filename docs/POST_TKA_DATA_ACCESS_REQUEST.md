# Post-TKA wound dataset access request (draft)

**Status:** draft only; no request has been sent.

**Study:** Ran et al., “Technical Feasibility of a Multimodal Electro-Optical
and Infrared Imaging Pipeline for Postoperative Wound Assessment After Total
Knee Arthroplasty,” JMIR Formative Research (2026),
[PMCID PMC13691468](https://pmc.ncbi.nlm.nih.gov/articles/PMC13691468/).

## Draft message

Subject: Research access request for paired RGB and radiometric IR wound masks

Dear corresponding author and study team,

I am preparing a research implementation for pixel-level localization of
postoperative wound tissue from paired visible and radiometric infrared
images. I read your 2026 study and would like to ask whether a deidentified,
research-use subset can be made available under your data-use and sponsor
approval process.

To determine whether the cohort supports a valid paired-modality evaluation,
could you share or confirm the following before any transfer?

1. The file manifest and counts of unique patients, sessions, RGB images,
   radiometric thermal arrays, masks, and paired observations.
2. Whether RGB and radiometric IR originals can be linked per observation,
   with stable patient/session IDs that support patient-disjoint splits.
3. Thermal sensor model, raw array encoding, value-to-Celsius conversion,
   invalid-pixel codes, and any available ambient/emissivity calibration data.
4. The EO-to-IR mapping or calibration transforms, transform direction, and
   any held-out landmark correspondences for independently checking alignment.
5. The exact tissue-mask label definitions, annotation protocol, annotator
   qualifications, and whether the four tissue classes are annotated on the
   clinical cohort, on public training images, or both.
6. The applicable data-use agreement, sponsor approval steps, allowed storage,
   publication and derived-mask terms, and whether masks may be used for
   external research benchmarking.

The intended first model output is research-only pixel localization of the
available wound-tissue labels. It will not be presented as a diagnosis. We
will not redistribute source data and will follow the approved governance and
security requirements. Please let me know the formal process and whether a
short protocol or institutional contact is required.

Sincerely,

[Researcher name]

[Institution / department]

[Institutional email]
