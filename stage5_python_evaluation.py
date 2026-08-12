#!/usr/bin/env python3
"""Stage 5 Python CPU production-path validation for AGI-VS."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "build"))

import alvs_cpp  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "Stages" / "stage5_python_results.json")
    args = parser.parse_args()

    generator = np.random.default_rng(20260812)
    color = generator.random((args.height, args.width, 3), dtype=np.float32)
    original = color.copy()
    atomizer = alvs_cpp.Atomizer()

    accelerated = atomizer.atomize_accelerated_numpy(color)
    multiscale = atomizer.atomize_multiscale_numpy(color, max_levels=2)
    projection = atomizer.project_multimodal_numpy(
        color, max_levels=2, patch_size=4, retention_ratio=0.25, max_tokens=0, embedding_dimension=4096
    )
    errors = [
        float(np.max(np.abs(np.asarray(accelerated["energy"]) - np.asarray(multiscale["energy"])))),
        float(np.max(np.abs(np.asarray(accelerated["flow_x"]) - np.asarray(multiscale["flow_x"])))),
        float(np.max(np.abs(np.asarray(accelerated["flow_y"]) - np.asarray(multiscale["flow_y"])))),
    ]
    samples_ms: list[float] = []
    for _ in range(args.iterations):
        start = time.perf_counter_ns()
        projection = atomizer.project_multimodal_numpy(
            color, max_levels=2, patch_size=4, retention_ratio=0.25, max_tokens=0, embedding_dimension=4096
        )
        samples_ms.append((time.perf_counter_ns() - start) / 1_000_000.0)

    rejected_noncontiguous = False
    try:
        atomizer.project_multimodal_numpy(np.asfortranarray(color))
    except (TypeError, ValueError):
        rejected_noncontiguous = True

    expected_tokens = int(np.ceil(((args.height + 3) // 4) * ((args.width + 3) // 4) * 0.25))
    embeddings = np.asarray(projection["embeddings"])
    report = {
        "harness": "AGI-VS Stage 5 Python Production Validation",
        "input_shape": [args.height, args.width, 3],
        "tc_5_python_pipeline": {
            "backend": str(accelerated["backend"]),
            "maximum_layer_error": max(errors),
            "embedding_shape": list(embeddings.shape),
            "expected_embedding_shape": [expected_tokens, 4096],
            "pass": bool(max(errors) < 1.0e-6 and embeddings.shape == (expected_tokens, 4096)),
        },
        "tc_5_python_direct_contract": {
            "input_unchanged": bool(np.array_equal(color, original)),
            "input_copied": bool(projection["input_copied"]),
            "pass": bool(np.array_equal(color, original) and not bool(projection["input_copied"])),
        },
        "tc_5_python_latency": {
            "median_ms": float(np.median(np.asarray(samples_ms))),
            "p95_ms": float(np.percentile(np.asarray(samples_ms), 95)),
            "pass": bool(np.all(np.isfinite(np.asarray(samples_ms))) and min(samples_ms) > 0.0),
        },
        "tc_5_python_layout_contract": {"pass": bool(rejected_noncontiguous)},
    }
    report["overall_pass"] = all(value["pass"] for key, value in report.items() if key.startswith("tc_"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
