# T2.4 Art Institute Source Review Notes

**Scope**: Official-policy and metadata-interface review. No image media, thumbnails, IIIF resources, or manifests were downloaded or retained.

| Review point | Official evidence | Governance consequence |
| :--- | :--- | :--- |
| Item-level public-domain flag | The official artwork API exposes an `is_public_domain` field alongside a stable `id`, `title`, `image_id`, `department_title`, `classification_title`, and `subject_titles`. A minimal one-record response confirmed these fields are delivered by the provider. | The future candidate manifest can be built from finite, structured metadata and can exclude any record whose `is_public_domain` field is not `true`. |
| Image reference and provenance | The API returns `image_id` and the response configuration exposes the official IIIF base URL. | A later approved media acquisition can be constrained to provider-generated IIIF URLs derived from manifest fields, rather than arbitrary web URLs. |
| API data licence versus image eligibility | The inspected API response states that most returned metadata is CC0, while its description field is CC BY 4.0. The Art Institute’s image policy separately applies to images carrying its “CC0 Public Domain Designation.” | Metadata licensing must not be conflated with image rights. The retained pilot must require both `is_public_domain: true` and the documented first-party image-policy evidence; raw provider descriptions will not be retained as training text. |
| Non-eligible default record | The bounded API check returned an item with `is_public_domain: false`. | The review gate correctly rejects non-public-domain records even where public metadata and an image reference are present. |

| CC0 image policy and inquiry route | The Institute’s official image-licensing page repeats that only images with the “CC0 Public Domain Designation” are offered for unrestricted use and identifies `image-requests@artic.edu` for general image-licensing inquiries. The page again states that the user is responsible for any needed third-party permissions. | The local removal/escalation record will identify the institute’s image-licensing contact, but a credible third-party-rights, privacy, or safety concern will trigger immediate local quarantine and deletion before any external response. Assets without the explicit CC0 designation remain excluded. |
| Attribution context | The Institute requests a standard creator/title/date/museum caption, with this object information stated to be CC0. | The pilot will preserve source attribution fields in its manifest and data card even where attribution is not a legal condition of CC0 use. |

## References

[1]: https://api.artic.edu/docs/ "Art Institute of Chicago API Documentation"
[2]: https://api.artic.edu/api/v1/artworks?fields=id,title,is_public_domain,image_id,department_title,classification_title,subject_titles,thumbnail&limit=1 "Art Institute of Chicago API — minimal artwork metadata response"
[3]: https://www.artic.edu/collection-information/open-access/open-access-images "Art Institute of Chicago — Open Access Images"
[4]: https://www.artic.edu/collection-information/image-licensing "Art Institute of Chicago — Image Licensing"
[5]: https://www.artic.edu/terms "Art Institute of Chicago — Terms"
