# T2.1 → T2.2 Source-Verification Gate

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: **T2.1 METADATA REVIEW COMPLETE — MEDIA RETENTION AND TRAINING REMAIN BLOCKED**

---

## 1. Gate Decision

The bounded review queue was created and audited within the approved limit. The queue has 710 metadata-only records, all of which are quarantined. The review confirms basic metadata completeness and source-row CC BY 2.0 signals, but it does not establish item-level rights, privacy/safety suitability, text/image similarity, or removal controls. The Open Images licence page itself says users should verify each image [1].

> **Decision:** no record may be retained as pilot data or used for model training. The next permitted step, if approved, is a small manual source-verification and safety-review sample—not a training dataset download.

---

## 2. Required T2.2 Scope

A T2.2 approval would authorize only a controlled review sample of **no more than 50 records** selected from the existing 710-record quarantine queue. It may retrieve the source page and, where necessary for safety/privacy review, a single item’s media under a non-training review workspace. Every retrieved sample must be deleted or retained only as an explicit review artifact according to the final item-level decision.

| Action | Authorized by T2.2? |
| :--- | :--- |
| Select at most 50 IDs from the existing review queue | **Yes, if approved** |
| Retrieve source/landing-page evidence and record attribution/licence observations | **Yes, if approved** |
| Retrieve at most one item’s media solely when necessary for manual privacy/safety review | **Yes, if approved** |
| Maintain an item-level review log and deletion/retention decision | **Yes, if approved** |
| Retain any item as pilot training data | **No** |
| Retrieve more than 50 media items | **No** |
| Download annotations or a bulk dataset | **No** |
| Generate embeddings, tokens, or features | **No** |
| Train/fine-tune/evaluate a learned model | **No** |
| Add a new data source | **No** |

---

## 3. T2.2 Pass Criteria

| Criterion | Required Evidence |
| :--- | :--- |
| Record-level source and attribution | Canonical source page, creator/attribution observations, and record-specific licence evidence or a documented failure. |
| Licence and rights caveat | Reviewed terms record; unresolved/privacy/publicity/moral-rights issues documented as a block. |
| Privacy and safety | Documented human-review decision under the filtering/quarantine protocol. |
| Removal and retention | Source removal path and explicit local deletion/retention decision. |
| Split integrity | Candidate identifiers remain outside active training; no model use. |
| Audit trail | Reviewer, time, manifest checksum, decision, and evidence reference for each sampled record. |

A T2.2 review does not determine that 50 records are suitable for training. It only determines whether the project has enough source-level evidence to prepare a later, separately approved retained-pilot proposal.

---

## 4. Training Boundary

A training run will remain blocked after T2.2 until the owner has reviewed an explicit retained-pilot manifest, data-card records, review outcomes, split-integrity report, compute plan, base-model licence, and predeclared evaluation protocol. Training must then be separately authorized as a bounded adapter-baseline experiment.

## 5. Owner Approval Required

To authorize only the 50-record manual source-verification and safety-review sample, respond exactly:

`Approve T2.2 Source Verification Sample`

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
