# Candidate General Still-Image Profile

**Proposal version:** `0.2.0-proposal`<br>
**Machine-readable proposal:** [`general_still_image.proposal.json`](general_still_image.proposal.json)<br>
**Phase:** P1 — profile, workload, and resource contract<br>
**Status:** Drafted and internally checked as a proposal; not approved. No owner, security, runtime, consumer, or release review has occurred.<br>
**Date:** 2026-10-07; P4 engineering-scope and P6 engineering implementation addenda: 2026-10-08

This is a narrow, task-neutral design recommendation. “General still image” means no task-specific semantics; it does **not** claim support or validation for every format, source population, domain, or consumer. The JSON profile has `status: proposal`; its candidate limits and policies are not production SLOs, accepted limits, or evidence of conformance. D-015 authorizes only the bounded P5/P6 decoder engineering work in Phase 4; D-017 later authorizes one forward-difference engineering implementation/test slice. Neither decision promotes this proposal or approves production use.

## Candidate input and behavior

| Area | Candidate proposal | Reason / limit |
|---|---|---|
| Request/workload shape | One caller-identified, already-decoded still raster per synchronous request; one complete observation or typed rejection. No batch, stream, ordering, or temporal meaning. | A workload shape can be proposed without inventing the real consumer, source population, arrival rate, or target. Those remain open. |
| Encoded input | The P4 engineering allowlist is binary Netpbm P5 (8-bit grayscale) and P6 (8-bit RGB), `maxval=255`, one image only. Other formats, sample ranges, animation and multipage input reject. This allowlist is not production approval. | A small dependency-free parser permits completion of P4 without selecting an external codec, license, or production integration policy. |
| Decoded layout | HWC, tightly packed contiguous rows; no strides or planes. Exact byte length is `W*H*C` for `uint8`; validate dimensions, channel order, sample range, and byte count before access. | A small descriptor surface makes size and address arithmetic reviewable. No implicit copy, layout inference, or normalization. |
| Channels and samples | `GRAY`, `RGB`, or `RGBA`; `uint8`, values `[0,255]`; maximum channels `C=4`. Reject `BGR/BGRA`, planar, high-bit-depth, float, palette, HDR, and undeclared combinations. | Preserve the values as supplied. This is a proposed compatibility envelope, not a claim that excluded data is invalid generally. |
| Color and grayscale | Preserve declared color/transfer metadata; if absent, leave it unknown. Do not assume sRGB, convert transfer functions, expand palettes, reorder channels, or derive grayscale. A `GRAY` input stays `GRAY`. | No color interpretation or lossy conversion is implied by channel count. Palette-coded encoded sources are not enabled. |
| Alpha | Preserve the supplied `RGBA` alpha channel; never composite or drop it. `GRAY` and `RGB` have no alpha. | A background/compositing rule would require consumer agreement and a versioned change. |
| Orientation | Use the supplied decoded pixel grid as-is; preserve orientation metadata if available or mark it unknown. Do not apply EXIF or other implicit rotation. | Any orientation correction needs a declared transform and source agreement. |
| Geometry | Identity only. Upper-left origin, `x` right, `y` down, pixel centers at `(x+0.5,y+0.5)`. No resize, crop, padding, pyramid, region, patch, or coordinate remapping. | Source and observation coordinates stay aligned without hidden geometry changes. |
| Active derived features | None. The candidate machine profile has `features.enabled: []`; no runtime feature values or masks are emitted. | No consumer need or Image owner approval has been supplied. |
| Deferred feature candidate | Forward differences `Dx[y,x,c]=X[y,min(x+1,W-1),c]-X[y,x,c]` and `Dy[y,x,c]=X[min(y+1,H-1),x,c]-X[y,x,c]`; two `H×W×C` `int16` arrays, units are input sample-code-value difference `[-255,255]`, final row/column replicated. Implemented and tested only as the D-017 engineering baseline; still disabled in the candidate profile. | A single `(y,x,c)` visit computes both differences; work and output count are exactly `2*P*C`. All pixels are defined, including one-row/one-column images; no validity mask is needed. The contract and test scope are in [`../p6/forward_difference_xy_v1.contract.json`](../p6/forward_difference_xy_v1.contract.json); this is not production approval. |
| Quality and uncertainty | An engineering-only descriptive `endpoint_code_fraction` method is specified under D-018: exact uint8 endpoint-code counts (0 or 255), denominator P for GRAY and 3P for RGB/RGBA, alpha excluded, units `fraction`, method/version tagged, `descriptive_only`. It is not a semantic quality score, probability, confidence, calibration, clipping diagnosis, or acceptance gate. Uncertainty is omitted while profile mode is disabled; explicit requirement returns `UNCERTAINTY_UNAVAILABLE`. | The machine profile remains unchanged: `status: proposal`, `features.enabled: []`, uncertainty mode `disabled`. No target event, dataset, calibration authority, or approved fallback exists; this engineering metric is not activated for runtime/production use. |
| Observation and storage | Publish metadata plus immutable pixel-payload reference, not embedded unbounded image bytes. Retention/access policy is `profile_defined` and unresolved. | Store, rights, access, checksum, and retention choices belong to named data/privacy/store owners. |
| Unsupported input outcome | Recommend typed rejection for unsupported format/layout, invalid descriptor, resource limit, cancellation/deadline, or integrity failure; draft stable codes and envelope are now specified in P2's [`error catalog`](../contracts/ERROR_CATALOG.md) and schema. | No silent conversion or partial observation. The P2 error contract remains a draft pending owner review. |

## Phase 6 engineering-only addendum

D-017 records a single **engineering candidate allowlist**: `candidate_forward_difference_xy_v1`, with mathematical version `forward-difference-xy-v1`. It authorizes the bounded C++20 implementation and its tests only. It is not a runtime/profile allowlist, and it does not enable an observation or publication path.

The machine-readable profile remains `status: proposal` and its `features.enabled` array remains empty. The existing difference output/work ceilings remain dormant proposal reserves, not approved production budgets. Pyramids, regions, patches, masks, IDs, learning, semantic recognition, ACT reverse rendering, Phase 7 behavior and production deployment remain outside this addendum.

The `color_profile_id` in the JSON identifies the *handling policy* “source-declared or unknown”; it is not an assertion that the input has a particular color space. The profile's output and scratch budgets reserve capacity for review of the disabled difference candidate; those reservations do not enable it.

## Phase 7 engineering-only addendum

D-018 implements one descriptive measurement over the P5 identity-canonical raster: the fraction of included `uint8` channel codes that are exactly `0` or `255`. The exact integer numerator/denominator are retained; GRAY includes its single channel, RGB includes R/G/B, and RGBA excludes alpha from both counts. The binary64 ratio is tagged with method `uint8-endpoint-code-fraction` version `1`, units `fraction`, image scope and `descriptive_only`. It does not measure semantic quality or clipping and is not a probability or calibrated confidence value. The full scope, limits, error contract, fixtures and exclusions are in [`../p7/endpoint_code_fraction_v1.contract.json`](../p7/endpoint_code_fraction_v1.contract.json) and [`../p7/README.md`](../p7/README.md).

This addendum is implementation evidence only, not a change to the machine profile. `general_still_image.proposal.json` remains `status: proposal`, `features.enabled` remains empty, and uncertainty remains disabled. No uncertainty values are emitted; when explicitly required, the P7 API returns `UNCERTAINTY_UNAVAILABLE`. No estimator, fallback, target event, dataset, threshold, runtime publication, production approval, or Phase 8 behavior is selected.

## Candidate ceilings and rationale

The following are explicit **proposal values** to make review concrete. They are conservative design-envelope choices, not measurements, workload-derived requirements, SLOs, production limits, or user-approved values. Runtime/security/profile owners may accept, revise, or reject each one after the real workload and target are identified.

| Limit | Candidate value | Rationale / status |
|---|---:|---|
| Encoded bytes | `67,108,864` bytes (`64 MiB`) | Proposal-only test ceiling for the P5/P6 engineering subset; not a production limit. |
| Width × height | `4096 × 4096` pixels maximum each dimension | A simple, bounded 16-megapixel square envelope for design review; not a statement that larger inputs are invalid. |
| Pixel count `P` | `16,777,216` | Exactly `4096*4096`; an independent checked cap prevents a large rectangular raster bypassing the area budget. |
| Channels `C` | `4` | Maximum of `GRAY`, `RGB`, and `RGBA`. |
| Decoded bytes | `67,108,864` bytes (`64 MiB`) | `P*C*1 byte` for `uint8`; exact tight HWC byte length is required. |
| Intermediate bytes | `67,108,864` bytes (`64 MiB`) | Reserve at most one full-size staging raster. Identity-only behavior needs no canonicalization copy; the ceiling is a conservative reserve, not permission to add an unreviewed transform. |
| Output elements | `134,217,728` | Reserved upper bound for two difference planes: `2*P*C`. No feature is active in this proposal. |
| Output bytes | `268,435,456` bytes (`256 MiB`) | Reserved difference output uses `int16`: `2*P*C*2 bytes`. |
| Work units | `134,217,728` | Covers the larger of the difference candidate (`P*C = 67,108,864`) and decoder work (`max_encoded_bytes + max_decoded_bytes = 134,217,728`, one unit per admitted input byte plus output sample byte). Proposal-only ceiling, not a production budget. |
| In-flight requests / queue | `1` / `0` | Serial, no-wait candidate; reject/backpressure rather than silently queue or shed. This does not define process-wide admission for other services. |
| Deadline | `10,000 ms` | Candidate finite cancellation ceiling only, not a latency SLO or performance promise. It must be measured and approved on a named target/workload. |
| Diagnostic bytes | `1,024` | Candidate bound for one bounded diagnostic response; payloads, paths, and unbounded labels are excluded. |
| Scales, regions, patches | `1`, `0`, `0` | Identity only; no multiscale or region/patch outputs. |

### Arithmetic and resource accounting

Use integer-only checked arithmetic before allocation or address calculation. At the candidate maxima:

```text
P = min(4096 * 4096, 16,777,216) = 16,777,216 pixels
Decoded = P * C * sizeof(uint8) = 16,777,216 * 4 * 1 = 67,108,864 bytes = 64 MiB
Difference elements = 2 axes * P * C = 134,217,728 int16 elements
Difference output = 134,217,728 * 2 bytes = 268,435,456 bytes = 256 MiB
Candidate difference work = P * C = 67,108,864 pixel-channel visits
Candidate decoder work = encoded bytes + decoded bytes
                      = 67,108,864 + 67,108,864 = 134,217,728 work units
Reserved simultaneous payload total = decoded + intermediate + output
                                  = 64 + 64 + 256 = 384 MiB per in-flight request
```

The `448 MiB` is a conservative sum of candidate encoded input, decoded raster, intermediate, and output caps if all were live simultaneously: `64 + 64 + 64 + 256 MiB`, with concurrency fixed at one and queue depth zero. The decoder itself allocates one decoded output after the caller-supplied checks; encoded input remains caller-owned. This sum excludes process/runtime baseline, allocator overhead, unrelated caller-owned memory, and any global process budget, which need a runtime owner. The current profile emits no derived features and needs no intermediate raster, so the 256 MiB output and 64 MiB scratch are dormant reserves, not expected consumption.

The candidate difference operation is `O(P*C)` time and output space with `C≤4`. The P5/P6 decoder is `O(B + P*C)` time and `O(P*C)` owned output space with `C≤3`; it scans a caller-bounded header once and copies the exact raster once, with constant parser state. Neither path uses an all-pairs or quadratic term. These are design-level bounds, not target performance or production security certification; candidate ceilings remain unapproved.

## Workload and resource inputs that remain open

Only the request *shape* is proposed. The actual source class and population, consumer/task, size and aspect-ratio distribution, arrival/burst rate, concurrency needs, target hardware/runtime, acceptable latency/throughput, availability objective, and acceptance owner are unknown. Synthetic fixture profiles remain test-only and do not answer these questions. The 4096-square and other ceilings above must therefore not be called production SLOs or evidence that a real workload fits.

The real consumer/workload and target choices remain open under O-001 and O-013; resource-cap approval remains open under O-012. Exact decoder/dependency policy (O-002/O-014), source and channel compatibility (O-003–O-007), enabled feature set (O-008), uncertainty (O-010), rights/retention/reference service (O-011), test/evidence authority (O-015), production ENCODER profile (O-016), security/release sign-off (O-017), and named appointments (O-018) remain unprovided. No owner appointment or review is inferred.

## P1 status and transition gate

The proposal package now contains a versioned Markdown rationale, a machine-readable `status: proposal` profile, explicit candidate capabilities and numeric ceilings, arithmetic, complexity variables, and an open-input register. The dependency-free harness checks the JSON schema shape and cross-checks the selected size/work/output arithmetic. These checks establish only that the written proposal is internally consistent; they do not approve its values, run image code, or establish implementation safety or performance.

**Phase 2 drafting was authorized by the user's direct statement dated 2026-10-07, and P2 was later closed under the user-approved user/assistant-only review model recorded in [`../P2_REVIEW_RECORD.md`](../P2_REVIEW_RECORD.md).** D-015 separately records the bounded P5/P6 Phase 4 engineering scope and the requirement to wait for user review before Phase 5. This proposal remains advisory and retains `status: proposal`; no workload data or production choices are inferred, and production/API/deployment gates remain separate.
