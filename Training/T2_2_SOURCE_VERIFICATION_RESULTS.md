# T2.2 Source-Verification Sample Results

**Status**: Completed bounded source-page review; retention and training blocked  
**Sample size**: 50 records from the existing 710-record quarantine queue  
**Media acquired**: **0**  
**Embeddings generated**: **0**  
**Training/fine-tuning runs**: **0**

---

## 1. Executed Scope

The T2.2 process selected a deterministic sample of 50 records from the metadata-only T2.1 queue. It requested only their declared Flickr landing pages under a short timeout and a five-worker concurrency cap. The review tool inspected bounded HTML responses and retained no page HTML or media. It did not request the original-image, thumbnail, mask, annotation, or other media URLs.

| Scope Control | Result |
| :--- | :--- |
| Maximum review size | **PASS** — 50 of 50 allowed records reviewed |
| Landing-page hosts | **PASS** — restricted to approved Flickr landing-page domain handling |
| Requested content type | **PASS** — page-level HTML only when returned as HTML |
| Maximum inspected body | **PASS** — bounded at 128 KiB per returned HTML page |
| Media/annotation download | **PASS** — 0 |
| Embeddings/features | **PASS** — 0 |
| Training eligibility | **PASS** — 0 eligible; all remain quarantined |

---

## 2. Source-Page Observations

| Observation | Measured Result | Interpretation |
| :--- | :--- | :--- |
| Completed HTTP requests | 45 / 50 | A source-page request completed for 45 records. |
| HTTP 200 responses | 39 / 50 | Page availability alone does not establish item-level rights or safety. |
| HTTP 403 responses | 1 / 50 | The evidence could not be reviewed through the bounded page request. |
| HTTP 404 responses | 5 / 50 | The source page was unavailable through the request. |
| Request errors | 5 / 50 | The evidence could not be reviewed through the bounded page request. |
| Required review metadata fields missing | 0 | Basic ID, landing URL, attribution-party, and licence-URL fields were present in the queue. |

The sampled source-row metadata continues to point to CC BY 2.0, but the Open Images licence documentation explicitly says that users should verify the licence of each image because no representation or warranty is made about individual image licence status [1]. A successful landing-page request is therefore evidence of accessibility only, not rights clearance.

---

## 3. Retention-Readiness Decision

The T2.2 audit returns **`PASS_BLOCKED_FOR_RETENTION`**. This means the bounded protocol operated correctly and did not widen into media collection or model use, but it correctly refuses to convert the queue into retained pilot data.

| Retention Requirement | T2.2 Result | Decision |
| :--- | :--- | :--- |
| Item-level licence verification | Unresolved for 50/50 | Blocks retention. |
| Privacy and safety review | Unresolved for 50/50 because media was not retained or inspected | Blocks retention. |
| Rights-caveat review | Unresolved for 50/50 | Blocks retention. |
| Removal-path confirmation | Unresolved for 50/50 | Blocks retention. |
| Perceptual/text similarity deduplication | Not performed under metadata-only scope | Blocks retention. |
| Training eligibility | 0/50 | Blocks training. |

The CC BY 2.0 deed permits sharing and adaptation subject to attribution and other terms, while also stating that privacy, publicity, or moral rights may require additional permissions [2]. The project treats these as mandatory item-level controls rather than assuming that a metadata licence URL settles the question.

---

## 4. Required Next Direction

The Open Images metadata route is not sufficient by itself to authorize a training corpus. A future pilot must either use a **named permissioned/first-party source** with documented use rights and a removal pathway, or receive a separately approved, manual record-level rights and safety-review process that produces a finite retained-item manifest. The latter should be assessed with appropriate legal/privacy review for the intended jurisdiction and deployment; this project documentation is not legal advice.

No download or training request should begin until one of these evidence paths is completed and explicitly approved.

## References

[1]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[2]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
