# Stage 1: Objective, Implementation & Evaluation Harness

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Implemented and verified on `feature/stage-1-core-substrate`  
**Owner Decision Required**: Approval is required before Stage 2 begins.

---

## 1. Ultimate Stage 1 Objective

Stage 1 establishes an auditable **CPU-native vision substrate** that accepts C-contiguous `float32` H×W×3 tensors directly from NumPy, performs Rec. 709 energy decomposition without an image-sized input copy, and remains safe under high-volume allocation stress. The work is deliberately scoped to the current repository's CPU/C++ substrate; CUDA pinned-host allocations and unified virtual addressing are deferred until a CUDA-capable execution environment is available.

> **Stage 1 exit condition:** the project must provide a zero-copy Python-to-C++ input route, a portable aligned-memory primitive, a runtime-selected SIMD energy path, deterministic output equivalence, memory-safety evidence, and reproducible automated evaluation commands.

| Delivered Component | Implementation Location | Acceptance Intent |
| :--- | :--- | :--- |
| 64-byte aligned tensor owner | `alvs_core.h`, `alvs_core.cpp` | Give native stages cache-line-aligned, explicit-lifetime tensor storage. |
| Direct interleaved tensor route | `Atomizer::atomizeInterleaved` | Process the caller-owned H×W×3 `float32` buffer without converting it into a `std::vector<Pixel>`. |
| SIMD energy kernel | `Atomizer::computeEnergyInterleaved` | Dispatch to AVX-512F, AVX2, or scalar code at compile time while preserving a common numerical contract. |
| Strict NumPy contract | `bindings.cpp` | Reject non-`float32` and non-C-contiguous inputs instead of silently materializing a copied buffer. |
| Native regression harness | `stage1_evaluation.cpp` | Verify allocation, numerical correctness, direct-route equivalence, degenerate geometry, and 4K characterization. |
| Python binding harness | `stage1_python_evaluation.py` | Verify pointer identity, metadata handoff latency, direct-path energy output, and rejection behavior. |
| CTest registration | `CMakeLists.txt` | Permit repeatable native regression execution from the build directory. |

---

## 2. Implementation Contracts

The native direct path operates on a caller-owned, interleaved RGB buffer. `atomizeInterleaved` writes Energy, Flow-X, and Flow-Y to caller-provided H×W output buffers; it does not allocate or copy an image-sized input buffer. The legacy `Atomizer::atomize(std::vector<Pixel>, ...)` route is retained for compatibility but delegates to the direct compute path after its legacy-owned color context is established.

The Python extension uses generic `py::array` arguments and validates both `float32` dtype and C-contiguity before accessing the data pointer. This design is intentional: typed pybind conversion may otherwise create a format-converting temporary. Arrays that cannot meet the direct path's memory-layout contract are rejected with an explicit exception rather than being copied implicitly.

| Contract | Required Behaviour | Failure Behaviour |
| :--- | :--- | :--- |
| Input type | NumPy `float32` | Explicit `ValueError` for any other dtype. |
| Input layout | C-contiguous H×W×3 | Explicit `ValueError` for non-contiguous data. |
| Input ownership | Retained by Python caller | C++ uses the supplied pointer only for the duration of the call. |
| Output ownership | Newly allocated NumPy H×W arrays | Python owns Energy, Flow-X, and Flow-Y outputs. |
| SIMD portability | AVX-512F, AVX2, or scalar fallback | Build remains executable when SIMD support is unavailable. |
| Degenerate geometry | 1×1, 1×N, and N×1 supported | Flow in the absent direction is defined as zero. |

---

## 3. Harness Design & Reproducibility

The release harness contains a quick CTest profile and a full Stage 1 profile. The full profile deliberately exercises **10,000,000 random pixels** for the scalar-versus-SIMD numerical comparison and performs **1,024 sequential 4 MiB aligned allocations**, representing **4 GiB cumulative allocation activity**. The 4K performance test is a characterization result, not a cross-hardware release gate; CPU model, instruction availability, frequency governance, and memory bandwidth vary materially across deployment targets.

A separate `Debug` build is used for Valgrind because the available Valgrind version cannot emulate the release binary's AVX-512F instructions. The bounded smoke profile executes the same code paths with smaller tensors and verifies allocation correctness and leak freedom without claiming performance parity.

```bash
# Release build and native regression suite
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON -DALVS_BUILD_STAGE1_EVALUATION=ON
cmake --build build --parallel
cd build && ctest --output-on-failure && ./stage1_evaluation

# Python extension: 4K zero-copy, numerical, and layout-contract checks
cd ..
python3 stage1_python_evaluation.py \
  --height 2160 --width 3840 --metadata-iterations 1000

# Portable memory-safety route
cmake -S . -B build-valgrind -DCMAKE_BUILD_TYPE=Debug \
  -DALVS_BUILD_PYTHON_MODULE=OFF -DALVS_BUILD_STAGE1_EVALUATION=ON
cmake --build build-valgrind --parallel
valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
  ./build-valgrind/stage1_evaluation --smoke
```

---

## 4. Pass/Fail Transition Tests

| ID | Test | Hard Pass Criterion | Result File |
| :--- | :--- | :--- | :--- |
| **TC-1.1** | Aligned allocation stress | 1,000+ 64-byte-aligned allocation cycles, 4 GiB cumulative activity, no allocation exception; memory-safety run reports no leaks. | `stage1_native_full_results.txt`, `stage1_valgrind_results.txt` |
| **TC-1.2** | Python zero-copy handoff | Native pointer equals NumPy data pointer; input-copy flag is false; 4K metadata handoff median is below 0.15 ms. | `stage1_python_results.json` |
| **TC-1.3** | SIMD numerical equivalence | Maximum absolute error against scalar Rec. 709 reference is less than `1e-6` across 10,000,000 pixels. | `stage1_native_full_results.txt` |
| **TC-1.4** | Legacy/direct route equivalence | Energy, Flow-X, and Flow-Y maximum absolute difference is less than `1e-6`. | `stage1_native_full_results.txt` |
| **TC-1.5** | Boundary safety | 1×1, 1×N, and N×1 tensors complete with finite output. | `stage1_native_full_results.txt` |
| **TC-1.6** | 4K direct-path characterization | Measurement is finite and positive; median and p95 are recorded for the target host. | `stage1_native_full_results.txt` |
| **TC-1.7** | Implicit-copy prevention | Fortran-contiguous input is rejected explicitly instead of being copied. | `stage1_python_results.json` |

---

## 5. Known Boundary & Stage 2 Prerequisite

Stage 1 does **not** claim GPU zero-copy, pinned-host allocation, CUDA unified virtual addressing, or a sub-2.5 ms full-frame vision pipeline. Those require accelerator-specific tooling and must be tested on declared target hardware. The completed direct CPU tensor interface is the appropriate handoff point for Stage 2, where multi-scale atomic layers and semantic feature fusion can be built without redesigning the memory contract.

No Stage 2 implementation should begin until the associated transition gate is approved by the project owner.
