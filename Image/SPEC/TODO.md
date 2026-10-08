# Image VISION Atomic Engineering TODO

**Status:** P0–P2 records remain in force; P3 accepted; bounded P4 admission/decode (D-015), identity-only P5 (D-016), forward-difference P6 (D-017), and descriptive-quality/atomic-failure P7 engineering slices (D-018) are complete and verified. Await explicit user approval before Phase 8.
**Source of truth:** [`PROJECT.md`](PROJECT.md), [`ROADMAP.md`](ROADMAP.md), [`PHASES.md`](PHASES.md).
**Rule:** A checkbox is complete only for the artifact or review it names. P1 proposal checkboxes attest to a drafted, internally checked recommendation only; they do not mean owner approval. A written test case is not a passing test. Split any task that cannot be completed and reviewed as one change.

## Phase P0 — Specification and scope freeze

- [x] Create the requested `Image/SPEC/` root and core specification files.
- [x] State Image-only precedence for the user’s C++/Assembly, math-library-only and no-ML-framework requirements.
- [x] Define `O(n²)` as forbidden across every input-scaled count and require explicit multivariable complexity bounds.
- [x] Preserve the VISION-observation→ENCODER→approved Cortex tensor boundary; do not modify Cortex.
- [x] Record the initial P0 documentation-only boundary; later component work requires separate, exact phase authorization (the current bounded P4 implementation is recorded in D-015).
- [x] Record the user's dated approval of the stated Image-scope boundaries; do not treat it as appointment of technical owners or approval of production choices.
- [x] Record approved decisions and every unprovided owner/profile/runtime/workload choice as open in `DECISIONS.md` and `TRACEABILITY.md`.
- [x] Confirm the legacy TensorFlow-oriented Image VISION proposal is superseded for this scope without altering global VISION or Cortex.

**P0 closeout (2026-10-07):** the scope decision record is closed only for the boundaries explicitly approved by the user. At that point P1 had not started; named owner appointments remained open (see O-018), and no P1 profile, runtime, workload, or production value was selected. The P0 closeout itself did not start P1 or authorize implementation; P1 proposal drafting began later under the separate user direction recorded below.

## Phase P1 — Profile, workload, and resource contract

**Progress record (2026-10-07):** the candidate package is complete for proposal drafting: [`profiles/general_still_image.proposal.md`](profiles/general_still_image.proposal.md) and [`profiles/general_still_image.proposal.json`](profiles/general_still_image.proposal.json). The JSON has `status: proposal`; the harness checks its schema and candidate arithmetic. Numeric ceilings are explicit recommendations only. No production profile is approved, and no owner, consumer, runtime, security, or release review is claimed.

### Proposal drafting — complete

- [x] Describe the candidate input/workload shape and explicitly leave the actual source population, consumer/task, distribution, target, and acceptance criteria open.
- [x] Recommend the P5/P6 engineering-test allowlist only, rejection of other formats and animation/multipage input, and HWC decoded-raster input; do not imply production approval.
- [x] Specify candidate channel orders, sample type/range, contiguous stride/layout behavior, and invalid-input handling.
- [x] Specify color/transfer, grayscale/palette, alpha, orientation, identity geometry, coordinate convention, and non-enabled transforms.
- [x] State the active capability set (no derived features) and the exact, disabled forward-difference candidate layout, units, border rule, optionality, and masks.
- [x] Assign review-only candidate ceilings for dimensions, pixels, channels, decoded/intermediate/output bytes and elements, work, concurrency, queue, deadline, and diagnostics; provide transparent arithmetic and memory accounting.
- [x] State the candidate operation's variables and subquadratic complexity argument; keep independent proof review and measurements open.
- [x] Create a versioned schema-valid `status: proposal` profile; distinguish it from the synthetic fixture profile and from an approved production profile.
- [x] Add harness validation for the proposal profile and its width/pixel, byte, output-element, and work arithmetic; record that checker success is not owner approval or implementation evidence.
- [x] Record required owner roles, candidate rationales, and unresolved production decisions without inventing appointments.

### P1 transition record and production-profile status

- [x] Record the user's direct statement that P1 gate criteria are met and P2 may start (D-012). This records transition authorization only; it does not fabricate named-owner reviews or user-unprovided profile/workload data.
- [x] Preserve `general_still_image.proposal.json` as `status: proposal`; a user-authorized P2 start is not a conversion to production status.
- [ ] Record actual named owner appointments, review identities, workload/target decisions, and any approved production profile only when those data are supplied by the accountable authorities.

### P1 review evidence details — not supplied in the P2 start statement

- [ ] Appoint the profile/Image, consumer, runtime/security, data/privacy/store, Encoder, test/evidence, and release authorities (O-018); no appointments are recorded.
- [ ] Identify the actual consumer/task, source populations, size/aspect distribution, arrival/burst/concurrency workload, target hardware/runtime, and acceptance owner (O-001/O-013).
- [ ] Have the appointed owners accept, revise, or explicitly defer the candidate input, canonicalization, feature, provenance/retention, and resource choices; approve production caps or keep the dependent capability disabled (O-002–O-012).
- [ ] Review the checked-arithmetic, peak-memory accounting, work definition, complexity argument, and target measurement plan with the appointed runtime/security/profile owners.
- [ ] Record security/dependency/release authority and any required restrictions; no security or release sign-off is claimed (O-014/O-017).
- [ ] Record owner decisions and produce a reviewed production profile/version, or explicit owner-approved deferrals, before production-profile approval or dependent capability enablement. P2 drafting is separately authorized by D-012.

## Phase P2 — Machine contracts

**Progress and closeout record (2026-10-07):** The user approved a two-party P2 review model (user/project owner and assistant), removed outside-review blockers, and authorized completion. The assistant's consistency/adversarial review and package evidence are recorded in [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). P2 is closed for specification work only; the candidate profile remains `status: proposal`. P3 has since started under the user's separate direction; P2 closeout does not authorize implementation.

- [x] Review `contracts/image_observation.schema.json` against the P2 observation requirements and correct the evidence-presence gap.
- [x] Review `contracts/image_profile.schema.json` against P1 budgets and complexity fields; keep the still-image candidate `status: proposal`.
- [x] Draft and consistency-review the runtime error catalog, stable codes, bounded messages, retryability and `state_changed=false` semantics.
- [x] Specify immutable payload references: identity, scheme, byte length, checksum, shape/type metadata, access and retention.
- [x] Specify transform and coordinate-map serialization, inverse/valid-domain rules, and source-frame identity.
- [x] Specify quality indicator identity/method/version/units/scope and acceptance ownership; profile-specific metrics/thresholds remain open.
- [x] Specify uncertainty target-event, granularity, calibration state, fallback and unchanged Encoder-sidecar convention; actual target/fallback approvals remain open.
- [x] Record per-field producer/owner role, type/units/shape, and lifetime in `contracts/OBSERVATION_FIELDS.md`; actual named appointments remain open.
- [x] Define draft runtime cross-field checks not expressible in JSON Schema.
- [x] Define strict version/unknown-field behavior and compatibility rules.
- [x] Draft `contracts/ERROR_CATALOG.md`, `contracts/COMPATIBILITY_POLICY.md`, and test-only observation/error/payload records without claiming production approval.
- [x] Add dependency-free package checks for draft schema shape, exact bindings, test fixture bytes, transform/profile/uncertainty/error cross-field rules, plus adversarial duplicate-key, non-finite-number, missing-evidence and malformed-transform probes; future component cases are separately labeled `not_run` or `blocked`.
- [x] Record user approval of the two-party review model and authorization to close P2; record assistant-side consistency/adversarial review and findings without claiming user field-by-field review or outside review.
- [x] Update exact schema bindings and rerun the package checker; keep production profile/security/dependency/API/release approvals and all P3 work separate.

**P2 status:** **closed 2026-10-07** for specification work under D-013 and [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). The contracts remain drafts; this closeout is not production approval, implementation authorization, or P3 start.

## Phase P3 — Harness and numeric oracles

**Status (2026-10-07; current harness includes later phases):** P3 coverage/oracle review was accepted under the user+assistant model by D-014; no outside reviewer was required. The original review snapshot passed 13/13 package assertions, mapped all 25 `IV-*` requirements and 52 runtime-invariant clauses, and recorded seven hand-derived exact oracles. The current checker has 15 assertions validating separate P4 and P5 evidence; the catalog has 70 definitions (46 `not_run`, 24 `blocked`). P4 records 33 admission/decode outcomes and P5 records 10 identity canonical-raster outcomes in separate run artifacts.

- [x] Create the machine-readable harness catalog and analytic fixture-set definition.
- [x] Define lifecycle statuses separately: each component case has `definition_status: defined` and `execution_status: not_run` or `blocked`; only actual run evidence may say `pass`/`fail`.
- [x] Map every normative `IV-*` requirement and each numbered `RUNTIME_INVARIANTS.md` clause to one or more machine-readable executable definitions and exact-match traceability tables.
- [x] Independently hand-derive all seven fixture outputs; freeze exact-integer `atol=0`, `rtol=0` comparisons and record rationale before implementation.
- [x] Define schema-validated run metadata: commit, dirty-tree fingerprint, profile/schema/input hashes, seed, host/runtime, exact command, counts, timestamps, per-check results, elapsed time, RSS scope, and dependency audit; compare repeat runs to verify stable outcomes and input/dependency fingerprints.
- [x] Implement the standard-library-only package checker (`python3 -I Image/SPEC/harness/check_spec.py`); it validates specification artifacts and recorded P4/P5 evidence but does not execute the C++ test suites.
- [x] Audit the Python harness import closure: standard library only, no harness ML package; record the repository's optional TensorFlow extra as unrelated context. P4/P5 host-test source/link audits are separate; no production binary/runtime dependency graph is certified.
- [x] At P3 review, run the original 13 package assertions and verify scope, links, schemas, contracts, fixtures, coverage, dependency policy and evidence metadata. The reviewed catalog then had 66 future component definitions; current P4 status is recorded in its separate artifact.
- [x] Record user acceptance of the P3 coverage/oracle review and explicit authorization to start P4 under the approved user+assistant model (D-014); no outside review is required.

## Phase P4 — Admission and bounded decode

**Status (D-015; subsequent transition D-016):** decoded-raster descriptor admission plus dependency-free binary PNM P5/P6 decoding for one 8-bit image with `maxval=255` passed 33/33 cases in normal and ASan/UBSan runs. The P4 report was presented and the user subsequently authorized the bounded P5 slice. The proposal stays `status: proposal`; limits are test candidates only.

- [x] Implement checked width/height/channel/sample/byte/work arithmetic and host pointer-representability checks for the admitted descriptor boundary.
- [x] Enforce descriptor, sample count, payload length and proposal-only test ceilings before any allocation; verify caller-owned non-owning view lifetime requirements.
- [x] Implement descriptor validation and fail-closed typed error mapping for valid/invalid/unsupported input kinds.
- [x] Verify declared HWC dimensions, channel count/order, `uint8 [0,255]` sample range, tight layout, and exact declared/actual payload length for decoded-raster references.
- [x] Keep descriptor admission separate from the explicit decoder API; unsupported encoded input kinds in `admit()` fail closed.
- [x] Test one-pixel, one-row, one-column, odd-sized, small-profile boundary and proposal-only 4096×4096×4 bound cases.
- [x] Test cancellation, expired deadline, typed resource-limit rejection, allocation-free success/rejection, and empty failure views; no partial raster view is returned.
- [x] Implement binary P5 grayscale and P6 RGB decoding with format and decoder identity; reject other PNM variants and non-255 sample ranges.
- [x] Bound encoded/header/dimension/pixel/channel/decoded-byte/work use with caller-supplied limits and checked arithmetic before allocation.
- [x] Require exact raster length; test malformed headers, integer overflow, truncation, trailing bytes, and concatenated/multipage payloads with empty typed failures.
- [x] Test sample bytes that resemble whitespace/comments, comments between tokens, CRLF headers, exact small limits, and the 4096×4096 proposal-only pixel boundary.
- [x] Review the bounded parser and dependency boundary; pass normal and ASan/UBSan runs with no external decoder library. This does not certify a production target or replace production owner/release approval.
- [x] Regenerate P4 evidence and verify exact catalog bindings and package consistency.
- [x] Present the verified P4 result; the user subsequently explicitly approved the bounded P5 transition under D-016.

## Phase P5 — Canonical pixels and geometry

- [x] Under D-016, implement only the current proposal's identity canonical-raster view for already-admitted HWC uint8 GRAY/RGB/RGBA; do not promote the profile from `proposal`.
- [x] Preserve every supported sample, declared channel order, and RGBA alpha byte exactly with a zero-copy read-only view; use independent literal exact-value oracles.
- [x] Record equal source/output dimensions, transform identity/version, source-to-target direction, explicit pixel-center matrix and inverse, and invertibility.
- [x] Test 1x1, 1xN, Nx1, odd shapes, GRAY/RGB/RGBA, alpha values, corners, centers and degenerate pixel-center extents.
- [x] Fail closed for conversions/inference, channel reorder, orientation application, compositing/dropping alpha, resize/crop/pad, malformed metadata, resource caps and overflowing input descriptors.
- [x] Run strict-warning C++20 normal and ASan/UBSan suites; validate exact test/catalog bindings and profile/source hashes in the package checker.
- [ ] Implement color/transfer conversion, grayscale/palette conversion, orientation changes, alpha compositing, resize/crop/pad, or unsupported layouts only after a separately approved profile/contract selects them.
- [ ] Verify behavior on an approved production target/profile; none is selected, and candidate ceilings remain test-only.
- [x] Present P5 evidence and wait for explicit user approval before Phase 6 or the future signal-to-image reverse renderer; D-017 later supplies authorization for the bounded Phase 6 baseline only.

## Phase P6 — Spatial evidence

- [x] Under D-017, implement only the candidate `forward-difference-xy-v1` contract for canonical HWC uint8 GRAY/RGB/RGBA.
- [x] Specify exact `Dx[y,x,c]` and `Dy[y,x,c]` formulas, int16 range `[-255,255]`, replicated edges, HWC channel order, output shape and retained identity coordinate mapping.
- [x] Specify and check `P`, `P*C`, exactly two output planes, `2*P*C` output elements/work units, output bytes, caller limits, overflow, cancellation/deadline and atomic failure behavior.
- [x] Cover constant, impulse, horizontal/vertical ramps, checkerboard, actual seeded bytes, RGB/RGBA ordering, 1×1/one-row/one-column, and exact deterministic replay with independent literal oracles.
- [x] Review the one-pass O(P*C) implementation and bounded scratch; keep pyramids, regions, patches, masks, IDs, learning, semantics and ACT reverse rendering out of scope.
- [x] Run strict-warning C++20 normal and ASan/UBSan builds; bind all 13 cases, contract/fixture/source hashes and proposal-only scope in Phase 6 evidence and package checks.
- [x] Preserve `status: proposal`, keep `features.enabled` empty, record only an engineering candidate allowlist, and leave production approval false.
- [ ] Add pyramids, regions, patches, token IDs, learning, semantic recognition, publication/observation behavior, or ACT reverse rendering only under a separate versioned authorization.
- [x] Stop after the Phase 6 closeout; D-018 later records the separate explicit Phase 7 authorization and bounded completion.

## Phase P7 — Quality, uncertainty and failure atomicity

- [x] Define and implement one bounded descriptive indicator separately from probabilistic uncertainty: `endpoint_code_fraction`, method `uint8-endpoint-code-fraction` version `1`, units `fraction`, scope `image`, descriptive-only effect, exact numerator/denominator, GRAY/RGB/RGBA channel inclusion, and alpha exclusion; keep it inactive in the proposal profile.
- [x] Add independent literal and controlled-change exact tests, checked arithmetic, caller limits, output bound, deterministic O(P*C) work and no input mutation.
- [x] Keep proposal uncertainty mode disabled: omit values by default and return `UNCERTAINTY_UNAVAILABLE` if explicitly required. Do not select a fallback or estimator without the missing authority/evidence.
- [ ] If calibrated uncertainty is proposed, approve target event, data rights, split, metrics and thresholds before evaluation.
- [x] Verify metric output is finite and in `[0,1]`; no uncertainty value or spatial granularity/mask payload is produced by this slice.
- [ ] Test unknown-regime, calibration, drift/OOD or estimator behavior only after a separately authorized estimator/profile exists; those capabilities are intentionally absent here.
- [x] Test stable, bounded, allowlisted error code/message pairs, nonretryability and `state_changed=false`; verify a secret marker never appears in errors.
- [x] Inject failures after partial local counting and before publication; verify no quality/uncertainty result and unchanged input. Exercise typed failure boundaries in supported P4/P5/P6 APIs; document/check that these phases expose no persistence API.
- [x] Verify no logs/telemetry API is introduced and error strings contain no pixels, private text, paths or identifiers.
- [x] Run 18/18 cases in strict normal and ASan/UBSan builds; validate separate P7 bindings, source hashes, P4/P5/P6 historical evidence and proposal-only scope with the full package checker.
- [x] Stop after the bounded Phase 7 engineering slice; await explicit user approval before Phase 8.

## Phase P8 — Runtime and streams

**D-019 bounded engineering slice complete:** synchronous still-image request lease only; one in-flight, zero queue; caller-supplied deadline capped at 10,000 ms; diagnostics capped at 1,024 bytes with zero diagnostic bytes emitted; cooperative cancellation forwarded to P4; drain/cancel-and-drain close; fixed aggregate snapshot. Profile remains proposal-only. See [`p8/README.md`](p8/README.md), [`P8_CLOSEOUT_RECORD.md`](P8_CLOSEOUT_RECORD.md), and the [P8 run artifact](harness/results/latest.p8.run_evidence.json).

- [x] Implement nonblocking request admission, bounded deadline and cancellation control; forward the same control into the existing P4 safe boundary.
- [x] Enforce exactly one active request and zero queue; return typed `BACKPRESSURE` without waiting or retaining a rejected request.
- [x] Implement terminal close, idempotent drain, cooperative cancel-and-drain, and new-instance reopen semantics.
- [x] Expose only a read-only by-value snapshot of fixed aggregate counters; emit no diagnostic strings or private input metadata.
- [x] Run 12/12 normal and ASan/UBSan cases with a 16-caller burst, queue-full, deadline/cancel, close/drain, privacy, and lifetime coverage; preserve separate P8 bindings.
- [x] Keep animation, uncertainty, frame transport, temporal reasoning, telemetry sinks, and observation publication disabled/absent under the unchanged proposal profile.
- [ ] Measure aggregate peak memory and sustained resource maxima for a named workload on an identified target; no workload, target, or accountable owner is supplied, and proposal ceilings are not production SLOs.
- [ ] Define frame order/time/reorder/gap policy and enable any frame transport only after a separate owner-backed contract; current profile rejects animation/multipage input.
- [ ] Define request identity, duplicate detection and idempotent retry at the observation-publication boundary; P8 has no idempotency key or observation store, and Phase 9 is not authorized.
- [ ] Add and validate an external telemetry sink only with a bounded owner-approved policy; this slice has a read-only local snapshot and no observation to publish.
- [ ] Leave video motion/temporal reasoning disabled unless separately specified and approved.

## Phase P9 — Observation assembly

- [ ] Build observations privately and publish only after structural and runtime validation succeeds.
- [ ] Validate payload reference identity, integrity, byte length, shape, dtype, immutability and access metadata.
- [ ] Cross-check image, feature, transform, mask, token and uncertainty alignment.
- [ ] Preserve source/request/trace identity and only caller-supplied time/frame metadata.
- [ ] Test duplicate request behavior and atomic publication under injected reference/store failure.
- [ ] Test strict unsupported-version and unknown-field rejection.
- [ ] Verify serialization contains references and metadata, not unbounded embedded image bytes.
- [ ] Produce a versioned compatibility report for the observation contract.

## Phase P10 — ENCODER handoff

- [ ] Obtain named ENCODER owner and actual consumer profile before integration.
- [ ] Implement a typed observation adapter without feature embedding or sequence alignment inside Image VISION.
- [ ] Test that ENCODER owns lookup, order, alignment, mask and `X[B,S,F_in]` construction.
- [ ] Verify source refs, spatial metadata, time, modality and uncertainty remain in the sidecar unchanged.
- [ ] Verify no raw image, feature array or token ID is sent directly to Cortex M2.
- [ ] Verify invalid/padded positions follow ENCODER’s approved mask semantics.
- [ ] Record integration test evidence without modifying Cortex files or its approved schema.

## Phase P11 — Complexity, dependencies and safety

- [ ] Produce per-operation time and space complexity proofs with explicit `P,C,L,A,R,F,Q,B` variables.
- [ ] Audit all pairwise/nested-loop candidate generation and reject any quadratic-or-worse input-scaled path.
- [ ] Test scaling/work counters over multiple image and region sizes against the declared asymptotic model.
- [ ] Audit direct and transitive build/test/runtime dependencies; reject all ML libraries/frameworks.
- [ ] Audit linked binaries and packaged artifacts for prohibited ML runtimes.
- [ ] Fuzz or systematically mutate descriptors, strides, dimensions, payload references and corrupt encoded inputs.
- [ ] Run appropriate native memory/undefined-behavior/concurrency checks for the approved build environment.
- [ ] Verify allocation, queue and work caps under hostile and burst workloads.
- [ ] Review privacy, threat model, dependency provenance, patch response and recovery.

## Phase P12 — Conditional C++/Assembly optimization

- [ ] Name the operation, consumer, target, workload and owner-set requirement before optimization.
- [ ] Capture correct reference-path baseline and raw repeatable results first.
- [ ] Freeze the operation ABI, shape, units, error, determinism, cancellation and complexity contract.
- [ ] Implement the candidate in C++ and/or Assembly only within that contract.
- [ ] Compare candidate results against independent fixtures and the C++ reference for all boundary/random cases.
- [ ] Verify alignment, bounds, concurrency, feature selection and fallback behavior.
- [ ] Benchmark complete request path, copies, decode, queueing, memory and tail latency—not only kernel throughput.
- [ ] Require end-to-end owner-set benefit; otherwise record “not justified” and do not enable.
- [ ] Repeat dependency/complexity/safety gates after any optimized path is added.

## Phase P13 — Optional extensions

- [ ] For each proposed new image domain, state population, rights, privacy constraints, consumer task and held-out evaluation.
- [ ] For tokens, version tokenizer/profile/vocabulary, traversal and invalid-patch policy; prove Encoder embedding ownership.
- [ ] For custom learned methods, define training authority, objective ownership, data lineage, artifact lifecycle and rollback.
- [ ] Ensure no prohibited ML framework enters the dependency graph even for optional paths.
- [ ] Prove any extension remains subquadratic and resource-bounded.
- [ ] Separate temporal/video, OCR, recognition, segmentation, reconstruction and generation contracts from base image ingestion.
- [ ] Keep each extension disabled unless its distinct approval and acceptance gate passes.

## P14 — Target qualification and release

- [ ] Name release owner, runtime/profile allowlist, supported domains, consumer and target environment.
- [ ] Run all applicable contract, numeric, failure, determinism, resource, complexity, dependency and integration suites.
- [ ] Record target workload, measurement method, raw benchmark, uncertainty evidence and owner-set SLO result.
- [ ] Complete security, privacy, data rights, dependency/license and supply-chain review.
- [ ] Bind release to commit, schema/profile hashes, compiler/build configuration and dependency inventory.
- [ ] Produce limitations, known issues, operational health, disable and rollback instructions.
- [ ] Ensure semantic/AGI claims are restricted to separately evaluated evidence.
- [ ] Obtain explicit release authorization and retain the signed decision/evidence bundle.
