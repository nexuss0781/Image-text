#!/usr/bin/env python3
"""Stage 1 Python binding evaluation for AGI-VS.

This harness verifies that an HxWx3 NumPy float32 input is accepted without a
format-conversion copy, measures only metadata handoff latency, and checks the
numerical output of the direct native atomization path.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent
BUILD_DIR = REPO_ROOT / "build"
sys.path.insert(0, str(BUILD_DIR))

import alvs_cpp  # noqa: E402


THRESHOLD_MS = 0.15
NUMERIC_TOLERANCE = 1.0e-6


def percentile(values: list[float], percentile_value: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile_value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--metadata-iterations", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "Stages" / "stage1_python_results.json")
    args = parser.parse_args()

    if args.height <= 0 or args.width <= 0 or args.metadata_iterations <= 0:
        raise ValueError("Dimensions and metadata iterations must be positive")

    generator = np.random.default_rng(20260811)
    color = generator.random((args.height, args.width, 3), dtype=np.float32)
    atomizer = alvs_cpp.Atomizer()
    expected_address = int(color.__array_interface__["data"][0])

    # Warm the binding and dynamic loader before timing metadata handoff.
    warmup = atomizer.zero_copy_metadata(color)
    handoff_samples_ms: list[float] = []
    for _ in range(args.metadata_iterations):
        start_ns = time.perf_counter_ns()
        metadata = atomizer.zero_copy_metadata(color)
        handoff_samples_ms.append((time.perf_counter_ns() - start_ns) / 1_000_000.0)

    probe = atomizer.zero_copy_probe(color)
    energy = np.asarray(probe["energy"])
    expected_energy = (
        color[..., 0] * np.float32(0.2126)
        + color[..., 1] * np.float32(0.7152)
        + color[..., 2] * np.float32(0.0722)
    )
    max_energy_error = float(np.max(np.abs(energy - expected_energy)))

    rejected_noncontiguous = False
    try:
        atomizer.zero_copy_metadata(np.asfortranarray(color))
    except (TypeError, ValueError):
        rejected_noncontiguous = True

    median_handoff_ms = float(np.median(np.asarray(handoff_samples_ms)))
    p95_handoff_ms = percentile(handoff_samples_ms, 95.0)
    address_match = (
        int(warmup["input_address"]) == expected_address
        and int(metadata["input_address"]) == expected_address
        and int(probe["input_address"]) == expected_address
        and int(probe["observed_address"]) == expected_address
    )
    zero_copy_declared = not bool(warmup["input_copied"]) and not bool(probe["input_copied"])
    output_shape_valid = energy.shape == (args.height, args.width) and energy.dtype == np.float32

    results = {
        "harness": "AGI-VS Stage 1 Python Binding Evaluation",
        "input_shape": [args.height, args.width, 3],
        "input_bytes": int(color.nbytes),
        "simd_backend": atomizer.simd_backend(),
        "tc_1_2": {
            "name": "zero-copy pybind11 handoff",
            "input_address_matches_native_pointer": address_match,
            "binding_declares_no_input_copy": zero_copy_declared,
            "median_metadata_handoff_ms": median_handoff_ms,
            "p95_metadata_handoff_ms": p95_handoff_ms,
            "threshold_ms": THRESHOLD_MS,
            "pass": address_match and zero_copy_declared and median_handoff_ms < THRESHOLD_MS,
        },
        "tc_1_3_python": {
            "name": "direct-path Rec. 709 numerical check",
            "maximum_absolute_error": max_energy_error,
            "threshold": NUMERIC_TOLERANCE,
            "output_shape_valid": output_shape_valid,
            "pass": max_energy_error < NUMERIC_TOLERANCE and output_shape_valid,
        },
        "tc_1_7": {
            "name": "non-contiguous input rejection",
            "pass": rejected_noncontiguous,
        },
    }
    results["overall_pass"] = all(
        test["pass"] for key, test in results.items() if key.startswith("tc_")
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
