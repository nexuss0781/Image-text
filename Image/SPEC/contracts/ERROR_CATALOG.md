# Image VISION Error Catalog

**Status:** P2 consistency/adversarial review is complete under the two-party model in [`../P2_REVIEW_RECORD.md`](../P2_REVIEW_RECORD.md). This catalog remains a draft; it is not production API, security, privacy, or release approval. The schema is [`image_error.schema.json`](image_error.schema.json).

Every failure returns one `image_vision_error` envelope with the exact supported `error_version`, the request and trace identities, `component: VISION_IMAGE`, the selected profile identity, a stable `code`, a bounded safe message, `retryable`, and `state_changed: false`. The code identifies the failure class; callers must not parse the message for control flow. No error publishes an observation or leaves persistent state changed. Request-local scratch is discarded before return.

## Stable codes and default handling

| Code | Meaning and use | Retry policy |
|---|---|---|
| `INVALID_DESCRIPTOR` | Required input metadata is absent, malformed, internally inconsistent, or violates the declared layout/stride contract. | Never retry the unchanged request. |
| `UNSUPPORTED_FORMAT` | The declared or detected format/layout is not enabled by the selected profile. | Never retry unchanged; select a separately enabled profile or change the input. |
| `CORRUPT_PAYLOAD` | Bytes are truncated, malformed, or fail the enabled parser/decoder's validity checks. | Never retry the same immutable bytes. |
| `RESOURCE_LIMIT` | Checked dimensions, bytes, elements, work, concurrency, diagnostics, or other declared budget cannot be met. Arithmetic overflow is rejected as this code or `INVALID_DESCRIPTOR` according to the violated contract. | Never retry unchanged under the same profile and budget. |
| `PROFILE_MISMATCH` | A record, operation, capability, or value contradicts the selected profile or its registered version. | Never retry unchanged. |
| `NONFINITE_INPUT` | A numeric input or computed value is NaN or infinite, or a required finite-value check fails. | Never retry the same payload and profile. |
| `TRANSFORM_FAILURE` | A declared transform cannot be applied or its matrix, chain, domain, dimensions, or coordinate mapping is invalid. | Never retry unchanged. |
| `FEATURE_FAILURE` | An enabled deterministic feature operation fails its own checked contract. | Never retry unchanged; do not publish partial features. |
| `TOKENIZER_FAILURE` | A separately approved token producer fails. Token output is disabled unless a distinct profile and vocabulary are approved. | Never retry unchanged. If token output is disabled, report `PROFILE_MISMATCH` instead. |
| `UNCERTAINTY_UNAVAILABLE` | The profile requires uncertainty but neither an approved fallback nor a valid calibrated method is available. | Never retry unchanged unless an authorized configuration changes. |
| `REFERENCE_INVALID` | A payload reference is missing, mutable, unauthorized, expired under its declared retention, or has mismatched identity, length, checksum, shape, type, or content kind. | Never retry the same invalid reference. |
| `CANCELLED` | The caller cancelled before atomic publication completed. | Not retryable as the same request; a new caller-authorized request may be submitted. |
| `DEADLINE_EXCEEDED` | The request's declared deadline elapsed before completion. | Not retryable as the same request. A new request may use a separately authorized budget. |
| `BACKPRESSURE` | The finite active-request or queue limit prevents admission. No accepted image is silently dropped. | May be retryable only when `retryable=true`; supply `retry_after_ms` when known and honor idempotency. |
| `DEPENDENCY_UNAVAILABLE` | An approved external reference/dependency service is temporarily unavailable, not that the referenced object is invalid. | May be retryable only for a positively identified transient outage; supply `retry_after_ms` when known. |
| `UNSUPPORTED_VERSION` | The exact schema, profile, or contract version requested is not supported or cannot be negotiated. | Never retry unchanged; negotiate a supported exact version. |
| `INTERNAL_ERROR` | An unexpected failure that cannot be safely classified without disclosing implementation details. | Not retryable by default. |

The table is normative for stable category and default retry behavior. A future change to meanings or retryability changes the error contract and requires compatibility review. A transient retry is not permission to change payload, profile, limits, or semantics under the same request identity.

## Envelope and message rules

- `error_version` is exactly `0.2.0-draft` for this draft. Unsupported versions are rejected explicitly; there is no silent interpretation as the current version.
- `request_id`, `trace_id`, `profile_id`, and any supplied `profile_version` must match the failed request. `stage_id` may identify a bounded registered stage ID; it must not contain a path or raw caller text.
- `message` is non-empty and at most 512 UTF-8 bytes at runtime. It is a short fixed or allowlisted description. It must not echo pixels, encoded content, local paths, access tokens, private labels, or unbounded input text. JSON Schema's character limit is not a substitute for the byte limit.
- `retry_after_ms` is present only on a retryable transient error and is a finite nonnegative integer. If it is absent, callers use their own bounded retry policy; they do not infer a delay from `message`.
- `state_changed` is always `false`. This covers persistent state and published observations, not merely model weights. A failed request returns no observation, feature set, token set, or partial payload publication.
- Only `BACKPRESSURE` and transient `DEPENDENCY_UNAVAILABLE` may use `retryable: true` in this draft. All other codes use `false`. Retries must preserve the idempotency key, payload identity/checksum, and selected profile version; attempt counts and delay remain bounded by the caller/runtime contract.

## Ownership and open decisions

The schema and this catalog define draft wire meanings, not an appointed operational owner. No individual operational owner, message template registry, retry timing, dependency inventory, or production profile was supplied. Those choices remain open for any later production API freeze or release gate that depends on them; they do not block P2 specification closeout. The currently available example is synthetic and test-only: [`examples/image_error.fixture.json`](examples/image_error.fixture.json).
