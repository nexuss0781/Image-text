# T2 Source-Specific Review Package: Open Images V7

**Status**: Review complete from public documentation; no dataset content acquired  
**Candidate**: Open Images V7  
**Recommendation**: Do not authorize training. Consider only a separately approved, bounded record-level review queue.

---

## 1. Review Outcome

Open Images V7 is technically appropriate to evaluate a small visual-grounding adapter because of its published object, localization, segmentation, relationship, and narrative annotation modalities [1]. However, the licence posture is not suitable for an automatic bulk acquisition decision. The official source says its annotations are CC BY 4.0 and that images are listed as CC BY 2.0, while expressly cautioning that it makes no representation or warranty about the licence status of each image and that users should verify each image [2].

> **Review decision:** Open Images V7 may be considered for a **maximum 1,000-record manual review queue** only after an explicit owner authorization. No record is currently eligible for retention, embedding generation, training, fine-tuning, or model evaluation.

---

## 2. Evidence-Driven Risk Assessment

| Review Area | Evidence | Assessment | Required Control |
| :--- | :--- | :--- | :--- |
| Technical relevance | Official description lists labels, boxes, masks, relationships, narratives, and point labels [1] | Suitable candidate for supervised grounding research | Restrict the pilot purpose to declared visual-grounding tasks. |
| Image licence signal | Official source lists images as CC BY 2.0 but provides no per-image warranty [2] | Dataset-level signal is insufficient for blanket approval | Verify source/creator/licence evidence at record level. |
| Annotation licence | Official source identifies annotations as CC BY 4.0 [2] | Conditional on maintaining annotation provenance and attribution | Preserve annotation source, version, licence link, and adaptation record. |
| Attribution | CC BY 2.0 and 4.0 require appropriate credit, licence link, and change indication [3] [4] | Implementable only with complete source fields | Require the manifest’s attribution fields before retention. |
| Privacy/publicity/moral rights | Both CC deeds warn other rights may still be needed [3] [4] | Not resolved by licence label | Fail-closed privacy/sensitive-content review and human escalation. |
| Safety/content suitability | Public documentation alone does not provide a project-specific safety assessment | Unknown until controlled review | Apply filtering/quarantine protocol; no automatic inclusion. |
| Leakage/split integrity | Source may overlap with popular evaluation sources or prior models | Unknown until review and audit | Deterministic split assignment, deduplication, and external-overlap checks. |
| Retention/removal | No project retention artifact exists yet | Unresolved until reviewed record has source procedure | Require removal contact/procedure and review expiry for every retained record. |

---

## 3. Proposed Next-Step Authorization Boundary

The next decision is deliberately narrow. It would allow only preparation of up to 1,000 candidate record entries for manual review under the empty manifest template. It would not authorize bulk downloads, extraction of a corpus, reconstruction of web media, retention of records for training, generation of embeddings, or model training.

| Action | Proposed T2.1 Status |
| :--- | :--- |
| Assemble up to 1,000 source-record review entries | Requires owner approval |
| Capture source/terms/attribution evidence | Requires owner approval and restricted review process |
| Download bulk images or annotations | Not authorized |
| Retain pilot training samples | Not authorized |
| Compute embeddings or token caches | Not authorized |
| Train or fine-tune adapter/model | Not authorized |
| Use COCO, DataComp, LAION, or Common Crawl content | Not authorized |

---

## 4. Readiness Checklist for T2.1

| Prerequisite | Status |
| :--- | :--- |
| Governance charter | Complete |
| Candidate registry | Complete and JSON-validated |
| Source-specific boundary | Complete |
| Terms/provenance assessment | Complete from public documentation |
| Empty record manifest | Complete and JSON-validated |
| Filtering/quarantine protocol | Complete |
| Adapter-baseline evaluation plan | Complete |
| Owner authorization for a review queue | **Pending** |

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[2]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[3]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
[4]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
