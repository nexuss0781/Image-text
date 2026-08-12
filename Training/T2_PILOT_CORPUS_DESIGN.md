# T2 Pilot Corpus Design — Pending Acquisition Approval

**Status**: Design only. No image, text, metadata bulk export, or model-training run has been initiated.  
**Depends on**: `T0_GOVERNANCE_CHARTER.md` and `candidate_dataset_registry.json`  
**Next decision**: A separate pilot-acquisition approval is required before any source is accessed beyond public documentation.

---

## 1. Pilot Objective

The pilot is designed to test whether a trainable cross-modal adapter can improve task-specific visual grounding over the deterministic Stage 4 token baseline while preserving Stage 1–5 performance contracts. It is **not** a foundation-model pretraining run and is not intended to establish an AGI claim.

The pilot must be small enough for manual review, full provenance capture, deterministic reruns, and clear ablation. It must include isolated development and held-out evaluation partitions before training configuration is finalized.

---

## 2. Proposed Source Sequence

| Priority | Source Type | Proposed Role | T2 Decision Rule |
| :--- | :--- | :--- | :--- |
| **A** | Named permissioned or first-party source | Primary pilot training material | Mandatory. No pilot starts without one reviewed source with explicit compatible permission or terms. |
| **B** | Reviewed Open Images subset | Secondary supervised grounding material | Consider only after current source/split terms, attribution, and privacy/content controls have been reviewed. The source’s annotation breadth may support grounding tasks [1]. |
| **C** | COCO-like benchmark split | Held-out evaluation only | Remains outside the initial training pool to reduce direct benchmark contamination. Terms and prior-exposure risks must be assessed before access. |
| **D** | DataComp/LAION/Common-Crawl web-derived candidates | Methodology or discovery only | Excluded from pilot acquisition unless a later source-level allow-list and reconstruction decision is approved. Public-web indexing is not sufficient training clearance [2] [3]. |

The pilot design deliberately has **no target sample count** at T1. Quantity must be selected only after the source-specific licence/terms, data quality, storage, compute budget, and review burden are known. This avoids treating a numeric target as a reason to relax provenance or safety requirements.

---

## 3. Required Pipeline Before Training

Every acquired pilot item must pass each step below. A failed or indeterminate step sends the item to quarantine rather than the training split.

| Step | Required Artifact | Pass Condition |
| :--- | :--- | :--- |
| Source registration | Immutable source ID, source record, terms snapshot, access date | All required provenance fields present. |
| Rights/terms review | Human review record and allowed-use category | Terms compatible with the approved research purpose and any attribution/retention requirements. |
| Privacy and safety triage | Filter version, flags, review outcome | No unresolved sensitive-content, PII, or policy issue for the proposed use. |
| Deduplication and leakage screening | Perceptual/text duplicate report plus benchmark overlap report | No unreviewed overlap across train/dev/test or selected external evaluation sets. |
| Quality screening | Annotation/caption-quality indicators and representative review | Meets predeclared quality threshold; low-confidence items quarantined. |
| Split assignment | Deterministic split rule and random seed | Each item assigned once; held-out split remains write-protected. |
| Dataset card | Versioned card and manifest checksum | Contents, terms, limitations, risks, and removal process documented. |

Dataset cards are used because they document contents, context, responsible-use considerations, and metadata such as licence, language, and size [4]. The project’s registry adds source-level terms evidence because large-scale provenance audits have found missing and unreliable licence information in popular aggregations [5].

---

## 4. Training and Evaluation Design

The first trainable experiment will freeze the Stage 1–3 core and use Stage 4 tokens as the visual interface. The initial learned element is a small cross-modal adapter. The experiment must compare a frozen deterministic-token baseline against the adapter under identical data splits, prompts, optimizer budget, and random seeds.

| Evaluation Category | Required Held-Out Evidence |
| :--- | :--- |
| Token/interface stability | Stage 1–5 CTest suite remains fully passing before and after each experiment. |
| Supervised visual grounding | Predeclared task metrics for the reviewed pilot’s allowed capabilities. |
| Cross-modal alignment | Retrieval, caption-grounding, or question-answering protocol appropriate to the selected adapter and data. |
| Calibration and uncertainty | Confidence/error analysis and explicit abstention or uncertainty behavior where designed. |
| Robustness | Declared corruption, distribution-shift, and prompt/image perturbation cases. |
| Safety and privacy | Held-out tests reflecting the documented source and intended-use risks. |
| Reproducibility | Training code revision, configuration, seed, environment, data manifest checksum, and checkpoint hash. |

---

## 5. T2 Approval Package Required

Before pilot acquisition may start, the owner must receive a finite source list, selected versions/splits, term or permission evidence, data card drafts, retention/removal workflow, sample-review protocol, filtering specification, deduplication plan, split-isolation plan, compute/storage budget, and proposed evaluation plan. Any web-media reconstruction request must be separately identified and justified.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[2]: https://laion.ai/faq/ "LAION FAQ — Dataset Index and Reconstruction Context"
[3]: https://github.com/mlfoundations/datacomp "DataComp — Public-Web Curation Benchmark"
[4]: https://huggingface.co/docs/hub/en/datasets-cards "Hugging Face Dataset Cards"
[5]: https://www.nature.com/articles/s42256-024-00878-8 "A Large-Scale Audit of Dataset Licensing and Attribution in AI"
