# Image VISION Decisions and Open Inputs

**Version:** `0.1.0-draft`
**Purpose:** distinguish decisions established by the current direction from choices that require named owners.
**Change rule:** material changes must identify the affected profile/schema, compatibility impact, rationale, owner, date, and rerun gates.

## Binding decisions for Image VISION

| ID | Decision | Basis / effect |
|---|---|---|
| D-001 | This package is Image-only and does not rewrite global audio/text VISION or Cortex. | Scope and repository change boundary. |
| D-002 | Implementation language boundary is C++ and Assembly with an audited mathematics library where required. | Current user instruction; exact library/compiler/ABI remain open. |
| D-003 | ML libraries and frameworks are prohibited in build, runtime, packaging and harness dependency closure, including transitive dependencies. | Current user instruction; a named build must be audited. |
| D-004 | `O(n²)` and worse over any input-scaled count are prohibited. | Current user instruction; complexity variables and bounds are explicit in `PROJECT.md`. |
| D-005 | Image VISION emits image observations; ENCODER owns embedding/alignment/masks and `X[B,S,F_in]`; Cortex receives only its approved tensor and sidecar. | Approved downstream contract; this package does not modify Cortex. |
| D-006 | The original documentation/setup task implemented no image component; later implementation requires its own phase-specific authorization. | Historical scope boundary; schemas/fixtures/catalog were preparation only until a separate gate is recorded. |
| D-007 | Legacy TensorFlow/Keras execution proposal is superseded for Image VISION only; source documents remain unchanged. | Resolves conflict with current user policy without changing global VISION/Cortex. |
| D-008 | Static gradients/features, patch IDs, learning, calibrated confidence, video semantics and domain-specific capabilities are not baseline commitments. | Require a profile, owner and independent acceptance evidence. |
| D-009 | The `image-text` prototype is not the implementation base and its historical benchmark is not Image VISION evidence. | Read-only assessment; see `/workspace/image-text-review.md` in the current workspace. |
| D-010 | P0 scope boundaries are approved for documentation closeout only; all unspecified owner appointments and technical/profile/workload choices remain open. | User approval dated 2026-10-07; exact scope and limits recorded below. |
| D-011 | The P1 general-still-image proposal, including concrete candidate ceilings and a schema-valid `status: proposal` JSON profile, is advisory only; it does not approve production values, assign owners, or authorize implementation. | User direction to start P1 and “do the best” dated 2026-10-07; see [`profiles/general_still_image.proposal.md`](profiles/general_still_image.proposal.md) and [`profiles/general_still_image.proposal.json`](profiles/general_still_image.proposal.json). |
| D-012 | The user states that the P1 gate criteria are met and directly authorizes Phase 2 contract drafting. This authorizes P2 specification work only; it does not silently promote the P1 candidate to an approved production profile or establish any named-owner review not documented here. | Direct user statement dated 2026-10-07; P2 proceeded with the existing candidate labeled `proposal`; the separately recorded P2 review was subsequently closed under D-013. |
| D-013 | The user sets the P2 review parties to the user/project owner and assistant only, removes any outside-review prerequisite for P2, and authorizes P2 completion after assistant-side consistency/adversarial review. This is approval of the review model and completion process, not a claim that the user manually reviewed individual fields or approved a production profile. | Direct user instruction dated 2026-10-07; see [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). |
| D-014 | The user accepts the Phase 3 coverage/oracle review under the established user-plus-assistant model and authorizes Phase 4. At that time, Phase 4 began with bounded C++ decoded-raster descriptor admission for the proposal's tightly packed HWC uint8 GRAY/RGB/RGBA subset; proposal ceilings were test bounds and no encoded format was then enabled. P5 was not authorized by this decision. | Direct user instruction dated 2026-10-07: “ok approved start phase 4.” This records P3 acceptance and P4 start; no outside reviewer is required and no user field-by-field review is claimed. D-015 below later expands the bounded P4 engineering scope without production approval. See [`p4/README.md`](p4/README.md) and the [P4 run artifact](harness/results/latest.p4.run_evidence.json). |
| D-015 | To finish Phase 4 before Phase 5, complete the previously communicated, bounded, dependency-free binary Netpbm P5/P6 decoder in C++20 alongside decoded-raster admission. The scope is exactly one 8-bit P5 grayscale or P6 RGB image with `maxval=255`, caller-supplied finite limits, exact payload length, and fail-closed unsupported/corrupt/multipage handling. Candidate limits remain proposal/test values. This engineering scope does not approve a production profile, codec dependency, deployment, or Phase 5. | User instruction dated 2026-10-08: complete everything in Phase 4, use the previously communicated bounded P5/P6 scope, build/run/fix, present evidence, and await approval before Phase 5. The user has not yet reviewed or accepted this implementation; no outside review is required under the established model. See [`P4_CLOSEOUT_RECORD.md`](P4_CLOSEOUT_RECORD.md), [`p4/README.md`](p4/README.md), and the [P4 run artifact](harness/results/latest.p4.run_evidence.json). |
| D-016 | The user explicitly authorizes Phase 5 after the P4 report. Implement only the current proposal's identity canonical-raster path: validate and expose exact-value HWC uint8 GRAY/RGB/RGBA views, preserve alpha, record equal source/output dimensions and the identity pixel-center map/inverse, and fail closed for all conversions, inferred metadata, orientation changes, resize/crop/pad, compositing/dropping alpha, or unsupported layouts. Keep the profile proposal-only and do not begin Phase 6. | User direction: “good finish phase 5 fastly,” with the explicit P5 authorization in the task context. This transition authorizes only the bounded P5 engineering slice and does not approve production policy, caps, deployment, or Phase 6. See [`p5/README.md`](p5/README.md), [`P5_CLOSEOUT_RECORD.md`](P5_CLOSEOUT_RECORD.md), and the [P5 run artifact](harness/results/latest.p5.run_evidence.json). |
| D-017 | The user explicitly approves starting and finishing only the bounded Phase 6 baseline: versioned deterministic forward differences `Dx[y,x,c]=X[y,min(x+1,W-1),c]-X[y,x,c]`, `Dy[y,x,c]=X[min(y+1,H-1),x,c]-X[y,x,c]`; two HWC int16 planes in `[-255,255]`, edge replication, preserved GRAY/RGB/RGBA order and P5 identity mapping; checked O(P*C) work and caller limits for pixels/channels/elements/bytes/work; fail-closed cancellation/deadline and exact independent tests. No pyramid, regions, patches, IDs, learning, semantic recognition, ACT reverse rendering or Phase 7. The general profile remains proposal-only and runtime-disabled. | Direct user instruction dated 2026-10-08: “start and finish phase 6,” with the exact implementation/test/scope constraints recorded in [`p6/forward_difference_xy_v1.contract.json`](p6/forward_difference_xy_v1.contract.json). This authorizes the engineering baseline, not production activation or the next phase. See [`P6_CLOSEOUT_RECORD.md`](P6_CLOSEOUT_RECORD.md) and the [P6 run artifact](harness/results/latest.p6.run_evidence.json). Wait for explicit user approval before Phase 7. |
| D-018 | The user explicitly authorizes starting and finishing Phase 7 only for capabilities supported by the existing proposal profile and evidence. Implement a precise descriptive endpoint-code fraction over P5 canonical HWC uint8 (GRAY counts its channel; RGB counts R/G/B; RGBA counts R/G/B and excludes alpha), with exact denominator, method/version/units, checked O(P*C) work, caller limits, controlled literal tests, and fixed safe errors. Keep uncertainty disabled and absent by default; explicit uncertainty requirement returns catalogued `UNCERTAINTY_UNAVAILABLE`. Inject/test atomic failure at P7 and supported P4/P5/P6 boundaries. Do not invent calibration, estimator, dataset, target event, threshold, approval, runtime/publication, persistence, Phase 8, reverse rendering, or Cortex changes. | Direct user instruction dated 2026-10-08, with the exact scope recorded in [`p7/endpoint_code_fraction_v1.contract.json`](p7/endpoint_code_fraction_v1.contract.json). The engineering slice is recorded in [`P7_CLOSEOUT_RECORD.md`](P7_CLOSEOUT_RECORD.md) and [`harness/results/latest.p7.run_evidence.json`](harness/results/latest.p7.run_evidence.json). This does not approve production use or the next phase; await explicit user approval before Phase 8. |
| D-019 | The user explicitly authorizes starting and finishing Phase 8 in speed mode, within the current proposal-only envelope: one in-flight request, zero queue, maximum 10,000 ms request deadline, diagnostic ceiling 1,024 bytes, animation off, and uncertainty off. Implement only bounded synchronous single-flight request control, immediate backpressure, cancellation/deadline forwarding, close/drain, and private aggregate snapshots. Do not invent frame-stream, duplicate-publication, named-workload, telemetry-sink, production-limit, or Phase 9 behavior. | Direct user instruction dated 2026-10-08 and the task-provided current proposal values; exact contract in [`p8/single_flight_runtime_v1.contract.json`](p8/single_flight_runtime_v1.contract.json). This authorizes the bounded engineering slice only; the production workload/resource gate remains open and no Phase 9 work is authorized. See [`P8_CLOSEOUT_RECORD.md`](P8_CLOSEOUT_RECORD.md) and the [P8 run artifact](harness/results/latest.p8.run_evidence.json). |

## P0 scope approval record

- **Date:** 2026-10-07.
- **Approval source:** the user's approval to start P0, together with the Image-scope constraints stated for this task. No organizational title or technical-owner role is inferred for the approver.
- **Approved for this Image scope:** low-level implementation is limited to C++/Assembly, with an audited mathematics library as the only library category approved in principle; no ML library or framework is allowed in any form; `O(n²)` or worse work over any input-scaled count is prohibited; the Image Observation → ENCODER → approved Cortex tensor boundary is preserved; and this P0 work is documentation/harness only, with no image component implementation.
- **Not selected or approved:** no specific math library, compiler/toolchain, ABI, architecture, codec, other dependency, profile, source population, use case, workload, runtime/deployment target, resource/performance limit, feature set, data/retention policy, named owner, CI runner, production ENCODER dimensions, or release authorization. Non-mathematics dependencies remain unapproved until the relevant owner approves and audits them.
- **Approval limit:** this record closes the P0 scope-decision documentation only. It is not a signature or appointment by any named Image, Encoder, runtime, data, security/privacy, test, or release owner; it does not approve P1 or later gates, production APIs, implementation, or deployment.

## P1 proposal status

- **Date:** 2026-10-07.
- **Direction:** the user started P1 and asked for the best proposal in the task-neutral, general-still-image direction.
- **Work product:** [`profiles/general_still_image.proposal.md`](profiles/general_still_image.proposal.md) and its [`schema-valid candidate profile`](profiles/general_still_image.proposal.json) recommend a narrow decoded-raster envelope, explicit sample/layout handling, identity geometry, no task-specific semantics or active derived feature, and forward differences only as a separately reviewable candidate. Candidate ceilings include transparent size/work/output arithmetic.
- **Status and limits:** this is proposal drafting, not an owner decision or approval. The machine-readable profile is explicitly `status: proposal`; its numbers are candidate ceilings, not production limits or SLOs. The harness checks schema shape and arithmetic only. No owner, security, runtime, consumer, or release review is claimed; no target/workload has been identified and no named owner appointed. Production limits, actual workload, and provenance/retention choices remain open.
- **Implementation boundary:** P1 remains profile/design work. No decoder, buffer API, image component, or deployment is authorized by this proposal.

## P1 transition and P2 start authorization

- **Date:** 2026-10-07.
- **User statement:** the user directly stated that Phase 1 gate criteria are met and authorized starting Phase 2.
- **Recorded effect:** Phase 2 machine-contract drafting is authorized within the existing Image-only documentation/harness scope. The observation/profile/error drafts may use the P1 candidate as an advisory proposal.
- **Evidence limit:** this record does not name reviewers or reproduce owner decisions. No actual named-owner review is claimed, no unprovided workload/profile value is created, and `general_still_image.proposal.json` remains `status: proposal`.
- **Gate limit at transition:** D-012 authorized P2 drafting only. The later P2 two-party review and closeout are recorded separately under D-013; production-profile, API-freeze, security, dependency, deployment, and release gates remain separate.

## P2 two-party review and closeout

- **Date:** 2026-10-07.
- **User instruction:** the user states that the only P2 review parties are the user and assistant, directs removal of outside-review blockers, and authorizes quick P2 completion.
- **Recorded approval:** the user approved this P2 review-party model and authorized completion. The assistant performed the documented consistency/adversarial review and closed P2 within that model. No outside review is claimed, and the user is not represented as having manually reviewed individual fields.
- **Scope and limits:** this closes Phase 2 specification work only. The schemas remain draft contracts; this does not approve production values, promote `general_still_image.proposal.json`, certify implementation/security/dependencies, freeze a production API, authorize image component work, or start P3. Later gates still require their own evidence and any applicable owner decisions.

## P3 acceptance and P4 start

- **Date and direct instruction:** 2026-10-07; the user accepted the Phase 3 coverage/oracle review and said “ok approved start phase 4.”
- **Review model:** the existing user/project-owner plus assistant model applies; no outside reviewer is required. This record does not claim manual user review of individual catalog rows or fixture values.
- **Authorized subset:** implement and validate bounded descriptor admission for non-owning, tightly packed HWC `uint8` GRAY/RGB/RGBA buffers in C++ with no external dependencies. Use candidate ceilings only as proposal/test limits. Check dimensions, arithmetic, layout, channels, declared/actual length, pointer representability, cancellation/deadline, typed errors, zero-allocation rejection, and no-partial-success behavior.
- **Explicit limits at D-014:** the proposal then had an empty `encoded_formats` list and D-014 authorized descriptor admission only; no decode implementation was started under that decision. D-015 later adds only the dependency-free P5/P6 `maxval=255` engineering test scope. The profile remains a proposal, production resource limits and broader decoder/security approval remain open, P5 remains unstarted, and Cortex is unchanged.
- **Evidence:** the dedicated P4 run artifact records the C++ test outcomes and normal plus ASan/UBSan runs separately from catalog lifecycle metadata. The earlier P3 run artifact remains an accurate pre-acceptance snapshot; this decision supersedes its pending-acceptance state.

## P4 implementation completion and approval gate

- **Date and direction:** 2026-10-08; the user directed completion of all Phase 4 work, a speed-oriented build/run/fix workflow, and a pause for user approval before Phase 5. The previously communicated small dependency-free P5/P6 subset is recorded as the engineering boundary; no production format choice or production value is inferred.
- **Implementation and review:** descriptor admission and the single-image P5/P6 decoder are implemented in C++20. The assistant reviewed the bounded parser, fail-closed behavior, allocation preflight, dependency boundary, case bindings, and fresh normal plus ASan/UBSan results under the user/project-owner plus assistant model. This is not production security/release certification or user code acceptance.
- **Evidence:** [`P4_CLOSEOUT_RECORD.md`](P4_CLOSEOUT_RECORD.md), [`p4/README.md`](p4/README.md), and [`harness/results/latest.p4.run_evidence.json`](harness/results/latest.p4.run_evidence.json). The component run reports 33/33 passing cases in both builds; the package checker separately validates the specification and evidence bindings.
- **Limits and transition:** the profile remains `status: proposal`; `PNM_P5`/`PNM_P6` and all candidate caps are for this bounded engineering/test scope only. Other formats, animation/multipage, production resource limits, and production security/release approval remain open. **The user has not yet approved the P5 transition; P5 is not started, and work is paused for review.** Cortex is unchanged.

## P5 identity canonicalization completion

- **Authorization:** D-016 records the user's explicit approval to start Phase 5 after the P4 report. No P5-to-P6 transition is authorized by that approval.
- **Implemented subset:** a dependency-free C++20, zero-copy canonical raster view for already-admitted HWC uint8 GRAY/RGB/RGBA data; exact sample/channel/alpha preservation; identity source/output dimensions; and an explicit invertible source-to-target pixel-center identity map. Color/transfer conversion or inference, channel reorder, orientation application, alpha compositing/dropping, resize/crop/pad, and all other layouts remain disabled and fail closed.
- **Evidence and limits:** [`P5_CLOSEOUT_RECORD.md`](P5_CLOSEOUT_RECORD.md), [`p5/README.md`](p5/README.md), and [`harness/results/latest.p5.run_evidence.json`](harness/results/latest.p5.run_evidence.json) record strict C++20, normal and ASan/UBSan results. The general still-image profile remains `status: proposal`; candidate ceilings are test inputs only. This is not production approval or user code acceptance.
- **Next gate:** Phase 6 and the future signal-to-image reverse renderer have not started. Wait for the user's explicit approval before Phase 6.

## P6 deterministic forward-difference completion

- **Authorization:** D-017 records the user's explicit approval to start and finish the exact Phase 6 baseline. The earlier D-016 P5 closeout correctly stated that P6 had not yet been authorized at that time; D-017 is the later transition.
- **Implemented subset:** C++20 `forward-difference-xy-v1` over a P5 identity-canonical HWC `uint8` GRAY/RGB/RGBA view. It emits exactly Dx and Dy planes, each `[H,W,C]` HWC `int16` in `[-255,255]`, preserving channel order and source-pixel index with replicated terminal edges. Checked arithmetic preflights `P`, `P*C`, `2*P*C` elements/work and bytes against five explicit caller limits; supported P4 cancellation/deadline controls fail without partial output. Complexity is O(P*C), with O(1) auxiliary scratch beyond two output arrays.
- **Verification:** [`harness/results/latest.p6.run_evidence.json`](harness/results/latest.p6.run_evidence.json) records 13/13 exact operator, pattern, channel-order, seeded replay, edge, limit, overflow, cancellation and deadline cases passing in strict normal and ASan/UBSan builds. The dependency-free checker validates the versioned contract, independent literal RGB/RGBA/seeded oracles, exact catalog/hash bindings, and proposal-only boundary.
- **Profile and scope:** `general_still_image.proposal.json` remains `status: proposal`; `features.enabled` remains empty. The candidate allowlist in the P6 engineering contract is test/implementation scope only, not production enablement. P4/P5 source and run artifacts remain unchanged; their historical ancestor commits are accepted only while exact implementation/profile input hashes still match.
- **Next gate at the D-017 closeout:** Phase 6 engineering work was complete; no Phase 7 work was included or started, and the Phase 7 transition was not yet approved at that time. D-018 later authorizes only the bounded Phase 7 engineering slice recorded below. No production workload, resource ceiling, profile, deployment, security/release approval, or semantic capability is claimed. See [`P6_CLOSEOUT_RECORD.md`](P6_CLOSEOUT_RECORD.md).

## P7 descriptive quality and atomic failure completion

- **Authorization:** D-018 records the user's direct authorization to start and finish the bounded Phase 7 work described here. The user/project owner and assistant are the review parties; no outside reviewer is required for this engineering closeout.
- **Implemented subset:** C++20 `endpoint_code_fraction` over the P5 identity-canonical HWC `uint8` GRAY/RGB/RGBA raster. Count exact `0` and `255` codes; denominator is `P` for GRAY and `3P` for RGB/RGBA; alpha is excluded. Retain exact integer counts and a binary64 fraction in `[0,1]`, tagged method `uint8-endpoint-code-fraction` version `1`, units `fraction`, image scope and `descriptive_only`. The metric is not probability, confidence, calibration, semantic quality, clipping diagnosis or an acceptance score.
- **Uncertainty/errors:** the profile's uncertainty mode is disabled, and `features.enabled` remains empty. Default results contain no uncertainty; an explicit require-uncertainty request returns `UNCERTAINTY_UNAVAILABLE` with no quality or uncertainty result. No estimator, fallback, calibration data, target event, threshold or approval was selected. Errors use fixed catalogued codes/messages (≤512 UTF-8 bytes), are nonretryable, report `state_changed=false`, and never echo payload bytes, private text, paths or identifiers.
- **Verification:** the P7 runner reports 18/18 passing exact metric, controlled-change, limits, malformed/non-finite, cancellation/deadline, uncertainty, secret-marker, injected-failure, and P4/P5/P6 boundary/pipeline cases in strict normal and ASan/UBSan builds; no external dependencies. The package checker binds separate P7 case IDs and verifies that P4/P5/P6 source hashes and historical evidence remain unchanged. See [`p7/README.md`](p7/README.md), [`P7_CLOSEOUT_RECORD.md`](P7_CLOSEOUT_RECORD.md), and the [P7 run artifact](harness/results/latest.p7.run_evidence.json).
- **Scope limits and next gate:** no persistence/publication API exists; tests confirm failure results are empty and caller input remains unchanged. This engineering result does not activate the metric in the profile or close production calibration/fallback decisions. The profile remains `status: proposal`; production approval is false. No P8 runtime/streams, reverse image rendering, or Cortex changes. **Stop and await explicit user approval before Phase 8.**

## P8 bounded single-flight still-request runtime

- **Authorization:** D-019 records the user's explicit approval dated 2026-10-08 to start and finish Phase 8, with speed-mode execution. The approved proposal-only engineering ceilings are one in-flight request, zero queued requests, a 10,000 ms maximum request deadline, and 1,024 diagnostic bytes. Animation remains disabled and uncertainty remains disabled. These are candidate test values, not production limits.
- **Implemented subset:** C++20 `single-flight-still-request-v1` provides nonblocking admission, immediate `BACKPRESSURE`, cooperative cancellation and bounded steady-clock deadlines forwarded through the existing P4 `AdmissionControl`, drain/cancel-and-drain close, terminal close semantics, and a read-only aggregate snapshot. It stores no image data, queue, labels, paths, or diagnostic strings. P8 does not create observations or change P4–P7 sources.
- **Verification:** [`harness/results/latest.p8.run_evidence.json`](harness/results/latest.p8.run_evidence.json) records 12/12 strict normal and ASan/UBSan cases, including a 16-caller admission burst, zero-queue behavior, P4 cancellation/deadline propagation, close/drain, and telemetry snapshot privacy. Separate bindings preserve the shared catalog and P4–P7 historical artifacts.
- **Explicit exclusions:** frame/stream transport, ordering/reordering/gap semantics, duplicate detection, idempotent publication retries, an external telemetry sink, observation publication, target-process peak-memory measurement, and a named workload are not supplied or claimed. A repeated active submission is indistinguishable from any other and is rejected with `BACKPRESSURE`; a later attempt is a new request. The profile remains `status: proposal`, `features.enabled` remains empty, uncertainty disabled, and production approval false.
- **Gate and next phase:** the bounded runtime slice is implemented and verified; the roadmap's named-workload/resource gate and all production/runtime-owner approvals remain open. No Phase 9 work is authorized. See [`p8/README.md`](p8/README.md), [`P8_CLOSEOUT_RECORD.md`](P8_CLOSEOUT_RECORD.md), and the [P8 contract](p8/single_flight_runtime_v1.contract.json).

## Decisions required before a production profile

All rows below remain open. No numeric value is approved merely because a schema accepts it. The “Accountable input” column names the needed responsibility role, not an appointed person or team; no named owner was supplied by the P0 approval. Each row needs a named accountable owner and a written choice or explicit deferral before its dependent gate.

| ID | Open decision | Accountable input (role needed; appointment open) | Blocks |
|---|---|---|---|
| O-001 | Initial use case, consumer, supported image populations and named success criteria | Image/consumer owner | Profile freeze; any semantic/domain claim |
| O-002 | Supported encoded formats, decoder and animation/multipage policy | Runtime/Image owner | Decode implementation |
| O-003 | Accepted decoded layouts, types, ranges, strides and ownership/lifetime model | Image/runtime owner | Input API |
| O-004 | Canonical channel/color/transfer and grayscale/palette policy | Image owner | Canonicalization |
| O-005 | Alpha preservation or explicit compositing color | Image/consumer owner | Alpha-bearing input |
| O-006 | Orientation policy and transform representation | Image/source owner | Geometry contract |
| O-007 | Whether resize/crop/pad/pyramid/region/patch outputs are needed and their exact rules | Consumer owner | Corresponding operators |
| O-008 | Baseline low-level feature families, formulas, units, channels, borders and shapes | Image/consumer owner | Feature implementation |
| O-009 | Whether any discrete visual-token producer is required, including vocabulary and validity policy | Encoder + Image owner | Token output; otherwise disabled |
| O-010 | Uncertainty target event, granularity, approved conservative fallback or calibrated estimator | Consumer/calibration owner | Uncertainty-bearing production contract |
| O-011 | Data provenance, license/rights, privacy, retention and payload-reference service | Data/privacy/store owner | Persisted payloads and domain claims |
| O-012 | Encoded/input/output byte, dimension, work, memory, concurrency, queue, deadline and diagnostic limits; proposal ceilings exist but are not approved | Runtime/security owner | Profile and deployment |
| O-013 | Target hardware/runtime, workload distribution, performance metric and SLO | Consumer/release owner | Performance qualification |
| O-014 | Exact mathematics library, version/license, non-ML codec/support dependencies, toolchain, ABI and dependency approval | Runtime/build owner | Reproducible build and native release |
| O-015 | Production harness/CI ownership, evidence retention, and any future review model | Test/release owner; P3 review model fixed for the accepted baseline by D-014 | Production CI/governance; does not reopen P3 acceptance |
| O-016 | Named ENCODER production profile `B,S,F_in`, sequence limits and sidecar fields | ENCODER owner | Live integration; synthetic tests are not production values |
| O-017 | Security review, decoder patch policy, binary/dependency audit and release authority | Security/release owner | Production release |
| O-018 | Name the accountable person/team for each required authority: source/profile, data/privacy/store, runtime/build, ENCODER, security, test/evidence/CI, and release | User-appointed owners; no person/team named | P1 production profile, production API freeze/release, and every non-P2 gate requiring that authority; does not block P2 closeout under D-013 |

## Explicitly deferred choices

- No production image width/height, pixel budget, feature width, scale count, patch size, vocabulary, calibration threshold, latency target, throughput target, memory cap or target device is assigned here.
- No codec, compiler, math library brand, SIMD/Assembly ISA, packaging tool, CI service or decoder vendor is recommended by this specification.
- No OCR, classification, detection, segmentation, image search, reconstruction, generation, video motion, cross-modal alignment, custom training objective or update path is selected.
- No uncertainty fallback numeric payload is approved until its owner and contract are named. “High uncertainty” is not a substitute for a versioned value and target-event semantics.

## Decision record template

```text
ID:
Date:
Decision owner(s):
Question and alternatives considered:
Selected value/policy or explicit deferral:
Rationale and evidence:
Affected requirements/schema/profile:
Complexity/resource implications:
Compatibility and migration:
Gate(s) impacted:
Approval status:
```
