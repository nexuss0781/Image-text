# T2.3 Permissioned Source Discovery

**Project**: AGI Vision Substrate (AGI-VS)
**Status**: Discovery complete; no source has been acquired, retained, embedded, or used for training
**Decision required**: Select one named source pathway for a source-specific retained-pilot review
**Author**: Manus AI

---

## 1. Purpose and Boundary

T2.3 identifies lawful, governable paths that could supply a **small retained pilot** for the AGI-VS adapter-baseline experiment. It follows the T2.2 decision that Open Images V7 cannot be retained on the evidence reviewed and that training remains locked. This document is a comparison of pathways, not permission to acquire any data.

The recommended pilot is intended to validate the approved visual-token interface and precommitted adapter-baseline evaluation plan. It is not evidence of general visual intelligence, a substitute for broad-scale data governance, or authorization to describe the resulting system as AGI.

> **Fail-closed rule:** every selected asset must have a documented rights basis, provenance record, privacy/safety outcome, removal pathway, deterministic split assignment, deduplication decision, and reproducible manifest before it can enter a retained pilot. Public accessibility alone is not permission.

---

## 2. Decision Method

Candidate pathways were judged against the mandatory controls in the T0 Governance Charter. The readiness score represents the pathway’s **potential to produce a governable pilot after source-specific evidence is attached**. It is not a legal opinion, a procurement decision, or an approval to use any source.

| Dimension | Weight | Decision Question |
| :--- | ---: | :--- |
| Rights and permission clarity | 25 | Can the project show an explicit, compatible training/fine-tuning right? |
| Provenance and removal controls | 20 | Can every retained asset be traced, versioned, and removed if necessary? |
| Privacy and safety governability | 15 | Can the source support practical sensitive-content and personal-data controls? |
| Annotation and task fitness | 15 | Does it support the declared visual-grounding pilot objective? |
| Split integrity and evaluation fit | 10 | Can the source support held-out partitions and leakage review? |
| Reproducibility and access controls | 10 | Can the exact selection, transforms, and access boundaries be reproduced? |
| Operational feasibility | 5 | Is a bounded pilot feasible within available review, storage, and compute capacity? |

A pathway must pass every hard control, score at least **80/100**, and have no unresolved high-severity issue before it may be proposed to the owner as a retained-pilot source. Until that proposal is approved, the score remains informational only.

---

## 3. Ranked Comparison

| Rank | Source pathway | Discovery candidate | Readiness potential | Proposed pilot scale | Principal advantages | Principal limitations and gate risks |
| :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| 1 | **User-owned or commissioned images with explicit annotations** | A corpus the project owner owns, commissions, or receives under a written training-use grant | **95** once a named corpus and agreements are supplied | 250–1,000 assets | Direct control over permission, collection instructions, labels, retention, and removal; strongest fit for a domain-specific task | No named source exists yet; ownership alone does not resolve recognisable-person consent, third-party marks, safety, or annotation quality |
| 2 | **Directly permissioned commercial/provider dataset** | A provider offering a written AI-training data licence, such as a negotiated multimodal collection | **90** after contract review | 500–5,000 assets | Can provide diverse media, standardized delivery, contractual assurances, and a provider contact for removal/support | Cost, contractual scope, downstream model/output rights, audit rights, and provider-specific privacy assurances must be reviewed; public marketing pages are not a licence |
| 3 | **Art Institute of Chicago CC0 public-domain allow-list** | Only works explicitly labeled “CC0 Public Domain Designation” in the Institute’s first-party collection | **84** after asset-level screening | 250–500 assets | The Institute states that designated images may be used for any purpose, including commercial use, and exposes collection metadata via a public API [1] [2] | Narrow cultural-heritage domain; the Institute cautions that users remain responsible for third-party permissions; artwork imagery does not validate broad real-world perception |
| 4 | **Smithsonian CC0 first-party allow-list** | Only Smithsonian items explicitly marked CC0, retained with rights metadata | **82** after asset-level screening | 250–500 assets | First-party institution, public developer tooling, very diverse object types, and a stated CC0 category usable for commercial and noncommercial purposes [3] [4] | Smithsonian states that CC0 does not guarantee absence of third-party, privacy, publicity, or other rights; no blanket collection approval; source scale increases review burden |
| 5 | **Synthetic images from a named licensed generator** | A tightly specified prompt-and-label corpus generated under a verified provider plan | **78** as a standalone path; suitable only for tooling validation unless combined with another path | 250–1,000 assets | Exact control of classes, captions, nuisance factors, and exclusions; complete prompt/output provenance can be created | The provider’s output-use terms and plan must be captured at generation time; synthetic bias, artifacts, label leakage, brands, people, and unsafe prompts require review; does not establish real-world generalization |
| 6 | **Open Images V7 through deeper manual review** | A finite, record-level allow-list beyond the T2.2 metadata and landing-page sample | **45** under current evidence | 0 proposed | Existing discovery work and annotations may inform review design | T2.2 denied retention. Rights, privacy/safety, removal, and deduplication were unresolved for all 50 sampled records. This route remains expensive and is not recommended as the initial retained pilot. |

The **highest-ranked actionable pathway** is a named user-owned or commissioned corpus because it creates the most direct evidence chain. If the owner cannot provide or commission such a source, a limited **Art Institute CC0 allow-list** is the recommended non-commercial fallback for pipeline and process validation only, subject to a separate source-specific review. A commercial provider path may be preferable when the owner has budget and needs broad, real-world visual coverage, but it cannot proceed without contract evidence.

---

## 4. Path-Specific Evidence Required

### 4.1 User-Owned or Commissioned Corpus

The owner must provide a named source, asset inventory boundary, and documentation showing that the owner or provider has granted the project the right to retain and use the assets for the declared adapter-training purpose. Where people are recognisable, the proposal must describe consent/release status, exclusions, and removal contacts. Commissioned annotations require the annotation instructions, worker/contract terms, quality checks, and known label limitations.

| Required artifact | Minimum content |
| :--- | :--- |
| Permission record | Ownership statement or written grant that expressly covers retained model training/fine-tuning, evaluation, and internal reproducibility. |
| Source manifest | Finite source IDs, original filenames or stable IDs, creation/receipt date, modality, and planned cap. |
| Data card | Collection purpose, capture method, geography/timeframe, known biases, annotations, intended use, and exclusions. |
| Privacy and safety plan | Recognisable-person and sensitive-content treatment, reviewer role, escalation route, and exclusion labels. |
| Removal procedure | Named contact, identity checks, deletion propagation steps, retention review date, and evidence log. |

### 4.2 Directly Permissioned Commercial or Partner Data

A commercial path is viable only when a signed or otherwise binding agreement specifically covers the planned model-training use. The project may not infer that an ordinary stock subscription, web access, or marketing statement permits model training.

| Required artifact | Minimum content |
| :--- | :--- |
| Executed terms or written authorization | Licence scope; permitted models, locations, term, access, retention, training/fine-tuning, evaluation, and downstream model/output use. |
| Provider data sheet | Source origin, collection process, annotation origin, known restrictions, provider contacts, and version/date. |
| Privacy and rights assurance | Provider’s representation of permissions, any model/property/publicity constraints, and incident/removal path. |
| Delivery and audit specification | Fixed delivery manifest, checksums, permitted user/access controls, audit rights, and withdrawal/update mechanism. |
| Cost and capacity approval | Owner-approved quote or budget boundary, pilot size cap, storage location, and permitted compute environment. |

### 4.3 First-Party CC0 Institution Allow-List

The Art Institute of Chicago says that its “CC0 Public Domain Designation” images may be used for any purpose, including commercial use, while placing responsibility for third-party permissions on the user [2]. Smithsonian similarly distinguishes CC0-marked content, which it says may be used commercially, from other content with separate restrictions; it cautions that other rights may still apply [4]. Therefore, the project must retain only specifically marked assets and cannot use a collection-wide scrape.

| Required artifact | Minimum content |
| :--- | :--- |
| Explicit-item allow-list | Stable item IDs/URLs and a recorded CC0 indicator for every proposed asset; assets without that indicator are excluded. |
| Rights snapshot | Provider policy and item-page metadata captured with retrieval date; preservation of requested attribution/caption text where supplied. |
| Domain suitability statement | Why a cultural-heritage/object pilot is relevant to the specific visual-token or grounding capability being evaluated. |
| Safety/privacy screen | Assessment of human depictions, sensitive historical material, graphic content, and third-party/publicity signals; exclusion log. |
| Removal/retention record | Provider contact, local removal procedure, data-card review date, and asset deletion verification process. |

### 4.4 Controlled Synthetic Data

Synthetic data can validate interfaces, split discipline, and reproducible training execution. It must not be characterized as a proxy for broad real-world perception or as proof of general capability. The project must select a named provider and capture the precise product plan, policy, and output-use terms applicable on the generation date; Adobe, for example, publishes separate generative-AI user guidelines that must be reviewed together with the applicable product terms before any provider is selected [5].

| Required artifact | Minimum content |
| :--- | :--- |
| Provider and terms snapshot | Named generator, plan/account category, dated output-use terms, policy constraints, and any commercial-use limitation. |
| Generation manifest | Prompt templates, negative prompts, seed where available, model/version, timestamps, output checksum, and creator account. |
| Content control specification | Prohibited personal likenesses, minors, sexual/violent content, hateful content, protected marks, public figures, and deceptive labels. |
| Quality and leakage review | Manual sample review, duplicate check, label/prompt leakage test, and held-out prompt-family assignment. |
| Synthetic-use limitation | Documented statement that results measure controlled-data behavior and do not establish real-world generalization. |

### 4.5 Open Images V7 Manual Review Route

This route is deliberately lower priority. T2.2 established that bounded metadata and source-page review were insufficient to retain a single record. No Open Images record may be acquired or retrained on unless a future, separately approved source-specific procedure resolves rights, privacy/safety, removal, deduplication, and evaluation leakage for every retained item.

---

## 5. Proposed Source-Specific Retained-Pilot Gate

After the owner selects a pathway and names a source, the next work item is **T2.4 Source-Specific Retained-Pilot Review**. It will remain discovery/documentation-only until explicitly approved. A source may be proposed for acquisition only when the following checklist is complete.

| Gate control | Pass condition | Evidence record |
| :--- | :--- | :--- |
| Named finite source | Provider and exact asset boundary are specified | Source declaration and manifest draft |
| Training-use right | Explicit compatible permission/terms are recorded | Dated authorization/terms snapshot and use-category decision |
| Provenance | Every candidate asset can be traced to the named source | Item-level records and checksums |
| Privacy and safety | Review process, exclusion taxonomy, and escalation route are accepted | Review protocol and sample decision log |
| Removal and retention | Operational deletion path and review date exist | Removal register and retention schedule |
| Task fit | Source supports a declared, bounded capability objective | Capability-to-annotation mapping |
| Deduplication and splits | Deterministic train/dev/held-out partitions and duplicate rules are defined | Split seed, manifest, and leakage report plan |
| Reproducibility | Retrieval/transformation versions and checksums are defined | Data card and build/review revisions |
| Model and compute scope | Base-model terms, adapter configuration, compute cap, and predeclared tests are documented | T3 proposal annex |

> **No gate is passed by a pathway score alone.** The owner must approve the source-specific retained-pilot proposal before any media is downloaded or retained. The owner must then approve a distinct T3 Training Authorization after the retained-pilot package passes review.

---

## 6. Owner Decision Required

Please choose **one** of the following decisions. No media download, corpus creation, training, or fine-tuning will begin from this document alone.

| Response | Effect |
| :--- | :--- |
| `Select Path A: [named user-owned or commissioned source]` | Begins a documentation-only source-specific review once the ownership/permission evidence is supplied. |
| `Select Path B: [named commercial or partner provider]` | Begins a documentation-only review of the provider’s written terms/proposal, cost boundary, and data-governance evidence. |
| `Select Path C1: Art Institute CC0 allow-list` | Prepares a finite, no-download candidate-review protocol for CC0-designated objects only. |
| `Select Path C2: Smithsonian CC0 allow-list` | Prepares a finite, no-download candidate-review protocol for CC0-marked items only. |
| `Select Path S: [named generator and plan]` | Prepares a synthetic-data governance proposal, without generating media. |
| `Request another source comparison: [source]` | Assesses a user-named source under the same T0 controls, without acquiring data. |

`Approve T3 Training` is **not yet valid**. It may be considered only after a named source completes T2.4, the owner approves the retained-pilot package, and the separate T3 training preconditions are evidenced.

---

## References

[1]: https://www.artic.edu/collection-information/open-access "Art Institute of Chicago — Open Access"
[2]: https://www.artic.edu/collection-information/open-access/open-access-images "Art Institute of Chicago — Open Access Images"
[3]: https://www.si.edu/openaccess "Smithsonian Open Access"
[4]: https://www.si.edu/termsofuse "Smithsonian Terms of Use"
[5]: https://www.adobe.com/legal/licenses-terms/adobe-gen-ai-user-guidelines.html "Adobe Generative AI User Guidelines"
[6]: https://www.shutterstock.com/data-licensing "Shutterstock — Data Licensing"
[7]: ../Stages/T0_GOVERNANCE_CHARTER.md "T0 Governance Charter"
[8]: T2_2_TO_T3_RETAINED_PILOT_AND_TRAINING_GATE.md "T2.2 to T3 Retained-Pilot-Data and Training Authorization Gate"
