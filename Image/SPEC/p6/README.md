# Phase 6 — Deterministic Forward-Difference Baseline

**Contract:** [`forward_difference_xy_v1.contract.json`](forward_difference_xy_v1.contract.json) (`1.0.0-engineering-proposal`)<br>
**Implementation:** [`forward_difference.hpp`](forward_difference.hpp), [`forward_difference.cpp`](forward_difference.cpp)<br>
**Tests/evidence:** [`../harness/p6/test_forward_difference.cpp`](../harness/p6/test_forward_difference.cpp), [`../harness/results/latest.p6.run_evidence.json`](../harness/results/latest.p6.run_evidence.json)<br>
**Status:** bounded Phase 6 engineering baseline complete; candidate is not production-enabled.

## Versioned mathematical contract

For canonical tightly packed HWC `uint8` input `X` with dimensions `H×W×C`, `C∈{1,3,4}`:

```text
Dx[y,x,c] = X[y,min(x+1,W-1),c] - X[y,x,c]
Dy[y,x,c] = X[min(y+1,H-1),x,c] - X[y,x,c]
```

The operator returns exactly two `H×W×C` HWC planes, in Dx-then-Dy order, with signed `int16` values in `[-255,255]`. Subtraction is neighbor minus current; each channel is independent and channel order is preserved. The output index `(y,x,c)` maps to the same canonical-input pixel/channel index, and the P5 identity transform is retained. Edge replication makes the terminal column of Dx and terminal row of Dy zero. A one-row input has all-zero Dy; a one-column input has all-zero Dx; a 1×1 input yields one zero in each plane.

The implementation computes each pair in one pass. Checked preflight arithmetic derives `P=W*H`, `S=P*C`, output elements `2*S`, output bytes `2*S*sizeof(int16)`, and work units `2*S`; each is compared with an explicit caller-supplied limit before allocation. One work unit means one directional result (including a replicated-edge zero). The loops are O(P*C), and auxiliary scratch is O(1); total owned output is exactly two O(P*C) vectors. C++20 `AdmissionControl` cancellation and deadlines are checked before allocation, during traversal, and before success. Failure results contain neither plane.

Only the existing P5 identity-canonical HWC uint8 GRAY/RGB/RGBA view is accepted. There are no implicit conversions, other sample types, other layouts, or other channel orders. This is a deterministic low-level spatial evidence candidate, not a semantic feature.

## Engineering proposal and activation status

The implementation allowlist for this Phase 6 engineering slice contains only `candidate_forward_difference_xy_v1`. The general still-image profile remains `status: proposal`, and `features.enabled` remains empty. The implementation/test allowlist is not a production runtime allowlist, profile approval, API freeze, or deployment authorization. Candidate limits remain proposal/test values.

No pyramid, region, patch, mask, token ID, learning, semantic recognition, ACT reverse rendering, quality/uncertainty behavior, observation assembly, publication, ENCODER handoff, or Phase 7 work is included. No Cortex file is changed. Production workload/target, owner approvals, resource ceilings, security/privacy/release review, and production feature enablement remain open.
