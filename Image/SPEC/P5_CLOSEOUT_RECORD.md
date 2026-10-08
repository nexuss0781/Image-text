# Phase 5 Closeout Record — Identity Canonical Raster View

**Decision:** D-016
**Status:** Bounded identity-only engineering slice complete; profile remains proposal-only.
**Scope:** Phase 5 canonical raster identity view and pixel-center identity transform only.
**Next phase:** Phase 6 has not started and requires explicit user approval.

## Authorization and boundary

After the Phase 4 report, the user explicitly authorized Phase 5 (“good finish phase 5 fastly”; D-016). The task boundary was the current proposal's enabled behavior: identity geometry; declared/unknown source color with no conversion; preserve source channel order and alpha; and do not infer metadata. The authorization did not approve a production profile, runtime, resource limit, owner decision, deployment, or Phase 6.

The work is limited to a dependency-free C++20 API taking an already-admitted P4 raster view and returning either a non-owning canonical view with exact original bytes or a typed fail-closed result. The canonical view supports HWC uint8 GRAY, RGB, and RGBA only. Dimensions are unchanged; the transform record explicitly binds source and target frame identifiers/dimensions and carries a row-major 3×3 identity matrix and inverse under the upper-left-origin x-right/y-down pixel-center convention. RGBA alpha is retained byte-for-byte. The transform helper accepts only coordinates in the closed pixel-center extent and handles degenerate dimensions; dimensions above `2^52` reject so all half-integer centers remain exactly representable in binary64. Sample bytes borrow the P4 view, and frame/color strings borrow the request; the caller must keep both backing stores alive and immutable while using the result.

All non-identity geometry; color/transfer conversion or inference; channel reorder; grayscale/palette conversion; orientation application or inference; alpha compositing, dropping, or synthesis; and other layouts are disabled and reject. There is no image allocation, pixel scan, output write, observation, or publication API. The profile JSON remains `status: proposal`.

## Verification

The P5 runner compiles both the P4 admission dependency and P5 implementation/tests with C++20, `-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Werror`, runs normal and ASan/UBSan builds, and audits host dynamic links. Exact output bytes are compared with independent literal oracles. Ten cases cover:

1. 1×1 grayscale exact sample and format.
2. 1×N RGBA exact RGB and alpha bytes, including transparent/partial/opaque values.
3. N×1 RGB exact values.
4. Odd 3×5 grayscale values.
5. Odd 3×3 RGB values.
6. Odd 2×3 RGBA values and alpha.
7. Equal source/output dimensions, exact forward and inverse identity matrices, corners/centers, and 1×1, 1×N, N×1 coordinate bounds.
8. Rejection of conversion/inference, channel reorder, orientation application, alpha dropping, and resize.
9. Rejection of insufficient limits, invalid declarations, and an empty source view.
10. Overflowing input dimensions rejected at P4 admission before a P5 view can be produced.

**Recorded result:** 10/10 cases pass in the normal strict-warning build and 10/10 pass under AddressSanitizer and UndefinedBehaviorSanitizer. The standard-library package checker validates the P5 evidence, current profile/source hashes, catalog bindings, phase scope, and P4/P5 artifacts separately; it does not rerun C++ tests. Exact run metadata is in [`harness/results/latest.p5.run_evidence.json`](harness/results/latest.p5.run_evidence.json).

## Complexity, resource and dependency statement

For raster dimensions `W×H` and channel count `C∈{1,3,4}`, checked arithmetic verifies `P=W×H` and `S=P×C`, exact admitted sample-span length, host representation and explicit caller ceilings. Pixel data are not visited; the canonical result is an aliasing view. Time and auxiliary space are `O(1)` in image size, plus no image-scaled output allocation. Identifier checks are bounded by the contract's 128-byte maximum. One metadata work unit is explicitly preflighted. No external dependency, ML framework, codec, or math library is used.

## Non-claims and remaining gates

This closeout does not promote the candidate profile or its limits; approve a production target, workload, color/transfer/orientation/alpha policy, or owner appointment; certify a production binary/security posture; enable transformations or unsupported layouts; or establish image understanding, semantic capability, or AGI. External owner, security, privacy, data, release, runtime, and production integration inputs remain open where applicable. The result is not a user code-acceptance signature.

**Stop condition:** Do not begin Phase 6 or the future signal-to-image reverse renderer until the user explicitly approves that next transition.
