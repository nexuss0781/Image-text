# AGI-VS Real-World Observation Proof Set

**Status**: Complete; eight rights-reviewed real-world proof images acquired, processed, and validated
**Purpose**: Demonstrate that the frozen AGI Vision Substrate receives real-world images and converts each one into distinct, reproducible numerical visual signals.
**Boundary**: Observation and benchmark only. No model, semantic encoder, adapter, core C++ implementation, or parameter is trained or changed.

---

## 1. Proof-Set Scope

The proof set will contain a small, intentionally diverse collection of **eight real photographs** spanning city, animal, house/building, landscape, and vehicle scenes. The target source is Wikimedia Commons, restricted to files with explicit item-level **CC0 or public-domain** licensing metadata and a reachable original/download URL. Images with visible people, faces, licence ambiguity, unsafe content, trademarks that dominate the image, or delivery failures will be rejected and replaced before retention.

| Scene class | Target count | Intended visual contrast |
| :--- | ---: | :--- |
| City / skyline | 2 | Dense edges, repeated geometry, depth, high spatial complexity. |
| Animal | 2 | Organic contours, local texture, non-rectilinear shape. |
| House / building | 2 | Architectural structure, rectilinear edges, stable large regions. |
| Landscape / vehicle | 2 | Broad gradients or prominent object boundaries at a distinct visual scale. |

Every approved image must have a source page, direct delivery URL, author/attribution field when provided, licence value, public-domain/CC0 evidence, retrieval time, source checksum, and a local content checksum. All approved source media will be retained under `Proofs/images/` solely for this benchmark and committed with its source record. The proof set is not a training corpus.

---

## 2. Input and Signal Contract

Each source image will be deterministically converted to an RGB `float32`, C-contiguous **512 × 512** letterboxed input without cropping. This normalizes the benchmark workload while preserving all image content. The original source size and the derived-input checksum will be recorded.

For every image, the proof report will record the following frozen, non-learned outputs:

| Signal family | Representative recorded evidence |
| :--- | :--- |
| Stage 1 atomic signals | Mean, standard deviation, minimum, maximum, and selected quantiles of energy, horizontal flow, and vertical flow. |
| Stage 2 multi-scale signals | Wavelet-level shapes, semantic-gate feature vector, gate weights, complexity, and entropy. |
| Stage 4 visual tokens | Retained-token count, source-patch count, 4,096 embedding dimensions, token RMS range, global embedding checksum, and top importance-patch locations. |
| Interface integrity | C-contiguous input confirmation, zero-copy flag, observed input address consistency, and backend metadata. |
| Performance | Warmed, repeated per-image latency distribution on the same standardized input: median, p95, minimum, maximum, mean, and frames-per-second equivalent. |

A compact signal digest and signal-distance matrix will compare images. The digest does not identify the meaning of a city, animal, or house; it proves that their distinct visual structures generate distinct substrate outputs.

---

## 3. Hard Controls and Pass Criteria

| Control | Pass condition |
| :--- | :--- |
| Rights and delivery | Each file has explicit item-level CC0/public-domain metadata and a recorded source page and delivery URL. |
| Privacy and safety | Visual review confirms no discernible people/faces and no sensitive content. |
| Data boundary | Exactly eight approved proof images; no additional discovery results retained. |
| No training | Benchmark script neither calls fitting code nor writes model weights. |
| Determinism | Repeated projection of each standardized input has a maximum token difference no greater than `1e-7`. |
| Signal diversity | No two 4,096-dimensional pooled signal vectors have an exact identical checksum; pairwise distances are recorded. |
| Performance | Each image has at least 30 post-warmup measurements, with configuration and hardware/backend recorded. |
| Regression safety | The complete Stage 1–5 CTest suite passes after the observation benchmark. |

The final proof must describe the exact claim: **the frozen substrate maps real images to measurable and different visual signals at recorded speed.** It must not claim that the system has semantic understanding, video-event understanding, or AGI-level intelligence.
