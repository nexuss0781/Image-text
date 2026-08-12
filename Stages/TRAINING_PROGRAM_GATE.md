# AGI-VS Data Curation, Training & Fine-Tuning Program Gate

**Project**: AGI Vision Substrate (AGI-VS)  
**Status**: Proposed post-Stage-5 program; **no corpus has been downloaded, reconstructed, or used for training**  
**Decision Required**: Explicit approval is required before data acquisition, corpus reconstruction, model training, or fine-tuning begins.

---

## 1. Purpose and Non-Claim

The completed Stage 1–5 work delivers a performant, testable **vision software substrate**. It does not constitute a trained AGI system, a pretrained vision-language model, or evidence of general intelligence. The next program must therefore focus on auditable dataset selection, lawful access, training, fine-tuning, and held-out evaluation—not on assigning an AGI label in advance.

> **Program objective:** train and evaluate an evidence-backed multimodal vision system on a documented, licensed or permissioned corpus, using the AGI-VS substrate as its efficient visual front end. Advancement is based on capability and safety gates, not an unsupported claim of AGI.

Large web-derived image-text indexes can be useful research inputs but are not blanket media licences. LAION describes its datasets as internet indexes containing URLs and associated alt text rather than original media, and states that downstream users reconstruct any selected media themselves [2]. Likewise, the dataset-provenance literature finds high rates of missing or miscategorized licences and recommends source-level lineage rather than trusting an aggregate label [4].

---

## 2. Dataset-Selection Policy

The selection strategy is **permissioned-first, provenance-first, quality-first**. A source may enter the pilot only after a dataset card, licence record, source URL or provider record, content-policy decision, PII review, and removal/takedown process are present. Aggregated web indexes may be considered only as discovery layers; every reconstructed item must satisfy the project allow-list before retention or training use.

| Priority | Candidate Source Family | Intended Contribution | Required Decision Before Use |
| :--- | :--- | :--- |
| **1** | Permissioned, first-party, or commissioned image–text data | Core production-quality visual grounding and domain coverage | Written use permission, documented consent where applicable, and versioned source agreement. |
| **2** | Open Images | Object/relationship/segmentation-oriented supervised grounding; the official description identifies roughly 9 million annotated images and multiple annotation modalities [5]. | Confirm current image and annotation terms, attribution handling, and downstream-use compatibility for the selected split. |
| **3** | COCO and other benchmark-specific datasets | Held-out evaluation for recognition, detection, segmentation, and captioning; COCO describes itself as a large-scale object-detection, segmentation, and captioning dataset [6]. | Benchmark licence and split-specific use review; keep evaluation sets isolated from training. |
| **4** | DataComp-style filtered candidate pools | Controlled data-curation experiments; DataComp is explicitly designed to benchmark dataset design for fixed CLIP-style models [7]. | Review the applicable access terms and construct a provenance-filtered subset; do not treat a web pool as pre-cleared training data. |
| **5** | LAION/Common-Crawl-derived discovery indexes | Research-only candidate discovery and retrieval analysis; LAION-5B reports image–text pairs with quality and content-detection metadata [3]. | Per-item provenance/rights screening, content filters, takedown support, and explicit approval for every retained subset. |

**Initial recommendation:** begin with a small, documented mix of permissioned or clearly licensed data plus curated Open Images-style supervised material. Use COCO-like assets only as held-out benchmarks where permitted. Defer all web-index reconstruction until the allow-list, provenance database, and removal mechanism have passed review.

---

## 3. Training Architecture

The first trainable component should be a **cross-modal adapter**, not an unbounded end-to-end foundation-model training run. It will consume Stage 4’s 4096-dimensional visual-token interface, map tokens to the selected language-model embedding space, and train under frozen or tightly controlled visual and language backbones. This limits compute, supports ablation, and makes the source of any improvement measurable.

| Layer | Initial Training Decision | Verification Requirement |
| :--- | :--- | :--- |
| Stage 1–3 atomic vision core | Freeze as reference implementation | Preserve numerical contracts and current regression suite. |
| Stage 4 token projector | Freeze for baseline; optionally train a documented adapter replacement later | Compare token count, RMS stability, and downstream performance against the deterministic baseline. |
| Cross-modal adapter | Train first | Validate shape, loss, calibration, retrieval, captioning/VQA tasks, and held-out generalization. |
| Selected VLM/LLM backbone | Begin frozen; consider parameter-efficient fine-tuning only after pilot success | Publish exact model version, licence, parameter scope, and evaluation deltas. |
| Safety/quality heads | Train only from reviewed data with independent held-out validation | Measure harmful-content, privacy, and hallucination-related failure modes under declared protocols. |

---

## 4. Sequential Execution Plan and Gates

| Phase | Deliverable | Hard Gate to Advance |
| :--- | :--- | :--- |
| **T0: Governance** | Intended-use statement, risk register, acquisition policy, data-retention/takedown process, and evaluation protocol | Owner approval and legal/privacy review appropriate to the deployment jurisdiction. |
| **T1: Dataset registry** | Machine-readable ledger with dataset version, source, licence/terms, access date, content filters, provenance confidence, and split assignment | No missing required fields; every pilot item linked to a reviewable source record. |
| **T2: Pilot curation** | Small representative pilot corpus and frozen held-out set | Duplicate/leakage audit, PII/content-filter report, and sampling-quality review pass. |
| **T3: Adapter baseline** | Reproducible training configuration, random seeds, checkpoints, loss curves, and substrate ablations | Training stable; no regression in Stage 1–5 contracts; held-out task baseline recorded. |
| **T4: Fine-tuning** | Parameter-efficient fine-tune only where licence and model terms allow it | Better than frozen baseline on predeclared held-out metrics without unacceptable safety, fairness, or provenance failures. |
| **T5: Scale decision** | Cost, hardware, energy, safety, and quality report | Owner approves a bounded scale-up budget after reviewing evidence. |
| **T6: Release assessment** | Model card, data card, evaluation report, known limitations, and rollback plan | Independent reproducibility review and deployment-specific acceptance tests. |

---

## 5. Evaluation Framework for AGI-Vision Eligibility

The project should use the phrase **AGI-Vision eligibility** only as an internal research target meaning that the system has met explicitly declared visual, language-grounding, robustness, efficiency, and safety thresholds. It must not be presented as proof of general intelligence.

| Capability Dimension | Minimum Evidence Before Advancement |
| :--- | :--- |
| Visual perception | Held-out detection, segmentation, recognition, OCR/document, and spatial-relation evaluation relevant to the intended domain. |
| Vision-language grounding | Held-out image–text retrieval, captioning, and question-answering evaluation using a target-model-specific protocol. |
| Compositional reasoning | Controlled multi-object, multi-step spatial, temporal, and counterfactual tests with error taxonomy. |
| Robustness | Corruptions, distribution shifts, adversarial prompt/image conditions, and calibration assessment. |
| Efficiency | End-to-end latency, throughput, token budget, memory, and energy measurements on declared target hardware. |
| Data stewardship | Dataset registry completeness, source/terms evidence, removal handling, deduplication/leakage checks, and PII/content-filter reports. |
| Safety and human impact | Predefined misuse, harmful-content, privacy, bias, and uncertain-output handling tests with documented mitigations. |

---

## 6. Immediate Approval Gate

Approval to begin this program should unlock **T0–T1 only**: governance, dataset discovery, candidate comparison, and creation of the provenance registry. It must **not** automatically authorize downloading/reconstructing copyrighted media, ingesting personal data, or starting large-scale training.

A separate approval will be requested before T2 pilot acquisition and again before T3 model training. This staged approach prevents irreversible training decisions before corpus rights, provenance, safety controls, and evaluation criteria have been examined.

**Required response to unlock T0–T1:** `Approve Training Program T0-T1`

---

## References

[1]: https://commoncrawl.org/ "Common Crawl — Open Web Data"
[2]: https://laion.ai/faq/ "LAION FAQ — Dataset Index, Reconstruction, and Takedown Context"
[3]: https://proceedings.neurips.cc/paper_files/paper/2022/hash/a1859debfb3b59d094f3504d5ebb6c25-Abstract-Datasets_and_Benchmarks.html "LAION-5B — NeurIPS 2022"
[4]: https://www.nature.com/articles/s42256-024-00878-8 "A Large-Scale Audit of Dataset Licensing and Attribution in AI"
[5]: https://storage.googleapis.com/openimages/web/factsfigures_v7.html "Open Images V7 — Description"
[6]: https://cocodataset.org/ "COCO Dataset"
[7]: https://github.com/mlfoundations/datacomp "DataComp — Dataset Design Benchmark"
