#!/usr/bin/env python3
"""Stage 2 Python API contract evaluation for AGI-VS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "build"))

import alvs_cpp  # noqa: E402


TOLERANCE = 1.0e-6


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=193)
    parser.add_argument("--width", type=int, default=257)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "Stages" / "stage2_python_results.json")
    args = parser.parse_args()

    generator = np.random.default_rng(20260812)
    color = generator.random((args.height, args.width, 3), dtype=np.float32)
    input_pointer = int(color.__array_interface__["data"][0])
    input_snapshot = color.copy()
    atomizer = alvs_cpp.Atomizer()

    metadata = atomizer.zero_copy_metadata(color)
    result = atomizer.atomize_multiscale_numpy(color, max_levels=2)
    energy = np.asarray(result["energy"])
    expected_energy = (
        color[..., 0] * np.float32(0.2126)
        + color[..., 1] * np.float32(0.7152)
        + color[..., 2] * np.float32(0.0722)
    )
    levels = result["wavelet_levels"]
    gate_features = np.asarray(result["gate_features"])
    gate_weights = np.asarray(result["gate_weights"])

    expected_level_shapes = [
        [(args.height + 1) // 2, (args.width + 1) // 2],
        [(args.height + 3) // 4, (args.width + 3) // 4],
    ]
    level_shapes = [list(np.asarray(level["approximation"]).shape) for level in levels]
    all_bands_shaped = all(
        np.asarray(level[band]).shape == tuple(level_shapes[index])
        for index, level in enumerate(levels)
        for band in ("detail_horizontal", "detail_vertical", "detail_diagonal")
    )

    rejected_noncontiguous = False
    try:
        atomizer.atomize_multiscale_numpy(np.asfortranarray(color), max_levels=2)
    except (TypeError, ValueError):
        rejected_noncontiguous = True

    max_error = float(np.max(np.abs(energy - expected_energy)))
    gate_sum = float(np.sum(gate_weights))
    results = {
        "harness": "AGI-VS Stage 2 Python API Evaluation",
        "input_shape": [args.height, args.width, 3],
        "tc_2_python_direct_input": {
            "pointer_matches": int(metadata["input_address"]) == input_pointer,
            "binding_declares_no_input_copy": not bool(metadata["input_copied"]),
            "input_unchanged": bool(np.array_equal(color, input_snapshot)),
            "pass": int(metadata["input_address"]) == input_pointer
            and not bool(metadata["input_copied"])
            and bool(np.array_equal(color, input_snapshot)),
        },
        "tc_2_python_numerical": {
            "maximum_energy_error": max_error,
            "threshold": TOLERANCE,
            "pass": bool(max_error < TOLERANCE),
        },
        "tc_2_python_pyramid": {
            "level_count": len(levels),
            "observed_level_shapes": level_shapes,
            "expected_level_shapes": expected_level_shapes,
            "all_detail_band_shapes_valid": all_bands_shaped,
            "pass": bool(len(levels) == 2 and level_shapes == expected_level_shapes and all_bands_shaped),
        },
        "tc_2_python_gate": {
            "feature_count": int(gate_features.size),
            "weight_count": int(gate_weights.size),
            "weight_sum": gate_sum,
            "complexity": float(result["complexity"]),
            "entropy": float(result["entropy"]),
            "pass": bool(
                gate_features.size == 4
                and gate_weights.size == 6
                and abs(gate_sum - 1.0) < TOLERANCE
                and bool(np.all(gate_weights >= 0.0))
                and np.isfinite(result["complexity"])
                and np.isfinite(result["entropy"])
            ),
        },
        "tc_2_python_layout_contract": {"pass": bool(rejected_noncontiguous)},
    }
    results["overall_pass"] = all(value["pass"] for key, value in results.items() if key.startswith("tc_"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
