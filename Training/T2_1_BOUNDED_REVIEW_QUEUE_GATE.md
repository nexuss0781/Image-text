# T2.1 Bounded Review-Queue Acquisition Gate

**Project**: AGI Vision Substrate (AGI-VS)  
**Program**: Data Curation, Training & Fine-Tuning  
**Status**: **SOURCE REVIEW PASS — BOUNDED REVIEW QUEUE REQUIRES OWNER AUTHORIZATION**

---

## 1. Gate Decision

The T2 source-specific review is complete for the proposed Open Images V7 boundary. The project now has a finite review cap, public-documentation terms assessment, an empty manifest template, attribution requirements, filtering/quarantine protocol, split-integrity controls, and a reproducible adapter-baseline evaluation plan.

> **Decision:** The Open Images V7 proposal is eligible only for a controlled, record-level review queue. It is **not** eligible for bulk acquisition, retained pilot data, embeddings, training, fine-tuning, or deployment.

---

## 2. Evidence Summary

| Requirement | Evidence | Outcome |
| :--- | :--- | :--- |
| Finite source boundary | `T2_PROPOSED_ACQUISITION_BOUNDARY.md` limits the queue to 1,000 candidate records | **PASS** |
| Source terms evidence | Official source identifies annotation and image licence signals but states a no-warranty/per-image-verification caveat [1] | **PASS — conditionally scoped** |
| Attribution controls | CC BY 2.0/4.0 evidence requires credit, licence link, and modification disclosure [2] [3] | **PASS — manifest fields required** |
| Rights caveats | Privacy, publicity, and moral-rights caveats documented | **PASS — fail-closed review required** |
| Empty manifest | JSON validation passed; `candidate_records` is empty; bulk download/training are false | **PASS** |
| Content/privacy controls | Filtering/quarantine protocol provides prohibited categories and reviewer states | **PASS** |
| Split/evaluation integrity | Deterministic split, duplicate, benchmark-overlap, and held-out controls defined | **PASS** |
| Training authorization | No corpus, embedding, or training run exists | **PASS — correctly blocked** |

---

## 3. Exact Scope of a T2.1 Approval

If approved, T2.1 will authorize only the creation of **up to 1,000 review-queue entries** under the manifest schema. Each entry must be associated with record-level source, attribution, licence, annotation, safety/privacy, rights-caveat, split, removal, and checksum fields. A missing or ambiguous field sends the entry to quarantine.

| Action | Authorized by T2.1? |
| :--- | :--- |
| Create a review queue of up to 1,000 source-record entries | **Yes, if explicitly approved** |
| Collect public terms and provenance evidence for those entries | **Yes, if explicitly approved** |
| Bulk-download images, annotations, or metadata | **No** |
| Reconstruct web media | **No** |
| Retain records as training corpus | **No** |
| Generate embeddings or token caches | **No** |
| Train/fine-tune any model or adapter | **No** |
| Add another source family | **No** |

---

## 4. Gate Preconditions and Stop Conditions

Before any review entry is made, the process must have an approved source snapshot, review logging location, access-control plan, attribution capture procedure, filter/quarantine process, and removal contact path. The process must stop if terms become unavailable or contradictory, per-record attribution cannot be recorded, privacy/safety evidence is unresolved, source access implies a prohibited bulk download, or the proposed action exceeds the 1,000-record cap.

The queue itself remains a **review artifact**, not a training dataset. Any retention decision requires a later T2.2 gate with a reviewed manifest, sample-review outcomes, source-specific terms evidence, split-isolation report, and a proposed finite retained-item count.

---

## 5. Owner Approval Required

To authorize the strictly bounded T2.1 review queue described above, respond exactly:

`Approve T2.1 Review Queue`

This will not authorize media download, corpus retention, model training, or fine-tuning.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[2]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
