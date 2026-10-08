# P8 Single-Flight Still-Request Runtime

**Version:** `single-flight-still-request-v1`

**Status:** Bounded C++20 engineering slice verified under D-019; general profile remains `proposal`.

**Authority:** [`../DECISIONS.md`](../DECISIONS.md), [`single_flight_runtime_v1.contract.json`](single_flight_runtime_v1.contract.json)

## Scope

P8 supplies request-control/lifecycle plumbing only. It does not decode, transform, analyze, or publish image bytes. Limits are caller-supplied per `Runtime` and are constrained by the current proposal values:

| Control | Candidate ceiling | Runtime behavior |
|---|---:|---|
| Active requests | 1 | Exactly one request lease may be active |
| Queue depth | 0 | No internal request queue or capacity wait |
| Deadline | 10,000 ms | Effective deadline is the earlier of the configured duration and optional caller deadline |
| Diagnostic bytes | 1,024 bytes | No diagnostic strings are emitted; snapshot reports zero bytes |

These are proposal-derived engineering test bounds, **not** production defaults, target limits, or SLOs. Invalid concurrency/queue/deadline shapes return `INVALID_LIMITS`; values beyond the approved candidate ceilings return `RESOURCE_LIMIT`.

## API and lifecycle

- `Runtime::try_begin_request()` never waits for capacity. If a request is already active, it returns `BACKPRESSURE` immediately; no request or image payload is queued or silently accepted.
- A successful `RequestLease` carries a `std::stop_token` and absolute `steady_clock` deadline as the existing P4 `AdmissionControl`. The exact same deadline/cancellation control can therefore be used at P4–P7 safe boundaries.
- `CancellationHandle::request_cancel()` cooperatively requests stop only while its lease is active. A cancellation racing after finalization is ignored. If cancellation linearizes before `finish()`, completion reports `CANCELLED`; otherwise an expired lease reports `DEADLINE_EXCEEDED`.
- Finishing a lease or letting its RAII destructor run releases the active slot and wakes a closer. `close(drain)` stops new admission and waits. `close(cancel_active_and_drain)` first requests cooperative stop, then waits for lease completion.
- Close is terminal and idempotent. A new runtime instance is the reopen mechanism. The runtime destructor requests stop without blocking; shared request-control state remains valid until any outstanding lease finalizes.

The caller must use `close()` only from a control thread that is not responsible for finishing the active lease. Cancellation is cooperative, not preemptive; an active component must reach its existing safe boundary and finalize its lease for a cancel-and-drain call to return.

## Privacy and resource bounds

`Runtime::snapshot()` returns a by-value, fixed-field aggregate: accepting/active flags and saturating lifecycle counters. It contains no request ID, label, path, image bytes, pixel values, caller text, or mutable handle. There is no external telemetry sink, logging callback, or diagnostic text buffer. Reading a snapshot does not alter admission or completion outcomes.

Admission and control-state work are O(1). The runtime retains at most one constant-size request-control object, and has no queue or image-payload buffer. P4–P7 retain their independent byte/work/resource validation and receive the effective request control. This is not a measurement of whole-process peak memory or any named target workload.

## Explicit non-goals

- No frame transport, animation, multipage input, timestamp/order/reorder/gap policy, or temporal algorithm is enabled. The proposal profile continues to reject animation.
- No duplicate detection, persistent request identity, idempotency cache, automatic retry, observation assembly/publication, or telemetry sink is introduced. An active repeat submission is simply `BACKPRESSURE`; a later call is a new request. Publication retry semantics require a later owner-approved contract.
- No uncertainty, semantic inference, production profile activation, production SLO, workload/resource certification, Cortex change, or Phase 9 implementation is claimed.

## Verification

From repository root:

```sh
python3 Image/SPEC/harness/p8/run_p8.py
```

The runner uses strict C++20 warning flags and produces normal plus ASan/UBSan results. Twelve tests cover candidate ceilings, effective deadlines, immediate zero-queue backpressure, a 16-caller burst with exactly one admission, P4 cancellation/deadline propagation, drain/cancel-and-drain, terminal close/reopen, destructor cancellation/lifetime, and privacy-safe snapshot behavior. Results remain separate in [`../harness/results/latest.p8.run_evidence.json`](../harness/results/latest.p8.run_evidence.json); case bindings are separate so P4–P7 catalog/evidence inputs are preserved.
