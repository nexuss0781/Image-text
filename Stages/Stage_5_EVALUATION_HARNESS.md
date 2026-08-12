# Stage 5: Production Readiness, Release Validation & Evaluation Harness

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Verified CPU-path release candidate; GPU and container-runtime acceptance deferred  
**Owner Decision Required**: Approval is required before the separate data-curation and training program begins.

---

## 1. Ultimate Stage 5 Objective

Stage 5 establishes a reproducible CPU production path for the current vision substrate. It combines the previously verified Stage 1–4 contracts into an end-to-end production harness, registers all five native stages with CTest, validates a bounded soak profile, records latency statistics, produces a source-and-evidence integrity manifest, and provides a multi-stage CPU container recipe.

> **Stage 5 exit condition:** the release path must be reproducibly buildable, all Stage 1–5 regressions must pass, the integrated CPU pipeline must preserve Stage 2/3 numerical equivalence, the short operational soak must show bounded resident-memory behavior, and release evidence must be checksum-manifested.

| Delivered Component | Implementation Location | Contract |
| :--- | :--- | :--- |
| Production validation harness | `stage5_evaluation.cpp` | Validates Stage 3 dispatch, Stage 2 atomic layers, and Stage 4 visual-token projection together. |
| Full CTest registration | `CMakeLists.txt` | Runs Stage 1–5 quick regressions from a single release build. |
| Python production harness | `stage5_python_evaluation.py` | Independently validates the accelerated, multi-scale, and token-projection extension routes. |
| Reproducible release workflow | `scripts/production_validate.sh` | Builds a fresh release tree, executes CTest, runs native/Python production checks, and creates a manifest. |
| Artifact manifest | `scripts/release_manifest.py` | Hashes source and evidence artifacts and records commit, platform, and dirty-state metadata. |
| CPU container recipe | `Dockerfile`, `.dockerignore` | Defines an auditable multi-stage CPU image; no GPU capability is implied. |

---

## 2. Production Contract & Scope Boundary

The Stage 5 production path is **CPU verified**. It uses the actual Stage 3 OpenMP + AVX path when available, the Stage 2 Haar representation, and the Stage 4 deterministic token interface. Its test image is an 80×64 float32 tensor, producing 80 retained tokens of dimension 4096 under the default 4×4 patch and 25% retention configuration.

The original GPU/TensorRT/container-operational targets are not represented as passed. Docker is not installed on the validation host, and CUDA/TensorRT hardware or tooling is absent. The Dockerfile is a static release artifact only; its build, image footprint, startup-time, and runtime execution must be revalidated in a container-capable target environment.

| Contract | Required Behaviour | Validated Result |
| :--- | :--- | :--- |
| Full CPU pipeline | Stage 3 layers match Stage 2 layers; Stage 4 produces `[80, 4096]` output | Maximum layer deviation `0.0`; 80 tokens × 4096 dimensions. |
| Input ownership | Source RGB tensor remains unchanged through the integrated route | Confirmed by native and Python harnesses. |
| Release regression | All registered Stage 1–5 tests pass | 5/5 CTest tests passed. |
| Short operational soak | Bounded post-warm-up resident-memory growth during 500 frames | 0-byte observed RSS growth; bounded-test threshold 16 MiB. |
| Latency characterization | Record finite end-to-end CPU latency distribution | 12.998576 ms median; 13.285131 ms p95. |
| Release integrity | Manifest includes all expected source and evidence artifacts | Expected-artifact set complete. |

---

## 3. Evaluation Harness

The native `stage5_evaluation` harness uses three tests. The integration test exercises accelerated atomization, multi-scale atomization, semantic gating, and visual-token projection over one source tensor. The soak test warms the pipeline and then processes 500 frames in the full profile. The latency test reports median and p95 for the same integrated CPU path. A `--smoke` mode limits memory instrumentation to two frames so Valgrind remains practical while the uninstrumented full profile retains the longer stability test.

```bash
# Fresh reproducible CPU release workflow
./scripts/production_validate.sh

# Individual native suite
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DALVS_BUILD_PYTHON_MODULE=ON \
  -DALVS_BUILD_STAGE1_EVALUATION=ON \
  -DALVS_BUILD_STAGE2_EVALUATION=ON \
  -DALVS_BUILD_STAGE3_EVALUATION=ON \
  -DALVS_BUILD_STAGE4_EVALUATION=ON \
  -DALVS_BUILD_STAGE5_EVALUATION=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/stage5_evaluation
python3 stage5_python_evaluation.py

# Bounded portable memory instrumentation
OMP_NUM_THREADS=1 valgrind --leak-check=full --show-leak-kinds=all \
  --errors-for-leak-kinds=definite,indirect --error-exitcode=99 \
  ./build-valgrind/stage5_evaluation --smoke
```

---

## 4. Pass/Fail Transition Tests

| ID | Test | Hard Pass Criterion | Result Artifact |
| :--- | :--- | :--- | :--- |
| **TC-5.1** | End-to-end CPU integration | Stage 2/3 layer error below `1e-6`, unchanged RGB input, and 80 × 4096 token output. | `stage5_native_full_results.txt` |
| **TC-5.2** | Bounded stability profile | 500-frame checksum complete and post-warm-up RSS growth no greater than 16 MiB. | `stage5_native_full_results.txt` |
| **TC-5.3** | Integrated latency characterization | Finite positive median and p95 values are reported. | `stage5_native_full_results.txt` |
| **TC-5.P1** | Python integration | Accelerated and multi-scale layers agree below `1e-6`; expected token shape is produced. | `stage5_python_results.json` |
| **TC-5.P2** | Python ownership and layout contracts | RGB input unchanged and not copied; non-contiguous input rejected. | `stage5_python_results.json` |
| **TC-5.P3** | Python latency characterization | Finite positive median and p95 projection-route values are reported. | `stage5_python_results.json` |
| **TC-5.M1** | Memory-safety smoke test | Zero definite, indirect, and possible loss; zero Valgrind errors. | `stage5_valgrind_results.txt` |
| **TC-5.R1** | Reproducible release workflow | Fresh release build, all CTest tests, native/Python checks, and artifact manifest pass. | `stage5_production_validation_console.txt`, `stage5_release_manifest.json` |

---

## 5. Deferred Production Acceptance

A passing CPU release path is not a production claim for every target environment. The following must be independently revalidated on target infrastructure.

| Deferred Requirement | Current Constraint | Required Future Evidence |
| :--- | :--- | :--- |
| GPU/TensorRT deployment | No CUDA/TensorRT tooling or NVIDIA device is available | Device-labelled GPU/CPU equivalence, VRAM, latency, and engine-compatibility report. |
| Container size/startup | Docker daemon/CLI unavailable on validation host | Container build log, image digest/size, cold-start timing, and in-container full test output. |
| 24-hour, 100,000-frame stability | Current harness validates 500 frames only | Time-series RSS/allocator telemetry, failure report, and target workload record. |
| Semantic VLM quality | Stage 4 is an untrained deterministic projection interface | Model-specific adapter, benchmark evaluation, and held-out safety/quality suite. |

---

## 6. References

[1]: https://commoncrawl.org/ "Common Crawl — Open Web Data"
[2]: https://laion.ai/faq/ "LAION FAQ — Dataset Index, Reconstruction, and Takedown Context"
[3]: https://proceedings.neurips.cc/paper_files/paper/2022/hash/a1859debfb3b59d094f3504d5ebb6c25-Abstract-Datasets_and_Benchmarks.html "LAION-5B — NeurIPS 2022"
[4]: https://www.nature.com/articles/s42256-024-00878-8 "A Large-Scale Audit of Dataset Licensing and Attribution in AI"
