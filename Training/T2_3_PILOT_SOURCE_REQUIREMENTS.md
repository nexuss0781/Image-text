# T2.3 Pilot Source Requirements

**Status**: Discovery and design only; no source data acquired
**Purpose**: Define the minimum evidence a source must provide before a retained pilot or training proposal can be considered.

---

## 1. Selection Principle

The prior Open Images review established that dataset-level licence metadata and accessible landing pages do not necessarily establish item-level training rights, privacy suitability, or removal controls. T2.3 therefore prioritizes data sources with a direct permission relationship, a documented terms-of-use basis, or clear user ownership over sources that merely expose public URLs.

> **Acceptance principle:** a retained-pilot candidate must be reviewable as a finite asset with known provenance, explicit allowed purpose, a deletion/removal pathway, and a reproducible manifest. A source that cannot meet those conditions may be useful for discovery but is not a training candidate.

---

## 2. Hard Requirements

| Requirement | Minimum Evidence | Failure Outcome |
| :--- | :--- | :--- |
| Explicit training permission | Written grant, contract, terms, or ownership evidence that covers the declared training/fine-tuning purpose | Reject from retained pilot. |
| Defined source boundary | Named provider, version, split or asset list, modality, and maximum item count | Reject from retained pilot. |
| Provenance and attribution | Provider/source record, creator/attribution fields where applicable, acquisition date, and manifest checksum | Quarantine until complete. |
| Privacy and consent | Collection/consent basis, sensitive-content treatment, and a documented human escalation route | Reject or quarantine. |
| Removal and retention | Contact or mechanism for removal, local deletion procedure, and review/expiry date | Reject from retained pilot. |
| Safety/content controls | Declared inclusion/exclusion policy, filter version, and review route | Quarantine until complete. |
| Split and leakage integrity | Deterministic train/dev/held-out partitions and duplicate/benchmark-overlap process | Block training. |
| Reproducibility | Versioned data card, manifest, transforms, code revision, and audit record | Block training. |
| Model compatibility | Proposed base-model licence and adapter-training scope are documented | Block training. |

---

## 3. Weighted Decision Criteria

The final source comparison uses a 100-point weighted score. A source must score at least 80, pass every hard requirement, and have no unresolved high-severity risk before it can be recommended for a retained-pilot proposal.

| Dimension | Weight | Rationale |
| :--- | :---: | :--- |
| Rights and permission clarity | 25 | Explicit permission and use scope are the primary precondition for retained training data. |
| Provenance and removal controls | 20 | The project needs traceable origin, a manifest, and an operational response to removal requests. |
| Privacy and safety governability | 15 | Pilot content must have clear exclusion, review, and escalation rules. |
| Annotation/task fitness | 15 | The source must support the pilot’s visual-grounding objectives rather than merely increase volume. |
| Split integrity and evaluation fit | 10 | The pilot needs credible held-out evaluation and benchmark-leakage protections. |
| Reproducibility and access controls | 10 | The source must support versioned, auditable reuse within the approved scope. |
| Operational feasibility | 5 | The source must fit declared storage, compute, review, and maintenance capacity. |

---

## 4. Candidate Path Classes

| Path Class | Default Position | Conditions for Advancement |
| :--- | :--- | :--- |
| User-owned or commissioned data | Preferred | Demonstrable ownership or agreements; review all privacy/safety and split controls. |
| Directly permissioned partner/provider data | Preferred | Written allowed-use scope, data card, removal contact, and finite asset boundary. |
| Vendor-licensed commercial data | Conditional | Contract terms must explicitly cover model training/fine-tuning, retention, attribution, and downstream use. |
| Institutional research data with explicit access terms | Conditional | Confirm the permitted use, consent/ethics constraints, and retention/removal terms. |
| Public dataset with source-level rights evidence | Conditional, higher review burden | Finite verified manifest, attribution plan, privacy/safety review, and item-level or provider-level authorization. |
| Web crawl, URL index, or opaque aggregate | Not eligible for initial retained pilot | May inform discovery only; cannot advance without an independently reviewed finite allow-list. |

---

## 5. T2.3 Deliverable Boundary

T2.3 will identify and compare source *pathways* and their public evidence. It will not sign contracts, create provider accounts, accept terms on the owner’s behalf, download data, or train a model. A source-specific retained-pilot package will be presented for approval only after a candidate meets the requirements above.
