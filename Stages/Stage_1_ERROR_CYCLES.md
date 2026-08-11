# Stage 1 Error Cycles

**Project**: AGI Vision Substrate (AGI-VS)  
**Branch**: `feature/stage-1-core-substrate`  
**Scope**: Stage 1 core substrate modernization

| Cycle | Component | Observed Failure | Root Cause | Corrective Action | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `bindings.cpp` | pybind11 compilation failed with `The number of argument annotations does not match the number of function arguments`. | `zero_copy_metadata` was registered as an `Atomizer` instance method but its lambda omitted the bound `Atomizer` instance parameter. | Added an unused `const alvs::Atomizer&` first argument to the method lambda, preserving instance-method registration and the public API. The release build now succeeds. | Resolved |

No user-defined logic has been removed or semantically altered. The correction is limited to the binding signature required by pybind11.

| 2 | `bindings.cpp` | The Stage 1 Python evaluation accepted a Fortran-contiguous input instead of rejecting it, so the harness reported `TC-1.7` as failed. | The pybind11 `array_t<float, c_style>` conversion path could materialize an implicit C-contiguous temporary before entering the native method. | Replaced conversion-prone typed-array arguments with generic `py::array` arguments and added explicit `float32` and C-contiguity validation before using the raw data pointer. The release build succeeds after the correction. | Resolved |
| 3 | `stage1_python_evaluation.py` | The re-run stopped when the newly hardened binding correctly raised `ValueError` for a Fortran-contiguous array. | The harness treated only `TypeError` as the expected explicit rejection signal. | Expanded the expected-rejection handler to accept both `TypeError` and `ValueError`; no production logic changed. | Resolved |
| 4 | Valgrind validation | Valgrind terminated the optimized `-march=native` binary with `Illegal instruction`. | The release binary selected AVX-512F instructions that the installed Valgrind build does not emulate. This is a tooling limitation, not an application failure. | Built a separate portable `Debug` evaluation target without `-march=native` and executed the bounded smoke profile under Valgrind. The run completed with 0 errors, 0 bytes in use at exit, and no leaks. Release performance validation remains unchanged. | Resolved |
