# Image VISION Engineering Phases

**Version:** `0.1.0-draft`
**Status:** P0 scope decision closeout recorded 2026-10-07; P1-to-P2 and P2 closeout recorded; P3 coverage/oracle review accepted; bounded P4 admission/decode complete under D-015; D-016 identity-only P5, D-017 forward-difference P6, D-018 descriptive-quality P7, and D-019 single-flight still-request P8 engineering slices are implemented and verified; P9–P14 not started
**Companion:** [`ROADMAP.md`](ROADMAP.md) · [`TODO.md`](TODO.md)

A phase is a bounded engineering unit with entry inputs, permitted work, concrete outputs, acceptance evidence, and a transition gate. A failed gate means **stop, correct, or defer**; it never means lower the requirement silently. “Pass” applies only to the named contract, profile, build, and evidence. Phase descriptions alone do not authorize implementation; the current bounded P4 implementation scope is recorded in D-015, building on the P3 acceptance and P4 start in D-014.

## P0 — Specification and scope freeze

**Purpose:** establish one consistent authority for the Image VISION work and settle what the first deliverable claims.

**Inputs:** parent [`SPECS/VISION.md`](../../SPECS/VISION.md); the draft packet in [`src/Vision/IMAGE/`](../../src/Vision/IMAGE/README.md); approved ENCODER↔Cortex contract; current user policy and P0 scope approval in [`PROJECT.md`](PROJECT.md) and [`DECISIONS.md`](DECISIONS.md). Missing named-owner responses are recorded as open, not inferred.

**Process:** review responsibilities and exclusions; identify every inherited image requirement; resolve the legacy TensorFlow conflict for this scope; record required owner roles while leaving unprovided person/team appointments open; classify each capability as baseline, optional or prohibited; record approved boundaries and all unresolved choices.

**Outputs:** approved scope and precedence record; owner-role register with unprovided appointments explicitly open; dated decision/approval record; explicit success/non-claim statement; phase enablement list.

**Success criteria:** no contradictory image execution policy; C++/Assembly and audited mathematics-library boundary is explicit; ML libraries/frameworks prohibited; `O(n²)` ban defined over all input-scaled counts; Cortex remains unchanged; ENCODER boundary is intact; no production value is invented.

**Gate/transition:** the user’s scope-level approval closes P0 scope documentation only. It appointed no named technical owner and selected no profile/runtime/workload values. P1 proposal drafting began only after the user's later direction on 2026-10-07; all owner/profile/runtime/workload choices still block their dependent gates. No runtime API is frozen and no component implementation is authorized.

## P1 — Profile, workload, and resource contract

**Current status (2026-10-07):** the task-neutral proposal package is drafted: [`profiles/general_still_image.proposal.md`](profiles/general_still_image.proposal.md) and its schema-valid [`proposal-only JSON profile`](profiles/general_still_image.proposal.json) contain concrete candidate ceilings, arithmetic, workload shape, capability recommendations, and open inputs. The user directly stated that P1 gate criteria are met and authorized P2. The candidate remains `status: proposal`; no named-owner review evidence or production profile values are supplied or claimed here.

**Purpose:** bind design to actual input and consumer constraints instead of accidental defaults.

**Inputs:** P0 decisions; the user's task-neutral general-still-image direction; proposed source classes and workload shape; named consumer, runtime/security, data/store, and profile owners when appointed; deployment target if known. Missing production inputs stay open.

**Process:** prepare and internally check a task-neutral candidate for encoded formats and decoded layouts; define proposed color, alpha, orientation and geometry policies; specify candidate channel/sample and stride behavior; assign review-only candidate caps for encoded bytes, pixels, decoded/intermediate/output bytes, features, work, concurrency, queue, deadline and diagnostics, with explicit arithmetic; identify the workload shape and acceptance roles. Recommendations are labeled unapproved; actual production workload/target and owner appointments are marked open, not guessed.

**Outputs:** versioned rationale plus a schema-valid profile with `status: proposal`; workload-shape description; explicit open-value/resource register; candidate capability table; decisions with required owner role and rationale. An owner-approved production profile is a separate gate output, not implied by the proposal JSON.

**Success criteria:** candidate fields have precise proposed meanings; every unresolved value/owner is explicit; no production limit or enabled capability is implied by a fixture; eventual checked-arithmetic preflight and finite work/output bounds are specified; each proposed operator has a subquadratic complexity model; unsupported inputs have typed outcomes.

**Gate/transition:** the user's direct statement on 2026-10-07 declares the P1 criteria met and authorizes P2 drafting. This transition record does not invent named-owner reviews or promote the proposal to production status. Production profile approval, dependent capability enablement, and implementation remain separately gated.

## P2 — Machine contracts and compatibility rules

**Current status (2026-10-07):** P2 is complete and closed under the review model approved by the user: the user/project owner and assistant are the only review parties, with no outside-review prerequisite. The assistant performed a consistency/adversarial review and recorded the findings, fixes, and checker evidence in [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). This does not claim the user manually reviewed individual fields or approve a production profile/API. The contracts remain drafts.

**Purpose:** define wire/runtime shapes before components or adapters.

**Inputs:** P0 scope, P1 profile template, existing approved Encoder contract.

**Process:** review and version observation, profile, transform, feature, payload-reference, uncertainty, provenance and error records; specify immutable payload identity/length/checksum/access metadata; define required/optional fields and unknown-field handling; define cross-field invariants JSON Schema cannot express; define compatible change rules and profile/model ownership.

**Outputs:** versioned observation and profile schemas; [`contracts/OBSERVATION_FIELDS.md`](contracts/OBSERVATION_FIELDS.md); [`contracts/RUNTIME_INVARIANTS.md`](contracts/RUNTIME_INVARIANTS.md); [`contracts/ERROR_CATALOG.md`](contracts/ERROR_CATALOG.md); [`contracts/COMPATIBILITY_POLICY.md`](contracts/COMPATIBILITY_POLICY.md); [test-only example records](contracts/examples/README.md).

**Success criteria:** every observation field has producer, units/type/shape, lifetime and owner; no raw pixels/tokens can be mistaken for Encoder features; the uncertainty convention matches ENCODER; schema rejects unrecognized or incompatible forms; failure carries `state_changed=false`.

**Gate/transition:** close P2 when the schemas, field catalog, runtime invariants, error/compatibility rules, and test-only examples are consistent; assistant-side adversarial review is recorded; and the user-approved two-party closeout is recorded in [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). No outside reviewer is a P2 prerequisite. P2 closure does not itself start P3, authorize implementation, or approve production use.

## P3 — Harness and numeric-oracle baseline

**Current status (2026-10-07):** the baseline artifacts were reviewed and accepted by the user under the user/project-owner plus assistant model in D-014; no outside review was required. At acceptance, the machine catalog mapped all 25 `IV-*` requirements and 52 runtime-invariant clauses, and seven analytic fixtures had independent hand-derivations with exact integer tolerances (`atol=0`, `rtol=0`). The original P3 snapshot passed 13/13 package assertions and its repeat-run checks. Later catalog entries and P4 evidence are maintained separately from that historical snapshot. This acceptance closes P3 and starts P4 under D-014; D-015 records the bounded completion scope.

**Purpose:** make correctness and failure claims falsifiable before implementation.

**Inputs:** accepted P2 contracts; hand-computable fixtures; test owner; allowed build/dependency policy.

**Process:** map each normative MUST to one or more cases; fix independent expected outputs; define positive, negative, boundary, malformed, concurrency, resource, privacy and integration families; assign `defined`, `not_run`, `pass`, `fail`, or `blocked` status; define result artifact fields, seed/profile/commit capture, tolerance ownership, and reproducibility rules.

**Outputs:** runnable-harness interface requirements; machine-readable case catalog and fixture vectors; traceability links; evidence-record schema and test-run procedure.

**Success criteria:** every normative contract has test coverage; expected numeric values are independently derived; row/column/single-pixel behavior is explicit; cases can distinguish a correct rejection from a crash or partial success; no harness dependency introduces an ML framework.

**Gate/transition:** the user accepted the coverage/oracle review and authorized P4 in D-014 under the user+assistant model. The older P3 evidence file remains a historical pre-acceptance snapshot. Do not call unexecuted catalog definitions “passing tests”; executed P4 outcomes live in the dedicated P4 run artifact.

## P4 — Admission and bounded decode

**Current status (D-015; later transition D-016):** the bounded P4 engineering scope is implemented and verified. It includes descriptor admission plus a dependency-free C++20 binary Netpbm P5/P6 decoder for one 8-bit image with `maxval=255`. The P4 runner passed 33/33 cases in normal and ASan/UBSan builds. Its report was presented; the user subsequently authorized the bounded P5 slice. The profile remains `status: proposal`; all caps are test candidates, not production limits.

**Purpose:** reject unsafe descriptors and decode only the exact, explicitly bounded encoded subset without hidden defaults or partial output.

**Inputs:** P2 descriptor/error contracts; P3 accepted case definitions; D-014 P3/P4 transition; D-015's bounded P5/P6 implementation scope. The candidate profile is not production-approved. The decoder's encoded, header, dimension, pixel, channel, decoded-byte, and work ceilings are supplied explicitly per call.

**Process:** validate decoded-raster descriptors with checked dimension/stride/byte arithmetic and return a read-only non-owning view; for P5/P6, parse a bounded header, check profile ceilings and exact payload length before allocation, copy into owned output once, retain explicit format/decoder identity, reject other variants/ranges and trailing/multipage bytes, and check cancellation/deadlines. No transform, observation, feature, or Cortex path is included.

**Outputs:** a valid caller-owned decoded-raster view, an owned P5/P6 `DecodedRaster` with format and decoder identity, or a typed fail-closed result with no partial raster. Decoder complexity is `O(B + P*C)` time and `O(P*C)` owned output space, with bounded header scanning and constant parser state.

**Success criteria:** admission and decoder cases cover positive/boundary, malformed, unsupported, truncated, extra, concatenated, overflow, resource-limit, cancellation and deadline paths; limit failures occur before image-sized allocation; exact samples/format/dimensions agree with fixtures; normal and supported sanitizer runs pass; dependencies and evidence bindings are audited. Production limits, external owner/security/release approval, other formats, and broader integration are not claimed.

**Gate/transition:** technical P4 work is complete under D-015 and recorded in [`P4_CLOSEOUT_RECORD.md`](P4_CLOSEOUT_RECORD.md). The user later explicitly authorized the bounded P5 start under D-016. P4 evidence remains phase-specific; it does not claim production approval.

## P5 — Canonical pixels and spatial geometry

**Current status (D-016):** the approved identity-only engineering slice is implemented and verified in [`P5_CLOSEOUT_RECORD.md`](P5_CLOSEOUT_RECORD.md). It does not complete or enable any unapproved conversion, orientation, or non-identity geometry capability; the general profile remains proposal-only.

**Purpose:** make every pixel conversion and spatial change explicit and invertible where possible.

**Inputs:** validated decoded-raster view or P5/P6 output from P4; P1 color/orientation/alpha/resize proposal; P3 canonicalization fixtures.

**Process:** for this authorized slice, validate an already admitted HWC uint8 GRAY/RGB/RGBA view, expose a zero-copy canonical view with exact sample/channel/alpha preservation, and emit an explicit identity transform with source/output dimensions and pixel-center matrix/inverse. Preflight output-byte/work limits. All conversions, inferred color/transfer/orientation metadata, orientation changes, alpha compositing/dropping, resize/crop/pad, and unsupported layouts reject closed.

**Outputs:** a non-owning canonical raster view with preserved samples and declared channel format; an identity transform record; or a typed fail-closed result with an empty view. No payload reference, observation, or publication API is introduced.

**Success criteria for this slice:** independent exact-value oracles pass for 1x1, 1xN, Nx1, odd dimensions, GRAY/RGB/RGBA, and alpha values; dimensions and identity/inverse maps agree at pixel centers, corners, and degenerate extents; resource/overflow and unsupported-policy cases reject without a partial view; strict-warning C++20 and ASan/UBSan runs pass. No sample conversion or copy is performed. Non-identity operations and production-target replay remain disabled/unselected.

**Gate/transition:** the D-016 identity-only engineering slice is recorded in [`P5_CLOSEOUT_RECORD.md`](P5_CLOSEOUT_RECORD.md). At that closeout, the proposal remained unapproved for production and Phase 6 was not yet authorized; D-017 later records the user's explicit Phase 6 authorization. The profile remains proposal-only and all other P5 operators remain disabled. A transform-policy change increments profile/contract as required.

## P6 — Deterministic local spatial evidence

**Current status (D-017):** the user explicitly authorized starting and finishing only the bounded forward-difference baseline. The versioned contract, implementation, independent exact tests, normal/sanitizer evidence and package-check bindings are complete. See [`P6_CLOSEOUT_RECORD.md`](P6_CLOSEOUT_RECORD.md) and [`p6/README.md`](p6/README.md).

**Purpose:** implement exactly one deterministic, pre-semantic spatial operator without promoting the candidate profile.

**Inputs:** the P5 identity-canonical HWC `uint8` GRAY/RGB/RGBA view; [`p6/forward_difference_xy_v1.contract.json`](p6/forward_difference_xy_v1.contract.json); explicit caller-supplied limits for pixels, channels, output elements, output bytes and work; and P4 cancellation/deadline control.

**Process:** compute only `Dx[y,x,c] = X[y,min(x+1,W-1),c] - X[y,x,c]` and `Dy[y,x,c] = X[min(y+1,H-1),x,c] - X[y,x,c]`. Preserve HWC order and the P5 identity coordinate transform. Produce two `[H,W,C]` `int16` planes in `[-255,255]`, with replicated edges, checked preflight arithmetic and no partial output. Count exactly `2*P*C` directional results; traverse in `O(P*C)` time with O(1) auxiliary scratch.

**Outputs:** exactly the two versioned Dx/Dy planes, shape/channel metadata, retained identity transform, exact work/output counters, or a typed fail-closed result with both planes empty. No observation, descriptor, mask, region, patch, token ID, or publication API is added.

**Success criteria:** literal exact oracles pass for constant, impulse, horizontal/vertical ramps, checkerboard, seeded byte vectors, RGB/RGBA ordering, one-row/one-column/1×1, and deterministic replay; checked arithmetic and all five caller limits reject safely; cancellation/deadline reject atomically; strict-warning C++20 and ASan/UBSan suites pass; no external dependency or Cortex change.

**Gate/transition:** D-017 completed the engineering baseline only; at that closeout, Phase 7 had not been authorized. D-018 later records the user's approval and the bounded Phase 7 engineering closeout below. The implementation allowlist is proposal-only, `features.enabled` remains empty, and the general profile remains `status: proposal`. Pyramid/regions/patches, learning, semantic recognition, ACT reverse rendering and production activation remain out of scope.

## P7 — Quality, uncertainty, and atomic error model

**Historical status at D-018 closeout:** the user explicitly authorized Phase 7 and the bounded implementation/evidence scope is complete. At that time Phase 8 had not started; D-019 later authorized only the separate bounded P8 slice described below. See [`P7_CLOSEOUT_RECORD.md`](P7_CLOSEOUT_RECORD.md), [`p7/README.md`](p7/README.md), and [`harness/results/latest.p7.run_evidence.json`](harness/results/latest.p7.run_evidence.json). The profile remains proposal-only.

**Purpose:** implement only a deterministic descriptive quality indicator supportable by the current P5 raster contract, omit disabled uncertainty, return a typed unavailable error when uncertainty is explicitly required, and preserve all-or-nothing error behavior.

**Inputs:** the P5 identity-canonical HWC `uint8` GRAY/RGB/RGBA view; [`p7/endpoint_code_fraction_v1.contract.json`](p7/endpoint_code_fraction_v1.contract.json); caller-supplied pixel/channel/work/output limits; P4 cancellation/deadline control; and the current proposal profile, whose uncertainty mode is disabled. No target event, calibration dataset, threshold, owner decision, or fallback approval is assumed.

**Process:** compute `endpoint_code_fraction` version `uint8-endpoint-code-fraction/1` in one row-major pass. Count exact `uint8` codes `0` or `255`; the denominator is `P` for GRAY and `3P` for RGB/RGBA. GRAY includes its one channel; RGB includes R/G/B; RGBA includes R/G/B and excludes alpha from both counts. Retain exact integer numerator/denominator and the finite binary64 quotient in `[0,1]`, with units `fraction`, scope `image`, and `acceptance_effect: descriptive_only`. Check arithmetic and all caller limits before indexing; check cancellation/deadline during work and before result construction. Use fixed, allowlisted error codes/messages; inject quality-stage faults and exercise supported P4/P5/P6 failure boundaries. No input bytes are modified and no persistence/publication API exists.

**Outputs:** the descriptive quality record only, with exactly 24 logical scalar payload bytes (two `uint64` counts plus one IEEE-754 binary64 value; metadata excluded), or a typed fail-closed result. Uncertainty is absent by default. If a caller requires it while profile mode is disabled, return `UNCERTAINTY_UNAVAILABLE` without any quality or uncertainty result. All errors are nonretryable, have bounded allowlisted messages and report `state_changed=false`.

**Success criteria:** exact literal/controlled-change oracles pass; runtime is `O(P*K)` with `K≤3` and `O(1)` auxiliary scratch; malformed/non-finite metadata, invalid limits, output bounds, cancellation/deadline, missing/disabled uncertainty and secret-marker non-disclosure are tested; injected failures return no metric/uncertainty and preserve input bytes; supported P4/P5/P6 boundaries are tested; strict C++20 normal and ASan/UBSan runs pass; package evidence binds sources and exact existing catalog IDs. No estimate is described as probability, calibration, confidence, or semantic quality.

**Gate/transition:** D-018 closed only the supportable Phase 7 engineering slice under the user/project-owner plus assistant review model; no outside reviewer was a blocker. It did not select a fallback/calibration method or authorize production/runtime publication. The machine profile remains `status: proposal`, `features.enabled` remains empty, and uncertainty remains disabled. Calibration, fallback, target-event, dataset, threshold, and production-owner decisions stay open. **At that historical closeout, work stopped pending explicit Phase 8 approval; D-019 subsequently authorizes the bounded P8 engineering slice only.** No streams/runtime were included in P7; reverse image rendering and Cortex remain unchanged.

## P8 — Bounded request runtime and frame transport

**Current status (D-019):** the approved, supportable proposal-only slice is implemented in [`p8/request_runtime.hpp`](p8/request_runtime.hpp) and verified by [`harness/results/latest.p8.run_evidence.json`](harness/results/latest.p8.run_evidence.json). It enforces one active request, zero queue, a caller-bounded deadline no greater than 10,000 ms, diagnostic budget no greater than 1,024 bytes, cooperative cancel, drain/close, and private aggregate snapshots. Animation, frame transport, streams, and uncertainty remain disabled. The machine profile remains `status: proposal`; no production workload, target SLO, telemetry sink, or observation publication is claimed.

**Purpose:** enforce budgets during concurrent operation without inventing temporal meaning.

**Inputs:** P1 resource profile; P4–P7 components; stream owner policies; telemetry/privacy policy.

**Process:** implement request lifetime, deadline/cancellation, in-flight cap, queue behavior, duplicate/idempotent retry rules, optional reorder window, close/drain semantics and best-effort telemetry; distinguish a caller-supplied frame sequence from video understanding.

**Outputs:** bounded runtime state; typed backpressure/cancellation/deadline responses; read-only health and telemetry; explicit stream-gap accounting where an upstream owner drops frames.

**Success criteria:** queue, memory, work, diagnostics and active requests remain under declared caps during burst/sustain tests; full queue returns typed backpressure; no silent shedding or timestamp fabrication; telemetry outage does not change an observation; cancellation and close release scratch state.

**Gate/transition:** the bounded engineering slice is complete under D-019, but the roadmap's **named workload policy/resource gate remains open** because no production workload, target, or accountable owner was supplied; proposal-derived test ceilings are not production evidence. No frame/stream policy, idempotency/publication behavior, or external telemetry sink is invented. Phase 9 remains unauthorized. Sequence-level motion/temporal algorithms require a separate contract.

## P9 — Observation assembly, references, and publication

**Purpose:** publish one self-consistent immutable observation only after every field/reference passes.

**Inputs:** P2 schemas; successful P4–P8 outputs; bounded payload/reference provider contract.

**Process:** resolve immutable payload IDs, byte lengths, checksums, dtype/shape and access/retention declarations; verify profile/transform/feature/uncertainty alignment; assign observation identity and provenance; validate schema plus runtime cross-field invariants; atomically publish or return typed error.

**Outputs:** canonical Image Observation; immutable payload-reference set; trace and validation evidence.

**Success criteria:** all required metadata is present and truthful; stale, missing, mismatched or corrupt references reject; source time and identity are preserved as supplied, never fabricated; no post-publication mutation; retries obey idempotency.

**Gate/transition:** serializer/parser compatibility and atomic-publication tests pass. Retention authority remains with the designated store/environment.

## P10 — ENCODER integration boundary

**Purpose:** ensure the image observation feeds the approved representation owner without bypass or ownership leakage.

**Inputs:** approved image observation; ENCODER owner and concrete profile; approved ENCODER↔Cortex contract.

**Process:** pass observation references to ENCODER; verify ENCODER performs token lookup/embedding, sequence ordering/alignment, valid-mask construction and assembly of fixed positive `X[B,S,F_in]`; preserve uncertainty/spatial/source/time/modality metadata in its sidecar; test downstream shape/mask policy without sending image payloads to Cortex.

**Outputs:** integration fixtures, adapter contract and explicit conformance record (or typed unsupported-profile outcome).

**Success criteria:** image pixels, encoded bytes, visual IDs, image feature arrays and metadata never enter M2 `X` as an Image VISION shortcut; ENCODER retains the mask and sidecar unchanged; Cortex consumes only its approved numeric tensor; no Cortex file/schema is modified by this phase.

**Gate/transition:** Encoder owner signs the concrete profile and integration evidence. Synthetic fixtures cannot stand in for production dimensions.

## P11 — Complexity, dependency, and adversarial assurance

**Purpose:** prove the system obeys the user’s constraints under worst supported profiles, not just average examples.

**Inputs:** source/build/dependency inventory; all enabled operator proofs; work/resource counters; hostile and boundary cases; security owner.

**Process:** audit loops, candidate generation and allocation growth; demonstrate checked arithmetic at public/native boundaries; inspect direct/transitive dependencies and final binaries for prohibited ML frameworks; test unusual dimensions, overflow, malformed data, queue floods, cancellation races and telemetry privacy; maintain a risk register.

**Outputs:** complexity proof set; dependency and binary audit; adversarial test evidence; security/privacy/dependency findings and remediation.

**Success criteria:** no `O(n²)`/worse input-scaled algorithm or hidden pairwise term; no prohibited ML dependency; every profile has finite budgets; no malformed request causes unchecked pointer arithmetic, unbounded work, partial publication or private content leak; all unresolved risks have owner-approved disposition.

**Gate/transition:** independent review accepted. Any prohibited dependency or quadratic operation blocks the affected build/profile.

## P12 — C++ optimization and Assembly review (conditional)

**Purpose:** optimize only an accepted operation when a named workload demonstrates a material need.

**Inputs:** correct P6 operation and reference tests; named consumer workload; target/runtime and SLO; P11 dependency/complexity baseline.

**Process:** capture baseline, hardware/software, inputs, warmup, repetitions, p50/p95/tail where appropriate, throughput, peak memory, thread count, numerical error and end-to-end timings; record why C++/Assembly changes are proposed; implement only inside the frozen operation contract; compare against independent and C++ reference paths; test alignment, feature dispatch, concurrency and fallback.

**Outputs:** measured decision record, exact source/build artifact, parity report, reproducible raw benchmark, or a record that optimization is not justified.

**Success criteria:** same contract and outputs within predeclared tolerance; no undefined behavior or data-dependent unbounded memory; subquadratic complexity; end-to-end owner-set criterion met after decode/copy/queue costs; portable C++ behavior remains correct. No favorable end-to-end result means no Assembly kernel is enabled.

**Gate/transition:** separate owner approval for each architecture/profile. An isolated microbenchmark is insufficient.

## P13 — Optional scope expansion

**Purpose:** admit new image domains or trainable/token/temporal capabilities without weakening the baseline.

**Inputs:** named consumer and use case; data/rights/privacy authority; extension specification; custom algorithm owner; Learning/update authorization if applicable.

**Process:** define input distribution and task success before algorithm; add a profile and compatibility strategy; document model/data provenance, held-out baselines, failure modes, uncertainty, update lifecycle, complexity and bounded resources; review custom implementation/dependency restrictions; define rollback and opt-out.

**Outputs:** separate versioned extension contract, data/evaluation plan, implementation proposal and gate decision.

**Success criteria:** task claims are measurable and held out; no ML framework is introduced; any custom trainable update is Learning-authorized; no semantic authority leaks into Image VISION; extension is feature-gated and remains subquadratic; baseline still conforms when extension is off.

**Gate/transition:** explicit separate approval. Otherwise the capability is not implemented and is not a baseline blocker.

## P14 — Target qualification and release

**Purpose:** authorize a named build/profile for a named consumer, not declare generic image intelligence.

**Inputs:** approved profiles; all applicable contracts, tests, workload measurements, security/privacy and dependency review; release owner; rollback plan.

**Process:** create a reproducible release dossier binding commit, schemas, profile hashes, compiler/build settings, math library/dependency manifest, test-run IDs, raw artifacts, performance results, known limitations and failure/recovery decisions; check version compatibility and deploy/rollback controls.

**Outputs:** signed release decision; enabled profile allowlist; auditable artifact; support/runbook and limitations; rollback/disable procedure.

**Success criteria:** applicable gates pass; target caps and owner SLOs are met; no unreviewed dependencies or quadratic paths; Encoder boundary holds; uncertainty claims match the evidence; declared domain is the only supported claim. No AGI/semantic claim follows from this gate.

**Gate/transition:** release owner authorizes activation. Any material profile/schema/compiler/decoder/operator change follows change control and reruns impacted gates.
