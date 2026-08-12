# Stage 2: Objective, Implementation & Evaluation Harness

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Implemented and verified on `feature/stage-1-core-substrate`  
**Owner Decision Required**: Approval is required before Stage 3 begins.

---

## 1. Ultimate Stage 2 Objective

Stage 2 augments the verified Stage 1 atomic vision substrate with a **lossless multi-scale energy representation** and a compact, trainable semantic-routing interface. The implementation uses a two-dimensional orthonormal Haar analysis pyramid over the Stage 1 Rec. 709 Energy layer. Each level produces an approximation band and horizontal, vertical, and diagonal detail bands while preserving original energy-layer reconstruction at floating-point precision.

The same direct H×W×3 `float32` memory contract remains valid. `atomizeMultiScaleInterleaved` reads the caller-owned RGB tensor directly, writes caller-owned Energy and Flow output layers, and creates only the explicit pyramid metadata and wavelet outputs necessary for the Stage 2 representation.

> **Stage 2 exit condition:** multi-scale decomposition must preserve energy reconstruction, expose mathematically orthogonal Haar basis functions, maintain the Stage 1 no-copy input contract, and produce finite, normalized semantic-routing weights through a trainable gate.

| Delivered Component | Implementation Location | Contract |
| :--- | :--- | :--- |
| Multi-scale Haar pyramid | `HaarWaveletPyramid`, `WaveletLevel`, `Atomizer::decomposeEnergyPyramid` | Produces edge-replicated levels that support odd image dimensions and exact inverse reconstruction of the represented energy layer. |
| Deterministic inverse | `Atomizer::reconstructEnergyPyramid` | Reconstructs the original Energy layer from approximation and three detail bands. |
| Direct multi-scale API | `Atomizer::atomizeMultiScaleInterleaved` | Preserves caller ownership of the RGB input and produces Stage 1 layers, a wavelet pyramid, gate features, and gate output. |
| Semantic attention gate | `SemanticAttentionGate` | A compact trainable softmax router over RGB, Energy, Flow-X, Flow-Y, wavelet detail, and wavelet approximation representations. |
| Python multi-scale API | `Atomizer.atomize_multiscale_numpy` | Returns Stage 2 tensors, per-level bands, gate features, gate weights, complexity, and entropy. |
| Native and Python harnesses | `stage2_evaluation.cpp`, `stage2_python_evaluation.py` | Establish reproducible numerical, interface, gate-stability, and memory-safety evidence. |

---

## 2. Implementation Contracts

The pyramid uses normalized 2×2 Haar basis vectors. In the interior of an image, each analysis unit maps four energy samples to one low-frequency approximation and three directional detail coefficients. For odd widths or heights, the final source row or column is edge-replicated for analysis and the inverse writes only the original spatial extent. This provides deterministic original-geometry reconstruction without silently resizing inputs.

The gate consumes four bounded visual statistics: a bias term, normalized energy variance, normalized Flow power, and normalized wavelet-detail power. It uses a stable softmax to output six non-negative weights summing to one. Its `trainStep` method performs bounded gradient descent on cross-entropy targets and reports the gradient L2 norm for stability monitoring.

| Contract | Required Behaviour | Failure Behaviour |
| :--- | :--- | :--- |
| Wavelet input | Stage 1 Energy H×W layer | Empty input returns an empty pyramid; inconsistent pyramids throw explicit errors on reconstruction. |
| Pyramid geometry | Ceiling-halved dimensions at each level | Odd dimensions remain represented at original spatial extent. |
| Inverse reconstruction | Float-domain energy reconstruction | The harness fails below the PSNR threshold. |
| Gate output | Six finite, non-negative weights summing to one | Invalid learning rate or target simplex raises an explicit exception. |
| Stage 1 compatibility | C-contiguous `float32` RGB input only | Non-conforming arrays are rejected rather than copied. |

---

## 3. Evaluation Harness

The native harness tests repository images (`city.jpg`, `dog.jpg`, and `gradient.jpg`) to verify that the actual implementation reconstructs the Energy layer, not merely a synthetic matrix. It separately verifies the transform basis itself, because statistical correlation between detail coefficients in arbitrary natural images is not an orthogonality test. The Python harness validates direct input pointer identity, odd-dimension pyramid geometry, direct numerical output, gate-simplex integrity, and layout rejection.

```bash
# Release build and native Stage 1 + Stage 2 regression suite
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON \
  -DALVS_BUILD_STAGE1_EVALUATION=ON \
  -DALVS_BUILD_STAGE2_EVALUATION=ON
cmake --build build --parallel
cd build && ctest --output-on-failure && ./stage2_evaluation

# Python direct multiscale API validation
cd ..
python3 stage2_python_evaluation.py

# Portable debug memory-safety validation
cmake -S . -B build-valgrind -DCMAKE_BUILD_TYPE=Debug \
  -DALVS_BUILD_PYTHON_MODULE=OFF \
  -DALVS_BUILD_STAGE1_EVALUATION=OFF \
  -DALVS_BUILD_STAGE2_EVALUATION=ON
cmake --build build-valgrind --parallel
valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
  ./build-valgrind/stage2_evaluation
```

---

## 4. Pass/Fail Transition Tests

| ID | Test | Hard Pass Criterion | Result Artifact |
| :--- | :--- | :--- | :--- |
| **TC-2.1** | Multi-scale reconstruction | Minimum Energy-layer PSNR above 58 dB across all three repository images. | `stage2_native_full_results.txt` |
| **TC-2.2** | Semantic-gate convergence | Cross-entropy decreases over ten epochs and maximum gradient L2 norm stays below 10.0. | `stage2_native_full_results.txt` |
| **TC-2.3** | Haar-basis orthogonality | Maximum off-diagonal basis inner product and norm error below `1e-4`. | `stage2_native_full_results.txt` |
| **TC-2.4** | Gate representation contract | Two wavelet levels; finite gate values; six non-negative weights sum to one. | `stage2_native_full_results.txt` |
| **TC-2.5** | Direct multi-scale equivalence | Caller RGB remains unchanged; direct and owned Energy/Flow paths match above the PSNR threshold. | `stage2_native_full_results.txt` |
| **TC-2.P1** | Python direct multi-scale route | Native metadata pointer matches NumPy data pointer; input remains unchanged. | `stage2_python_results.json` |
| **TC-2.P2** | Python output integrity | Energy error below `1e-6`; correct odd-dimension level shapes; gate simplex is valid. | `stage2_python_results.json` |
| **TC-2.P3** | Input-layout protection | Fortran-contiguous input is rejected rather than copied. | `stage2_python_results.json` |
| **TC-2.M1** | Native memory safety | Valgrind reports zero errors and no heap blocks in use at exit. | `stage2_valgrind_results.txt` |

---

## 5. Scope Boundary & Stage 3 Prerequisite

The Stage 2 gate is a **trainable routing primitive**, not a pretrained vision-language semantic model. Its convergence harness uses controlled target distributions to validate gradient stability and parameter-update behavior. It does not claim benchmark-level VQA, object recognition, or language grounding quality; those require a defined labelled dataset, a selected target model, and a later multimodal training/evaluation stage.

Stage 3 may now assume a stable Stage 2 contract: direct RGB input maps to base atomic layers, a reconstructible multi-scale Energy pyramid, and normalized semantic-routing metadata. Stage 3 must accelerate these same mathematical outputs without changing the Stage 1/2 numerical contracts or reintroducing input copies.
