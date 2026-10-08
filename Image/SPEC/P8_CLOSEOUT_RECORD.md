# Phase 8 Bounded Engineering Closeout

**Date:** 2026-10-08

**Decision:** D-019

**Contract:** [`p8/single_flight_runtime_v1.contract.json`](p8/single_flight_runtime_v1.contract.json)

**Implementation:** [`p8/request_runtime.hpp`](p8/request_runtime.hpp), [`p8/request_runtime.cpp`](p8/request_runtime.cpp)

**Evidence:** [`harness/results/latest.p8.run_evidence.json`](harness/results/latest.p8.run_evidence.json)

## Authorization and boundary

The user explicitly authorized starting and finishing Phase 8 in speed mode. The approved candidate envelope is one in-flight request, zero queued requests, a maximum request deadline of 10,000 ms, a maximum diagnostics budget of 1,024 bytes, animation disabled, and uncertainty disabled. These numbers are proposal-derived engineering ceilings, not production limits or SLOs. P4/P5/P6/P7 closeout changes and their historical run artifacts were preserved; no P4–P7 component source or shared case catalog was changed.

## Delivered

- C++20 nonblocking single-flight admission with exactly one active lease and zero queue; an occupied runtime returns `BACKPRESSURE` immediately without retaining the new request.
- Effective `steady_clock` deadline equal to the minimum of the configured request-duration ceiling and an optional earlier caller deadline, forwarded with cooperative cancellation via the existing P4 `AdmissionControl`.
- RAII slot release, cancellation handle, terminal idempotent drain/cancel-and-drain lifecycle, and safe late-cancellation behavior.
- Read-only by-value snapshot of fixed aggregate counters; no image data, identifiers, paths, labels, diagnostic strings, external telemetry sink, or observation publication.
- Separate P8 case bindings and evidence validation, retaining all P4–P7 source/catalog fingerprints.

## Verification

The P8 runner reports **12/12 cases passing** in both strict normal and ASan/UBSan builds. Coverage includes candidate-limit rejection, bounded effective deadlines, zero-queue backpressure/retry-after-release, a 16-caller concurrent burst with exactly one accepted lease, P4 cancellation/deadline propagation, drain and cancel-and-drain close, terminal/idempotent lifecycle, destructor cancellation/lifetime safety, and private read-only telemetry snapshots. The evidence records the profile/source/schema/catalog hashes, exact separate bindings, compile flags, host dynamic-link audit, and worktree fingerprint.

The package checker now validates the P8 contract and run evidence. Because adding P8 necessarily changes the repository after the P7 run, the P7 result's existing worktree fingerprint is preserved and validated as **historical** alongside its exact original source/catalog hashes; the P7 artifact itself was not regenerated or edited.

## Remaining gate and non-claims

**The bounded engineering work authorized by D-019 is complete. The full roadmap P8 named-workload/resource gate is not passed**, because no target, named workload, accountable owner, or production resource/SLO input was provided. The candidate ceilings are not treated as measurements.

No animation/frame transport, ordering/timestamp/reorder/gap policy, duplicate request identity, idempotent observation publication/retries, external telemetry sink, observation assembly, production activation, or target peak-memory certification is claimed. The proposal profile remains unchanged with `status: proposal`, `features.enabled: []`, animation disabled, and uncertainty disabled. Cortex and non-Image components are unchanged.

**Stop here. Phase 9 has not been started or authorized.**
