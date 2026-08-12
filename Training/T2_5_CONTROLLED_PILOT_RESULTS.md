# T2.5 Controlled Pilot: Final Measured Result

**Status**: **PASS — reproducible controlled adapter experiment completed**
**Scope**: Frozen AGI-VS Stage 1–4 visual interface plus a train-only ridge adapter on a project-owned procedural corpus
**Non-claim**: This is not a pretrained VLM, real-world vision model, production model, or evidence of AGI.

---

## 1. Executive Result

The project completed an end-to-end, governance-controlled training run after the Art Institute of Chicago’s media-delivery endpoint blocked automated access to the selected metadata-reviewed source. The fallback corpus was created locally from versioned repository code and contains only colored geometric scenes with deterministic source-of-truth captions and relations. No external media was retained for this successful run.

The learned adapter (**B1**) materially improved held-out visual-to-structured-text retrieval and spatial-relation accuracy over the fixed, no-training baseline (**B0**). The test was rerun with the same seed; feature cache, held-out result object, and checkpoint hash were identical across runs.

> **Conclusion:** the frozen Stage 4 representation can feed a small learned adapter that improves on a declared controlled held-out task. The result validates the runnable data, token, training, and reproducibility path; it does not validate open-world visual understanding.

---

## 2. Corpus and Governance Result

| Control | Measured result |
| :--- | :--- |
| Corpus source | 384 project-owned deterministic scenes generated locally by `scripts/generate_t25_owned_scenes.py`. |
| External media | **0** downloaded or retained in the successful pilot corpus. |
| Content boundary | RGB geometric shapes only; no people, faces, biometrics, personal data, text rendered in images, brands, third-party artwork, sexual content, or violence. |
| Split isolation | 287 train, 41 development, and 56 held-out records assigned before fitting. |
| Provenance | Every record records its scene specification, generator seed, output checksum, caption, attributes, and split. |
| Exact duplicates | 384 unique image checksums and 384 unique captions; audit passed. |
| Visual review | A representative 24-scene contact sheet was reviewed and matched the declared non-sensitive geometric-content boundary. |
| Removal/retention | Every record is regenerable and locally removable by asset ID; review expiry is 90 days after generation. |

The corpus audit passed with no hard failures. Its manifest SHA-256 is `c0d0f00ca999eb7f7aa173ad982bdf5ae07eef269140b4bf43f95bc3af4666c0` [1].

---

## 3. Frozen Visual Interface and Training Configuration

| Component | Final configuration |
| :--- | :--- |
| Vision substrate | Existing Stage 1–4 implementation; Stage 1–3 and Stage 4 projector remained frozen. |
| Python binding | `alvs_cpp` from `build-production`; AVX-512F backend available. |
| Input contract | 256 × 256 C-contiguous `float32` RGB tensors; binding reported `input_copied: false`. |
| Stage 4 tokens | 32 retained tokens from 256 source patches per scene, with 4,096 dimensions per token. |
| Visual feature | RMS-normalized mean pooling of frozen Stage 4 tokens: 384 × 4,096 feature matrix. |
| Text target | Locally generated 52-dimensional structured attribute vector for color, shape, size, count, and spatial relations. |
| Baseline B0 | Fixed seeded random projection; no fitted visual adapter. |
| Adapter B1 | Closed-form dual ridge-regression projection fitted only on the 287-record training split. |
| Development selection | Ridge alpha chosen from 0.01, 0.1, 1, 10, and 100 on development Recall@1 then MRR; selected alpha = 0.1. |
| Threshold policy | A global attribute-F1 threshold was selected on development only and frozen for held-out scoring. Field-wise slot accuracy is reported alongside thresholded F1. |

Feature extraction required **4.256 seconds** for all 384 images, or approximately **11.1 ms per image** on the recorded CPU environment [2].

---

## 4. Held-Out Result

| Metric | B0: fixed no-training baseline | B1: learned adapter | B1 − B0 |
| :--- | ---: | ---: | ---: |
| Retrieval Recall@1 | 3.57% | **17.86%** | **+14.29 pp** |
| Retrieval Recall@5 | 5.36% | **42.86%** | **+37.50 pp** |
| Mean reciprocal rank | 0.0794 | **0.2995** | **+0.2201** |
| Thresholded attribute F1 | 0.7658 | **0.9829** | **+0.2170** |
| Field-wise attribute-slot accuracy | 24.74% | **41.01%** | **+16.28 pp** |
| Spatial-relation accuracy | 31.33% | **50.60%** | **+19.28 pp** |

The primary retrieval and structured field metrics all improve over B0. The field-wise slot accuracy is particularly important because it does not depend on the development-selected global decision threshold. The full machine-readable report, including every development hyperparameter result and the checkpoint digest, is retained as `Training/artifacts/t2_5_adapter_report.json` [2].

---

## 5. Integrity and Reproducibility

| Check | Result |
| :--- | :--- |
| Stage 4 same-input determinism | Repeated projection of the first sample was identical within the configured `1e-7` pooled-feature tolerance. |
| Numerical stability | No NaN or Inf values in frozen features, targets, or fitted adapter weights. |
| Held-out isolation | Held-out records were excluded from fitting and development alpha/threshold selection. |
| Substrate regressions | All five native CTest stages passed after the experiment. |
| Independent rerun | Feature-cache SHA-256, held-out result object, and checkpoint SHA-256 were all identical. |
| Checkpoint SHA-256 | `8a65f15ba45d6d4bb8b62a6c82bc9543bc43685d1173e3823b3d43e67c5c4374` |

---

## 6. External Source Block and Corrective Decision

The Art Institute of Chicago route was reviewed through a bounded metadata-only T2.4 process. The metadata source and public-domain field were accessible, but the official manifest-locked IIIF delivery URL responded with an `HTTP 403` Cloudflare challenge in this environment. The retrieval process was terminated after detecting the block and wrote **zero retained image files**. The project did not bypass the access control or substitute an unreviewed mirror.

The project-owned corpus was selected to complete a real runnable experiment without weakening permission, provenance, or safety controls. The retained T2.4 metadata review remains useful documentation but is not part of the training corpus [3].

---

## 7. Limitations and Next Evidence Gate

The present result is intentionally narrow. The structured text vectors are generated from known scene specifications rather than from a language model. The images are simple geometric scenes, not photographs or open-world imagery. As a consequence, the measured improvement cannot be generalized to captioning, visual question answering, real-world object recognition, medical/surveillance/identity use, or AGI.

A future broader-data run must start with a delivery-accessible **named permissioned or first-party source**, complete the same item-level manifest and audit process, and preserve held-out evaluation. It must not absorb the controlled-corpus result as proof that an external source is automatically approved.

## References

[1]: artifacts/t2_5_owned_scene_audit_report.json "T2.5 Project-Owned Visual-Scene Corpus Audit"
[2]: artifacts/t2_5_adapter_report.json "T2.5 Controlled Adapter Report"
[3]: T2_4_ART_INSTITUTE_SOURCE_REVIEW.md "T2.4 Art Institute CC0 Source-Specific Review"
[4]: T2_5_PROJECT_OWNED_CORPUS_SELECTION.md "T2.5 Project-Owned Deterministic Visual-Scene Pilot"
[5]: ../Stages/TRAINING_PROGRAM_GATE.md "AGI-VS Data Curation, Training and Fine-Tuning Program Gate"
