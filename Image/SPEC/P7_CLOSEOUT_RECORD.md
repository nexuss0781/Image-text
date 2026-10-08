# Phase 7 closeout record

**Date:** 2026-10-08  
**Decision:** D-018  
**Status:** bounded Phase 7 engineering slice complete; profile and production approval remain open. Await explicit user approval before Phase 8.

## Authorized scope and delivered metric

D-018 records the user's authorization to start and finish only the Phase 7 capabilities supportable by the current P5 contract and proposal profile. Review is by the user/project owner and assistant; no outside reviewer is required for this engineering closeout.

The implementation consumes a P5 identity-canonical, tightly packed HWC `uint8` GRAY/RGB/RGBA view and returns one descriptive indicator: **`endpoint_code_fraction`**, method `uint8-endpoint-code-fraction`, version `1`, scope `image`, units `fraction`, and `acceptance_effect: descriptive_only`.

For `P = width × height`, the exact integer numerator `N` counts included channel samples whose code is exactly `0` or exactly `255`. The denominator is `D=P` for GRAY and `D=3P` for RGB or RGBA. GRAY includes its intensity channel; RGB includes R/G/B; RGBA includes R/G/B and excludes alpha from both counts. The returned binary64 value is `binary64(N) / binary64(D)`, with `0≤N≤D`, `D>0`, finite range `[0,1]`. The exact counts are retained. Work is exactly `D` sample visits, `O(P×K)` with `K≤3`; auxiliary scratch is `O(1)`. The logical scalar payload is bounded to 24 bytes (two `uint64` counts plus one IEEE-754 binary64 value; static metadata and C++ object padding excluded). All limits are caller-supplied and dimensions/counts are checked before indexing.

This fraction is not probability, confidence, calibration, semantic quality, clipping diagnosis, suitability, or a task-acceptance score.

## Uncertainty and failures

The machine profile remains `status: proposal`, `features.enabled` remains empty, and uncertainty mode remains `disabled`. Successful results omit uncertainty entirely. If the caller explicitly requires uncertainty, the function returns `UNCERTAINTY_UNAVAILABLE` with both quality and uncertainty absent. No uncertainty estimator, fallback, target event, dataset, calibration, threshold, or approval was selected.

The bounded API maps failures to fixed, catalogued codes and exact allowlisted messages of at most 512 UTF-8 bytes. All mapped failures are nonretryable and report `state_changed=false`; messages do not interpolate bytes, private text, paths, or identifiers. The implementation assembles its result only after final control, bounds, and value checks. Test-only fault injection fails after the first locally counted sample or immediately before result construction; both paths return no quality or uncertainty and preserve input bytes. P4 admission, P5 canonicalization, and P6 operator failures are also checked for empty stage results, unchanged input, nonretryability, and `state_changed=false`. These stages expose no persistence/publication API; this slice adds no persistence, logging, or telemetry API.

Cancellation and expired deadlines are checked before validation and scanning, at each row, periodically during long rows, and before result construction. The tests cover zero/overwide limits, work/pixel/output bounds, arithmetic overflow, malformed raster dimensions/layout/policy, non-finite transform metadata, uncertainty omission/unavailability, and secret-marker non-disclosure. Raster samples are `uint8`, so non-finite sample values are not representable; the applicable floating metadata path is explicitly tested.

## Verification

The separate P7 runner is [`harness/p7/run_p7.py`](harness/p7/run_p7.py); its exact output is [`harness/results/latest.p7.run_evidence.json`](harness/results/latest.p7.run_evidence.json). It reports **18/18 passing tests in the strict normal build and 18/18 in the AddressSanitizer/UndefinedBehaviorSanitizer build** using C++20 and `-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Werror`. The test binary's recorded dynamic links are limited to the host C++ runtime and system libraries; the implementation uses no external dependency or ML framework.

| Tests | Cases | Coverage |
|---|---|---|
| P7-TEST-001–006 | QUAL-001 | Literal GRAY/RGB/RGBA counts; alpha exclusion; controlled one-code change; exact bounds; method metadata |
| P7-TEST-007–010 | ERR-003, UNC-002 | Caller limits/output bytes/overflow; malformed layouts and metadata; non-finite transform metadata; cancellation and deadline |
| P7-TEST-011 | UNC-005 | Default uncertainty omission and explicit `UNCERTAINTY_UNAVAILABLE` |
| P7-TEST-012 | ERR-004 | Fixed safe message and secret-marker non-disclosure |
| P7-TEST-013–017 | ERR-002 | P7 post-sample/pre-publication injected faults and atomic P4/P5/P6 boundary failures |
| P7-TEST-018 | QUAL-001 | Read-only supported P4→P5→P6→P7 success path |

P7 IDs bind to existing catalog definitions in [`harness/p7/case_bindings.json`](harness/p7/case_bindings.json), without editing the shared P6 case catalog or its historical result. After the closeout documents were frozen, the full package checker [`harness/check_spec.py`](harness/check_spec.py) passed **19/19 assertions**, including P4/P5/P6 historical source/evidence validation, exact P7 contract/oracle and bindings, P7 worktree fingerprint, scope, and link checks. Its generated run artifacts are in `/tmp/p7-package-check-final/` for this task.

## Preserved scope and next gate

The pre-existing local P6 closeout/source/catalog changes were known and retained. No P4, P5, or P6 implementation source, P4/P5/P6 test source, or P4/P5/P6 run artifact was edited as part of P7. The P7 package check validates the earlier phase input hashes and preserves P6's recorded worktree fingerprint as historical evidence; P7's case bindings and run artifact are separate.

The descriptive metric is not enabled in the profile or wired into runtime observation publication. No P8 runtime/streams, uncertainty calibration, reverse image rendering, or Cortex edits are included. **Stop here and await explicit user approval before Phase 8.**
