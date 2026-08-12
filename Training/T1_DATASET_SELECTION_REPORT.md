# T1 Candidate Dataset-Selection Report

**Status**: Discovery complete; all candidates remain blocked from acquisition  
**Scope**: Training Program T0–T1  
**Decision requested next**: Pilot-acquisition review of specifically named, reviewed sources and splits

---

## 1. Executive Conclusion

The T1 discovery work identifies a **governance-first candidate stack**, not an immediately downloadable corpus. The strongest direction for an initial pilot is a named permissioned or first-party source, complemented only after review by a narrowly defined supervised visual-grounding source. Public-web indexes are valuable for methodology and discovery but should not enter a pilot merely because index metadata is available.

This approach is grounded in the observed distinction between documentation and training clearance. Open Images publishes rich visual annotations, including labels, boxes, segmentation, relationships, and localized narratives [1]. In contrast, LAION describes its releases as internet indexes that require downstream users to reconstruct selected images, which makes source-level review essential [2]. A large data-provenance audit further reports substantial ambiguity and misclassification in public licence metadata, supporting a rule that unknown or conflicting terms are excluded from the initial pilot [3].

---

## 2. Candidate Comparison

| Candidate | Intended Role | Evidence Strength | Primary Risks | T1 Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| Named permissioned/first-party source | Core pilot training | **Highest once identified** | Consent, purpose limitation, privacy, retention | **Required primary source.** Discover and review a specific provider before any pilot starts. |
| Open Images V7 subset | Supplementary supervised grounding | **Medium**; official description provides scope and modalities | Split-specific terms, attribution, imagery privacy/content, benchmark leakage | **Conditional candidate.** Review current terms and select only a documented split after owner approval. |
| COCO split | Held-out capability evaluation | **Medium**; official site provides task/evaluation and terms entry point | Terms, split contamination, prior exposure | **Evaluation-only candidate.** Do not include in initial training pool. |
| DataComp | Curation-method benchmark | **Low for individual media**; methodology is documented | Public-web source terms, content, PII, scale | **Methodology-only at T1.** No download or reconstruction. |
| LAION index | Discovery/policy analysis | **Low for individual media**; it is an index rather than retained media | Copyright, takedown, source volatility, unsafe content, PII | **Discovery-only.** No reconstruction without later explicit authorization. |
| Common Crawl | Web-source discovery | **Low for individual media** | Linked-content rights, privacy, safety, provenance | **Discovery-only.** No bulk collection or linked-media retrieval. |

---

## 3. Evidence and Design Implications

Open Images is technically promising for supervised grounding because its official description identifies image labels, boxes, masks, relationships, and localized narratives at substantial scale [1]. This does not resolve its use for the project; the governing terms, selected split, attribution method, privacy/safety filtering, and retained-item manifest must still be reviewed.

COCO exposes an official dataset/task/evaluation/terms entry point [4], making it suitable to evaluate a reviewed system under a carefully isolated protocol. T1 treats it as evaluation-only to avoid contaminating the first training pilot with a widely used benchmark.

DataComp is useful as a curation benchmark because it holds model settings fixed while focusing on dataset-selection choices, but it also describes public-web image-text pools and acquisition tooling [5]. That makes it a useful methodological reference, not a presumption that individual media are cleared for this project.

The registry and data-card template therefore record provider evidence, terms snapshots, modality, source-level provenance confidence, content/privacy risks, removal controls, split controls, and a hard training-eligibility status. This follows the documentation logic advocated by dataset cards [6] and supports the trustworthiness-oriented lifecycle approach of the NIST AI RMF [7].

---

## 4. T1 Exit Checklist

| Requirement | Result |
| :--- | :--- |
| Intended use and explicit exclusions defined | **Complete** — `T0_GOVERNANCE_CHARTER.md` |
| Mandatory provenance/terms/privacy/safety controls defined | **Complete** — `T0_GOVERNANCE_CHARTER.md` |
| Candidate sources researched without acquisition | **Complete** — `T0_T1_RESEARCH_NOTES.md` |
| Machine-readable registry created and validated | **Complete** — `candidate_dataset_registry.json` |
| Data-card template created | **Complete** — `DATASET_CARD_TEMPLATE.md` |
| Staged pilot design created | **Complete** — `T2_PILOT_CORPUS_DESIGN.md` |
| Pilot media, metadata corpus, or training run started | **Not authorized; not performed** |

---

## 5. Pilot-Acquisition Gate Conditions

No pilot acquisition can begin until the owner approves a finite list of specific sources and splits with the following evidence attached: exact terms/permission records, proposed item or source boundaries, retention/removal policy, privacy/safety filtering plan, representative-sample review plan, split-isolation and duplication plan, storage/compute estimate, and model/evaluation protocol. A request involving web-media reconstruction must explicitly identify the source-level allow-list and is not implied by this report.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[2]: https://laion.ai/faq/ "LAION FAQ — Dataset Index and Reconstruction Context"
[3]: https://www.nature.com/articles/s42256-024-00878-8 "A Large-Scale Audit of Dataset Licensing and Attribution in AI"
[4]: https://cocodataset.org/ "COCO — Common Objects in Context"
[5]: https://github.com/mlfoundations/datacomp "DataComp — Dataset Design Benchmark"
[6]: https://huggingface.co/docs/hub/en/datasets-cards "Hugging Face Dataset Cards"
[7]: https://www.nist.gov/itl/ai-risk-management-framework "NIST AI Risk Management Framework"
