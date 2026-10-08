# Phase 2 Contract Examples

These records are synthetic, test-only examples for schema and cross-field conformance. They are not production data, an owner-approved profile, an implementation result, or a compatibility promise.

- [`image_observation.fixture.json`](image_observation.fixture.json) exercises an identity transform, typed immutable pixel/uncertainty references, quality metadata, and the ENCODER uncertainty convention. Its associated bytes and digests are in [`payload_fixtures.json`](payload_fixtures.json).
- [`image_error.fixture.json`](image_error.fixture.json) exercises the stable error envelope and `state_changed: false`.
- [`../../profiles/fixture_profile.example.json`](../../profiles/fixture_profile.example.json) is explicitly `fixture_only`. The separate general still-image profile remains `proposal`.

`fixture` scheme references resolve only inside the synthetic payload fixture set. They do not represent a production blob store, access policy, retention authority, or decoder.
