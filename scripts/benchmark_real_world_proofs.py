#!/usr/bin/env python3
"""Extract representative frozen AGI-VS signals and benchmark each approved proof image.

This script has no fitting, optimization, trainable parameters, or checkpoint writes. It
normalizes each retained proof copy to a letterboxed 512x512 RGB input, invokes the existing
Stage 1–4 Python interface, and records compact numerical signal summaries and timing data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

CANVAS_SIZE = 512
WARMUP_RUNS = 5
MEASURED_RUNS = 30
EMBEDDING_DIMENSION = 4096


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numeric_summary(values: np.ndarray) -> dict[str, float]:
    flat = np.asarray(values, dtype=np.float32).reshape(-1)
    return {
        "mean": float(np.mean(flat)),
        "stddev": float(np.std(flat)),
        "minimum": float(np.min(flat)),
        "p05": float(np.quantile(flat, 0.05)),
        "p50": float(np.quantile(flat, 0.50)),
        "p95": float(np.quantile(flat, 0.95)),
        "maximum": float(np.max(flat)),
    }


def letterbox_rgb(path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    with Image.open(path) as image:
        source = image.convert("RGB")
        original_width, original_height = source.size
        scale = min(CANVAS_SIZE / original_width, CANVAS_SIZE / original_height)
        resized_size = (max(1, round(original_width * scale)), max(1, round(original_height * scale)))
        resized = source.resize(resized_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0))
    offset = ((CANVAS_SIZE - resized_size[0]) // 2, (CANVAS_SIZE - resized_size[1]) // 2)
    canvas.paste(resized, offset)
    pixels = np.ascontiguousarray(np.asarray(canvas, dtype=np.float32) / np.float32(255.0))
    return pixels, {
        "original_size": [original_width, original_height],
        "standardized_size": [CANVAS_SIZE, CANVAS_SIZE],
        "resized_content_size": list(resized_size),
        "letterbox_offset": list(offset),
        "rgb_float32_c_contiguous": bool(pixels.flags.c_contiguous and pixels.dtype == np.float32),
        "standardized_input_sha256": sha256_bytes(pixels.tobytes()),
    }


def project(atomizer: Any, pixels: np.ndarray) -> dict[str, Any]:
    return atomizer.project_multimodal_numpy(
        pixels,
        max_levels=2,
        patch_size=16,
        retention_ratio=0.25,
        max_tokens=32,
        embedding_dimension=EMBEDDING_DIMENSION,
    )


def timing_summary(milliseconds: list[float]) -> dict[str, float]:
    ordered = sorted(milliseconds)
    p95_index = min(len(ordered) - 1, int(np.ceil(len(ordered) * 0.95)) - 1)
    median = float(statistics.median(ordered))
    return {
        "runs": len(milliseconds),
        "minimum_ms": float(min(milliseconds)),
        "median_ms": median,
        "mean_ms": float(statistics.fmean(milliseconds)),
        "p95_ms": float(ordered[p95_index]),
        "maximum_ms": float(max(milliseconds)),
        "fps_equivalent_from_median": float(1000.0 / median),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition-manifest", type=Path, required=True)
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--distance-csv", type=Path, required=True)
    args = parser.parse_args()

    acquisition = json.loads(args.acquisition_manifest.read_text(encoding="utf-8"))
    records = acquisition.get("records", [])
    if acquisition.get("status") != "pass" or len(records) != 8 or acquisition.get("core_training_or_modification") is not False:
        raise RuntimeError("approved eight-record no-training acquisition manifest required")

    sys.path.insert(0, str(args.module_dir.resolve()))
    import alvs_cpp  # type: ignore[import-not-found]

    atomizer = alvs_cpp.Atomizer()
    summaries: list[dict[str, Any]] = []
    pooled_vectors: list[np.ndarray] = []
    asset_ids: list[str] = []

    for record in sorted(records, key=lambda row: row["asset_id"]):
        image_path = Path(record["local_copy"])
        pixels, input_contract = letterbox_rgb(image_path)
        zero_copy = atomizer.zero_copy_probe(pixels)
        accelerated = atomizer.atomize_accelerated_numpy(pixels)
        multiscale = atomizer.atomize_multiscale_numpy(pixels, max_levels=2)
        first = project(atomizer, pixels)
        repeated = project(atomizer, pixels)
        embeddings = np.asarray(first["embeddings"], dtype=np.float32)
        repeated_embeddings = np.asarray(repeated["embeddings"], dtype=np.float32)
        if embeddings.shape != repeated_embeddings.shape or embeddings.shape[1] != EMBEDDING_DIMENSION:
            raise RuntimeError(f"{record['asset_id']}: invalid Stage 4 token shape")
        determinism_error = float(np.max(np.abs(embeddings - repeated_embeddings)))
        if determinism_error > 1.0e-7:
            raise RuntimeError(f"{record['asset_id']}: non-deterministic token output {determinism_error}")
        if not np.isfinite(embeddings).all():
            raise RuntimeError(f"{record['asset_id']}: non-finite token output")

        for _ in range(WARMUP_RUNS):
            project(atomizer, pixels)
        timings: list[float] = []
        for _ in range(MEASURED_RUNS):
            begin = time.perf_counter_ns()
            project(atomizer, pixels)
            timings.append((time.perf_counter_ns() - begin) / 1_000_000.0)

        importance = np.asarray(first["importance"], dtype=np.float32)
        patch_y = np.asarray(first["patch_y"], dtype=np.uint64)
        patch_x = np.asarray(first["patch_x"], dtype=np.uint64)
        token_rms = np.sqrt(np.mean(np.square(embeddings, dtype=np.float64), axis=1))
        ranked = np.argsort(-importance, kind="stable")[:8]
        top_patches = [
            {"patch_y": int(patch_y[index]), "patch_x": int(patch_x[index]), "importance": float(importance[index])}
            for index in ranked
        ]
        pooled = np.mean(embeddings, axis=0, dtype=np.float64).astype(np.float32)
        pooled_vectors.append(pooled)
        asset_ids.append(record["asset_id"])
        summaries.append({
            "asset_id": record["asset_id"],
            "scene_class": record["scene_class"],
            "source_file_title": record["source_file_title"],
            "source_copy_sha256": record["local_copy_sha256"],
            "input_contract": input_contract,
            "interface_integrity": {
                "zero_copy_probe_input_copied": bool(zero_copy["input_copied"]),
                "zero_copy_probe_address_match": int(zero_copy["input_address"]) == int(zero_copy["observed_address"]),
                "project_input_copied": bool(first["input_copied"]),
                "simd_backend": atomizer.simd_backend(),
                "simd_available": bool(atomizer.simd_available()),
                "accelerated_backend": accelerated["backend"],
                "accelerated_worker_threads": int(accelerated["worker_threads"]),
                "accelerated_parallel_enabled": bool(accelerated["parallel_enabled"]),
            },
            "stage1_atomic_signals": {
                "energy": numeric_summary(np.asarray(accelerated["energy"])),
                "flow_x": numeric_summary(np.asarray(accelerated["flow_x"])),
                "flow_y": numeric_summary(np.asarray(accelerated["flow_y"])),
            },
            "stage2_multiscale_signals": {
                "wavelet_level_count": len(multiscale["wavelet_levels"]),
                "wavelet_level_shapes": [list(level["input_shape"]) for level in multiscale["wavelet_levels"]],
                "gate_features": [float(value) for value in np.asarray(multiscale["gate_features"])],
                "gate_weights": [float(value) for value in np.asarray(multiscale["gate_weights"])],
                "complexity": float(multiscale["complexity"]),
                "entropy": float(multiscale["entropy"]),
            },
            "stage4_visual_tokens": {
                "source_patch_count": int(first["source_patch_count"]),
                "retained_token_count": int(first["retained_token_count"]),
                "embedding_dimension": int(first["embedding_dimension"]),
                "embedding_sha256": sha256_bytes(embeddings.tobytes()),
                "pooled_embedding_sha256": sha256_bytes(pooled.tobytes()),
                "token_rms": numeric_summary(token_rms),
                "top_importance_patches": top_patches,
                "repeated_projection_max_abs_error": determinism_error,
            },
            "performance": timing_summary(timings),
        })

    matrix = np.vstack(pooled_vectors).astype(np.float64)
    matrix /= np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
    cosine_distance = 1.0 - matrix @ matrix.T
    args.distance_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.distance_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["asset_id", *asset_ids])
        for index, asset_id in enumerate(asset_ids):
            writer.writerow([asset_id, *[f"{float(value):.9f}" for value in cosine_distance[index]]])

    off_diagonal = [float(cosine_distance[row, column]) for row in range(len(asset_ids)) for column in range(row + 1, len(asset_ids))]
    if any(value <= 1.0e-12 for value in off_diagonal):
        raise RuntimeError("at least one pair of real-world proof images produced an indistinguishable pooled signal")
    report = {
        "schema_version": "1.0",
        "status": "pass",
        "claim": "Frozen AGI-VS Stage 1–4 substrate produced deterministic, non-identical structured signals for each approved real-world proof image; no training or core modification occurred.",
        "acquisition_manifest_sha256": acquisition.get("acquisition_manifest_sha256"),
        "configuration": {
            "standardized_input": "512x512 RGB float32 letterbox; no crop",
            "stage4_max_levels": 2,
            "stage4_patch_size": 16,
            "stage4_retention_ratio": 0.25,
            "stage4_max_tokens": 32,
            "stage4_embedding_dimension": EMBEDDING_DIMENSION,
            "warmup_runs": WARMUP_RUNS,
            "measured_runs": MEASURED_RUNS,
            "training_or_parameter_update": False,
        },
        "environment": {
            "module_dir": str(args.module_dir),
            "platform": platform.platform(),
            "python": sys.version,
            "simd_backend": atomizer.simd_backend(),
        },
        "signal_diversity": {
            "distance_metric": "cosine distance between per-image mean-pooled frozen Stage 4 embeddings",
            "pair_count": len(off_diagonal),
            "minimum_pairwise_distance": float(min(off_diagonal)),
            "maximum_pairwise_distance": float(max(off_diagonal)),
            "mean_pairwise_distance": float(np.mean(off_diagonal)),
            "distance_matrix_csv": str(args.distance_csv),
        },
        "records": summaries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "records": len(summaries),
        "minimum_pairwise_distance": report["signal_diversity"]["minimum_pairwise_distance"],
        "median_ms": {row["asset_id"]: row["performance"]["median_ms"] for row in summaries},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
