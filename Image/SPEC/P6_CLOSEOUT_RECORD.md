# Phase 6 closeout record

D-017 explicitly authorized starting and finishing only the bounded Phase 6 forward-difference baseline. That engineering work is complete; Phase 7 has **not** started and remains gated on explicit user approval.

## Implemented contract

`forward-difference-xy-v1` accepts a P5 identity-canonical, tightly packed HWC `uint8` view in GRAY, RGB or RGBA order. For every channel, it computes exactly:

```text
Dx[y,x,c] = X[y,min(x+1,W-1),c] - X[y,x,c]
Dy[y,x,c] = X[min(y+1,H-1),x,c] - X[y,x,c]
```

The result has exactly two `[H,W,C]` HWC `int16` planes, retaining input channel order and identity pixel mapping. Values lie in `[-255,255]`; replicated terminal edges make the final column of `Dx` and final row of `Dy` zero. One-row, one-column and 1×1 rasters are defined by the same equations.

All count/byte arithmetic is checked before allocation. The caller must provide finite limits for pixels, channels, total output elements, output bytes and work units. Output elements and declared work are each exactly `2*P*C`, output bytes are `2*P*C*sizeof(int16)`, and traversal is `O(P*C)`. The only auxiliary scratch state is bounded scalar/row-index state beyond the two output arrays. Unsupported channel/type/layout metadata, malformed input, invalid limits, overflow, exceeded limits, cancellation or deadline return a typed failure with both output planes empty; no partial result is published.

## Verification

The exact C++20 tests use independent literal expected values for constant, impulse, horizontal and vertical ramps, checkerboard, RGB and RGBA channel ordering, a fixed xorshift32-seeded RGB byte vector, degenerate dimensions, and deterministic replay. Boundary tests exercise each caller limit, invalid zero limits, unsupported metadata, arithmetic overflow, cancellation and expired deadlines.

The suite passed **13/13 cases** in both the strict-warning normal build and the AddressSanitizer/UndefinedBehaviorSanitizer build. Build flags include `-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow -Werror`; the implementation uses only C++20 standard-library facilities. Machine-readable results and hashes are recorded in [`harness/results/latest.p6.run_evidence.json`](harness/results/latest.p6.run_evidence.json). The full package-check result is recorded outside the repository by the standard checker command documented in [`README.md`](README.md).

The P6 contract, independent fixtures, catalog bindings and evidence schema are cross-checked by the package checker. P4/P5 source files and their historical run artifacts remain unchanged; the checker accepts those prior-commit artifacts only while their recorded source/profile hashes still match.

## Proposal boundary and next gate

The profile at [`profiles/general_still_image.proposal.json`](profiles/general_still_image.proposal.json) remains `status: proposal`, and `features.enabled` remains empty. The candidate allowlist authorizes this engineering implementation and its tests only; it is not runtime/profile enablement, production approval, a deployment decision or a performance claim.

No pyramid, region, patch, mask, token ID, learning, semantic-recognition, observation/publication behavior, ACT reverse rendering or Phase 7 work is included. Production limits, workload validation, owners, target approval, security/release approval and broader image support remain open. Stop here and wait for explicit user approval before Phase 7.
