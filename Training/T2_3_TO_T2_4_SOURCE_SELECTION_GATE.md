# T2.3 → T2.4 Source Selection Gate

**Project**: AGI Vision Substrate (AGI-VS)
**Gate status**: **T2.3 DISCOVERY COMPLETE — NO SOURCE SELECTED — RETENTION AND TRAINING LOCKED**

---

## 1. Decision

T2.3 has completed a documentation-only comparison of permissioned, first-party, public-domain, commercial, and synthetic pilot-source pathways. It created no provider accounts, accepted no terms on the owner’s behalf, downloaded no media, retained no corpus, generated no embeddings, and ran no training.

The comparison confirms that the project’s most practical route to a governable pilot is either a **named user-owned/commissioned source** or a **named provider with written training permission**. If neither is available, a bounded allow-list of explicitly CC0-marked assets from the Art Institute of Chicago is a viable but domain-limited fallback for validating the pipeline and governance workflow. The Smithsonian CC0 route is a secondary first-party fallback. Open Images V7 remains denied for initial retention under T2.2.

> **Decision:** T2.3 is complete. The project cannot begin data acquisition, retention, embedding generation, model training, or fine-tuning until the owner selects a named source and that source passes T2.4 Source-Specific Retained-Pilot Review.

---

## 2. Evidence Produced

| Artifact | Outcome | Control Effect |
| :--- | :--- | :--- |
| `T2_3_PILOT_SOURCE_REQUIREMENTS.md` | Defines hard requirements, weighted criteria, and 80/100 readiness threshold | Prevents pathway selection from replacing item-level evidence. |
| `T2_3_SOURCE_DISCOVERY_NOTES.md` | Records official first-party policy/terms findings and unresolved provider conditions | Creates a traceable discovery record without content acquisition. |
| `T2_3_PERMISSIONED_SOURCE_DISCOVERY.md` | Provides ranked comparison, evidence matrices, and owner response options | Supports a source selection that can advance to a bounded review. |
| `candidate_dataset_registry.json` | Adds T2.3 candidate pathways and preserves explicit training blocks | Maintains machine-readable provenance and eligibility status. |

---

## 3. Source Selection Options

| Selection response | Next permitted activity | Not authorized by this response |
| :--- | :--- | :--- |
| `Select Path A: [named user-owned or commissioned source]` | Document ownership/permission, boundary, data card, and review protocol | Uploading, downloading, retaining, or training on assets. |
| `Select Path B: [named commercial or partner provider]` | Review written terms/proposal, data sheet, cost boundary, and removal/privacy controls | Signing a contract, creating an account, purchasing, or downloading data. |
| `Select Path C1: Art Institute CC0 allow-list` | Prepare a no-download review protocol for a finite set of explicit CC0 designations only | Bulk access, scraping, downloading, or treating collection-level access as blanket permission. |
| `Select Path C2: Smithsonian CC0 allow-list` | Prepare a no-download review protocol for a finite set of CC0-marked items only | Bulk access, scraping, downloading, or ignoring third-party/privacy caveats. |
| `Select Path S: [named generator and plan]` | Review dated provider plan/terms and create a synthetic-data governance proposal | Generating media, collecting output, or training. |
| `Request another source comparison: [source]` | Perform a documentation-only governance assessment | Acquiring or retaining that source. |

---

## 4. T2.4 Pass Conditions

T2.4 will produce a **retained-pilot proposal**, not a training run. It may request a later, separate pilot-acquisition approval only when all conditions below have recorded evidence.

| Condition | Required evidence |
| :--- | :--- |
| Named, finite source | Provider identity, exact version/asset boundary, modalities, and pilot-size cap. |
| Explicit compatible use right | Dated terms, written grant, contract, or per-item designation that permits the declared retained training purpose. |
| Item-level provenance | Stable IDs, source URLs/provider records, dates, rights indicators, and planned checksums. |
| Privacy and safety plan | PII/sensitive-content review, exclusions, escalation path, and documented reviewer decision format. |
| Removal and retention | A removal contact/mechanism, local deletion process, audit record, and review/expiry date. |
| Task and annotation fit | Declared capability objective, annotation quality plan, known limitations, and misuse exclusions. |
| Split and duplicate controls | Deterministic train/dev/held-out assignment, leakage review, and duplicate-detection method. |
| Reproducible implementation boundary | Data card, manifest schema, transform versions, access control, base-model terms, compute cap, and predeclared evaluation tests. |

A later **pilot-acquisition gate** must be approved by the owner after T2.4 passes. A distinct **T3 Training Authorization** remains required after the retained-pilot material is reviewed and accepted.

---

## 5. Owner Action Required

Select one exact response from Section 3, replacing the bracketed text with a source name where required. Do **not** respond with `Approve T3 Training` yet; that authorization remains unavailable until a named source has passed T2.4 and the owner has separately approved retained-pilot acquisition.

## References

[1]: T2_3_PERMISSIONED_SOURCE_DISCOVERY.md "T2.3 Permissioned Source Discovery"
[2]: ../Stages/T0_GOVERNANCE_CHARTER.md "T0 Governance Charter"
[3]: T2_2_TO_T3_RETAINED_PILOT_AND_TRAINING_GATE.md "T2.2 to T3 Retained-Pilot-Data and Training Authorization Gate"
