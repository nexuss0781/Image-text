# Image VISION Specification and Harness Home

This directory is the engineering source of truth for the **Image VISION** scope in AGI-Core. It contains requirements, phase gates, test/harness definitions, contract schemas, decision/traceability records, bounded Phase 4 admission/decode, the identity-only Phase 5 canonical-raster view, the Phase 6 forward-difference baseline, the bounded Phase 7 descriptive-quality/atomic-failure slice, and the Phase 8 proposal-only single-flight request runtime. The full image pipeline is not implemented and the candidate profile remains proposal-only.

## Governing documents

- [PROJECT.md](PROJECT.md) — formal scope, architecture, mathematical model, authority boundaries, implementation constraints, contracts and evidence standard.
- [ROADMAP.md](ROADMAP.md) — ordered end-to-end engineering sequence and conditional branches.
- [PHASES.md](PHASES.md) — phase-by-phase inputs, process, outputs, acceptance criteria and transition gates.
- [TODO.md](TODO.md) — atomic phase-mapped engineering backlog.
- [DECISIONS.md](DECISIONS.md) — current policy decisions, deferred owner inputs and change-control record.
- [P2_REVIEW_RECORD.md](P2_REVIEW_RECORD.md) — user-approved two-party review model, assistant-side review findings, verification, and P2 closeout.
- [P4_CLOSEOUT_RECORD.md](P4_CLOSEOUT_RECORD.md) — historical assistant-side implementation review and evidence for D-015, captured before the later D-016 P5 authorization.
- [P5_CLOSEOUT_RECORD.md](P5_CLOSEOUT_RECORD.md) — D-016 authorization and bounded identity-only P5 historical closeout.
- [P6_CLOSEOUT_RECORD.md](P6_CLOSEOUT_RECORD.md) — D-017 authorization, bounded forward-difference results, proposal-only status, non-claims and the Phase 7 stop.
- [P7_CLOSEOUT_RECORD.md](P7_CLOSEOUT_RECORD.md) — D-018 authorization, exact descriptive metric, disabled-uncertainty behavior, atomicity evidence, non-claims and the Phase 8 approval stop.
- [P8_CLOSEOUT_RECORD.md](P8_CLOSEOUT_RECORD.md) — D-019 authorization, one-flight/zero-queue runtime, deadline/cancel/lifecycle evidence, explicit frame/workload exclusions and Phase 9 stop.
- [TRACEABILITY.md](TRACEABILITY.md) — source-to-requirement-to-contract-to-harness map.

## Machine contracts and harness

- [`contracts/image_observation.schema.json`](contracts/image_observation.schema.json) — candidate structural schema for the upstream image observation.
- [`contracts/image_profile.schema.json`](contracts/image_profile.schema.json) — processing/resource/complexity profile schema.
- [`contracts/RUNTIME_INVARIANTS.md`](contracts/RUNTIME_INVARIANTS.md) — runtime checks that structural schemas cannot enforce.
- [`contracts/image_error.schema.json`](contracts/image_error.schema.json) — typed, state-atomic error envelope.
- [`contracts/OBSERVATION_FIELDS.md`](contracts/OBSERVATION_FIELDS.md) — draft field producers, roles, types/units/shapes and lifetimes.
- [`contracts/ERROR_CATALOG.md`](contracts/ERROR_CATALOG.md) — canonical draft codes, meanings, retries and safe-message rules.
- [`contracts/COMPATIBILITY_POLICY.md`](contracts/COMPATIBILITY_POLICY.md) — exact-version, unknown-field and migration rules.
- [`contracts/examples/README.md`](contracts/examples/README.md) — synthetic test-only records and resolvable fixture payloads.
- [`profiles/fixture_profile.example.json`](profiles/fixture_profile.example.json) — small **synthetic test-only** profile example; it is not a production default.
- [`profiles/general_still_image.proposal.md`](profiles/general_still_image.proposal.md) — P1 rationale, candidate limits/arithmetic, and unresolved owner inputs.
- [`profiles/general_still_image.proposal.json`](profiles/general_still_image.proposal.json) — schema-valid `status: proposal` profile; values are advisory, not production defaults.
- [harness/HARNESS.md](harness/HARNESS.md) — harness responsibilities, run evidence and acceptance policy.
- [`harness/check_spec.py`](harness/check_spec.py) — dependency-free package-integrity checker; does not run Image VISION components.
- [`harness/run_evidence.schema.json`](harness/run_evidence.schema.json) — reproducible run-result envelope.
- [`harness/p4/run_p4.py`](harness/p4/run_p4.py) and [`harness/p4/p4_evidence.schema.json`](harness/p4/p4_evidence.schema.json) — C++ admission/decode runner and separate evidence contract.
- [`p4/raster_admission.hpp`](p4/raster_admission.hpp), [`p4/raster_admission.cpp`](p4/raster_admission.cpp), and [`p4/README.md`](p4/README.md) — D-015 decoded-raster admission and bounded dependency-free P5/P6 decoder.
- [`harness/p5/run_p5.py`](harness/p5/run_p5.py) and [`p5/README.md`](p5/README.md) — strict C++20 identity-view/geometry tests and supported-operation boundaries.
- [`p5/canonical_raster.hpp`](p5/canonical_raster.hpp), [`p5/canonical_raster.cpp`](p5/canonical_raster.cpp), and [`harness/results/latest.p5.run_evidence.json`](harness/results/latest.p5.run_evidence.json) — zero-copy canonical view, explicit identity transform, and separate P5 run record.
- [`p6/forward_difference_xy_v1.contract.json`](p6/forward_difference_xy_v1.contract.json) and [`p6/README.md`](p6/README.md) — versioned Phase 6 math/resource contract and implementation boundary.
- [`p6/forward_difference.hpp`](p6/forward_difference.hpp), [`p6/forward_difference.cpp`](p6/forward_difference.cpp), and [`harness/p6/run_p6.py`](harness/p6/run_p6.py) — dependency-free C++20 operator and strict normal/sanitizer runner.
- [`harness/p6/p6_evidence.schema.json`](harness/p6/p6_evidence.schema.json) and [`harness/results/latest.p6.run_evidence.json`](harness/results/latest.p6.run_evidence.json) — Phase 6 evidence contract and run record.
- [`harness/fixtures/p6_forward_difference_vectors.json`](harness/fixtures/p6_forward_difference_vectors.json) — independent literal RGB/RGBA and seeded-byte oracles.
- [`p7/endpoint_code_fraction_v1.contract.json`](p7/endpoint_code_fraction_v1.contract.json), [`p7/quality_indicator.hpp`](p7/quality_indicator.hpp), [`p7/quality_indicator.cpp`](p7/quality_indicator.cpp), and [`p7/README.md`](p7/README.md) — exact descriptive metric, bounded C++20 implementation and uncertainty/error boundary.
- [`harness/fixtures/p7_endpoint_code_fraction_vectors.json`](harness/fixtures/p7_endpoint_code_fraction_vectors.json), [`harness/p7/test_quality_indicator.cpp`](harness/p7/test_quality_indicator.cpp), and [`harness/p7/run_p7.py`](harness/p7/run_p7.py) — literal oracles, failure injection, supported-boundary checks and strict normal/sanitizer runner.
- [`harness/p7/p7_evidence.schema.json`](harness/p7/p7_evidence.schema.json), [`harness/p7/case_bindings.json`](harness/p7/case_bindings.json), and [`harness/results/latest.p7.run_evidence.json`](harness/results/latest.p7.run_evidence.json) — exact separate case bindings and P7 run artifact; the shared P6 catalog remains unchanged.
- [`p8/single_flight_runtime_v1.contract.json`](p8/single_flight_runtime_v1.contract.json), [`p8/request_runtime.hpp`](p8/request_runtime.hpp), [`p8/request_runtime.cpp`](p8/request_runtime.cpp), and [`p8/README.md`](p8/README.md) — bounded synchronous runtime contract and implementation.
- [`harness/p8/test_request_runtime.cpp`](harness/p8/test_request_runtime.cpp), [`harness/p8/run_p8.py`](harness/p8/run_p8.py), [`harness/p8/case_bindings.json`](harness/p8/case_bindings.json), and [`harness/results/latest.p8.run_evidence.json`](harness/results/latest.p8.run_evidence.json) — strict C++20 tests, separate case bindings, and P8 evidence.
- [`harness/case_catalog.json`](harness/case_catalog.json) — machine-readable definitions and lifecycle metadata; executed outcomes live in separate P4/P5/P6/P7/P8 run artifacts.
- [`harness/fixtures/analytic_patterns.json`](harness/fixtures/analytic_patterns.json) — tiny hand-computable input and expected-output vectors.

## Binding policy for this scope

The current user direction is authoritative for Image VISION: implementation uses C++ and Assembly at low abstraction levels with an audited mathematics library as needed; **machine-learning libraries and frameworks are prohibited**; and `O(n²)` or worse complexity over any input-scaled count is prohibited. Every operation must state explicit variables, work, memory, and profile bounds. These rules do not rewrite non-image VISION or Cortex.

Image VISION emits structured observations only. ENCODER owns visual-token embedding, cross-observation alignment, valid masks, and construction of the approved numeric `X[B,S,F_in]` tensor. Cortex receives only the approved numeric tensor and aligned sidecar. This package neither modifies Cortex nor permits an Image-to-Cortex shortcut.

The older packet under [`src/Vision/IMAGE/`](../../src/Vision/IMAGE/README.md) remains unchanged for auditability. Its TensorFlow/Keras-specific execution plan is superseded for this Image VISION scope by the current policy; other global VISION documents and Cortex contracts remain untouched. The former `image-text` repository review is diagnostic context only and is not a source implementation.

## Current status

P0–P2 decisions remain as recorded, with the candidate profile still `status: proposal`. Under D-015, P4 admission and bounded binary P5/P6 `maxval=255` decoding pass 33/33 cases in normal and ASan/UBSan runs. Under D-016, the identity-only P5 canonical-view slice passes 10/10 cases. Under D-017, the Phase 6 `forward-difference-xy-v1` operator passes 13/13 exact, limit, replay, cancellation and deadline cases in both strict normal and ASan/UBSan builds. Under D-018, the P7 descriptive `endpoint_code_fraction` slice passes 18/18 literal metric, uncertainty-disabled, privacy, failure-atomicity and P4/P5/P6-boundary cases in both builds. It is an exact fraction of included uint8 channel codes equal to 0 or 255 (GRAY includes its channel; RGB includes R/G/B; RGBA excludes alpha), tagged `fraction`/`descriptive_only` and not a probability, calibration, confidence, clipping diagnosis or semantic quality score. Under D-019, the bounded P8 runtime slice passes 12/12 strict normal and ASan/UBSan tests: one active request, zero queue, explicit backpressure, bounded deadline/cancel propagation, drain/close, and private aggregate snapshots. Animation/frame transport, external telemetry sinks, observation publication, named workload evidence and production activation remain disabled or open. `features.enabled` remains empty and uncertainty remains disabled. Reverse image rendering and Cortex remain unchanged. See the [P4](P4_CLOSEOUT_RECORD.md), [P5](P5_CLOSEOUT_RECORD.md), [P6](P6_CLOSEOUT_RECORD.md), [P7](P7_CLOSEOUT_RECORD.md), and [P8](P8_CLOSEOUT_RECORD.md) closeout records.

Phase 2 artifacts include the field catalog, runtime invariants, stable error catalog, compatibility policy, and [test-only examples](contracts/examples/README.md). Package-checker success is not itself the P2 review, component conformance, or production approval.

The standard-library package checker validates specification artifacts and separate P4/P5/P6/P7/P8 run evidence; it does not execute C++ tests or certify a production target/binary. The current catalog maps all 25 `IV-*` requirements and 52 runtime-invariant clauses, with 75 component definitions (51 `not_run`, 24 `blocked`). The current checker has 21 assertions, including the P8 contract and evidence checks. P4/P5/P6 historical results and all their source/catalog hashes remain unchanged; P7 preserves and validates its recorded historical worktree fingerprint, and P8 uses separate bindings. Run package evidence outside the repository with `python3 -I Image/SPEC/harness/check_spec.py --output-dir /tmp/image-spec-check`. Named workload/resource measurements, approved production limits, calibrated uncertainty, frame/duplicate policy, observation publication, ENCODER production dimensions, named owner appointments, and release authorization remain open in [DECISIONS.md](DECISIONS.md). Phase 9 is not authorized.
