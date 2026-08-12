# Stage 5 Error Cycles

**Project**: AGI Vision Substrate (AGI-VS)  
**Branch**: `feature/stage-1-core-substrate`  
**Scope**: Stage 5 production validation

| Cycle | Component | Observed Failure | Root Cause | Corrective Action | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `stage5_evaluation.cpp` | Stage 5 CTest target terminated with a segmentation fault; the compiler also emitted narrowing warnings for pipeline layer buffers. | Brace initialization of `std::vector<float>` selected the initializer-list constructor, creating one-element vectors containing `width × height` rather than vectors sized to the pixel count. | Replaced brace initialization with explicit size-constructor expressions, rebuilt, and reran all Stage 1–5 tests successfully. | Resolved |

No core algorithm is implicated; this is a harness allocation defect.

| 2 | `stage5_python_evaluation.py` | Python evaluation did not start because the layer-error list had unbalanced parentheses. | Each `float(np.max(...))` expression had one missing closing parenthesis. | Restored the three closing parentheses and reran the Python production validation successfully. | Resolved |

| 3 | Stage 5 Valgrind harness | The ordinary `--quick` production profile exceeded practical instrumentation time because each frame produces 80 × 4096 embeddings. | Valgrind multiplies the cost of allocation and floating-point execution across the 30-frame quick soak loop. | Added a two-frame `--smoke` profile for instrumentation while retaining the longer release stability profile; the smoke run reports 0 definite, indirect, or possible loss and 0 Valgrind errors. | Resolved |
