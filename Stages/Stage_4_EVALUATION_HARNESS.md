# Stage 4: Objective, Visual-Token Projection & Evaluation Harness

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Deterministic CPU-compatible visual-token integration implemented and verified  
**Owner Decision Required**: Approval is required before Stage 5 begins.

---

## 1. Ultimate Stage 4 Objective

Stage 4 converts the verified Stage 1–3 atomic visual representation into a compact, LLM-shaped token interface. The implementation creates patch-level features from Energy, Flow-X, Flow-Y, and the finest Haar approximation/detail bands, ranks patches using the Stage 2 semantic gate, retains a configurable token budget, and produces RMS-normalized embeddings of a requested dimension. The default interface returns **4096-dimensional** token vectors, suitable in shape for many contemporary LLM backbones.

The implementation is deliberately deterministic and self-contained. It does **not** claim learned alignment with Llama, Qwen, or another pretrained VLM; a trained projection adapter and model-specific calibration are separate requirements. It also does not claim VQAv2/GQA quality or real-time video performance, because no target VLM, labelled dataset, or video workload has been selected for this stage.

> **Stage 4 exit condition:** atomic layers must map to deterministic, normalized 4096-dimensional embeddings under a configurable adaptive token budget while retaining direct input ownership and explicit layout validation.

| Delivered Component | Implementation Location | Contract |
| :--- | :--- | :--- |
| Projection interface | `VisualTokenProjector`, `VisualTokenProjection`, `ProjectionConfig` | Converts atomic layers and Stage 2 wavelets into token-major embedding vectors. |
| Adaptive pruning | `VisualTokenProjector::project` | Ranks patches with gate-weighted Energy, Flow, approximation, and detail signals. |
| RMS normalization | `VisualTokenProjector::project` | Normalizes each token embedding to unit RMS, with numerical epsilon protection. |
| Deterministic tie behavior | `VisualTokenProjector::project` | Uses stable ordering by importance, then patch row and column. |
| Python multimodal API | `Atomizer.project_multimodal_numpy` | Runs direct Stage 2 atomization and Stage 4 projection without copying the RGB input. |
| Native/Python harnesses | `stage4_evaluation.cpp`, `stage4_python_evaluation.py` | Validate shape, budget, normalization, determinism, direct ownership, and invalid-layout handling. |

---

## 2. Projection & Token-Budget Contract

The projector tiles the spatial domain into configurable patches; its default patch size is 4×4. For every patch it aggregates Energy, absolute directional flow, flow magnitude, approximation energy, and directional detail magnitude. The semantic gate supplies representation weights to construct a ranking score. After stable sorting, the projector retains `ceil(source_patches × retention_ratio)` tokens, optionally bounded by `max_tokens`.

The embedding is a deterministic, fixed-basis projection followed by RMS normalization. This makes the implementation reproducible and auditable without embedding an untrained opaque neural network. A later learned adapter can replace the fixed basis only if it preserves the token-budget, output-shape, and numerical-safety contracts.

| Contract | Required Behaviour | Failure Behaviour |
| :--- | :--- | :--- |
| Input | Stage 1/2 C-contiguous H×W×3 `float32` tensor | Non-conforming layout is rejected before native processing. |
| Patch size | Positive integer | Zero patch size raises an explicit error. |
| Retention ratio | Finite and in `(0, 1]` | Out-of-range ratio raises an explicit error. |
| Output | Token-major `[retained_tokens, embedding_dimension]` | Invalid embedding dimension raises an explicit error. |
| Normalization | Per-token RMS equals 1 within tolerance | Harness fails on RMS deviation. |
| Ordering | Importance is non-increasing | Stable row/column ordering resolves equal-score ties. |

---

## 3. Evaluation Harness

The native harness exercises the projector over an 80×64 synthetic mixed-gradient/checkerboard tensor, which produces 320 source patches at a 4×4 patch size. With the default 25% retention ratio, it retains 80 tokens: an exact **75% token reduction**. The Python harness validates the direct API independently, including input pointer identity and Fortran-layout rejection.

```bash
# Release build and Stage 1–4 regression suite
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON \
  -DALVS_BUILD_STAGE1_EVALUATION=ON \
  -DALVS_BUILD_STAGE2_EVALUATION=ON \
  -DALVS_BUILD_STAGE3_EVALUATION=ON \
  -DALVS_BUILD_STAGE4_EVALUATION=ON
cmake --build build --parallel
cd build && ctest --output-on-failure && ./stage4_evaluation

# Python direct multimodal projection validation
cd ..
python3 stage4_python_evaluation.py

# Portable memory validation
cmake -S . -B build-valgrind -DCMAKE_BUILD_TYPE=Debug \
  -DALVS_BUILD_PYTHON_MODULE=OFF \
  -DALVS_BUILD_STAGE1_EVALUATION=OFF \
  -DALVS_BUILD_STAGE2_EVALUATION=OFF \
  -DALVS_BUILD_STAGE3_EVALUATION=OFF \
  -DALVS_BUILD_STAGE4_EVALUATION=ON
cmake --build build-valgrind --parallel
OMP_NUM_THREADS=1 valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
  ./build-valgrind/stage4_evaluation
```

---

## 4. Pass/Fail Transition Tests

| ID | Test | Hard Pass Criterion | Result Artifact |
| :--- | :--- | :--- | :--- |
| **TC-4.1** | Embedding output contract | Positive retained-token count and `[tokens, 4096]` layout; max RMS error below `1e-4`. | `stage4_native_full_results.txt` |
| **TC-4.2** | Adaptive budget | Exact source count and 25% retained count; 75% reduction; non-increasing importance. | `stage4_native_full_results.txt` |
| **TC-4.3** | Determinism and source integrity | Identical repeated projection and unchanged RGB source. | `stage4_native_full_results.txt` |
| **TC-4.4** | Configuration safety | `max_tokens` cap enforced and invalid retention ratio rejected. | `stage4_native_full_results.txt` |
| **TC-4.P1** | Python shape and RMS contract | `[80, 4096]` result with max RMS error below `1e-4`. | `stage4_python_results.json` |
| **TC-4.P2** | Python budget and ordering contract | 320 source patches, 80 retained tokens, 75% reduction, sorted importance. | `stage4_python_results.json` |
| **TC-4.P3** | Python deterministic direct route | Identical repeated embeddings; direct input pointer; source unchanged. | `stage4_python_results.json` |
| **TC-4.P4** | Layout protection | Fortran-contiguous input rejected. | `stage4_python_results.json` |
| **TC-4.M1** | Memory safety | Zero definite, indirect, and possible loss; zero Valgrind errors. | `stage4_valgrind_results.txt` |

---

## 5. Scope Boundary & Stage 5 Prerequisite

Stage 4 validates **interface shape, deterministic token compression, and numerical behavior**, not semantic-task quality. The original VQA accuracy criterion requires a named target VLM, an adapter-training plan, a permitted labelled benchmark dataset, and reproducible inference infrastructure. The streaming-video latency criterion similarly requires a defined video ingestion pipeline and target frame-resolution budget.

Stage 5 may now prepare production packaging, CI, and benchmark infrastructure for the verified CPU path. Any claim of VLM semantic accuracy, VQA quality retention, or live-video reasoning must remain deferred until those model- and dataset-specific acceptance tests are implemented.
