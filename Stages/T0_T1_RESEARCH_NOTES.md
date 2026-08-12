# T0–T1 Research Notes: Governance & Candidate-Dataset Evidence

**Scope**: Approved discovery and governance only. No dataset content has been acquired, reconstructed, retained, or used for training.

| Source | Key Finding | T0–T1 Design Decision |
| :--- | :--- | :--- |
| NIST AI Risk Management Framework | NIST describes AI RMF as a voluntary framework intended to incorporate trustworthiness considerations into AI design, development, use, and evaluation. | Use an intended-use statement, risk register, documented controls, review evidence, and release gates rather than informal dataset selection. |
| Hugging Face Dataset Cards documentation | Dataset cards provide users context about dataset contents and responsible use; the documentation identifies metadata such as licence, language, and size. | Every candidate registry entry requires an evidence URL, terms/licence status, scope, data modality, estimated scale, known limitations, and review status. |
| Open Images V7 official description | The source describes roughly 9 million images with labels, boxes, segmentations, visual relationships, localized narratives, and point-level labels. | Treat Open Images as a high-value **candidate** for supervised visual grounding; still require split-specific terms, attribution, and downstream-use review before pilot acquisition. |
| LAION FAQ and LAION-5B paper | LAION describes its releases as indexes with URL/alt-text metadata, while the paper reports large-scale image–text pairs and detection metadata. | Treat web indexes only as discovery candidates, never as blanket licences; reconstruction and retention remain gated by source-level review. |
| Data Provenance Initiative audit | The cited audit reports that licence documentation can be sparse or miscategorized. | Reject unknown or ambiguous terms from the initial pilot; retain evidence at the source rather than trusting an aggregator label. |

## References

[1]: https://www.nist.gov/itl/ai-risk-management-framework "NIST AI Risk Management Framework"
[2]: https://huggingface.co/docs/hub/en/datasets-cards "Hugging Face Dataset Cards"
[3]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[4]: https://laion.ai/faq/ "LAION FAQ"
[5]: https://proceedings.neurips.cc/paper_files/paper/2022/hash/a1859debfb3b59d094f3504d5ebb6c25-Abstract-Datasets_and_Benchmarks.html "LAION-5B"
[6]: https://www.nature.com/articles/s42256-024-00878-8 "A Large-Scale Audit of Dataset Licensing and Attribution in AI"

| COCO official site | The site identifies COCO as Common Objects in Context and exposes dataset, task, evaluation, and terms-of-use materials. | Treat COCO as a held-out evaluation candidate; verify the relevant release terms and preserve split isolation before any use. |
| DataComp repository | DataComp frames curation as a benchmark with fixed model settings over public-web image–text pools and explicitly describes acquisition tooling and multi-scale storage requirements. | Treat DataComp as a methodology/curation benchmark, not as pre-cleared training media; do not run its download tooling during T0–T1. |

[7]: https://cocodataset.org/ "COCO — Common Objects in Context"
[8]: https://github.com/mlfoundations/datacomp "DataComp — Dataset Design Benchmark"

| Open Images V7 licensing section | The official page states Google LLC licenses annotations under CC BY 4.0 and lists images as CC BY 2.0, while expressly warning that it makes no representation or warranty about each image’s licence status and advising users to verify each image. | The T2 proposal may use Open Images only as a **manually verified, finite candidate list**; bulk acquisition, a blanket licence assumption, or unverified item retention is disallowed. |
| Creative Commons BY 2.0 deed | The deed permits sharing/adaptation subject to attribution, licence-link, and change-indication conditions, while noting no warranties and that privacy, publicity, and moral rights may require additional permissions. | A per-item attribution/provenance record and review for additional rights are mandatory for any candidate item; licence visibility does not eliminate privacy or publicity review. |

[9]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses "Open Images V7 — Licences"
[10]: https://creativecommons.org/licenses/by/2.0/ "Creative Commons Attribution 2.0 Generic"
