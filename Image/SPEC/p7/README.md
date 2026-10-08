# Phase 7 — Descriptive quality and atomic failure slice

Phase 7 implements one bounded engineering metric over the Phase 5 identity-canonical HWC `uint8` raster: **`endpoint_code_fraction`**, method `uint8-endpoint-code-fraction` version `1`. Its exact contract is [`endpoint_code_fraction_v1.contract.json`](endpoint_code_fraction_v1.contract.json); the implementation is [`quality_indicator.hpp`](quality_indicator.hpp) and [`quality_indicator.cpp`](quality_indicator.cpp).

For `P = width × height`, the metric counts included samples equal to exactly `0` or `255`. Its numerator is that endpoint count; its denominator is `P` for GRAY and `3P` for RGB/RGBA. GRAY includes its one channel, RGB includes R/G/B, and RGBA includes R/G/B while excluding alpha from both counts. The reported value is the binary64 quotient of the retained exact integer counts, in `[0,1]`, with units `fraction`, scope `image`, and `acceptance_effect: descriptive_only`. This is not a probability, confidence, calibration result, semantic quality judgment, clipping diagnosis, or task-acceptance score.

The implementation performs one row-major pass in `O(P*K)` time, where included channels `K` are at most three, uses `O(1)` auxiliary scratch, and never edits input bytes. The caller supplies pixel, channel, work, and output-byte limits. Checked arithmetic runs before indexing; work is exactly the denominator, and the scalar output payload is exactly 24 logical bytes (two `uint64` counts and one IEEE-754 binary64 fraction, excluding metadata/object padding). Cancellation and steady-clock deadlines are checked before work, by row, periodically within long rows, and immediately before publication of the result object.

The selected proposal profile binds uncertainty to `disabled`. With default options, the result contains no uncertainty payload or values. If a caller explicitly requires uncertainty, the function returns `UNCERTAINTY_UNAVAILABLE` and no quality or uncertainty result. There is no estimator, fallback, calibration data, target event, threshold, or approval. Every error uses an exact catalog code and a fixed allowlisted message under 512 UTF-8 bytes, is not retryable, and reports `state_changed=false`; caller bytes, paths, private text, and identifiers are never interpolated into errors.

The return object is assembled only after all checks pass. Any failure (including a deterministic test-only injected failure after partial local counting or immediately before result construction) returns with both optionals empty. The fault injection overload is compiled only with `AGI_IMAGE_P7_TESTING`; it is absent from the ordinary API. P4, P5, and P6 are exercised at their existing typed failure boundaries and in a supported P4→P5→P6→P7 success path. No persistence, publication, logging, telemetry, or shared mutable state API exists in these stages; the tests also verify input bytes remain unchanged.

Run the strict normal and ASan/UBSan test builds with:

```sh
python3 Image/SPEC/harness/p7/run_p7.py
```

The runner writes [`../harness/results/latest.p7.run_evidence.json`](../harness/results/latest.p7.run_evidence.json). Test IDs bind to existing catalog definitions through [`../harness/p7/case_bindings.json`](../harness/p7/case_bindings.json), leaving Phase 6's shared case catalog and historical evidence unchanged.

The general profile remains `status: proposal`, `features.enabled` remains empty, and production approval remains false. The metric is engineering-only and is not wired into runtime observation publication. This slice does not add an uncertainty estimator, dataset, target event, thresholds, fallback, calibration, streams/runtime, Phase 8, reverse image rendering, or any Cortex change.
