# T2.4 Art Institute CC0 Source-Specific Review

**Status**: **PASS for bounded manifest construction only; media acquisition not yet performed**
**Selected source**: Art Institute of Chicago Open Access Images
**Pilot cap**: 300 retained images maximum

---

## 1. Review Decision

The Art Institute of Chicago is approved as the source for a **metadata-only finite-manifest construction step**. Its official image policy allows images bearing the “CC0 Public Domain Designation” to be used for any purpose, including commercial use, without additional permission. The official API exposes the required item-level public-domain and image-reference metadata. The same sources make clear that CC0 status does not remove the user’s responsibility to assess potential third-party rights [1] [2] [3].

> **T2.4 decision:** proceed to a finite candidate manifest only. No item becomes retained training data until it passes the recorded asset-level eligibility, safety, provenance, removal, split, and duplicate controls below.

---

## 2. Control Assessment

| T0 hard control | Evidence and decision | Status |
| :--- | :--- | :---: |
| Explicit training-compatible right | Provider policy permits any-purpose use for items with the CC0 Public Domain Designation. The manifest will retain only records whose first-party API reports `is_public_domain: true` and that satisfy the documented image-policy condition. | **Pass for reviewed candidates only** |
| Defined source boundary | The source is a 300-item maximum list from the provider’s artwork API, generated with a fixed query, seed, and eligibility rules. | **Pass** |
| Provenance and attribution | Stable artwork ID, source URLs, rights indicator, title, classification, department, retrieval time, provider policy URLs, and later file checksums will be recorded. | **Pass subject to manifest audit** |
| Privacy and consent | The source is cultural-heritage material, but the review will exclude metadata signals for portraits, people, nudity, violence, sensitive historical material, and uncertain cases. No inference of consent is made from public access. | **Pass subject to conservative screen** |
| Content safety | Records must pass a metadata-based exclusion taxonomy and an image-level review after acquisition; uncertainty is quarantine. | **Pass subject to two-stage screen** |
| Removal and retention | Local process: quarantine immediately on a credible concern, revoke the manifest ID, delete asset/derivatives/checkpoints where applicable, log action, and contact `image-requests@artic.edu` if source clarification is required. Review expiry is 90 days after acquisition. | **Pass** |
| Split isolation | A deterministic 70/15/15 split by source ID will be created before media acquisition, with held-out IDs inaccessible to training code. | **Pass subject to manifest audit** |
| Duplicates and leakage | Exact image hash and perceptual-hash checks will be performed after acquisition; title normalization and source-ID rules are applied before acquisition. Held-out items will not participate in training or selection. | **Pass subject to duplicate audit** |
| Reproducibility | The selection query, code revision, random seed, manifest checksum, policy URLs, transforms, and environment will be versioned. | **Pass subject to generated evidence** |

---

## 3. Conservative Eligibility Rules

A candidate must meet every inclusion rule and no exclusion rule. The rule set favors a smaller, cleaner pilot over coverage.

| Rule type | Requirement |
| :--- | :--- |
| Include | `is_public_domain` is exactly `true`; non-empty stable item ID and image ID; non-empty title; non-empty classification or department; official IIIF URL derivable from API configuration. |
| Include | Text target is built only from title, classification, and department; no raw provider description or artist biography is used as model text. |
| Exclude | Metadata contains terms associated with portraiture, people, nudity, sexual content, violence, weapons, death, war, trauma, sacred/religious sensitivity, or anatomy. |
| Exclude | Missing/ambiguous public-domain indicator, absent image reference, missing target text, duplicate normalized title, invalid image dimensions, or incomplete provenance fields. |
| Quarantine | Any item whose metadata creates a rights, privacy, safety, cultural-sensitivity, or task-fit uncertainty. Quarantine is a rejection for this pilot, not a request to infer a favorable answer. |

---

## 4. Retention and Removal Procedure

The retained-pilot package must store an `asset_id` as the join key across the manifest, downloaded image, preprocessing output, training row, checkpoint lineage, and deletion log. A request or credible issue concerning an asset triggers the following fail-closed workflow: immediately block further use, remove the asset from active splits, delete the original and derived copies, invalidate dependent checkpoints where feasible or document the limitation, update the manifest and report, and record the outcome. The data steward should use the Art Institute’s image-licensing contact for source clarification when needed [3].

No asset may remain beyond the 90-day review date without a documented renewal decision. There is no onward redistribution of source images, derived corpus files, or image-containing checkpoints.

---

## 5. Advancement Condition

The next step is a scripted metadata-only candidate selection and audit. If the audit produces fewer than 300 clean candidates or detects any hard-control failure, the pilot will reduce in size or stop rather than relaxing the controls. If the audit passes, the project may acquire only the exact approved manifest assets and no additional material.

## References

[1]: https://www.artic.edu/collection-information/open-access/open-access-images "Art Institute of Chicago — Open Access Images"
[2]: https://api.artic.edu/docs/ "Art Institute of Chicago API Documentation"
[3]: https://www.artic.edu/collection-information/image-licensing "Art Institute of Chicago — Image Licensing"
[4]: T2_4_ART_INSTITUTE_SOURCE_REVIEW_NOTES.md "T2.4 Art Institute Source Review Notes"
[5]: ../Stages/T0_GOVERNANCE_CHARTER.md "T0 Governance Charter"
