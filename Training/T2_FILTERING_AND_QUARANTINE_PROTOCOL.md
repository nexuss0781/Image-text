# T2 Filtering, Quarantine, and Removal Protocol

**Status**: Protocol only; no candidate data has been processed  
**Default posture**: Fail closed — unverified or ambiguous records are quarantined and excluded from all model use.

---

## 1. Objective

This protocol defines the minimum review flow for any future Open Images V7 candidate record after a source-specific acquisition gate has been approved. It does not authorize content retrieval, embedding creation, model training, or retention. It exists so that a future decision can be audited against a fixed process rather than an informal collection step.

---

## 2. Decision States

| State | Meaning | Permitted Actions |
| :--- | :--- | :--- |
| `unreviewed` | No evidence has been reviewed | None; record cannot be used. |
| `terms_pending` | Source/attribution/licence evidence incomplete | None; seek clarification or quarantine. |
| `automated_flagged` | A technical rule indicates privacy, safety, quality, or duplication risk | No model use; route to human review or quarantine. |
| `human_review_required` | Automated screening is insufficient or uncertain | No model use; documented reviewer decision required. |
| `quarantined` | Rejected, unresolved, removed, or unsafe record | No training, evaluation, embedding, or derivative retention. |
| `eligible_pending_owner_gate` | All required evidence passes review | Still cannot be retained or used until the gate explicitly permits it. |
| `authorized_retention` | Owner-approved record under a defined pilot | Use limited to the approved manifest, purpose, split, and retention period. |

---

## 3. Mandatory Review Stages

| Stage | Required Check | Failure Result |
| :--- | :--- | :--- |
| 1. Source identity | Stable source record and canonical source reference | Quarantine. |
| 2. Attribution and terms | Item-level evidence, creator/attribution fields, licence link, and caveat review | Quarantine or terms-pending. |
| 3. Annotation record | Annotation type/version and annotation-licence evidence | Quarantine. |
| 4. Privacy/sensitive-content triage | PII, biometric/identity, minors, health, private document/location, or other sensitive-context indicators | Human review required or quarantine. |
| 5. Safety/content triage | Explicit/sexual content, exploitation, violence, self-harm, hateful/harassing material, or content outside declared purpose | Human review required or quarantine. |
| 6. Quality and purpose fit | Annotation/caption coherence, corruption, relevance to approved task, and known limitation check | Quarantine. |
| 7. Deduplication and leakage | Perceptual/text duplicate checks against prospective splits and protected benchmarks | Quarantine or explicit split reassignment. |
| 8. Retention/removal | Removal contact/procedure and expiry/review date | Quarantine. |

---

## 4. Human-Review Requirements

Human review is mandatory for all records that are flagged, ambiguous, sensitive, or otherwise outside automatic-rule confidence. The reviewer must record the decision, rationale, date, policy version, and any required retention limitations. No record may bypass human review because it is expensive or because a queue is near its target size.

The source-specific assessment notes that Open Images’ published licence statement includes a no-warranty caveat and says each image should be verified; this protocol treats that caveat as a hard requirement for record-level evidence, not a procedural footnote [1]. The Creative Commons deeds also state that privacy, publicity, and moral rights may require additional permissions, supporting a separate rights-caveat check [2] [3].

---

## 5. Removal and Incident Handling

A removal request, rights dispute, privacy concern, or unsafe-content incident immediately freezes the affected record and all derivative uses. The record’s manifest identifier, source reference, split assignment, transformation history, and any derived artifact references must be available for review. The project must document the outcome, remove the record within the agreed process, and rerun any impacted data-manifest, duplicate, and evaluation-integrity checks before proceeding.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[2]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
