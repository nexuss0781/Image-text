#!/usr/bin/env python3
"""Stage 3 Python dispatch contract evaluation for AGI-VS."""

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

TOLERANCE = 1.0e-6


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "Stages" / "stage3_python_results.json")
    args = parser.parse_args()

    generator = np.random.default_rng(20260812)
    color = generator.random((args.height, args.width, 3), dtype=np.float32)
    original = color.copy()
    pointer = int(color.__array_interface__["data"][0])
    atomizer = alvs_cpp.Atomizer()

    reference_energy, reference_flow_x, reference_flow_y = atomizer.atomize_numpy(color)
    warmup = atomizer.atomize_accelerated_numpy(color)
    times_ms: list[float] = []
    for _ in range(args.iterations):
        start = time.perf_counter_ns()
        result = atomizer.atomize_accelerated_numpy(color)
        times_ms.append((time.perf_counter_ns() - start) / 1_000_000.0)

    max_error = max(
        float(np.max(np.abs(reference_energy - result["energy"]))),
        float(np.max(np.abs(reference_flow_x - result["flow_x"]))),
        float(np.max(np.abs(reference_flow_y - result["flow_y"]))),
    )
    metadata = atomizer.zero_copy_metadata(color)
    rejected_noncontiguous = False
    try:
        atomizer.atomize_accelerated_numpy(np.asfortranarray(color))
    except (TypeError, ValueError):
        rejected_noncontiguous = True

    median_ms = float(np.median(np.asarray(times_ms)))
    report = {
        "harness": "AGI-VS Stage 3 Python Dispatch Evaluation",
        "input_shape": [args.height, args.width, 3],
        "tc_3_python_equivalence": {
            "maximum_abs_error": max_error,
            "threshold": TOLERANCE,
            "pass": bool(max_error < TOLERANCE),
        },
        "tc_3_python_direct_input": {
            "pointer_matches": int(metadata["input_address"]) == pointer,
            "binding_declares_no_input_copy": not bool(metadata["input_copied"]),
            "input_unchanged": bool(np.array_equal(color, original)),
            "pass": bool(
                int(metadata["input_address"]) == pointer
                and not bool(metadata["input_copied"])
                and np.array_equal(color, original)
            ),
        },
        "tc_3_python_dispatch": {
            "backend": str(result["backend"]),
            "worker_threads": int(result["worker_threads"]),
            "simd_enabled": bool(result["simd_enabled"]),
            "parallel_enabled": bool(result["parallel_enabled"]),
            "gpu_available": bool(result["gpu_available"]),
            "median_dispatch_ms": median_ms,
            "pass": bool(
                result["backend"] in {"cpu-openmp-avx", "cpu-openmp-scalar", "cpu-avx-reference", "cpu-reference"}
                and int(result["worker_threads"]) >= 1
                and median_ms > 0.0
            ),
        },
        "tc_3_python_layout_contract": {"pass": bool(rejected_noncontiguous)},
    }
    report["overall_pass"] = all(value["pass"] for key, value in report.items() if key.startswith("tc_"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
