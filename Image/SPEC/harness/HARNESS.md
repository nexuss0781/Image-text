# Image VISION Conformance Harness

**Status:** P3 coverage/oracle review accepted under D-014; P4, P5, D-017 P6, D-018 P7, and D-019 bounded P8 have separate C++ runners and evidence artifacts. The bounded P8 single-flight engineering slice is complete; the named-workload/production gate remains open and Phase 9 is not authorized. The Python checker validates specifications and recorded evidence only; it does not execute C++ tests.
**Scope:** machine contracts, numeric oracle definitions, admission validation, failure atomicity, bounded work/resources, dependencies, privacy, and ENCODER handoff.
**Authority:** [`../PROJECT.md`](../PROJECT.md), [`../PHASES.md`](../PHASES.md), [`../TRACEABILITY.md`](../TRACEABILITY.md)

## 1. Purpose and evidence discipline

The harness is the test home for Image VISION. Its machine-readable inventory is [`case_catalog.json`](case_catalog.json), analytic vectors are in [`fixtures/analytic_patterns.json`](fixtures/analytic_patterns.json), [`fixtures/p6_forward_difference_vectors.json`](fixtures/p6_forward_difference_vectors.json), and [`fixtures/p7_endpoint_code_fraction_vectors.json`](fixtures/p7_endpoint_code_fraction_vectors.json), and run artifacts capture package and P4/P5/P6/P7/P8 evidence. P7 and P8 bind to existing catalog definitions through separate phase binding files to preserve the historical P6 catalog hash; the P8 bindings only claim its implemented lifecycle/admission subcases. A case definition is not a test execution; a Python checker pass is not implementation conformance; no artifact establishes a production capability or approved profile.

From the repository root, run the standard-library package/evidence checker with Python 3.11+:

```sh
python3 -I Image/SPEC/harness/check_spec.py
```

By default, the checker writes current package evidence to `results/after-p4/`, preserving the historical pre-acceptance P3 snapshot in `results/latest.*`. Use `--output-dir <path>` to choose another destination. The checker strictly parses JSON, validates the declared schema subset and local references, checks test-only examples and cross-field contracts, independently checks manually recorded analytic oracles, verifies requirement/invariant traceability, validates Markdown links and policy flags, audits Python imports, and validates the recorded P4/P5/P6/P7/P8 evidence and bindings. It does not rebuild or execute C++.

Run the bounded Phase 4 C++ admission and P5/P6 decode tests, including sanitizer checks when supported, with:

```sh
python3 Image/SPEC/harness/p4/run_p4.py
```

The exact admission/decoder subset, non-owning lifetime contract, unsupported capabilities, and evidence are documented in [`p4/README.md`](../p4/README.md). The runner compiles into a temporary directory and writes actual outcomes to [`results/latest.p4.run_evidence.json`](results/latest.p4.run_evidence.json). The Python checker validates this record but does not refresh its test results.

Run the bounded Phase 5 identity canonical-raster suite with:

```sh
python3 Image/SPEC/harness/p5/run_p5.py
```

The P5 API, zero-copy lifetime rules, exact identity geometry, disabled operations, and evidence are documented in [`p5/README.md`](../p5/README.md). The dedicated runner writes [`results/latest.p5.run_evidence.json`](results/latest.p5.run_evidence.json). It uses admitted P4 input views and tests only identity behavior; it does not enable non-identity transforms or modify the proposal profile.

Run the bounded Phase 6 forward-difference suite with:

```sh
python3 Image/SPEC/harness/p6/run_p6.py
```

The runner builds normal and ASan/UBSan variants using strict C++20 warnings, audits host dynamic links, checks exact catalog bindings and writes [`results/latest.p6.run_evidence.json`](results/latest.p6.run_evidence.json). Its versioned mathematical/resource contract is [`../p6/forward_difference_xy_v1.contract.json`](../p6/forward_difference_xy_v1.contract.json), implementation is [`../p6/README.md`](../p6/README.md), and P6 evidence is checked by [`p6/p6_evidence.schema.json`](p6/p6_evidence.schema.json). The separate dependency-free package checker validates the recorded artifact but does not rerun the C++ suites.

Run the bounded Phase 7 descriptive quality and atomic-failure suite with:

```sh
python3 Image/SPEC/harness/p7/run_p7.py
```

This runner builds strict C++20 normal and ASan/UBSan variants, checks exact bindings to existing catalog IDs using [`p7/case_bindings.json`](p7/case_bindings.json), audits host dynamic links, and writes [`results/latest.p7.run_evidence.json`](results/latest.p7.run_evidence.json). Its exact metric and failure contract is [`../p7/endpoint_code_fraction_v1.contract.json`](../p7/endpoint_code_fraction_v1.contract.json); the C++ implementation and scope are in [`../p7/README.md`](../p7/README.md). P7's 18 outcomes are run evidence, not catalog lifecycle edits.

Run the bounded Phase 8 single-flight request-runtime suite with:

```sh
python3 Image/SPEC/harness/p8/run_p8.py
```

The runner builds strict C++20 normal and ASan/UBSan variants and audits dynamic links. The 12 tests cover one-active/zero-queue admission, immediate backpressure, deadline and cancellation forwarding to P4, drain/cancel-and-drain close, terminal lifecycle, and the private aggregate snapshot. [`p8/case_bindings.json`](p8/case_bindings.json) maps only to existing catalog IDs so P6's catalog hash remains unchanged. Frame transport, named-workload measurement, a telemetry sink, idempotent publication, and observation emission are not implemented. Evidence is written to [`results/latest.p8.run_evidence.json`](results/latest.p8.run_evidence.json) and checked by [`p8/p8_evidence.schema.json`](p8/p8_evidence.schema.json).

The current catalog has **75 Image component case definitions**: 51 `not_run`, 24 `blocked`. Catalog lifecycle fields stay as definitions; executed results are recorded only in run artifacts. The P4 artifact binds 33 tests, P5 binds 10, P6 binds 13, P7 binds 18, and P8 binds 12 tests to their phase-specific cases. P7/P8 use separate binding files to leave the Phase 6 catalog hash unchanged. Six cataloged package checks plus P8 contract/evidence validation contribute to the current checker's 21 assertions; they validate contracts, traceability, evidence, and scope, but do not execute C++ component tests. `not_applicable` is allowed only with a profile-specific rationale from an accountable owner.

## 2. Normative coverage

[`../TRACEABILITY.md`](../TRACEABILITY.md) maps each high-level `IV-*` requirement and every numbered clause in [`../contracts/RUNTIME_INVARIANTS.md`](../contracts/RUNTIME_INVARIANTS.md) to concrete case definitions. The same map is machine-readable in the catalog and checked for exact agreement. IDs `RI-SS.NN` identify clause `NN` in runtime-invariants section `SS`; the required-probe statement in section 9 is `RI-09.01`.

The case definitions cover schema contracts; analytic numeric patterns and degenerate dimensions; transforms; decoded-raster admission and disabled decoders; failure atomicity; resources and complexity; dependencies/native paths; privacy and telemetry; immutable references and provenance; ENCODER/Cortex boundaries; and claim review. The catalog describes cases and lifecycle metadata, not test outcomes.

## 3. Numeric oracles and tolerances

Every current analytic fixture has an assistant-authored manual derivation independent of an Image implementation, exact integer `dx` and `dy` arrays, and explicit `absolute_tolerance: 0` and `relative_tolerance: 0`. The P6 vectors additionally include literal RGB/RGBA channel-order cases and a fixed xorshift32-seeded byte vector. The P7 vectors bind exact endpoint numerator/denominator/value literals for GRAY, RGB and alpha-excluding RGBA, plus a one-code controlled change. The checker independently recomputes these small formulas only as a consistency check; it does not generate or replace the recorded expected values.

The P6 operator uses HWC row-major coordinates and replicated edge samples. A one-pixel raster therefore yields zero in both directions; a one-row raster has zero `dy`; a one-column raster has zero `dx`. P7's descriptive fraction is a separate exact endpoint-code count over GRAY or RGB color channels (RGBA alpha excluded), with no threshold. Any future non-integer oracle must record its comparison rule, numeric units, predeclared tolerances, and tolerance owner before candidate results are inspected.

## 4. Reproducibility and result metadata

The Python package-check evidence binds to the Git commit, worktree fingerprint, source/input hashes, profile/schema IDs, Python runtime and command, timestamps, per-check outcomes, checker-process RSS, and Python dependency inventory. P4/P5/P6/P7/P8 C++ artifacts bind implementation/test/profile or contract hashes, compiler, strict flags, build/run commands, outcomes, normal and sanitizer results, and host dynamic links. P4/P5 historical runs bind unchanged inputs. The P6 result and its original worktree fingerprint remain a preserved historical snapshot. P7 likewise preserves its frozen historical fingerprint and exact source/catalog hashes. P8 binds the current worktree excluding only its own generated result artifact. Neither workflow uses network access or nondeterministic test inputs. The temporary host builds are not production binary audits.

The original P3 snapshot records the candidate profile as reference-only and captured the 13-assertion baseline before the user accepted the coverage/oracle review. That historical artifact remains unchanged. D-014 records P3 acceptance/P4 start, D-015 bounded P4 admission/decode, D-016 identity-only P5, D-017 the forward-difference P6 baseline, D-018 the bounded descriptive-quality/atomic-failure P7 slice, and D-019 the bounded P8 runtime slice. P4 records 33/33, P5 10/10, P6 13/13, P7 18/18, and P8 12/12 outcomes in strict normal and ASan/UBSan runs. Package-checker timing and RSS are not Image component resource measurements.

## 5. Dependency policy and audit boundary

The Python harness import closure uses standard-library modules only; no ML framework or external Python harness dependency is present. The P4, P5, P6, P7 and P8 C++ sources use standard-library headers; their run artifacts record host test-build dynamic links. The repository's existing optional TensorFlow extra is recorded as context only and is not imported or installed for these checks.

The host-build include/link audits do **not** certify a production target, transitive packaging, loaded plugins, or broader dependencies. P4 uses no external decoder library; P5 identity canonicalization uses no external dependency. Production dependency/security review remains separate. The Python checker audit is not a substitute for production binary review.

## 6. Complexity, resources, and failure cases

For every enabled operation, document a multivariable bound using `P=W·H`, `C`, `A`, `L`, `R`, `F`, `Q`, and concurrency `B` as applicable. State which terms are profile-bounded and prove output counts are bounded. Reject every input-scaled pairwise term, including `P²`, `R²`, `Q²`, and `P·R` when both scale with input. Work counters corroborate a proof; timing does not replace it.

P4 admission checks descriptor arithmetic and bounded metadata in constant time with constant auxiliary storage; it does not inspect samples or allocate. The P4 decoder performs one bounded header parse and one output copy in `O(B + P*C)` time and `O(P*C)` output space. P5 validates checked `P=W×H` and `S=P×C`, then returns an aliasing identity view without scanning pixels: `O(1)` time and auxiliary space in image size, with no image-sized output allocation. This is not a total-pipeline or production peak-memory certification.

P4 tests cover descriptor and decoder errors, empty failure results, caller-owned views, exact P5/P6 sample fidelity, unsupported variants, malformed/truncated/extra/concatenated input, resource bounds, cancellation, and deadlines. P5 tests cover exact identity bytes, channel/alpha retention, explicit pixel-center identity maps, degenerate/odd shapes, and fail-closed unsupported policies/resource overflow. P6 tests cover exact Dx/Dy values, one-row/one-column/1×1, RGB/RGBA order, seeded replay, five independent caller limits, arithmetic overflow, unsupported layouts, cancellation/deadline, and empty atomic failures. P7 tests cover literal numerator/denominator/value for GRAY/RGB/RGBA (excluding alpha), exact controlled changes, output/work limits, malformed and non-finite metadata, cancellation/deadline, disabled/missing uncertainty, fixed safe errors, secret-marker non-disclosure, injected failures after local partial work and before result construction, P4/P5/P6 typed failure boundaries, and an exact read-only P4→P7 supported path. P8 tests cover one accepted request under a concurrent burst, explicit zero-queue backpressure, same-control cancellation/deadline propagation into P4, close/drain/cancel, and fixed aggregate telemetry snapshots. The P8 layer is O(1) in time and auxiliary control state, stores no image bytes/queue/diagnostic string, and does not measure a named workload or target peak memory. The profile remains proposal-only with `features.enabled` empty; uncertainty, animation, frame transport, and temporal reasoning remain disabled. Calibration, fallback, dataset, target event, thresholds, idempotent publication, reverse image rendering, and Cortex changes remain open/out of scope.

## 7. Non-goals

This harness does not certify third-party decoder memory safety, production dependency/binary provenance, data rights, image authenticity, medical suitability, deployment reliability, visual semantics, or AGI. Synthetic fixtures prove only their declared arithmetic and package consistency. P5 is an identity-view engineering slice; no conversion, non-identity geometry, production profile, or broad capability is enabled.
