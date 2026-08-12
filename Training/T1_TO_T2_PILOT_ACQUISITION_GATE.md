# T1 → T2 Pilot-Acquisition Gate

**Project**: AGI Vision Substrate (AGI-VS)  
**Program**: Data Curation, Training & Fine-Tuning  
**Gate Status**: **T0–T1 COMPLETE — PILOT ACQUISITION BLOCKED PENDING SPECIFIC SOURCE APPROVAL**

---

## 1. Gate Decision

The approved governance and discovery work is complete. The program now has an intended-use charter, explicit exclusions, mandatory data controls, source research notes, a validated machine-readable provenance registry, a dataset-card template, and a staged pilot-corpus design. No corpus, image, bulk metadata export, web-media reconstruction, training run, fine-tune, or model checkpoint has been acquired or created.

> **Decision:** T0–T1 passes as a governance and discovery phase. It does **not** authorize data acquisition. A discrete T2 approval must identify the exact sources, versions/splits, and terms/permission evidence to be considered.

---

## 2. T0–T1 Evidence Summary

| Deliverable | Result | Gate Outcome |
| :--- | :--- | :--- |
| Intended-use statement and exclusions | Sensitive/high-impact uses and automatic web-media collection explicitly excluded | **PASS** |
| Governance roles and mandatory controls | Provenance, terms, privacy, safety, split, retention, and reproducibility controls defined | **PASS** |
| Candidate research | Permissioned sources, Open Images, COCO, DataComp, LAION, and Common Crawl assessed without acquisition | **PASS** |
| Candidate provenance registry | JSON registry validates successfully; all non-permissioned candidates remain blocked | **PASS** |
| Dataset-card template | Source, terms, risks, split, reproducibility, and removal fields defined | **PASS** |
| Pilot design | Adapter-first, split-isolated, held-out-evaluation plan created | **PASS** |
| Training or data acquisition | None performed | **PASS — correctly blocked** |

---

## 3. Candidate Status at the Gate

| Candidate Class | Status | May Be Acquired Now? |
| :--- | :--- | :--- |
| Named permissioned/first-party source | Needs identification and source-specific review | **No** |
| Open Images V7 subset | Conditional candidate; requires current terms and selected-split review | **No** |
| COCO benchmark split | Evaluation-only candidate pending terms and leakage review | **No** |
| DataComp public-web pool | Methodology-only; not cleared at item level | **No** |
| LAION/Common-Crawl web-derived indexes | Discovery-only; reconstruction requires a later allow-list decision | **No** |

---

## 4. Exact T2 Approval Package Required

To request pilot acquisition, submit a finite, reviewable package that includes:

| Requirement | Required Detail |
| :--- | :--- |
| Named sources | Provider, canonical URL, exact version, selected split, and requested purpose. |
| Rights evidence | Terms/licence snapshot or written permission, attribution duties, restrictions, and review decision. |
| Data boundary | Maximum intended item count or source list, modality, languages/domains, and exclusion rules. |
| Privacy/safety controls | PII and content-filter design, manual review sample plan, quarantine rules, and removal contact. |
| Split integrity | Train/dev/held-out assignment, duplication detection, and external-benchmark overlap procedure. |
| Operational plan | Storage, compute, access controls, retention duration, transformation versioning, and checksum manifest plan. |
| Evaluation plan | Frozen baseline, target adapter, held-out metrics, robustness checks, and stop criteria. |

No open-ended web crawl, bulk URL reconstruction, or large-scale model training is permissible under the T2 gate. Those actions require later review even after a pilot source is approved.

---

## 5. Owner Approval Required

If you want to proceed to a **limited pilot-acquisition review**, respond exactly:

`Approve T2 Pilot Acquisition Review`

That approval will allow preparation of a source-specific acquisition proposal and terms/provenance assessment. It will **not** automatically download data, reconstruct web media, or train a model.
