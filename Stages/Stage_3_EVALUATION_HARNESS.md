# Stage 3: Objective, Hardware Strategy & Evaluation Harness

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: CPU-accelerated dispatch implemented and verified; GPU acceptance deferred pending compatible hardware  
**Owner Decision Required**: Approval is required before Stage 4 begins.

---

## 1. Ultimate Stage 3 Objective

Stage 3 is responsible for improving throughput without changing the mathematically verified outputs of Stage 1 and Stage 2. Its design principle is **reference-first acceleration**: every optimized execution route must reproduce Rec. 709 Energy, Flow-X, and Flow-Y results of the reference core within a maximum absolute error of `1e-6`; GPU execution must be reported explicitly rather than emulated or inferred.

The validation host exposes six logical CPU workers, AVX-512F, and OpenMP support, but no NVIDIA device nodes, CUDA compiler, CUDA runtime, or OpenCL device. Stage 3 therefore implements and verifies a high-performance **OpenMP + AVX CPU dispatch path** with an exact reference fallback. CUDA, TensorRT, FP8, and GPU-memory acceptance are intentionally left unclaimed until a compatible accelerator host is available.

> **Stage 3 exit condition for this host:** direct tensor ownership remains intact; parallel CPU dispatch is deterministic and reference-equivalent; acceleration metadata is truthful; and the system remains safe when the parallel runtime is unavailable or configured to a single worker.

| Delivered Component | Implementation Location | Contract |
| :--- | :--- | :--- |
| Execution metadata | `ExecutionReport` | Identifies backend, worker count, SIMD state, parallel state, and GPU availability. |
| Parallel dispatch | `Atomizer::atomizeAcceleratedInterleaved` | Uses OpenMP rows plus the established SIMD Energy kernel when multiple workers are configured. |
| Parallel Flow kernel | `Atomizer::computeFlowInterleavedParallel` | Performs independent row writes while retaining the reference finite-difference boundary rule. |
| Single-worker fallback | `Atomizer::atomizeAcceleratedInterleaved` | Uses the scalar execution route when parallel execution is unavailable or configured to one worker. |
| Python accelerated API | `Atomizer.atomize_accelerated_numpy` | Returns output layers and truthful execution metadata without copying the RGB input. |
| Native and Python benchmarks | `stage3_evaluation.cpp`, `stage3_python_evaluation.py` | Validate equality, determinism, dispatch properties, input integrity, throughput characterization, and layout protection. |

---

## 2. Hardware-Aware Dispatch Contract

The dispatch API does not select an unavailable accelerator. When OpenMP has more than one worker, the backend is reported as `cpu-openmp-avx` or `cpu-openmp-scalar`; otherwise it reports `cpu-avx-reference` or `cpu-reference`. On the present validation host, `gpu_available` is `false`. This explicit behavior prevents downstream systems from treating CPU parallelism as GPU execution.

| Capability | Validation Host Result | Implementation Response |
| :--- | :--- | :--- |
| AVX-512F | Available | The existing Energy kernel retains AVX-512F dispatch. |
| OpenMP | Available; 6 workers | Energy rows and Flow rows execute in independent parallel regions. |
| CUDA/NVIDIA | Not available | No CUDA route is selected or benchmarked. |
| OpenCL | Not available | No OpenCL route is selected or benchmarked. |
| Single worker | Supported | Parallel regions are skipped to avoid runtime overhead and preserve reference semantics. |

---

## 3. Evaluation Harness

The native harness runs the reference and dispatched paths over the same deterministic 1080p RGB tensor, compares each output layer, repeats the dispatched execution for determinism, records dispatch metadata, and measures median latency. The Python harness checks the extension path, direct-input metadata, exact output equivalence, backend metadata, and rejection of non-C-contiguous input.

```bash
# Release build and complete Stage 1–3 regression suite
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON \
  -DALVS_BUILD_STAGE1_EVALUATION=ON \
  -DALVS_BUILD_STAGE2_EVALUATION=ON \
  -DALVS_BUILD_STAGE3_EVALUATION=ON
cmake --build build --parallel
cd build && ctest --output-on-failure && ./stage3_evaluation

# Python extension validation at 1080p
cd ..
python3 stage3_python_evaluation.py --height 1080 --width 1920 --iterations 10

# Portable one-worker memory validation
cmake -S . -B build-valgrind -DCMAKE_BUILD_TYPE=Debug \
  -DALVS_BUILD_PYTHON_MODULE=OFF \
  -DALVS_BUILD_STAGE1_EVALUATION=OFF \
  -DALVS_BUILD_STAGE2_EVALUATION=OFF \
  -DALVS_BUILD_STAGE3_EVALUATION=ON
cmake --build build-valgrind --parallel
OMP_NUM_THREADS=1 valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
  ./build-valgrind/stage3_evaluation --quick
```

---

## 4. Pass/Fail Transition Tests

| ID | Test | Hard Pass Criterion | Result Artifact |
| :--- | :--- | :--- | :--- |
| **TC-3.1** | Reference equivalence | Maximum Energy/Flow deviation below `1e-6`. | `stage3_native_full_results.txt` |
| **TC-3.2** | Dispatch determinism | Repeat-run output deviation is exactly zero and backend label remains stable. | `stage3_native_full_results.txt` |
| **TC-3.3** | Truthful dispatch report | At least one worker; parallel route requires more than one; CUDA state is reported accurately. | `stage3_native_full_results.txt` |
| **TC-3.4** | 1080p throughput characterization | Finite reference and dispatched latency, speedup, FPS, and backend values are reported. | `stage3_native_full_results.txt` |
| **TC-3.P1** | Python extension equivalence | Maximum output deviation below `1e-6`. | `stage3_python_results.json` |
| **TC-3.P2** | Python direct-input ownership | Native pointer equals NumPy pointer; caller input remains unchanged. | `stage3_python_results.json` |
| **TC-3.P3** | Python dispatch metadata | Backend is an allowed route; worker count is positive; median call latency is finite. | `stage3_python_results.json` |
| **TC-3.P4** | Input-layout protection | Fortran-contiguous input is rejected rather than copied. | `stage3_python_results.json` |
| **TC-3.M1** | Memory safety | Zero definite, indirect, or possible loss; zero Valgrind memory errors. | `stage3_valgrind_results.txt` |

---

## 5. GPU Acceptance Boundary

The original GPU-specific targets—custom CUDA fused kernels, TensorRT engines, FP8 calibration, GPU VRAM limits, and 500-FPS 1080p CUDA throughput—cannot be validated on this host because no GPU or CUDA toolchain exists. They are **not** represented as passed requirements.

Stage 4 may proceed only as a CPU-compatible multimodal integration stage if approved. Before a production GPU deployment, a GPU acceptance rerun must validate GPU/CPU numerical equivalence, VRAM peak consumption, TensorRT behavior, and accelerator latency on declared target hardware.
