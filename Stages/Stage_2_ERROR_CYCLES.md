# Stage 2 Error Cycles

**Project**: AGI Vision Substrate (AGI-VS)  
**Branch**: `feature/stage-1-core-substrate`  
**Scope**: Stage 2 neural-symbolic atomization

| Cycle | Component | Observed Failure | Root Cause | Corrective Action | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `stage2_evaluation.cpp` / CTest | `TC-2.1` failed because `city.jpg` could not be found when the executable ran from the CMake build directory. | The harness resolved sample image paths relative to the runtime working directory instead of the repository source directory. | Passed the absolute source directory through a CMake compile definition and resolved repository test assets from that stable root. The full Stage 2 harness now passes. | Resolved |

No Stage 2 algorithmic logic has failed; this is an evaluation-path portability defect.
| 2 | `bindings.cpp` / Stage 2 Python evaluation | `tc_2_python_gate` failed because returned gate weights summed to `0.6538377404212952` instead of one, despite the native gate test passing. | One-dimensional `py::array_t` construction selected a broadcasted zero-stride layout, causing every exposed element to alias the first native value. | Construct one-dimensional feature and weight arrays from an explicit shape vector. The returned arrays are now C-contiguous with valid strides and gate weights sum to one. | Resolved |
| 3 | `stage2_python_evaluation.py` | All numerical assertions reached the reporting step, but JSON serialization failed with `TypeError: Object of type bool is not JSON serializable`. | Some pass flags were NumPy boolean scalars rather than native Python `bool` values. | Normalized every Boolean pass expression to a Python `bool` before generating the machine-readable evidence file. The Stage 2 Python harness now completes and records an overall pass. | Resolved |
