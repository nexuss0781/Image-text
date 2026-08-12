# T2.1 Bounded Review-Queue Results

**Status**: Completed metadata-only review queue; all records quarantined  
**Source**: Open Images V7 official image-information endpoint  
**Media acquired**: **0**  
**Embeddings generated**: **0**  
**Training/fine-tuning runs**: **0**

---

## 1. Executed Scope

The T2.1 process retrieved a bounded **256 KiB byte-range** from the official Open Images image-information CSV and retained only complete CSV rows needed to form a record-review queue. The resulting queue contains **710 source records**, below the approved 1,000-record maximum. The process did not request image URLs, thumbnail URLs, annotations, masks, or other media assets. It did not execute any model or embedding workload.

The official download documentation identifies the image-information file as containing image identifiers, URLs, titles, authors, and licence information [1]. The official licence page states images are listed as CC BY 2.0, but also warns that the publisher makes no representation or warranty for each image’s licence status and says each image should be verified [2]. Therefore, the record-level licence URL found in metadata is treated as an input to review, not as an automatic clearance.

---

## 2. Audit Results

| Control | Measured Result | Outcome |
| :--- | :--- | :--- |
| Review-queue cap | 710 records; maximum allowed 1,000 | **PASS** |
| Record identifiers | 710 unique IDs; 0 exact-ID duplicates | **PASS** |
| Required metadata fields | 0 missing among required identifier, source, creator, and licence fields | **PASS — metadata completeness only** |
| Licence metadata | 710/710 rows contain `https://creativecommons.org/licenses/by/2.0/` | **PASS — metadata signal only** |
| Proposed deterministic split | 589 training, 62 development, 59 held-out | **PASS — proposal only; all rows remain blocked** |
| Media downloads | 0 | **PASS** |
| Embeddings | 0 | **PASS** |
| Retained training records | 0 | **PASS** |
| Training-eligible records | 0 | **PASS — correctly blocked** |
| Quarantined records | 710 | **PASS — fail-closed handling** |

---

## 3. What the Audit Did and Did Not Establish

The audit established the queue’s size limit, exact-ID uniqueness, basic metadata completeness, source-row licence field consistency, deterministic split proposal, and hard blocks against media downloads and training. It did **not** establish that any individual record is fully rights-cleared, safe, private, de-duplicated at the image/text level, or suitable for retention.

The CC BY 2.0 deed requires appropriate credit and a licence link, and it notes that other rights—including publicity, privacy, or moral rights—may require additional permissions [3]. These are record-level questions not resolved by a source-row licence string. The project must therefore keep all 710 entries in quarantine until a further finite approval covers item-level verification and sample-level safety/privacy review.

| Unresolved Control | Why It Remains Unresolved | Current Effect |
| :--- | :--- | :--- |
| Item-level source/licence verification | The dataset publisher’s no-warranty statement requires each image to be verified | No retention or use. |
| Privacy and sensitive-content review | Media was deliberately not downloaded or processed | No retention or use. |
| Safety/content review | Media was deliberately not downloaded or processed | No retention or use. |
| Perceptual/text similarity deduplication | Requires approved content/caption review beyond metadata-only scope | No training split is active. |
| Removal procedure confirmation | Must be associated with a reviewed record/source process | No retention or use. |

---

## 4. Reproducibility Artifacts

The following records reproduce the T2.1 boundary and audit result: `scripts/fetch_t21_metadata_fragment.sh`, `scripts/build_t21_review_queue.py`, `scripts/audit_t21_review_queue.py`, `t21_openimages_metadata_fragment.csv`, `t21_openimages_review_queue.json`, `t21_openimages_review_queue_audited.json`, and `t21_openimages_review_audit.json`. The tooling refuses media download and encodes `retained_training_records: 0` and `model_training_permitted: false` in its manifests.

## References

[1]: https://storage.googleapis.com/openimages/web/download_v7.html "Open Images V7 — Download and Data Formats"
[2]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[3]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
