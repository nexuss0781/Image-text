#!/usr/bin/env python3
"""Render a deterministic signal-distance and latency chart from the real-world proof report."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--distance-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    with args.distance_csv.open(encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    labels = rows[0][1:]
    distance = np.asarray([[float(value) for value in row[1:]] for row in rows[1:]], dtype=np.float64)
    records = {record["asset_id"]: record for record in report["records"]}
    median_ms = [records[label]["performance"]["median_ms"] for label in labels]

    plt.style.use("seaborn-v0_8-whitegrid")
    figure, (heatmap_axis, latency_axis) = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [1.3, 1]})
    image = heatmap_axis.imshow(distance, cmap="magma", vmin=0.0, vmax=max(0.1, float(distance.max())))
    heatmap_axis.set_title("Frozen Stage 4 Signal Distance\n(cosine distance of pooled 4,096-D tokens)", weight="bold")
    heatmap_axis.set_xticks(range(len(labels)), labels, rotation=55, ha="right", fontsize=8)
    heatmap_axis.set_yticks(range(len(labels)), labels, fontsize=8)
    for row in range(len(labels)):
        for column in range(len(labels)):
            heatmap_axis.text(column, row, f"{distance[row, column]:.3f}", ha="center", va="center", fontsize=6, color="white" if distance[row, column] > distance.max() * 0.52 else "black")
    colorbar = figure.colorbar(image, ax=heatmap_axis, fraction=0.046, pad=0.04)
    colorbar.set_label("Cosine distance")

    colours = ["#5B8FF9" if records[label]["scene_class"] in {"city", "building"} else "#61DDAA" if records[label]["scene_class"] == "animal" else "#F6BD16" for label in labels]
    bars = latency_axis.barh(labels, median_ms, color=colours)
    latency_axis.set_title("Frozen Pipeline Latency\n(512 × 512 input; median of 30 runs)", weight="bold")
    latency_axis.set_xlabel("Milliseconds")
    latency_axis.invert_yaxis()
    for bar, value in zip(bars, median_ms):
        latency_axis.text(value + 0.02, bar.get_y() + bar.get_height() / 2, f"{value:.2f}", va="center", fontsize=8)
    latency_axis.set_xlim(0, max(median_ms) * 1.15)

    figure.suptitle("AGI-VS Real-World Observation Proof — No Training or Core Modification", fontsize=14, weight="bold", y=1.03)
    figure.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
