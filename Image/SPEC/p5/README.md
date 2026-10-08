# Phase 5: identity canonical raster view and geometry

**Status:** The bounded D-016 identity-only engineering slice is implemented and verified. The general still-image profile remains `status: proposal`; this is not production approval or user code acceptance. Phase 6 and the future signal-to-image reverse renderer have not started.

## Implemented behavior

`canonical_raster.hpp` and `.cpp` expose `canonicalize_identity(...)` for an already-admitted P4 read-only raster view. Accepted data are tightly packed HWC `uint8` with declared GRAY, RGB, or RGBA channel order. On success, the canonical result is a **zero-copy view of the same immutable bytes**: every sample, channel position, and RGBA alpha value is preserved exactly. The result names the corresponding `GRAY_U8`, `RGB_U8`, or `RGBA_U8` pixel format and records equal source/output width and height.

The result contains a versioned `identity-v1` source-to-target transform, explicit row-major 3×3 identity matrix and inverse, and `invertible=true`. Coordinates use an upper-left origin, x right/y down, with pixel centers at `(column + 0.5, row + 0.5)`. Coordinate mapping accepts the closed continuous pixel-center extent `[0.5, width-0.5] × [0.5, height-0.5]`; one-pixel and single-axis dimensions are well-defined. Since the mapping representation is binary64, dimensions above `2^52` are rejected so every half-integer pixel center remains exactly representable. Values outside the extent and malformed/non-identity transform records reject.

The selected color-profile identifier is `source-declared-or-unknown-v1`; no color space or transfer function is inferred. The source orientation is treated as already decoded; no metadata is inferred or applied. Alpha is preserved when present and is not composited, dropped, or synthesized. Raster samples borrow the P4 view's backing buffer; transform/frame/color identifier strings borrow the request's backing storage. The caller keeps both storage areas alive and immutable for the complete use of the canonical result.

## Fail-closed exclusions

Color/transfer conversion or inference, grayscale/palette conversion, channel reorder, orientation application/inference, alpha compositing/dropping, resize, crop, pad, planar/strided layouts, and unknown channel orders are not enabled. Such policy requests, malformed identifiers, empty/invalid views, impossible arithmetic, and caller-limit failures return a typed error with an empty result. No allocation, pixel scan, sample write, observation assembly, payload-reference resolution, or publication path is introduced.

## Bounds and dependencies

For already-admitted raster dimensions `W`, `H`, and bounded `C ∈ {1,3,4}`, P5 performs checked `P=W×H` and `S=P×C` arithmetic and bounded metadata validation. It does not iterate over pixels or channels: time and auxiliary space are `O(1)` with respect to raster size, and the returned view aliases `S` input bytes rather than allocating output. The explicit metadata work count is one. The caller supplies finite width, height, pixel, output-byte, and work limits on every call; proposal values are not runtime defaults. The implementation uses C++20 standard-library facilities only, without a math library, codec, ML framework, or external dependency.

## Tests and evidence

From the repository root:

```sh
python3 Image/SPEC/harness/p5/run_p5.py
python3 -I Image/SPEC/harness/check_spec.py
```

The P5 runner uses strict C++20 warnings as errors and records normal and AddressSanitizer/UndefinedBehaviorSanitizer outcomes in [`../harness/results/latest.p5.run_evidence.json`](../harness/results/latest.p5.run_evidence.json). Ten test IDs are bound to catalog cases: exact literal byte oracles for 1×1 GRAY, 1×N RGBA, N×1 RGB, odd GRAY/RGB/RGBA; exact alpha preservation; dimensions/matrices/inverses and pixel-center mapping at corners/centers/degenerate extents; fail-closed disabled policies and malformed metadata; resource limits; and overflowing input rejection. The package checker verifies evidence hashes, exact test/catalog bindings, phase boundaries, and both build outcomes; it does not execute C++.

## Limits

The evidence is for this bounded engineering slice only. Proposal ceilings are explicit test inputs, not production limits. No approved target/workload, named owner, production color/orientation/alpha/geometry policy, security/release approval, or production profile is claimed. See [`../P5_CLOSEOUT_RECORD.md`](../P5_CLOSEOUT_RECORD.md) and [`../DECISIONS.md`](../DECISIONS.md).
