# T2.5 Project-Owned Deterministic Visual-Scene Pilot

**Status**: Selected after the Art Institute image-delivery endpoint blocked automated access; no external source media retained
**Source class**: Project-owned procedural corpus created from repository code
**Purpose**: Run a complete, reproducible visual-to-structured-text adapter experiment under a fully controlled permission and provenance boundary.

---

## 1. Source Change

The Art Institute of Chicago T2.4 metadata review passed for a finite CC0 allow-list, but its official IIIF image endpoint returned a Cloudflare challenge (`HTTP 403`) to the automated manifest-locked retrieval process. The process was stopped with **zero image files retained**. That delivery block does not invalidate the provider’s metadata policy; it makes the selected assets unavailable for this runnable environment.

The pilot therefore changes to a **project-owned deterministic visual-scene corpus**. Every source image, annotation, caption, split, and manifest will be generated locally by a versioned repository script. It will use only basic geometric primitives and RGB colors. It will contain no people, biometric information, third-party artwork, logos, external captions, web-crawled material, or provider-derived source images.

> **Rights decision:** the project owns the generated corpus as an output of its own repository code. This removes the external licensing, removal-contact, and source-provenance dependencies that blocked the Art Institute delivery path. It does not turn this controlled corpus into evidence of broad real-world visual competence.

---

## 2. Bounded Training Objective

The corpus will consist of simple scenes containing two or three colored geometric objects. Each scene has source-of-truth attributes for object shape, color, size, count, and left/right or above/below spatial relations. A normalized caption is generated from the same deterministic scene record, such as “a red circle is left of a blue square.”

| Element | Decision |
| :--- | :--- |
| Corpus owner | AGI-VS project; all artifacts created locally from tracked generator code. |
| Source media | 384 deterministic 256 × 256 RGB PNG scenes, with no external image download. |
| Target representation | Structured caption embedding derived from the locally generated scene record; caption text is retained for retrieval interpretation only. |
| Visual encoder | Frozen Stage 1–4 AGI-VS visual-token interface. |
| Trainable model | Compact learned projection from pooled Stage 4 tokens to the structured text-embedding space. |
| Baseline B0 | Fixed deterministic random projection with no fitted visual adapter. |
| Adapter B1 | Ridge-trained cross-modal projection fit only on the frozen training split. |
| Split allocation | Deterministic 70% train, 15% development, 15% held-out, with no scene ID reuse. |
| Held-out measures | Caption-retrieval Recall@1, Recall@5, MRR, attribute F1, spatial-relation accuracy, numerical stability, and deterministic rerun equivalence. |
| Explicit limitation | The corpus validates data governance, full pipeline execution, token-interface compatibility, and a controlled relation-learning task. It cannot establish performance on photographs, people, open-world semantics, safety-critical use, or AGI. |

---

## 3. Data Controls

| T0 control | Project-owned implementation |
| :--- | :--- |
| Permission | Repository-owned generator, annotations, captions, and output manifest; no external asset licence required. |
| Provenance | Every record includes generator version, random seed, scene specification, caption, output checksum, and split. |
| Privacy and safety | No people, faces, biometric data, personal data, sexual content, violence, brands, or external images. |
| Removal and retention | Any record can be regenerated from its scene ID; local removal deletes its image, manifest row, derived feature, and checkpoint lineage. Review expiry is 90 days. |
| Split integrity | Deterministic split assignment before training; held-out records are excluded from fitting and development selection. |
| Reproducibility | Generator seed, scene manifest hash, encoder build, adapter configuration, metrics code, and outputs are recorded. |

---

## 4. Advancement

T2.5 may proceed directly to local corpus generation and audit because the source is project-owned and its content boundary is fully specified. The Art Institute metadata-only artifacts remain in the repository as evidence of the blocked external-source path; they must not be treated as a retained corpus and their images must not be retried without a future access-specific review.
