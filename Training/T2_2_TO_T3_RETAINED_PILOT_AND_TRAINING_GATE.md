# T2.2 → T3 Retained-Pilot-Data & Training Authorization Gate

**Project**: AGI Vision Substrate (AGI-VS)  
**Gate Status**: **T2.2 REVIEW COMPLETE — OPEN IMAGES PILOT RETENTION DENIED — TRAINING LOCKED**

---

## 1. Gate Decision

The T2.2 source-verification sample completed within its 50-record cap and produced no media download, embeddings, retained data, or model training. The review process itself passed its containment controls, but it did not establish the rights, safety, privacy, removal, and deduplication evidence necessary to retain any sampled item as pilot data. All sampled records remain quarantined.

> **Decision:** no Open Images V7 record is authorized for pilot retention, embedding generation, model training, fine-tuning, or evaluation. The proposed Open Images pilot cannot advance to T3 on the evidence currently available.

---

## 2. Evidence Summary

| Gate Requirement | Result | Gate Outcome |
| :--- | :--- | :--- |
| Bounded sample cap | 50 records reviewed; cap = 50 | **PASS** |
| Media containment | 0 image, thumbnail, annotation, or other media downloads | **PASS** |
| Model containment | 0 embeddings and 0 training-eligible records | **PASS** |
| Basic metadata completeness | No required source/attribution/licence fields missing | **PASS — metadata only** |
| Source accessibility | 39 HTTP 200, 1 HTTP 403, 5 HTTP 404, and 5 request errors | **Informational; not rights evidence** |
| Item-level licence verification | Unresolved for all 50 records | **FAIL for retention** |
| Privacy and safety review | Unresolved for all 50 records | **FAIL for retention** |
| Rights-caveat/removal review | Unresolved for all 50 records | **FAIL for retention** |
| Perceptual/text deduplication | Not performed | **FAIL for retention** |
| Retained pilot data | 0 records | **Correctly blocked** |
| Training or fine-tuning | Not started | **Correctly blocked** |

The source’s own licence page says users should verify each image because it makes no representation or warranty about every image’s licence status [1]. The Creative Commons licence deeds also note that other rights, including privacy, publicity, and moral rights, may require additional permissions [2] [3]. The gate therefore treats the metadata-only CC BY URLs as insufficient for training authorization.

---

## 3. Paths Forward

The project can advance only through one of the following evidence paths.

| Path | Prerequisites | T3 Eligibility |
| :--- | :--- | :--- |
| **A. Permissioned/first-party pilot** | Named provider, written permission or explicit compatible terms, source data card, privacy/safety process, removal pathway, finite split manifest | Preferred path. Eligible for a later retained-pilot review. |
| **B. Independently reviewed public-content pilot** | Finite item list, record-level terms evidence, attribution plan, media safety/privacy review, removal path, deduplication and split report, relevant professional review as needed | Possible but more demanding. Eligible only after a fresh retention gate. |
| **C. Synthetic or user-owned pilot** | Demonstrable ownership/permission, known generation/source policy, safety/quality review, held-out evaluation design | Suitable for tooling validation; does not itself prove broad visual capability. |

---

## 4. Training Preconditions

Before any adapter/model training may be authorized, the owner must approve a finite retained-pilot manifest that includes source IDs, terms/permission evidence, item-level data cards, review outcomes, exclusion/quarantine log, removal/retention procedure, deterministic train/dev/held-out split, deduplication report, storage/access plan, base-model licence, compute budget, training configuration, and predeclared evaluation/safety tests.

A separate **T3 Training Authorization** will be required after the retained-pilot package passes review. No external data source may be downloaded for training simply because it appears in the discovery registry.

---

## 5. Owner Decision Required

The recommended next step is to identify a **named permissioned/first-party or user-owned pilot source**. If you can provide one, I can prepare its source-specific review package.

Alternatively, if you want a design-only comparison of viable permissioned/first-party source options without acquiring data, respond:

`Approve T2.3 Permissioned Source Discovery`

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[2]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
