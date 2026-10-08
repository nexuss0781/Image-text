# Image VISION Contract Compatibility Policy

**Status:** P2 consistency review is complete under the user-approved two-party model in [`../P2_REVIEW_RECORD.md`](../P2_REVIEW_RECORD.md). This policy remains a draft; role-specific production/API-freeze approval is a later gate. It covers observation, profile, error, transform, payload-reference, and uncertainty contracts and does not approve a production profile or authorize implementation.

## Exact-version parsing and unknown fields

Each record declares its schema or error version, and each profile binds the exact profile, observation, and error schema versions it was authored against. A producer may emit a record only for a version explicitly supported by the receiving contract. A receiver accepts only explicitly supported versions; it does not assume that a higher or lower version is compatible. A version mismatch returns `UNSUPPORTED_VERSION` (or `PROFILE_MISMATCH` when the version itself is supported but the record contradicts the selected profile).

Unknown fields are rejected at every object boundary (`additionalProperties: false`). Unknown enum values, content kinds, codes, transform operators, profile capabilities, and payload schemes are rejected. Readers must not ignore unknown fields, map them to a default, or silently discard them. This intentionally favors detectable incompatibility over accidental semantic change.

## Draft and post-freeze versioning

The current schemas are marked `-draft`; they are work products under review and provide no production compatibility guarantee. Before API freeze, any material change may produce a new draft version, and dependent examples, profiles, hashes, and conformance checks must be updated together.

After a reviewed freeze, use `MAJOR.MINOR.PATCH` for each independently versioned contract:

- **PATCH** is limited to editorial metadata or a validator correction that does not change accepted wire records, field meaning, numeric interpretation, error behavior, or security/privacy obligations.
- **MINOR** may add optional fields or new capability values only after an explicit compatibility review and capability negotiation. Because strict readers reject unknown fields and enum values, a minor version is not automatically safe for an older reader; the receiver must explicitly support that exact version/capability set.
- **MAJOR** is required for field removal or renaming, requiredness/type/shape/unit/range changes, enum removals or changed meaning, transform direction/coordinate changes, payload identity/integrity changes, uncertainty convention or target semantics changes, error-code/retry behavior changes, or any weakening of rejection/atomicity/privacy rules.

No implicit migration, lossy conversion, default insertion, shape repair, field dropping, or version downgrade is performed. A migration is a separately named and versioned adapter with input/output versions, deterministic rules, explicit failure mappings, and compatibility tests. It may not change image values, coordinates, uncertainty, or ownership without an explicitly approved migration contract.

## Profile identity and change control

A profile is identified by `(profile_id, profile_version)` and an exact content hash in its approval record. That identity/version pair is immutable. Changing enabled formats, layouts, channels, canonicalization, geometry, feature operators, resource limits, uncertainty mode, retention/access behavior, implementation restrictions, or complexity declarations creates a new profile version and reruns every affected gate. A profile's `contract_versions` are exact bindings, not a range.

`status: proposal` remains advisory and cannot be activated. `status: fixture_only` is test-only. `status: approved` is syntactic evidence only unless a separate authorization record is resolvable and binds the exact profile bytes/hash, named approving authorities, date, workload/target scope, decisions and permitted capability set. The JSON field `approval_record_id` points to that evidence; it does not replace it. No owner or production value is inferred from a schema-valid record.

A schema or profile hash mismatch, expired/revoked approval, or unknown profile version rejects before processing. Consumers pin versions; they do not follow a mutable `latest` alias. Rollback means explicitly selecting a previously approved immutable version, never mutating the old profile in place.

## Ownership and later production approvals

P2 specification completion does not require outside reviewers. Before a production API freeze or release, schema semantics affecting downstream behavior, payload access/retention, security/privacy, error exposure, version allowlists, and migrations still require whatever decisions and authority the relevant production gate calls for. These are role requirements, not appointments; no named person or team is recorded here. They do not reopen the P2 closeout.

The compatibility policy itself is a draft decision. Its approval, named roles, exact supported-version registry, deprecation window, migration service, and production signing/verification mechanism remain unresolved. Test-only records are in [`examples/`](examples/); they do not demonstrate compatibility of an implementation.
