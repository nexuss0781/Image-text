# T0 Governance Charter: AGI-VS Training and Fine-Tuning Program

**Status**: Approved planning artifact; no data acquisition or model training authorized  
**Scope**: Training Program T0–T1 only  
**Owner**: Project owner  
**Technical scope**: The existing AGI-VS CPU vision substrate and its future trainable cross-modal adapter

---

## 1. Intended Use and Explicit Exclusions

The intended research use is to develop a multimodal vision system that consumes the verified AGI-VS visual-token interface and supports evidence-based visual understanding tasks such as recognition, grounded description, retrieval, spatial relation analysis, and task-specific visual question answering. Model behavior must be measured on held-out, documented tasks and described by capability rather than labelled as AGI.

The program will not automatically collect web media, infer consent from public availability, ingest private material, process restricted biometric or health data, or rely on opaque aggregate-dataset licences. It will not deploy a trained system for high-impact decisions, surveillance, identity inference, medical interpretation, legal determinations, or other sensitive uses without a separately defined project, domain review, and deployment controls.

> **Control principle:** the training corpus is a governed asset. A candidate source is not training-eligible until its purpose, origin, terms, risks, filtering, access, retention, and removal pathway are recorded and reviewed.

---

## 2. Governance Roles and Decision Authority

| Role | Required Decision or Evidence | May Authorize |
| :--- | :--- | :--- |
| Project owner | Approves gates, intended use, resource envelope, and release decision | T0–T1, pilot acquisition, training, scale-up, or deployment gates. |
| Technical lead | Maintains reproducible code, split isolation, training configuration, and evaluation harnesses | Technical readiness only; cannot override data restrictions. |
| Data steward | Maintains provenance registry, licence/terms evidence, removal record, retention limits, and dataset cards | Candidate review recommendation; cannot acquire rejected or unreviewed data. |
| Safety and privacy reviewer | Reviews PII, sensitive-content, representational-harm, and misuse controls | Risk-acceptance recommendation and stop conditions. |
| Independent evaluator | Runs held-out tests and confirms reproducibility | Evaluation sign-off; not corpus-selection authority. |

---

## 3. Mandatory Data Controls

| Control | Minimum Requirement Before Pilot Acquisition |
| :--- | :--- |
| Provenance | Source provider, source URL, version/date, modality, collection method, and evidence snapshot must be recorded. |
| Terms and licence | Exact governing terms or licence URL and a human-readable use-category decision must be recorded; unknown or conflicting terms are rejected from the initial pilot. |
| Purpose limitation | Each source must map to a declared capability objective and may not be repurposed without registry review. |
| Split isolation | Training, development, held-out evaluation, and red-team sets must be assigned before training starts; suspected duplicates trigger review. |
| Privacy and PII | Data steward records expected PII exposure, filter approach, incident path, and retention/removal procedure. |
| Content safety | Candidate must have documented filtering for explicit, exploitative, hateful, self-harm, and otherwise unsuitable content for the declared use. |
| Removal and retention | Each retained item must have a removal/takedown process and retention expiry or review date. |
| Reproducibility | Candidate subset specifications, filters, random seeds, checksums, and transformation versions must be versioned. |
| Human review | Representative samples and documented risk flags must be reviewed before any pilot is acquired. |

The NIST AI RMF frames trustworthy-AI risk management as a lifecycle concern across design, development, use, and evaluation [1]. Dataset cards similarly emphasize communicating dataset context and responsible-use considerations and allow metadata such as licence, language, and size [2]. These references guide documentation structure; they do not replace legal, privacy, or domain-specific review.

---

## 4. Stop Conditions

T0–T1 must stop and return to the owner for a new decision if a candidate source has absent/ambiguous terms, unresolved ownership signals, a missing removal pathway, substantial undocumented personal/sensitive content, inadequate provenance evidence, suspected benchmark leakage, or a proposed use outside this charter. The project must also stop before any downloadable corpus, web-media reconstruction, or training workload begins unless the pilot-acquisition gate has been approved.

---

## 5. Evidence Required for the T1 Exit Gate

The T1 exit package must contain a governance-approved candidate registry, a rationale and risk score for every candidate, a proposed pilot composition that is not yet acquired, a split-isolation plan, a dataset-card template, a removal/retention workflow, and a training-readiness checklist. It must state all unresolved legal, privacy, compute, and model-licence questions explicitly.

## References

[1]: https://www.nist.gov/itl/ai-risk-management-framework "NIST AI Risk Management Framework"
[2]: https://huggingface.co/docs/hub/en/datasets-cards "Hugging Face Dataset Cards"
