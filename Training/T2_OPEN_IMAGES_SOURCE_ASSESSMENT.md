# T2 Source Assessment: Open Images V7

**Assessment status**: Conditional candidate only; acquisition not authorized  
**Assessment scope**: Public documentation review; no source data, media, identifiers, or bulk metadata accessed or retained  
**Proposed use if later approved**: Small manually verified visual-grounding pilot, not full-dataset training

---

## 1. Source and Modality Assessment

Open Images V7 is a technically relevant candidate because the official description reports a broad set of visual annotations: image-level labels, bounding boxes, segmentation masks, visual relationships, localized narratives, and point-level labels [1]. The source is potentially useful for a controlled adapter baseline that tests visual grounding and spatial-relation interfaces over the existing AGI-VS substrate.

The candidate is not being selected on scale alone. The project’s pilot must remain small enough for record-level attribution, rights review, safety triage, leakage checks, and reproducibility artifacts. The proposed maximum is a **1,000-record review queue**, with no retained training items until a later acquisition decision.

---

## 2. Terms and Attribution Assessment

The official Open Images licence section states that annotations are licensed by Google LLC under CC BY 4.0 and that images are listed as CC BY 2.0. The same source cautions that it makes no representations or warranties regarding each image’s licence status and says each image should be verified by the user [2]. This caveat blocks bulk reliance on a dataset-level licence statement.

The referenced CC BY 2.0 and CC BY 4.0 deeds permit sharing and adaptation subject to attribution, licence-link, and change-indication conditions; both also state that no warranties are given and that publicity, privacy, or moral rights may require additional permissions [3] [4]. The project will therefore require item-level provenance and attribution evidence before retaining any candidate record.

| Review Topic | Assessment | Required Control |
| :--- | :--- | :--- |
| Dataset annotations | Published as CC BY 4.0 according to source documentation | Preserve annotation provenance, licence link, and attribution data. |
| Images | Listed as CC BY 2.0, with explicit publisher no-warranty caveat | Verify the record-level source/licence indication and associated attribution fields before retention. |
| Attribution | Required by CC BY deeds | Maintain creator/source, title if supplied, licence URL, and modification/transformation record. |
| Additional rights | Privacy, publicity, and moral rights are not resolved by licence summary alone | Apply privacy/safety screen and quarantine uncertain records. |
| Jurisdiction/contract review | Not completed in T2 planning | Escalate to an appropriate reviewer before acquisition if the intended use requires it. |

---

## 3. Privacy, Safety, and Content Controls

No automated classifier can conclusively resolve the project’s privacy or safety risk. For any future review queue, the project will operate a fail-closed policy: unresolved records are quarantined. The following categories require exclusion or escalation: personal/sensitive data, identifiable individuals in sensitive settings, minors, explicit or exploitative content, medical/health contexts, private documents or location signals, severe violence/self-harm, hateful/harassing material, and captions or annotations inconsistent with the approved research purpose.

The project will retain neither quarantined media nor their derived embeddings. Any later acquisition plan must identify the exact filter implementation, version, human-review escalation route, removal workflow, and retention policy.

---

## 4. Split Isolation and Evaluation Controls

The future pilot must decide train, development, and held-out allocation deterministically before model fitting. It must run image and text deduplication across those partitions and perform a documented overlap assessment against any external benchmark considered for evaluation. COCO remains an evaluation-only candidate at this stage and is not included in the proposed Open Images pilot training boundary.

The system must keep a split manifest checksum, prevent write access to the held-out set during experiment design, and record prior-model exposure limitations. Any inability to establish split integrity blocks use of the candidate record.

---

## 5. Decision

**Current decision: conditionally suitable for a later manually verified review queue, but not approved for acquisition or training.** The candidate can advance only if the owner approves a source-specific package that includes current terms evidence, record-level provenance fields, attribution procedure, content/privacy filters, human-review protocol, removal/retention workflow, deterministic split plan, storage/access controls, and the adapter-baseline evaluation plan.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[2]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[3]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
[4]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
