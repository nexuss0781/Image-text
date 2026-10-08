# Image VISION Requirements Traceability

**Version:** `0.1.0-draft`
**Purpose:** map inherited and new requirements to normative documents, machine contracts, harness cases and release evidence. IDs are stable within this packet; additions require unique IDs.

## Requirement map

| ID | Requirement | Source / authority | Specification location | Contract or harness evidence | Release evidence |
|---|---|---|---|---|---|
| IV-001 | Accept only explicitly declared and profile-enabled image inputs; validate before allocation. | Parent VISION §6.4, legacy image input draft, current scope | `PROJECT.md` §§3,5,9; P4 | `image_profile.schema.json`; `ADM-*`, `DEC-*` cases | Format matrix, overflow/bounds report |
| IV-002 | Preserve source identity and supplied time/frame metadata; never invent capture time. | Parent VISION §§4,7; observation draft | `PROJECT.md` §§5,7–9; P8/P9 | `image_observation.schema.json`; `SRC-*` cases | Provenance and ordering integration report |
| IV-003 | Make channel, range, color/transfer, alpha and orientation policies explicit. | Parent VISION P4; prior preprocessing draft | `PROJECT.md` §5; P1/P5 | Profile schema; `PIX-*`, `GEO-*` cases | Golden numeric vectors and transform audit |
| IV-004 | Record geometry transforms and coordinate frames for every spatial payload. | Parent VISION §6.4; prior feature/observation drafts | `PROJECT.md` §§5–7; P5/P6/P9 | Observation schema transform fields; `GEO-*` cases | Coordinate mapping and non-invertible-domain report |
| IV-005 | Emit only low-level, modality-honest features unless semantic capability is separately approved. | Parent VISION §§1,6; integration boundary | `PROJECT.md` §§3,6,10; P6/P13 | Feature descriptors; `FEAT-*` cases | Operator contract and claim review |
| IV-006 | Reject malformed, unsupported, non-finite, overflowing and over-budget inputs with typed errors; no partial observation. | Parent VISION P7; prior quality/failure draft | `PROJECT.md` §§8–9; P4/P7/P9 | Error catalog; `ERR-*`, `ATOMIC-*`; P7 failure/error contract and injected/boundary tests | Failure injection and resource report; P7 run artifact |
| IV-007 | Keep quality indicators distinct from calibrated uncertainty; preserve `[0,1]`, `0=highest confidence`, `1=highest uncertainty` for uncertainty only. | Approved Encoder contract §51; prior uncertainty draft | `PROJECT.md` §8; P7/P10 | Observation schema; `QUAL-*`, `UNC-*`; P7 descriptive metric/disabled uncertainty contract | Calibration report or approved fallback record remains open; P7 evidence proves omission/unavailable behavior only |
| IV-008 | Ensure all computation is subquadratic for input-scaled counts; specify variables and bounds. | Current user direction | `PROJECT.md` §4; all phase definitions | Profile complexity fields; `COMP-*` cases | Operation proofs, work-scaling results |
| IV-009 | Prohibit ML libraries/frameworks, including transitive harness/runtime dependencies. | Current user direction | `PROJECT.md` §4; P11/P12/P13 | Profile policy field; `DEP-*` cases | Dependency manifest + binary/link audit |
| IV-010 | Use C++/Assembly and an audited math-library boundary; optimized Assembly follows the same contract/reference. | Current user direction | `PROJECT.md` §4; P12 | Build/evidence manifest; `NATIVE-*` cases | Toolchain, ABI, parity and fallback dossier |
| IV-011 | Bound memory, work, queue and telemetry; use explicit backpressure and cancellation. | Parent VISION P1/P8/§12; prior stream draft | `PROJECT.md` §9; P1/P8/P11 | Profile schema; `RES-*`, `STR-*`, `TEL-*` cases | Named workload resource report |
| IV-012 | Telemetry is read-only and excludes private pixels/content/paths by default. | Parent VISION P8; prior telemetry draft | `PROJECT.md` §§8–9; P8 | Harness privacy tests | Telemetry inspection and sink-failure report |
| IV-013 | Image VISION emits observations only; ENCODER owns embedding, alignment, mask and numeric tensor assembly. | Approved `ENCODER_TENSOR_CONTRACT_PROPOSAL.md` §§18,43–53,83–89 | `PROJECT.md` §7; P10 | `ENC-*` cases and observation schema | Integration report; no direct M2 call |
| IV-014 | Cortex receives only approved finite `X[B,S,F_in]` and aligned sidecar; this work does not change Cortex. | Approved Encoder↔Cortex structure | `PROJECT.md` §§3,7,11; P10 | `ENC-*` cases | Diff/audit confirms no Cortex change |
| IV-015 | Do not claim image understanding/AGI from schema, features, synthetic fixtures, or speed tests. | Parent VISION anti-definition; repository integration/evidence boundary | `PROJECT.md` §§1,3,10 | `CLAIM-*` cases / review checklist | Release claim review and task-level held-out evidence |
| IV-016 | Keep frame identity and timestamps caller-owned; no temporal model in base scope. | Parent VISION stream and prior stream draft | `PROJECT.md` §§5,9; P8/P13 | `SRC-*`, `STR-*` cases | Frame adapter contract, if enabled |
| IV-017 | Preserve unique identity, immutable payload references, producer/profile/runtime provenance. | Prior observation contract and parent VISION P5 | `PROJECT.md` §§7–8; P2/P9 | Observation schema; `REF-*`, `PROV-*` cases | Cross-field validator and integrity report |
| IV-018 | Every requirement and test status is traceable; case definition is not execution. | Current engineering request; evidence policy | `ROADMAP.md`, `PHASES.md`, `TODO.md`, `harness/HARNESS.md` | `case_catalog.json`; separate `harness/p7/case_bindings.json` reuses existing cases without changing lifecycle metadata | Raw P4/P5/P6/P7 run artifacts and reviewed gate record |
| IV-019 | P0 records only the user-approved Image-scope boundaries; unnamed owners and unprovided profile/runtime/workload choices remain open, and no component implementation is authorized. | User scope approval dated 2026-10-07 | `DECISIONS.md` P0 approval record; `PHASES.md` P0; `TODO.md` P0 closeout | Dated decision record and open-input register | Gate review confirms no owner appointment, later-phase approval, production value, or implementation is inferred |
| IV-020 | P1 proposal drafting is advisory only; candidate policies and ceilings do not resolve open production values/owner appointments, pass review gates, or authorize implementation. | User direction to start P1 and “do the best” dated 2026-10-07 | `profiles/general_still_image.proposal.md` and `.proposal.json`; harness proposal-profile checks; `DECISIONS.md` P1 status; `PHASES.md` P1; `ROADMAP.md`; `TODO.md` | Proposal document, schema-valid `status: proposal` profile, arithmetic checks, and explicit open-decision register | Appointed owners review the actual workload/target and record a versioned profile/resource decision before P1 exit or production enablement |
| IV-021 | Wire contracts bind exact versions, reject unknown fields/values, and follow an explicit compatibility/migration policy. | Phase 2 contract direction; user authorization to start P2 dated 2026-10-07 | `contracts/COMPATIBILITY_POLICY.md`; all three machine schemas; `contracts/RUNTIME_INVARIANTS.md` | `CONTRACT-*` cases; schema/package checks | Contract and release authorities accept compatibility policy and exact supported-version registry |
| IV-022 | Payload references bind immutable identity, content kind, exact bytes/checksum, numeric shape/type/layout, access, and retention. | Phase 2 payload-reference requirement; IV-017 | `contracts/image_observation.schema.json`; `contracts/OBSERVATION_FIELDS.md`; `contracts/RUNTIME_INVARIANTS.md` | `REF-*` cases; resolvable test-only payload examples | Store/data/privacy authorities review resolver, access, expiry, rights, and immutable publication semantics |
| IV-023 | Transform chains state source-to-target pixel-center mappings, dimensions, frames, invertibility, and valid domains. | Phase 2 transform requirement; IV-004 | Observation schema; `contracts/OBSERVATION_FIELDS.md`; runtime invariants | `GEO-*` cases; identity example and cross-field checker probes | Image/source/consumer authorities accept numeric mapping rules and transform evidence |
| IV-024 | Quality is method-tagged descriptive evidence; uncertainty is profile-controlled, finite, aligned, and preserved under the ENCODER convention. | Approved ENCODER contract §51; Phase 2 quality/uncertainty requirement; IV-007 | Observation/profile schemas; runtime invariants; observation field catalog; `p7/endpoint_code_fraction_v1.contract.json` | `QUAL-*`, `UNC-*`, `ENC-*`; P7 literal and controlled-change cases | Consumer/calibration and ENCODER authorities must approve target event, fallback/calibration, granularity, and sidecar semantics; P7 evidence is descriptive-only |
| IV-025 | Errors use stable catalog codes and bounded safe messages, explicit retryability, and `state_changed=false`; no failure publishes partial output. | Phase 2 error requirement; IV-006 and approved state atomicity convention | `contracts/image_error.schema.json`; `contracts/ERROR_CATALOG.md`; runtime invariants; P7 fixed-message map | `ERR-*` cases; test-only error record; P7 secret-marker and fault-injection cases | Image/runtime/security/privacy/release authorities accept production error and retry semantics |

## Phase 3 executable coverage map


Every high-level `IV-*` requirement maps to machine-readable definitions in [`harness/case_catalog.json`](harness/case_catalog.json). Runtime clause IDs follow the `RI-SS.NN` convention recorded in [`contracts/RUNTIME_INVARIANTS.md`](contracts/RUNTIME_INVARIANTS.md). Catalog lifecycle fields remain definition metadata (`not_run` or `blocked`); executed P4 admission/decode, P5 identity-view, P6 forward-difference, and P7 quality/atomicity outcomes are recorded in phase-specific run artifacts. P7 test IDs bind to existing catalog cases in a separate file so the P6 source/catalog hashes and historical result remain unchanged. D-015–D-018 record bounded engineering scopes; the profile remains proposal-only and production approval is not claimed.


### High-level requirements

| Requirement | Case definitions | Component execution state |
|---|---|---|
| `IV-001` | `ADM-001`, `ADM-002`, `ADM-003`, `ADM-004`, `ADM-005`, `ADM-006`, `DEC-001`, `DEC-002`, `DEC-003`, `DEC-004`, `PROF-001`, `PROF-002`, `PROF-003` | blocked, not_run |
| `IV-002` | `PROV-001` | not_run |
| `IV-003` | `PIX-001`, `PIX-002`, `PIX-003`, `PIX-004`, `PIX-005`, `PIX-006`, `PROF-004` | blocked, not_run |
| `IV-004` | `DIF-002`, `FEAT-002`, `GEO-001`, `GEO-002`, `GEO-003`, `GEO-004`, `GEO-005`, `GEO-006`, `SPEC-PHASE-CONTRACT-001` | blocked, not_run |
| `IV-005` | `DIF-001`, `DIF-002`, `DIF-003`, `FEAT-001`, `FEAT-002`, `FEAT-003`, `FEAT-004`, `SPEC-PHASE-CONTRACT-001` | blocked, not_run |
| `IV-006` | `ADM-002`, `ADM-003`, `ADM-004`, `ADM-007`, `DEC-002`, `DEC-003`, `DIF-004`, `DIF-005`, `ERR-001`, `ERR-002`, `ERR-003`, `ERR-004`, `FEAT-003`, `GEO-003`, `GEO-006`, `PIX-002`, `PIX-004`, `PIX-005`, `PIX-006`, `PROF-001`, `PROF-003`, `PROF-004`, `REF-001`, `REF-002`, `REF-004`, `SPEC-PHASE-CONTRACT-001`, `UNC-002` | blocked, not_run |
| `IV-007` | `QUAL-001`, `UNC-001`, `UNC-002`, `UNC-003`, `UNC-004`, `UNC-005` | blocked, not_run |
| `IV-008` | `COMP-001`, `COMP-002`, `COMP-003`, `DIF-001`, `DIF-003`, `DIF-004`, `FEAT-001`, `FEAT-004`, `NATIVE-001`, `NATIVE-002`, `PROF-005`, `RES-001`, `RES-002`, `SPEC-PHASE-CONTRACT-001` | blocked, not_run |
| `IV-009` | `DEP-001`, `DEP-002`, `PROF-005` | blocked, not_run |
| `IV-010` | `DEP-001`, `NATIVE-001`, `NATIVE-002`, `NATIVE-003` | blocked |
| `IV-011` | `ADM-006`, `ADM-007`, `COMP-002`, `DIF-005`, `ERR-003`, `NATIVE-002`, `PROF-002`, `RES-001`, `RES-002`, `RES-003`, `STR-001`, `STR-002` | blocked, not_run |
| `IV-012` | `TEL-001`, `TEL-002` | not_run |
| `IV-013` | `ENC-001`, `ENC-002`, `UNC-004` | blocked |
| `IV-014` | `ENC-001`, `ENC-002`, `ENC-003` | blocked |
| `IV-015` | `CLAIM-001`, `CLAIM-002` | blocked, not_run |
| `IV-016` | `DEC-004`, `STR-001` | blocked |
| `IV-017` | `ERR-002`, `PROV-001`, `REF-001`, `REF-002`, `REF-003` | not_run |
| `IV-018` | `SPEC-ADMISSION-001`, `SPEC-CANONICAL-001`, `SPEC-CATALOG-001`, `SPEC-SPATIAL-001` | package check only |
| `IV-019` | `SPEC-SCOPE-001` | package check only |
| `IV-020` | `CONTRACT-002` | not_run |
| `IV-021` | `CONTRACT-001`, `CONTRACT-002`, `CONTRACT-003` | not_run |
| `IV-022` | `REF-003`, `REF-004` | not_run |
| `IV-023` | `GEO-005` | not_run |
| `IV-024` | `QUAL-001`, `UNC-005` | not_run |
| `IV-025` | `CONTRACT-003`, `ERR-004` | not_run |

### P7 run bindings

The P7 runner executes `P7-TEST-001` through `P7-TEST-018`; exact mapping to the existing `QUAL-001`, `UNC-002`, `UNC-005`, `ERR-002`, `ERR-003`, and `ERR-004` definitions is in [`harness/p7/case_bindings.json`](harness/p7/case_bindings.json). The catalog's `execution_status` fields intentionally remain `not_run`/`blocked`; actual outcomes are in [`harness/results/latest.p7.run_evidence.json`](harness/results/latest.p7.run_evidence.json). P7 tests exercise the current engineering slice only and do not close the remaining calibration/production decisions in IV-007/IV-024/IV-025.

### P8 run bindings

The P8 runner executes `P8-TEST-001` through `P8-TEST-012`; exact mapping to the existing `ADM-007`, `RES-001`, `RES-003`, `STR-002`, and `TEL-001` definitions is in [`harness/p8/case_bindings.json`](harness/p8/case_bindings.json). The catalog's `execution_status` fields intentionally remain `not_run`/`blocked`; actual outcomes are in [`harness/results/latest.p8.run_evidence.json`](harness/results/latest.p8.run_evidence.json). The bindings cover only the tested single-flight admission/lifecycle subcases, not the broader frame-ordering, duplicate-publication retry, external-sink or named-workload requirements. Those boundaries remain open.

### Runtime invariant clauses


| Invariant | Case definitions | Execution state |
|---|---|---|
| `RI-01.01` | `CONTRACT-001`, `CONTRACT-002` | not_run |
| `RI-01.02` | `CONTRACT-001`, `PROF-005`, `REF-003`, `REF-004` | not_run |
| `RI-01.03` | `CONTRACT-002` | not_run |
| `RI-01.04` | `CONTRACT-002` | not_run |
| `RI-01.05` | `PIX-004`, `PROF-001`, `PROV-001` | not_run |
| `RI-01.06` | `ADM-004`, `ADM-005`, `DEC-001`, `DEC-002`, `PIX-005`, `PIX-006` | blocked, not_run |
| `RI-01.07` | `ADM-003`, `ADM-004`, `DIF-004`, `FEAT-003`, `PIX-006`, `REF-002`, `RES-001` | blocked, not_run |
| `RI-01.08` | `ADM-002`, `ADM-003`, `ADM-004`, `PROF-002`, `RES-001` | blocked, not_run |
| `RI-01.09` | `COMP-001`, `COMP-003`, `DEP-001`, `NATIVE-001`, `PROF-005` | blocked, not_run |
| `RI-01.10` | `PROF-002`, `RES-001`, `RES-002` | blocked, not_run |
| `RI-01.11` | `DEC-004`, `PIX-002`, `PROF-003`, `PROF-004` | blocked, not_run |
| `RI-02.01` | `REF-001`, `REF-003`, `REF-004` | not_run |
| `RI-02.02` | `PROV-001`, `REF-001` | not_run |
| `RI-02.03` | `FEAT-002`, `REF-002`, `REF-004`, `UNC-005` | blocked, not_run |
| `RI-02.04` | `PIX-004`, `REF-004`, `UNC-002` | not_run |
| `RI-02.05` | `REF-003`, `REF-004` | not_run |
| `RI-02.06` | `FEAT-002`, `REF-002`, `REF-004`, `UNC-004`, `UNC-005` | blocked, not_run |
| `RI-02.07` | `REF-003` | not_run |
| `RI-03.01` | `GEO-003`, `GEO-004`, `GEO-005`, `GEO-006` | not_run |
| `RI-03.02` | `GEO-003`, `GEO-005` | not_run |
| `RI-03.03` | `DIF-002`, `GEO-001`, `GEO-004`, `GEO-005`, `GEO-006` | not_run |
| `RI-03.04` | `GEO-001`, `GEO-005`, `GEO-006` | not_run |
| `RI-03.05` | `FEAT-004`, `GEO-002`, `GEO-005`, `UNC-004` | blocked, not_run |
| `RI-03.06` | `GEO-002`, `GEO-003`, `GEO-004`, `GEO-006`, `PIX-001`, `PIX-002`, `PIX-003`, `PIX-005`, `PIX-006` | blocked, not_run |
| `RI-04.01` | `DIF-001`, `DIF-002`, `DIF-003`, `DIF-004`, `FEAT-001`, `FEAT-002`, `FEAT-003`, `FEAT-004` | blocked, not_run |
| `RI-04.02` | `CLAIM-001`, `QUAL-001` | not_run |
| `RI-04.03` | `QUAL-001` | not_run |
| `RI-04.04` | `UNC-003`, `UNC-005` | blocked, not_run |
| `RI-04.05` | `UNC-001`, `UNC-002`, `UNC-005` | not_run |
| `RI-04.06` | `CLAIM-002`, `UNC-003`, `UNC-005` | blocked, not_run |
| `RI-04.07` | `UNC-003`, `UNC-005` | blocked, not_run |
| `RI-04.08` | `UNC-004`, `UNC-005` | blocked, not_run |
| `RI-04.09` | `UNC-005` | not_run |
| `RI-05.01` | `CONTRACT-002`, `PROV-001` | not_run |
| `RI-05.02` | `PROV-001`, `STR-001` | blocked, not_run |
| `RI-05.03` | `PROV-001`, `REF-001` | not_run |
| `RI-05.04` | `CONTRACT-001`, `ERR-002`, `FEAT-003`, `REF-001` | not_run |
| `RI-06.01` | `ERR-001`, `ERR-004` | not_run |
| `RI-06.02` | `ERR-001`, `TEL-001` | not_run |
| `RI-06.03` | `ERR-002`, `ERR-003` | not_run |
| `RI-06.04` | `ERR-003`, `ERR-004`, `STR-002` | blocked, not_run |
| `RI-06.05` | `ADM-007`, `DIF-005`, `ERR-002`, `ERR-003`, `TEL-002` | not_run |
| `RI-07.01` | `ADM-003`, `DIF-004`, `RES-001`, `RES-002` | blocked, not_run |
| `RI-07.02` | `COMP-001`, `COMP-002`, `COMP-003`, `NATIVE-001` | blocked |
| `RI-07.03` | `RES-003`, `STR-002`, `TEL-001` | blocked, not_run |
| `RI-07.04` | `TEL-001` | not_run |
| `RI-07.05` | `ADM-007`, `DIF-005`, `ERR-002`, `ERR-003`, `RES-002` | blocked, not_run |
| `RI-08.01` | `ENC-001`, `ENC-003` | blocked |
| `RI-08.02` | `ENC-001`, `ENC-002`, `ENC-003` | blocked |
| `RI-08.03` | `ENC-002`, `UNC-004`, `UNC-005` | blocked, not_run |
| `RI-08.04` | `ENC-003` | blocked |
| `RI-09.01` | `CONTRACT-001`, `CONTRACT-002`, `ENC-001`, `ENC-002`, `ENC-003`, `ERR-001`, `ERR-002`, `ERR-003`, `ERR-004`, `GEO-003`, `GEO-005`, `PROV-001`, `QUAL-001`, `REF-001`, `REF-002`, `REF-003`, `REF-004`, `RES-001`, `RES-002`, `RES-003`, `STR-001`, `STR-002`, `TEL-001`, `TEL-002`, `UNC-001`, `UNC-002`, `UNC-003`, `UNC-004`, `UNC-005` | blocked, not_run |

## Source reconciliation

| Source | Treatment in this scope |
|---|---|
| `SPECS/VISION.md` | Remains the global parent. Image VISION specializes P4/P5/P6/P7/P8; this packet does not rewrite audio/text or global authority. |
| `src/Vision/IMAGE/00`–`05`, `07`–`08` | Useful draft requirements are traced above and expanded into explicit requirements, stages, gates and harness cases. Their draft status does not equal approval. |
| `src/Vision/IMAGE/06_TENSORFLOW_CPP_UPGRADE_SPEC.md` | TensorFlow/Keras-first and custom-op routing conflict with the current Image-scope policy and are superseded here. File is left untouched for auditability. No TensorFlow operation is selected as the image reference path. |
| `src/Vision/IMAGE/image_observation.schema.json` | Candidate 0.1.0 baseline; this packet proposes a separate 0.3.1-draft schema with explicit policy/provenance and reference/transform alignment. Neither is an approved production contract. |
| `src/Cortex/ENCODER_TENSOR_CONTRACT_PROPOSAL.md` | Downstream boundary remains authoritative; Image VISION produces observations, not `X`. No Cortex edits are in scope. |
| `/workspace/image-text-review.md` | Read-only prototype assessment; its row/column edge cases, unchecked dimension cast and invalid benchmark evidence inform adversarial tests. It is not an implementation dependency or performance baseline. |

## Test-ID families

`case_catalog.json` provides concrete IDs. Prefixes map to: `ADM` admission; `DEC` decoder; `PIX` pixel/channel semantics; `GEO` transforms; `FEAT` features; `DIF` deterministic spatial differences; `QUAL` quality; `UNC` uncertainty; `ERR` errors/atomicity; `RES` resources; `STR` stream lifecycle; `TEL` telemetry/privacy; `REF` references; `PROV` provenance; `COMP` complexity; `DEP` dependency policy; `NATIVE` C++/Assembly equivalence; `ENC` Encoder boundary; `CONTRACT` schema/version compatibility; `CLAIM` evidence/claim hygiene.

## Status semantics

- **Specified:** requirement text and expected outcome exist.
- **Defined, not run:** a harness case or fixture is authored; no execution claim follows.
- **Passed:** a run artifact identifies commit, profile/schema version, build/runtime, command, result and reviewer.
- **Blocked:** a named owner input, target, contract, dependency or authority is missing.
- **Not applicable:** only when an accountable owner records why the requirement does not apply to the named profile.
