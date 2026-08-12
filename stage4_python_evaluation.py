#!/usr/bin/env python3
"""Stage 4 Python visual-token projection contract evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "build"))

import alvs_cpp  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=64)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "Stages" / "stage4_python_results.json")
    args = parser.parse_args()

    generator = np.random.default_rng(20260812)
    color = generator.random((args.height, args.width, 3), dtype=np.float32)
    original = color.copy()
    input_address = int(color.__array_interface__["data"][0])
    atomizer = alvs_cpp.Atomizer()

    result = atomizer.project_multimodal_numpy(
        color, max_levels=2, patch_size=4, retention_ratio=0.25, max_tokens=0, embedding_dimension=4096
    )
    repeat = atomizer.project_multimodal_numpy(
        color, max_levels=2, patch_size=4, retention_ratio=0.25, max_tokens=0, embedding_dimension=4096
    )
    embeddings = np.asarray(result["embeddings"])
    importance = np.asarray(result["importance"])
    source_count = int(result["source_patch_count"])
    retained_count = int(result["retained_token_count"])
    rms = np.sqrt(np.mean(np.square(embeddings), axis=1))

    rejected_noncontiguous = False
    try:
        atomizer.project_multimodal_numpy(np.asfortranarray(color))
    except (TypeError, ValueError):
        rejected_noncontiguous = True

    expected_source_count = ((args.height + 3) // 4) * ((args.width + 3) // 4)
    expected_retained_count = int(np.ceil(expected_source_count * 0.25))
    report = {
        "harness": "AGI-VS Stage 4 Python Projection Evaluation",
        "input_shape": [args.height, args.width, 3],
        "tc_4_python_shape": {
            "embedding_shape": list(embeddings.shape),
            "expected_shape": [expected_retained_count, 4096],
            "pass": bool(embeddings.shape == (expected_retained_count, 4096)),
        },
        "tc_4_python_normalization": {
            "max_rms_error": float(np.max(np.abs(rms - 1.0))),
            "pass": bool(np.max(np.abs(rms - 1.0)) < 1.0e-4),
        },
        "tc_4_python_budget": {
            "source_patch_count": source_count,
            "retained_token_count": retained_count,
            "reduction": 1.0 - retained_count / source_count,
            "importance_nonincreasing": bool(np.all(importance[:-1] >= importance[1:])),
            "pass": bool(
                source_count == expected_source_count
                and retained_count == expected_retained_count
                and np.all(importance[:-1] >= importance[1:])
            ),
        },
        "tc_4_python_determinism": {
            "pass": bool(
                np.array_equal(embeddings, np.asarray(repeat["embeddings"]))
                and np.array_equal(np.asarray(result["patch_y"]), np.asarray(repeat["patch_y"]))
                and np.array_equal(np.asarray(result["patch_x"]), np.asarray(repeat["patch_x"]))
            ),
        },
        "tc_4_python_direct_input": {
            "pointer_matches": int(result["input_address"]) == input_address,
            "binding_declares_no_input_copy": not bool(result["input_copied"]),
            "input_unchanged": bool(np.array_equal(color, original)),
            "pass": bool(
                int(result["input_address"]) == input_address
                and not bool(result["input_copied"])
                and np.array_equal(color, original)
            ),
        },
        "tc_4_python_layout_contract": {"pass": bool(rejected_noncontiguous)},
    }
    report["overall_pass"] = all(value["pass"] for key, value in report.items() if key.startswith("tc_"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
