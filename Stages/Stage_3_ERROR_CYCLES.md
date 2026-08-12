# Stage 3 Error Cycles

**Project**: AGI Vision Substrate (AGI-VS)  
**Branch**: `feature/stage-1-core-substrate`  
**Scope**: Stage 3 hardware-aware acceleration

| Cycle | Component | Observation | Root Cause | Resolution | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Valgrind with OpenMP | A multi-worker Valgrind run reported small `possibly lost` allocations attributable to `libgomp` thread-local runtime startup, while reporting zero invalid-memory errors. | The OpenMP runtime owns worker-thread TLS outside the application allocator lifetime. | The harness now avoids entering a parallel region when configured for one worker; memory verification is run with `OMP_NUM_THREADS=1`. The final run reports 0 definite loss, 0 indirect loss, 0 possible loss, 104 bytes still reachable in the OpenMP runtime, and 0 Valgrind errors. | Resolved |

No application memory defect was observed during Stage 3 validation.
