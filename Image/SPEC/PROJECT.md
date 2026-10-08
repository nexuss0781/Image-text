# AGI-Core Image VISION: Scope, Contracts, and Engineering Principles

**Specification ID:** `AGI-IMAGE-VISION-PROJECT`
**Version:** `0.1.0-draft`
**Status:** Engineering specification; bounded P4 admission/decode under D-015 and identity-only P5 engineering slice under D-016 are verified; profile remains proposal-only; Phase 6 awaits explicit user approval; no production approval
**Date:** 2026-10-07
**Parent:** [`SPECS/VISION.md`](../../SPECS/VISION.md), Spec 02
**Downstream boundary:** [`src/Cortex/ENCODER_TENSOR_CONTRACT_PROPOSAL.md`](../../src/Cortex/ENCODER_TENSOR_CONTRACT_PROPOSAL.md)

## Abstract

Image VISION is the image-modality input stage of AGI-Core. Its engineering purpose is to turn an explicitly described image payload into a bounded, validated, provenance-preserving observation that retains geometry, low-level visual evidence, quality indicators, and uncertainty semantics. It must remain faithful to the input contract: an image observation is not an interpretation of depicted content, a learned shared representation, an action, or proof of general intelligence.

This specification establishes an end-to-end contract for still images and independently identified raster frames; defines component responsibilities, data and coordinate models, resource and complexity bounds, failure atomicity, testing evidence, and integration ownership; and supplies a phased route from specification freeze to a separately gated release. Implementation is constrained to C++ and Assembly at low abstraction levels with an audited mathematics library where required. Machine-learning libraries and frameworks are prohibited. Every algorithm must avoid quadratic complexity in any input-scaled count; in particular, all-pairs pixel, region, patch, or token operations are disallowed. These are binding scope constraints, not a recommendation to replace the existing Cortex or global VISION implementation.

This package is not a general-purpose image engine. Under D-015 it includes bounded C++20 decoded-raster admission and a dependency-free binary Netpbm P5/P6 decoder limited to one 8-bit image with `maxval=255`; under D-016 it adds only a zero-copy identity canonical-raster view and explicit pixel-center identity transform for already-admitted HWC uint8 GRAY/RGB/RGBA rasters. All conversions, metadata inference, orientation changes, alpha compositing/dropping, resize/crop/pad, and unsupported layouts remain disabled. It includes no other decoder/codec, production profile, approved numerical limit, workload service level, trained artifact, or broad capability claim. The candidate profile remains `status: proposal`; all numeric ceilings are test bounds only. Phase 6 and the future signal-to-image reverse renderer have not started and require explicit user approval. The eventual system may participate in a broad vision-capable AGI, but “AGI vision” is an end-to-end claim that requires separate task-level evidence from the full consuming system.

**Keywords:** image perception; structured observation; spatial provenance; bounded computation; uncertainty; native systems; conformance testing; AGI evaluation

## 1. Problem and objective

An image input can be syntactically decodable yet unsuitable for safe processing: dimensions may overflow allocation arithmetic, channel order may be unknown, orientation may be implicit, rows may be strided, metadata may be untrusted, and derived values may lose their mapping to source coordinates. A downstream consumer cannot repair metadata that was invented, silently converted, or discarded at ingestion. Conversely, a perception front end must not claim semantic understanding merely because it produces features, regions, or token IDs.

Image VISION therefore has a deliberately narrow objective: for a declared input and immutable processing profile, produce either (a) one complete, versioned image observation whose payload references, spatial transforms, provenance, quality, and uncertainty satisfy their contracts, or (b) one typed rejection with no partial publication and no persistent state change. The objective is to preserve usable evidence and its limits while keeping work, memory, queues, and diagnostics bounded.

The design supports a broad *engineering envelope* of raster sources—files, buffers, cameras, network payloads, stored images, generated fixtures, and frames supplied by another stream owner—without asserting that every source or domain is enabled in the first profile. Codec, color, geometry, feature, retention, and resource behavior are profile-controlled. Medical, scientific, remote-sensing, document, chart, artwork, and natural-image inputs are not interchangeable validated populations; each requires declared data and consumer criteria before a profile claims support.

## 2. Formal model and terms

Let the admitted request be `r = (b, d, s, p, τ, β)`, where `b` is bounded encoded bytes or a decoded raster reference; `d` is a layout/format descriptor; `s` is caller-supplied source identity; `p` is a versioned processing profile; `τ` is optional caller-supplied time/frame metadata; and `β` is a resource/deadline/cancellation budget. A decoder `D_p` yields a decoded raster `X`; a declared canonicalization transform `T_p` yields `X_c`; deterministic or separately approved feature operators `Φ_p` yield optional evidence `F`; quality measurement `Q_p` yields descriptive indicators `q`; and an approved uncertainty method `U_p` yields `u` or a declared conservative fallback. Assembly produces an observation:

`O = (id, request, source, geometry, payload_refs, F?, q, u, provenance, profile)`.

The observable mapping is `r → O` or `r → E`, where `E` is a typed error. No path may emit a plausible `O` after an input, transform, resource, cancellation, or integrity failure. `D`, `T`, `Φ`, `Q`, and `U` are specified by profile and version; unspecified behavior is not a default.

For complexity analysis, define `W` and `H` as raster width and height; `P = W·H` as pixel count; `C` as channels; `L` as pyramid levels; `A` as local-neighborhood area; `R` as emitted regions; `F` as feature values per region or pixel; `Q` as patch/token count; and `B` as the number of simultaneously admitted requests. A profile supplies finite maxima for every such quantity and for bytes/work. These variables are never collapsed into a misleading single `n` where the hidden product could be quadratic.

**Quality indicator** means a measured property of image/processing (for example, clipping fraction) under a named method. **Uncertainty** means a value whose target event and calibration semantics are declared. Under the downstream convention, uncertainty is in `[0,1]`, with `0` highest confidence and `1` highest uncertainty. A quality score is not automatically a probability. **Observation** is the versioned upstream record and its bounded payload references; it is not a Cortex tensor.

## 3. System boundary and responsibilities

The image path is a modality-specific specialization of VISION P4 (image front end), P5 (observation assembly), P6 (uncertainty), P7 (validation/rejection), and P8 (telemetry). It runs before ENCODER. The conceptual pipeline is:

```text
Caller / environment
   │ bytes or declared raster + identity + profile + budget
   ▼
I1 admission → I2 bounded decode → I3 canonical pixels/geometry
   → I4 local spatial evidence (optional profile outputs)
   → I5 quality/uncertainty → I6 observation assembly/validation
   → I7 bounded runtime, errors and read-only telemetry
   │ image observation + opaque payload references
   ▼
ENCODER E1/E2: token embedding, ordering, alignment, mask and sidecar
   │ approved finite X[B,S,F_in] + aligned sidecar
   ▼
Cortex M2 and named consumers
```

Image VISION owns: input descriptor checks; enabled-format decoding; pixel/layout/color/alpha/orientation policy; spatial transforms; low-level profile-defined features; optional future discrete symbols only under a distinct approved contract; quality evidence; uncertainty metadata; observation identity and provenance; atomic rejection; bounded request/stream behavior; and privacy-preserving operational telemetry.

Image VISION does **not** own: image meaning, OCR/captioning, object or scene identity, semantic segmentation, task relevance, salience selection, cross-modal alignment, token embedding, a shared latent space, durable retention, Learning objectives or parameter commits, Cortex numeric projection, image generation/reconstruction, action, or proof of AGI. These functions belong to explicitly named downstream or governance owners. A future custom-trained algorithm written in the permitted low-level languages remains outside the baseline until its model/data/update authority and task evaluation are approved; the absence of an ML framework does not silently grant training authority.

## 4. Implementation and complexity policy

The following rules govern all production and test build paths for this scope:

1. The implementation boundary is C++ and Assembly, using a mathematics library only where numerical primitives require it. C++ owns checked contracts and general orchestration; Assembly may implement a specifically reviewed native operation under the same observable contract and must have an equivalent reference path. Exact compiler, ABI, architecture, library, license, and deployment choices remain owner decisions; this document does not recommend a vendor or toolchain.
2. Any machine-learning library or framework is prohibited in production, build, test, packaging, and runtime dependencies, including indirect/transitive dependency paths. The mathematics library is permitted for deterministic numerical operations. Any non-ML codec, I/O or support dependency also requires separate owner approval and audit; this specification recommends no vendor. The dependency inventory and binary/link audit must establish this distinction for a named build.
3. `O(n²)` and worse work are forbidden when `n` denotes any input-scaled count, including pixels, patches, regions, tokens, frames, or candidate pairs. This includes disguised pairwise distance tables, global all-to-all comparisons, quadratic attention/matching, and nested scans whose bounds both grow with input size. Assembly does not exempt an algorithm from the rule.
4. Complexity must be stated in the variables above. A plausible local pipeline bound is `O(P·C·A·L + R·F)` only when `A`, `L`, and per-item `F` have explicit profile ceilings and `R` has a proven linear bound in `P`. Peak memory must likewise include raster, intermediates, output, decoder scratch, and concurrency. A faster asymptotically quadratic implementation is still prohibited.
5. `O(P log P)` is not automatically prohibited, but it requires an operation-level proof, bounded profile, predeclared work budget, reference tests, and owner approval. A hidden `P×R`, `Q×Q`, or equivalent term cannot be justified by a general “linear in output” label. If a profile cannot prove subquadratic work, it is rejected before enablement.
6. All dimension, stride, byte-count, output-count, work-count, and address calculations use checked arithmetic before allocation, pointer arithmetic, or narrowing conversion. No silent cast, clipping, resizing, padding, layout inference, or algorithm substitution is permitted.

The allowed computation is not defined by a particular library API. The exact mathematics and scalar/array semantics belong to versioned operation contracts and hand-computable reference fixtures.

## 5. Image input, coordinates, and transforms

Inputs are either bounded encoded payloads with format evidence, or decoded raster descriptors with dimensions, channel count/order, element type, range, row/plane strides, color/transfer assumptions, and payload length/reference. Unknown order, range, orientation, or transfer characteristics remain unknown; they are not guessed from filenames, three channels, or host conventions. Decoders accept only formats explicitly enabled by a profile; animation and multi-page payloads require an explicit selection policy or typed rejection.

The source raster coordinate frame has origin at the upper-left, `x` increasing by column and `y` by row; locations denote pixel centers `(x+0.5,y+0.5)`. Every crop, pad, resize, orientation correction, pyramid step, feature grid, or patch grid must carry dimensions and a transform identity mapping it to its parent/source frame. Any operation that is not invertible must identify that fact and its valid domain. Source timestamps, device identity, authenticity and capture semantics are caller-owned; processing time is never substituted for capture time.

Canonical pixel representation is profile-defined, not universal. The profile specifies channel layout, color profile/transfer assumption, numeric type/range, grayscale/palette behavior, alpha preservation or explicit composite color, orientation, and any resize/crop/pad policy with interpolation and boundary rules. A transform is recorded as applied, not merely desired. In the absence of an approved transform, preserve the declared raster or reject; do not silently stretch or discard alpha.

## 6. Spatial evidence and optional symbols

A baseline may expose canonical pixels by reference and deterministic low-level operators whose definitions are complete (channels, sign, scale, units, border rule, shape, coordinate mapping, and work). For example, a forward difference per channel can be defined as `Dx[y,x,c]=X[y,min(x+1,W−1),c]−X[y,x,c]` and `Dy[y,x,c]=X[min(y+1,H−1),x,c]−X[y,x,c]`, with edge replication and unchanged axes. This is a mathematical fixture example, not a frozen production feature set. Degenerate shapes such as one row or one column remain mathematically defined; they are neither buffer errors nor grounds to invent neighbors.

Multi-scale pyramids, region partitions, patches, and discrete visual symbols are optional profile features. They must specify ordering, scale transforms, exact coverage, edge/partial-region masks, value bounds and output byte/work budgets. A symbol ID is meaningful only under its named profile and vocabulary; it is not an embedding, word, label, or shared visual language. Any future custom tokenizer or learned feature operator requires a named consumer, data governance, task/held-out metrics, artifact/version policy, update ownership, complexity proof and separately approved integration. No such operator or artifact is included in this setup.

## 7. Observation and downstream interfaces

The machine-readable observation contract is [`contracts/image_observation.schema.json`](contracts/image_observation.schema.json); the profile contract is [`contracts/image_profile.schema.json`](contracts/image_profile.schema.json); the error envelope is [`contracts/image_error.schema.json`](contracts/image_error.schema.json); and the Phase 2 draft defines field ownership in [`contracts/OBSERVATION_FIELDS.md`](contracts/OBSERVATION_FIELDS.md), cross-field rules in [`contracts/RUNTIME_INVARIANTS.md`](contracts/RUNTIME_INVARIANTS.md), stable failures in [`contracts/ERROR_CATALOG.md`](contracts/ERROR_CATALOG.md), and compatibility in [`contracts/COMPATIBILITY_POLICY.md`](contracts/COMPATIBILITY_POLICY.md). These remain candidate contracts. Runtime conformance also checks resolved immutable payload references, checksums/lengths, dtype and shape agreement, profile compatibility, coordinate maps, finite/range constraints, valid masks, token/grid alignment and resource totals.

Every accepted observation carries stable request and observation identities; source declaration; decoded and canonical geometry; pixel/feature references where retained; transform/profile IDs; quality; uncertainty with estimator/calibration/fallback provenance; and producer/runtime provenance. It does not embed arbitrary image bytes in a control message. Payload retention is access- and policy-controlled; a reference is not a promise of permanent storage.

VISION emits observations to ENCODER. ENCODER alone owns token lookup/embedding, sequence ordering and alignment, mask construction, and the approved numeric `X[B,S,F_in]` tensor. Source references, image modality tag, positions, spatial transforms, optional time, and uncertainty stay in the ENCODER-owned sidecar under its approved contract. Image VISION MUST NOT send raw pixels, encoded bytes, visual IDs, feature arrays, uncertainty, modality tags, or spatial values directly to Cortex M2, nor amend the Cortex schema. Cortex remains unchanged by this package.

## 8. Quality, uncertainty, errors, and authority

Quality measures are descriptive and method/version tagged. Acceptance is governed only by deterministic integrity, profile, and safety/resource constraints plus any owner-approved profile rule—not by hidden salience or a learned opinion of relevance. An accepted degraded image reports degradation and affected scope.

Uncertainty uses the downstream convention and is passed unchanged to ENCODER. Every value is finite and within `[0,1]`, and its granularity, target event, calibration state, estimator, calibration data version, and fallback are explicit. If there is no approved calibration, report the approved conservative fallback as uncalibrated; if no fallback is approved, reject or omit uncertainty only if the governing contract permits it. Never relabel brightness, blur, edge energy, or another heuristic as calibrated confidence. Image VISION does not directly set Active Inference precision, Attention, Emotion, or action policy.

Every failure has a stable typed code, bounded non-sensitive detail, request/trace/profile context, retryability and `state_changed=false`. No rejected request publishes a partial observation. Cancellation/deadline/resource failure releases request-local scratch state and leaves persistent parameters and previously published observations unchanged. Retries are idempotent only under the same request key and payload identity. Telemetry is read-only and best-effort; ordinary telemetry excludes pixels, payloads, extracted private content, local paths and unbounded user strings.

## 9. Resource, stream, and security model

Each enabled profile sets hard maxima for encoded bytes, width, height, pixels, channels, decoded/intermediate/output bytes, output elements, stages/work units, deadline, concurrent requests, queue depth, optional reorder window, and diagnostic size. Admission checks run before expensive allocation and are repeated using actual decoded dimensions. Overflow-safe preflight is mandatory. Queue-full behavior is explicit backpressure; any upstream frame dropping is reported by the stream owner and never hidden as complete ingestion.

Still images and externally identified frames are processed independently in this scope. Image VISION may preserve caller-provided stream ID, frame index and time, but does not infer motion, synchronize modalities, sample video, or invent temporal semantics. Temporal modeling, optical flow, tracking, clip understanding and sequence-level semantic inference require a separate contract.

Image bytes and metadata are untrusted. Decoder robustness, integer-safety, malformed layout, decompression bombs, high request rates, payload-reference substitution, privacy, and dependency provenance are release concerns. User image content is data, not an instruction to change code, policy, limits or permissions. A passing synthetic harness is not a decoder security certification.

## 10. Verification and release claims

The harness home [`harness/`](harness/HARNESS.md) separates contract checks, mathematical oracles, adversarial cases, complexity/resource checks, integration fixtures, and future workload evidence. Machine-readable cases are in [`harness/case_catalog.json`](harness/case_catalog.json); analytic vectors are in [`harness/fixtures/analytic_patterns.json`](harness/fixtures/analytic_patterns.json). Every `IV-*` requirement and numbered runtime-invariant clause maps to one or more case definitions. All seven current integer-oracle sets have independent hand derivations and zero-tolerance comparisons. A case definition is not a test run, and a schema validation is not proof of runtime behavior.

Conformance proceeds in levels: specification and profile approval; structural/runtime contract; exact numeric behavior; malformed-input and atomic failure; deterministic replay; bounded resources and subquadratic work; safe ENCODER handoff; and named workload/release evidence. Candidate ceilings appear in the unapproved P1 proposal; production performance thresholds, target hardware, representative distributions, calibration criteria, byte/time limits, and domain-specific quality metrics must be supplied or approved by accountable owners before their gate can pass. No production threshold is implied here.

A release may claim only that an identified implementation conforms to a named contract/profile and meets an explicitly measured workload gate. Local-feature correctness does not prove OCR, object recognition, scene understanding, visual reasoning, cross-modal alignment, autonomy, biological equivalence, or AGI. An AGI vision claim belongs to the complete deployed system and requires preregistered task-specific evidence, baselines, held-out evaluation, uncertainty analysis, failure analysis, and independent review.

## 11. Normative language, precedence, and current state

“MUST”, “MUST NOT”, “SHOULD”, and “MAY” indicate requirement strength. The current user direction makes C++/Assembly plus a mathematics library, prohibition of ML libraries/frameworks, and the `O(n²)` ban binding for this Image VISION scope. This `Image/SPEC/` package specializes the parent VISION document for image processing only; it does not silently rewrite the audio/text VISION design and does not change Cortex. Where the legacy image packet proposes TensorFlow/Keras or ML-framework execution, this new policy supersedes that proposal for Image VISION. The legacy files remain unmodified for traceability; consult [`TRACEABILITY.md`](TRACEABILITY.md).

The user approved the P0 scope boundaries on 2026-10-07; the approval record and its limits are in [`DECISIONS.md`](DECISIONS.md). That approval confirms only the stated Image-scope constraints and the Image Observation → ENCODER → approved Cortex tensor boundary. It does not appoint named owners, select profiles, workloads, codecs, runtimes, libraries/toolchains, resource limits, or production values, and it does not authorize component implementation or deployment.

P1 proposal drafting is complete as of 2026-10-07: the [`general still-image rationale`](profiles/general_still_image.proposal.md) and schema-valid [`proposal-only candidate profile`](profiles/general_still_image.proposal.json) provide explicit recommendations and arithmetic. The user subsequently stated that P1 gate criteria are met, authorized P2, approved the user/assistant-only P2 review model, and authorized P2 completion. P2 is closed under that model; see [`P2_REVIEW_RECORD.md`](P2_REVIEW_RECORD.md). The profile remains `status: proposal`; no production choices or outside reviews are inferred.

This packet does not authorize production deployment, freeze unresolved owner choices, or establish whole-system conformance. The user accepted the P3 coverage/oracle review and authorized P4 under D-014; D-015 records bounded admission and P5/P6 decoding; D-016 explicitly authorized and bounded the identity-only P5 slice. P4's C++20 suite passes 33/33 cases; P5 passes 10/10 exact-value and geometry cases in both normal and ASan/UBSan runs. Separate phase artifacts record outcomes, and the package checker validates bindings without rerunning C++. The catalog retains 70 component definitions with execution outcomes stored separately. The profile remains `status: proposal`; candidate limits remain test-only, transformations outside identity remain disabled, and no production security/release approval is claimed. **Phase 6 and the future signal-to-image reverse renderer have not started and require explicit user approval.** The host source/link audit does not certify a production runtime or binary. See [`P4_CLOSEOUT_RECORD.md`](P4_CLOSEOUT_RECORD.md), [`P5_CLOSEOUT_RECORD.md`](P5_CLOSEOUT_RECORD.md), [`PHASES.md`](PHASES.md), [`ROADMAP.md`](ROADMAP.md), [`TODO.md`](TODO.md), and [`DECISIONS.md`](DECISIONS.md).
