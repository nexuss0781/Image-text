#!/usr/bin/env python3
"""Run the bounded T2.5 adapter baseline on the project-owned scene corpus.

B0 uses a fixed deterministic random projection from frozen Stage 4 visual tokens. B1 fits
only a ridge-regression adapter on the declared training split. Development chooses alpha;
held-out records are used once for final measurements and never enter fitting or selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


TEXT_DIMENSION = 52
COLOR_OFFSET = 0
SHAPE_OFFSET = 18
SIZE_OFFSET = 33
COUNT_OFFSET = 42
RELATION_OFFSET = 44
COLORS = ("red", "blue", "green", "yellow", "purple", "orange")
SHAPES = ("circle", "square", "triangle", "diamond", "hexagon")
SIZES = ("small", "medium", "large")
RELATIONS = ("left of", "right of", "above", "below")


@dataclass
class Metrics:
    recall_at_1: float
    recall_at_5: float
    mean_reciprocal_rank: float
    attribute_f1: float
    attribute_slot_accuracy: float
    relation_accuracy: float

    def as_dict(self) -> dict[str, float]:
        return {
            "recall_at_1": self.recall_at_1,
            "recall_at_5": self.recall_at_5,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
            "attribute_f1": self.attribute_f1,
            "attribute_slot_accuracy": self.attribute_slot_accuracy,
            "relation_accuracy": self.relation_accuracy,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_rows(values: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def normalize_vector(values: np.ndarray) -> np.ndarray:
    return values / max(float(np.linalg.norm(values)), 1e-8)


def text_embedding(record: dict[str, Any]) -> np.ndarray:
    vector = np.zeros(TEXT_DIMENSION, dtype=np.float32)
    objects = record["objects"]
    for index, obj in enumerate(objects):
        if index >= 3:
            break
        vector[COLOR_OFFSET + index * len(COLORS) + COLORS.index(obj["color"])] = 1.0
        vector[SHAPE_OFFSET + index * len(SHAPES) + SHAPES.index(obj["shape"])] = 1.0
        vector[SIZE_OFFSET + index * len(SIZES) + SIZES.index(obj["size"])] = 1.0
    vector[COUNT_OFFSET + (len(objects) - 2)] = 1.0
    # Caption relations are object 0 relative to object 1, and object 2 relative to object 0 if present.
    relation_rows = record["attributes"]["relations"]
    first_relation = relation_rows[0]["relation"]
    vector[RELATION_OFFSET + RELATIONS.index(first_relation)] = 1.0
    if len(objects) == 3:
        third_relation = next(
            relation_row["relation"]
            for relation_row in relation_rows
            if relation_row["source"] == f"{objects[2]['size']} {objects[2]['color']} {objects[2]['shape']}"
            and relation_row["target"] == f"{objects[0]['size']} {objects[0]['color']} {objects[0]['shape']}"
        )
        vector[RELATION_OFFSET + 4 + RELATIONS.index(third_relation)] = 1.0
    return vector


def pooled_visual_features(atomizer: Any, image_path: Path, embedding_dimension: int) -> tuple[np.ndarray, dict[str, Any]]:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        pixels = np.ascontiguousarray(np.asarray(rgb, dtype=np.float32) / 255.0)
    result = atomizer.project_multimodal_numpy(
        pixels,
        max_levels=2,
        patch_size=16,
        retention_ratio=0.25,
        max_tokens=32,
        embedding_dimension=embedding_dimension,
    )
    embeddings = np.asarray(result["embeddings"], dtype=np.float32)
    if embeddings.ndim != 2 or embeddings.shape[1] != embedding_dimension or embeddings.shape[0] == 0:
        raise RuntimeError(f"invalid Stage 4 embedding shape {embeddings.shape}")
    if not np.isfinite(embeddings).all():
        raise RuntimeError("non-finite Stage 4 embeddings")
    pooled = normalize_vector(embeddings.mean(axis=0).astype(np.float32))
    metadata = {
        "retained_token_count": int(result["retained_token_count"]),
        "source_patch_count": int(result["source_patch_count"]),
        "embedding_dimension": int(result["embedding_dimension"]),
        "input_copied": bool(result["input_copied"]),
    }
    return pooled, metadata


def feature_matrix(atomizer: Any, manifest: dict[str, Any], image_dir: Path, output_path: Path, embedding_dimension: int) -> tuple[np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
    rows = sorted(manifest["records"], key=lambda record: record["asset_id"])
    features: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    asset_ids: list[str] = []
    projection_metadata: list[dict[str, Any]] = []

    first_features: np.ndarray | None = None
    for index, record in enumerate(rows):
        feature, metadata = pooled_visual_features(atomizer, image_dir / record["relative_path"], embedding_dimension)
        if index == 0:
            repeated, repeated_metadata = pooled_visual_features(atomizer, image_dir / record["relative_path"], embedding_dimension)
            determinism_error = float(np.max(np.abs(feature - repeated)))
            if determinism_error > 1e-7 or metadata != repeated_metadata:
                raise RuntimeError(f"Stage 4 token interface is not deterministic; max pooled error={determinism_error}")
            first_features = feature
        features.append(feature)
        targets.append(text_embedding(record))
        asset_ids.append(record["asset_id"])
        projection_metadata.append(metadata)

    x = np.vstack(features).astype(np.float32)
    y = np.vstack(targets).astype(np.float32)
    if first_features is None or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise RuntimeError("invalid feature or target matrix")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, features=x, targets=y, asset_ids=np.asarray(asset_ids, dtype="U32"))
    return x, y, asset_ids, projection_metadata


def split_indices(records: list[dict[str, Any]], asset_ids: list[str]) -> dict[str, np.ndarray]:
    split_by_id = {record["asset_id"]: record["split"] for record in records}
    result: dict[str, list[int]] = {"train": [], "dev": [], "held_out": []}
    for index, asset_id in enumerate(asset_ids):
        result[split_by_id[asset_id]].append(index)
    return {key: np.asarray(value, dtype=np.int64) for key, value in result.items()}


def standardize(train_x: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0, keepdims=True)
    scale = train_x.std(axis=0, keepdims=True)
    scale = np.maximum(scale, 1e-6)
    return (x - mean) / scale, mean, scale


def fit_ridge_dual(train_x: np.ndarray, train_y: np.ndarray, alpha: float) -> np.ndarray:
    gram = train_x @ train_x.T
    system = gram + np.eye(gram.shape[0], dtype=np.float32) * np.float32(alpha)
    dual = np.linalg.solve(system, train_y)
    return train_x.T @ dual


def retrieval_metrics(predictions: np.ndarray, targets: np.ndarray) -> tuple[float, float, float]:
    prediction_norm = normalize_rows(predictions)
    target_norm = normalize_rows(targets)
    similarity = prediction_norm @ target_norm.T
    ranks: list[int] = []
    for row in range(similarity.shape[0]):
        order = np.argsort(-similarity[row], kind="stable")
        rank = int(np.flatnonzero(order == row)[0]) + 1
        ranks.append(rank)
    ranks_array = np.asarray(ranks, dtype=np.float32)
    return (
        float(np.mean(ranks_array == 1)),
        float(np.mean(ranks_array <= 5)),
        float(np.mean(1.0 / ranks_array)),
    )


def f1_score(predictions: np.ndarray, targets: np.ndarray, threshold: float) -> float:
    binary_predictions = predictions >= threshold
    binary_targets = targets >= threshold
    true_positive = float(np.logical_and(binary_predictions, binary_targets).sum())
    false_positive = float(np.logical_and(binary_predictions, np.logical_not(binary_targets)).sum())
    false_negative = float(np.logical_and(np.logical_not(binary_predictions), binary_targets).sum())
    return (2.0 * true_positive) / max(2.0 * true_positive + false_positive + false_negative, 1.0)


def select_attribute_threshold(predictions: np.ndarray, targets: np.ndarray) -> float:
    # A global threshold is selected on the development split only and frozen for held-out use.
    candidates = np.linspace(-0.25, 0.75, 101, dtype=np.float32)
    return float(max(candidates, key=lambda threshold: (f1_score(predictions, targets, float(threshold)), -float(threshold))))


def attribute_slot_accuracy(predictions: np.ndarray, targets: np.ndarray) -> float:
    correct = 0
    total = 0
    for row in range(predictions.shape[0]):
        object_count = 2 + int(targets[row, COUNT_OFFSET + 1] > 0.5)
        for object_index in range(object_count):
            color_start = COLOR_OFFSET + object_index * len(COLORS)
            shape_start = SHAPE_OFFSET + object_index * len(SHAPES)
            size_start = SIZE_OFFSET + object_index * len(SIZES)
            for start, width in ((color_start, len(COLORS)), (shape_start, len(SHAPES)), (size_start, len(SIZES))):
                correct += int(np.argmax(predictions[row, start:start + width]) == np.argmax(targets[row, start:start + width]))
                total += 1
        correct += int(np.argmax(predictions[row, COUNT_OFFSET:COUNT_OFFSET + 2]) == np.argmax(targets[row, COUNT_OFFSET:COUNT_OFFSET + 2]))
        total += 1
    return float(correct / max(total, 1))


def relation_accuracy(predictions: np.ndarray, targets: np.ndarray) -> float:
    correct = 0
    total = 0
    for row in range(predictions.shape[0]):
        first_pred = int(np.argmax(predictions[row, RELATION_OFFSET:RELATION_OFFSET + 4]))
        first_target = int(np.argmax(targets[row, RELATION_OFFSET:RELATION_OFFSET + 4]))
        correct += int(first_pred == first_target)
        total += 1
        if targets[row, COUNT_OFFSET + 1] > 0.5:
            second_pred = int(np.argmax(predictions[row, RELATION_OFFSET + 4:RELATION_OFFSET + 8]))
            second_target = int(np.argmax(targets[row, RELATION_OFFSET + 4:RELATION_OFFSET + 8]))
            correct += int(second_pred == second_target)
            total += 1
    return float(correct / max(total, 1))


def evaluate(predictions: np.ndarray, targets: np.ndarray, attribute_threshold: float) -> Metrics:
    r1, r5, mrr = retrieval_metrics(predictions, targets)
    return Metrics(
        r1,
        r5,
        mrr,
        f1_score(predictions, targets, attribute_threshold),
        attribute_slot_accuracy(predictions, targets),
        relation_accuracy(predictions, targets),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--module-dir", type=Path, required=True)
    parser.add_argument("--local-run-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--embedding-dimension", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260812)
    args = parser.parse_args()

    audit = json.loads(args.audit_report.read_text(encoding="utf-8"))
    if audit.get("status") != "pass" or audit.get("training_permitted") is not True:
        raise RuntimeError("corpus audit did not pass; training is blocked")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("manifest_sha256") != audit.get("manifest_sha256"):
        raise RuntimeError("corpus audit and manifest hash differ; training is blocked")

    sys.path.insert(0, str(args.module_dir.resolve()))
    import alvs_cpp  # type: ignore[import-not-found]

    np.random.seed(args.seed)
    atomizer = alvs_cpp.Atomizer()
    args.local_run_dir.mkdir(parents=True, exist_ok=True)
    feature_path = args.local_run_dir / "stage4_pooled_features.npz"
    start_time = time.perf_counter()
    x, y, asset_ids, projection_metadata = feature_matrix(
        atomizer, manifest, args.image_dir, feature_path, args.embedding_dimension
    )
    extraction_seconds = time.perf_counter() - start_time
    split = split_indices(manifest["records"], asset_ids)
    if not all(split[key].size > 0 for key in ("train", "dev", "held_out")):
        raise RuntimeError("one or more data splits is empty")

    train_x_raw, dev_x_raw, held_x_raw = x[split["train"]], x[split["dev"]], x[split["held_out"]]
    train_y, dev_y, held_y = y[split["train"]], y[split["dev"]], y[split["held_out"]]
    train_x, x_mean, x_scale = standardize(train_x_raw, train_x_raw)
    dev_x = (dev_x_raw - x_mean) / x_scale
    held_x = (held_x_raw - x_mean) / x_scale

    rng = np.random.default_rng(args.seed)
    baseline_projection = rng.standard_normal((args.embedding_dimension, TEXT_DIMENSION), dtype=np.float32)
    baseline_projection /= math.sqrt(args.embedding_dimension)
    b0_dev_predictions = dev_x @ baseline_projection
    b0_threshold = select_attribute_threshold(b0_dev_predictions, dev_y)
    b0_dev = evaluate(b0_dev_predictions, dev_y, b0_threshold)
    b0_held = evaluate(held_x @ baseline_projection, held_y, b0_threshold)

    candidate_alphas = (0.01, 0.1, 1.0, 10.0, 100.0)
    candidates: list[dict[str, Any]] = []
    best: tuple[float, np.ndarray, Metrics, float] | None = None
    for alpha in candidate_alphas:
        weights = fit_ridge_dual(train_x, train_y, alpha)
        dev_predictions = dev_x @ weights
        attribute_threshold = select_attribute_threshold(dev_predictions, dev_y)
        metrics = evaluate(dev_predictions, dev_y, attribute_threshold)
        candidates.append({"alpha": alpha, "attribute_threshold": attribute_threshold, **metrics.as_dict()})
        if best is None or (metrics.recall_at_1, metrics.mean_reciprocal_rank, -alpha) > (best[2].recall_at_1, best[2].mean_reciprocal_rank, -best[0]):
            best = (alpha, weights, metrics, attribute_threshold)
    assert best is not None
    alpha, weights, b1_dev, b1_threshold = best
    b1_held = evaluate(held_x @ weights, held_y, b1_threshold)
    if not np.isfinite(weights).all():
        raise RuntimeError("non-finite fitted adapter weights")

    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.checkpoint,
        adapter_weights=weights.astype(np.float32),
        input_mean=x_mean.astype(np.float32),
        input_scale=x_scale.astype(np.float32),
        baseline_projection=baseline_projection.astype(np.float32),
        train_asset_ids=np.asarray([asset_ids[index] for index in split["train"]], dtype="U32"),
        dev_asset_ids=np.asarray([asset_ids[index] for index in split["dev"]], dtype="U32"),
        held_out_asset_ids=np.asarray([asset_ids[index] for index in split["held_out"]], dtype="U32"),
    )

    token_counts = np.asarray([row["retained_token_count"] for row in projection_metadata], dtype=np.int32)
    source_patch_counts = np.asarray([row["source_patch_count"] for row in projection_metadata], dtype=np.int32)
    report = {
        "experiment": "T2.5 project-owned controlled visual-to-structured-text adapter",
        "status": "pass" if b1_held.recall_at_1 > b0_held.recall_at_1 else "review_required_no_held_out_improvement",
        "manifest_sha256": manifest["manifest_sha256"],
        "corpus_audit_status": audit["status"],
        "code": {
            "runner": "scripts/run_t25_adapter_baseline.py",
            "module_dir": str(args.module_dir),
            "python": sys.version,
            "platform": platform.platform(),
        },
        "configuration": {
            "seed": args.seed,
            "embedding_dimension": args.embedding_dimension,
            "stage4_max_levels": 2,
            "stage4_patch_size": 16,
            "stage4_retention_ratio": 0.25,
            "stage4_max_tokens": 32,
            "text_target_dimension": TEXT_DIMENSION,
            "fitting": "closed-form dual ridge regression on train split only",
            "development_alphas": list(candidate_alphas),
            "selected_alpha": alpha,
            "attribute_threshold_policy": "global threshold selected on development data only and frozen for held-out evaluation",
            "B0_attribute_threshold": b0_threshold,
            "B1_attribute_threshold": b1_threshold,
        },
        "data": {
            "split_counts": {key: int(value.size) for key, value in split.items()},
            "feature_cache_sha256": sha256_file(feature_path),
            "feature_shape": list(x.shape),
            "held_out_used_for_fit": False,
        },
        "stage4_interface": {
            "backend": atomizer.simd_backend(),
            "simd_available": bool(atomizer.simd_available()),
            "input_copied": any(row["input_copied"] for row in projection_metadata),
            "retained_tokens": {"min": int(token_counts.min()), "max": int(token_counts.max()), "mean": float(token_counts.mean())},
            "source_patches": {"min": int(source_patch_counts.min()), "max": int(source_patch_counts.max()), "mean": float(source_patch_counts.mean())},
            "deterministic_repeated_first_sample": True,
        },
        "runtime": {"feature_extraction_seconds": extraction_seconds},
        "development": {"B0": b0_dev.as_dict(), "B1": b1_dev.as_dict(), "ridge_candidates": candidates},
        "held_out": {
            "B0": b0_held.as_dict(),
            "B1": b1_held.as_dict(),
            "delta_B1_minus_B0": {key: b1_held.as_dict()[key] - b0_held.as_dict()[key] for key in b1_held.as_dict()},
        },
        "checkpoint": {"path": str(args.checkpoint), "sha256": sha256_file(args.checkpoint)},
        "limitations": [
            "The text target is a local structured attribute embedding, not a pretrained language-model embedding.",
            "The corpus contains only deterministic geometric scenes and cannot establish real-world visual or language generalization.",
            "The experiment measures a frozen Stage 4 interface plus a closed-form adapter; it is not end-to-end foundation-model training.",
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "held_out": report["held_out"], "checkpoint_sha256": report["checkpoint"]["sha256"]}, sort_keys=True))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
