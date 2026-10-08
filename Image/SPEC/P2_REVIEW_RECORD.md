# Phase 2 Review and Closeout Record

**Date:** 2026-10-07<br>
**Decision:** P2 closed under the user-approved two-party review model<br>
**Decision record:** [`DECISIONS.md`](DECISIONS.md), D-013<br>
**Reviewed worktree base:** `d3907ca079ed15a3a50a9cabc01ca4b7febd0257`, with the local `Image/SPEC/` work in progress

## Review parties and approval

The user directed that the P2 review parties are the user/project owner and assistant only, that outside-review requirements must not block the phase, and that P2 should be completed. The user approved that review model and authorized completion. The assistant carried out the consistency and adversarial review recorded below.

This records the user's approval of the review-party model and completion process. It does **not** claim that the user manually inspected or approved each field, that an external reviewer participated, or that unprovided organizational appointments were made.

## Review performed

The assistant checked the observation, profile, and error schemas against the field catalog, runtime invariants, error catalog, compatibility policy, and synthetic fixtures. The adversarial pass covered exact-version and unknown-field rejection, evidence/reference presence, payload byte length and digest, transform-chain continuity and mapping requirements, profile/uncertainty binding, error atomicity/retry rules, and the proposal/fixture status boundary.

Substantive defects corrected during this review:

1. The observation schema could accept an empty `features.items` array as its only evidence. The evidence branch now requires at least one feature item; the observation schema is versioned as `0.3.1-draft`, and both profile bindings and the fixture are updated.
2. The checker accepted duplicate JSON object member names and exponent-overflow numbers that parse to infinity. Its strict loader now rejects both, with direct negative probes.
3. Cross-field checks now reject proposal-profile activation, unapproved emitted features, missing affine/nonlinear mapping data, inconsistent identity transforms, non-finite inverse matrices, spatial quality indicators without a region reference, and spatial uncertainty without alignment/transform identities.
4. Contradictory disabled-animation/accepting-policy and non-compositing/alpha-background profile combinations now reject.
5. The documented checker option for an output directory outside the repository crashed while writing evidence references. Paths are now recorded relative to the repository root and the external-directory invocation succeeds.

The runtime contract also makes explicit that enabled features are an allowlist, not a requirement that every enabled output appear in every observation. Visual-token emission remains rejected by the current profile contract until a separately versioned profile-authorization mechanism exists.

## Verification and outcome

The dependency-free checker completed with **12 passed, 0 failed**. This run checked the current schema structures and local references, fixture and proposal profiles, the synthetic observation/error and payload records, cross-field invariants and negative probes, error-catalog/schema equality, analytic fixture arithmetic, catalog traceability, local Markdown links, and the harness's declared dependency scope. It also succeeded with `--output-dir /tmp/p2-check-probe`, outside the repository.

The checker reports **66 future component cases** as defined or blocked, not executed. No Image VISION component was built or tested, and no production dependency graph or binary audit was performed. At P2 closeout, per-run evidence was written to `harness/results/latest.run_evidence.json`, `latest.raw.json`, and `latest.dependency_audit.json`; these mutable `latest.*` paths now contain the later Phase 3 run, while the **12 passed, 0 failed** count above remains the historical P2 result.

## P2 disposition and boundaries

P2's draft schemas, field catalog, runtime invariants, stable errors, compatibility policy, test-only examples, and package-level checks are complete and reviewed for specification consistency under D-013. No outside reviewer is required to close P2.

The schemas remain drafts and are not a production API approval. `general_still_image.proposal.json` remains `status: proposal`. No production profile, workload, numeric limit, codec, retention service, dependency, security decision, or release authority is approved here. No image component code or Cortex file was changed, and production readiness is not claimed. At P2 closeout P3 had not started; it was subsequently started under the user's separate direction.
