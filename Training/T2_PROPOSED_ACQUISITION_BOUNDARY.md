# T2 Proposed Pilot Acquisition Boundary — Open Images V7 Review Package

**Status**: Proposal only. No source content, item identifiers, bulk metadata, or downloadable media have been accessed or retained.  
**Proposed source**: Open Images V7, subject to source- and item-level review  
**Not a legal opinion**: This document defines an engineering review boundary and does not replace legal, privacy, or jurisdiction-specific advice.

---

## 1. Why This Source Is Proposed

Open Images V7 is proposed as a narrowly scoped supervised-grounding candidate because its official description identifies multiple complementary annotation types, including image-level labels, bounding boxes, segmentation masks, visual relationships, and localized narratives [1]. Those modalities are relevant to evaluating an adapter over the existing AGI-VS visual-token substrate.

The source is proposed only with strict constraints. The official Open Images licence page states that annotations are CC BY 4.0 and that images are listed as CC BY 2.0, but it also expressly states that the publisher makes no representation or warranty about each image’s licence status and advises users to verify each image [2]. The project therefore will not treat the dataset-level statement as an item-level blanket approval.

---

## 2. Proposed Boundary

| Boundary Element | Proposed Limit | Status |
| :--- | :--- | :--- |
| Candidate source | Open Images V7 only | Proposed; not accessed for acquisition. |
| Candidate material | Image, selected associated annotation, and attributable source record only | No media or metadata retained yet. |
| Maximum pilot review queue | **1,000 manually reviewable candidate records** | Proposed hard cap; no automatic expansion. |
| Maximum retained training pilot | **0 until a later acquisition and sample-review decision** | Currently blocked. |
| Annotation priority | Object/location and visual-relationship annotations; localized narratives only after separate content review | Proposed. |
| Excluded source classes | COCO, DataComp, LAION, Common Crawl, and any other web-index source | Explicitly excluded from this T2 proposal. |
| Intended use | Adapter-baseline research and held-out visual-grounding evaluation design | No deployment or sensitive-use authorization. |
| Media reconstruction | Not authorized | Remains blocked. |

The 1,000-record queue is a **review boundary**, not a download instruction. It is intended to make attribution, terms review, privacy screening, and representative human review practical before any data-retention decision.

---

## 3. Required Per-Record Evidence Before Retention

Every proposed record must have the following fields completed and pass review before it could ever be retained for a pilot. Records with missing fields are rejected or quarantined.

| Evidence Field | Requirement |
| :--- | :--- |
| Stable record identifier | Source-provided identifier and canonical source reference. |
| Original creator/source attribution | Creator, title if supplied, and source-link fields necessary to satisfy the applicable attribution requirements. |
| Licence evidence | Per-record licence indication plus date/time and source-page evidence. |
| Rights caveats | Explicit review of the source’s no-warranty statement and any publicity, privacy, moral-rights, or other restrictions. |
| Annotation origin | Annotation type, version, and annotation licence record. |
| Privacy/safety decision | Filter result, human-review outcome where flagged, and quarantine rationale if excluded. |
| Split decision | Deterministic assignment to proposed training/development/held-out queues before any model use. |
| Removal path | Provider/contact or source procedure plus local removal identifier. |
| Manifest information | Source/annotation checksum or stable evidence record sufficient for reproducibility. |

CC BY 2.0 requires appropriate credit, a licence link, and change indication under the deed, while its notices explain that other rights—such as publicity, privacy, or moral rights—may still constrain use [3]. This is why the project requires per-record attribution and risk fields rather than only a dataset-level licence label.

---

## 4. Filters and Quarantine Rules

The pilot review queue must exclude or quarantine records with unresolved licence evidence, visible sensitive personal data, identities in high-risk contexts, sexual/explicit content, content involving minors, health/medical information, violence or self-harm content, hateful/harassing content, personal documents, private-location signals, or annotation/caption content that conflicts with the intended research use. This is a conservative design choice, not a claim that automated filters can conclusively identify all such content.

Any record that cannot be confidently categorized must enter a **do-not-use quarantine**. The quarantine queue may not be used for training, evaluation, embedding computation, or model selection.

---

## 5. Acquisition Prerequisites

Before even a bounded review queue may be acquired, the owner must approve a final source package containing: a current terms snapshot, an exact requested version/split, item-record fields, attribution procedure, privacy/safety filter specification, manual-review protocol, retention period, removal procedure, access controls, split-isolation method, and pilot evaluation plan. This package must also identify the responsible reviewer roles listed in the T0 governance charter.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[2]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[3]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
