# T2 Adapter-Baseline Evaluation Plan

**Status**: Evaluation design only; no pilot data or training run exists  
**Purpose**: Define measurable success/failure criteria before any future training decision

---

## 1. Baseline Principle

The first future learning experiment must evaluate a small cross-modal adapter against the existing deterministic Stage 4 visual-token interface. Stage 1–3 vision operations remain frozen. The adapter may only be considered after the approved pilot data manifest, split isolation, and source controls are in place.

The experiment compares two conditions under identical data splits, prompts/tasks, random seeds, hardware declaration, and optimization budget:

| Condition | Trainable Components | Purpose |
| :--- | :--- | :--- |
| **B0: Deterministic-token baseline** | None in the visual substrate; any language-side baseline explicitly declared | Establishes current interface capability and failure taxonomy. |
| **B1: Adapter baseline** | Documented cross-modal adapter only | Measures whether learning improves declared held-out visual grounding tasks. |

No results may be described as general intelligence. The only allowable claims are those supported by predeclared held-out metrics and documented limitations.

---

## 2. Data and Split Controls

Before any training run, all records must have a stable manifest identifier, source/terms evidence, filter decision, and deterministic split assignment. The held-out partition must be write-protected, unavailable to model-selection workflows, and checked for perceptual/text duplicate overlap with training and development partitions. External benchmarks must be declared before use and checked for known contamination risks.

| Split | Purpose | Permitted Use |
| :--- | :--- | :--- |
| Training | Fit the adapter | Gradient updates only. |
| Development | Select hyperparameters and stopping point | No final headline metric. |
| Held-out | Final measured comparison | No tuning, prompt iteration, or repeated manual inspection driven by results. |
| Red-team | Safety/privacy/robustness probes | Failure taxonomy and mitigation evaluation only. |

---

## 3. Required Measurements

| Dimension | Minimum Measurement | Failure / Stop Condition |
| :--- | :--- | :--- |
| Software integrity | Stage 1–5 CTest and Python contracts before and after experiment | Any regression blocks the experiment. |
| Training stability | Loss curve, gradient norms, numerical exceptions, seed reproducibility | Divergence, NaN/Inf, or irreproducible run blocks advancement. |
| Held-out task quality | Predeclared visual-grounding metric appropriate to approved annotations | No improvement over B0, or unsupported metric substitution, requires review. |
| Token efficiency | Token count, embedding dimension, latency, and peak memory vs B0 | Unexplained efficiency regression requires review. |
| Calibration | Confidence/error or abstention analysis where model emits confidence | Unsafe or uncalibrated behavior requires mitigation review. |
| Robustness | Declared perturbation/corruption and distribution-shift checks | Material unreviewed regressions require review. |
| Safety/privacy | Red-team findings linked to dataset and intended-use risks | Severe unresolved failure blocks scale-up. |
| Provenance | Training manifest checksum, data-card IDs, source terms evidence | Missing or altered evidence invalidates the result. |

---

## 4. Reproducibility Record

Every run must record: code commit, substrate manifest, adapter architecture/version, selected base model and licence, environment and hardware, configuration, random seed, data manifest checksum, filter version, split-manifest checksum, checkpoint hash, metric code version, and complete metric output. A run lacking this record is not evidence for a later scale-up decision.

---

## 5. T2 Deliverable Boundary

This plan is ready for a later controlled pilot but does not authorize data acquisition or training. Its role is to prevent a corpus or model from being created without a precommitted way to measure quality, safety, efficiency, and provenance.
