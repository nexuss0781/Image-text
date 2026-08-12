# T2.4 Source Selection: Art Institute of Chicago CC0 Pilot

**Status**: Selected for source-specific review under the owner’s instruction to proceed; no media acquired yet
**Selected path**: C1 — Art Institute of Chicago CC0-designated allow-list
**Pilot purpose**: Validate a bounded visual-to-catalog-text adapter against the frozen AGI-VS Stage 1–4 substrate.

---

## 1. Source Decision

The project selects the **Art Institute of Chicago Open Access Images** pathway as the first actionable pilot source. The Institute’s official policy states that an image bearing the “CC0 Public Domain Designation” may be used for any purpose, including commercial use, without additional permission. The policy also states that users remain responsible for identifying any necessary third-party permissions. The pilot will therefore use only an explicit, finite allow-list of assets that carry the designation, rather than treating the institution’s complete collection as automatically eligible [1].

This source was selected because it has a first-party policy, a documented public API, stable collection records, an item-level public-domain indicator, and an accessible provider contact route. It is a narrow cultural-heritage/object dataset. Its results will measure a controlled pilot only and will not be presented as evidence of general real-world visual intelligence or AGI.

---

## 2. Bounded Capability Objective

The pilot will train and evaluate a compact adapter that consumes frozen Stage 4 AGI-VS visual tokens and predicts a normalized, source-provided catalog-text representation. The task is deliberately limited to **held-out visual-to-catalog retrieval within the reviewed CC0 asset set**. It tests whether a learned adapter improves retrieval of the corresponding title/classification text over a deterministic no-training baseline, under fixed train/development/held-out partitions.

| Element | Decision |
| :--- | :--- |
| Visual input | Frozen AGI-VS Stage 1–4 pipeline; Stage 4 visual tokens remain deterministic. |
| Text target | Source-provided title plus a normalized classification/department label, retained only when available and non-sensitive. |
| Trainable component | A small cross-modal projection/retrieval adapter; no end-to-end foundation-model training. |
| Maximum retained pilot size | 300 images, subject to every item passing T2.4 review. |
| Minimum class/text diversity | At least 20 source-provided classification or department categories where quality permits. |
| Split plan | Deterministic 70% training, 15% development, and 15% held-out allocation by manifest ID, with duplicate controls. |
| Held-out measure | Retrieval Recall@1, Recall@5, mean reciprocal rank, and comparison to the declared deterministic baseline. |
| Explicit non-claims | No claim of broad visual capability, real-world safety, generalization beyond the selected artwork domain, or AGI. |

---

## 3. Initial Safety and Privacy Scope

The pilot will exclude any candidate with a human-portrait designation, sensitive historical/violent/sexual content signals, uncertain rights status, missing public-domain indication, missing image reference, missing usable title, or a record that cannot be retrieved through the provider’s documented interfaces. Where the metadata cannot reliably identify a risk, the record will remain quarantined rather than being retained.

The source’s CC0 statement concerns copyright. It does not eliminate the need to screen for privacy, publicity, trademark, historical-sensitivity, or contextual safety concerns. The local removal procedure, retention expiry, reviewer decisions, and source contact will be recorded before any media acquisition [1].

---

## 4. T2.4 Evidence Still Required

| Control | Required before media acquisition |
| :--- | :--- |
| Item-level eligibility | API/object records showing the explicit public-domain indicator and a stable source ID for every retained candidate. |
| Finite boundary | A 300-item maximum candidate manifest with deterministic selection and split assignment. |
| Provenance | Source URL, API/object record, retrieval date, rights indicator, metadata values, and later file checksum. |
| Privacy and safety | Metadata-based exclusion report, manual review protocol for uncertain records, and exclusion/quarantine log. |
| Removal and retention | Provider contact, local deletion workflow, retention review date, and manifest linkage. |
| Duplicates and leakage | Perceptual duplicate procedure, title/text duplicate rules, and no training on held-out IDs. |
| Reproducibility | Versioned selection query, seed, manifest schema, transform version, and data-card evidence. |

The next phase will complete these requirements through metadata-only source review. It will not download image media until the finite allow-list and audit record pass the hard controls.

## References

[1]: https://www.artic.edu/collection-information/open-access/open-access-images "Art Institute of Chicago — Open Access Images"
[2]: https://www.artic.edu/collection-information/open-access "Art Institute of Chicago — Open Access"
