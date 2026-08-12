#!/usr/bin/env python3
"""Generate the project-owned deterministic visual-scene corpus for the T2.5 pilot.

The generator uses only local code plus Pillow primitives. It downloads no external data and
creates no people, text in images, brands, third-party artwork, or sensitive content.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

CANVAS_SIZE = 256
OVERSAMPLE = 3
BACKGROUND = (20, 25, 34)
COLORS = {
    "red": (221, 73, 73),
    "blue": (74, 133, 219),
    "green": (72, 171, 110),
    "yellow": (230, 190, 69),
    "purple": (161, 102, 206),
    "orange": (231, 137, 59),
}
SHAPES = ("circle", "square", "triangle", "diamond", "hexagon")
SIZES = {"small": 25, "medium": 33, "large": 41}
SLOTS = ((58, 58), (128, 58), (198, 58), (58, 128), (128, 128), (198, 128), (58, 198), (128, 198), (198, 198))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_split(seed: str, scene_id: int) -> str:
    value = int(hashlib.sha256(f"{seed}:split:{scene_id}".encode("utf-8")).hexdigest()[:8], 16) % 100
    if value < 70:
        return "train"
    if value < 85:
        return "dev"
    return "held_out"


def polygon_points(shape: str, center: tuple[float, float], radius: float, rotation: float) -> list[tuple[float, float]]:
    vertices = {"triangle": 3, "diamond": 4, "hexagon": 6}.get(shape)
    if vertices is None:
        raise ValueError(f"Unsupported polygon shape: {shape}")
    offset = -math.pi / 2 + rotation
    return [
        (center[0] + radius * math.cos(offset + 2 * math.pi * index / vertices), center[1] + radius * math.sin(offset + 2 * math.pi * index / vertices))
        for index in range(vertices)
    ]


def draw_shape(draw: ImageDraw.ImageDraw, obj: dict[str, Any], scale: int) -> None:
    x, y = obj["center"]
    x *= scale
    y *= scale
    radius = obj["radius"] * scale
    color = COLORS[obj["color"]]
    outline = tuple(max(0, channel - 42) for channel in color)
    if obj["shape"] == "circle":
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=outline, width=2 * scale)
    elif obj["shape"] == "square":
        draw.rounded_rectangle((x - radius, y - radius, x + radius, y + radius), radius=5 * scale, fill=color, outline=outline, width=2 * scale)
    else:
        points = [(px * scale, py * scale) for px, py in polygon_points(obj["shape"], obj["center"], obj["radius"], obj["rotation"])]
        draw.polygon(points, fill=color, outline=outline)
        draw.line(points + [points[0]], fill=outline, width=2 * scale, joint="curve")


def relation(a: dict[str, Any], b: dict[str, Any]) -> str:
    dx = a["center"][0] - b["center"][0]
    dy = a["center"][1] - b["center"][1]
    if abs(dx) >= abs(dy):
        return "left of" if dx < 0 else "right of"
    return "above" if dy < 0 else "below"


def object_phrase(obj: dict[str, Any]) -> str:
    return f"{obj['size']} {obj['color']} {obj['shape']}"


def make_caption(objects: list[dict[str, Any]]) -> str:
    first, second = objects[0], objects[1]
    sentence = f"A {object_phrase(first)} is {relation(first, second)} a {object_phrase(second)}."
    if len(objects) == 3:
        third = objects[2]
        sentence += f" A {object_phrase(third)} is {relation(third, first)} the first object."
    return sentence


def scene_attributes(objects: list[dict[str, Any]]) -> dict[str, Any]:
    relations = []
    for index, source in enumerate(objects):
        for target_index, target in enumerate(objects):
            if index == target_index:
                continue
            relations.append({
                "source": object_phrase(source),
                "relation": relation(source, target),
                "target": object_phrase(target),
            })
    return {
        "object_count": len(objects),
        "colors": [obj["color"] for obj in objects],
        "shapes": [obj["shape"] for obj in objects],
        "sizes": [obj["size"] for obj in objects],
        "relations": relations,
    }


def make_scene(scene_seed: int) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    rng = random.Random(scene_seed)
    object_count = 2 if rng.random() < 0.56 else 3
    slots = rng.sample(list(SLOTS), object_count)
    objects: list[dict[str, Any]] = []
    used_pairs: set[tuple[str, str]] = set()
    for index, slot in enumerate(slots):
        for _ in range(100):
            color = rng.choice(tuple(COLORS))
            shape = rng.choice(SHAPES)
            if (color, shape) not in used_pairs:
                used_pairs.add((color, shape))
                break
        size_name = rng.choice(tuple(SIZES))
        center = (
            max(44, min(212, slot[0] + rng.randint(-11, 11))),
            max(44, min(212, slot[1] + rng.randint(-11, 11))),
        )
        objects.append({
            "object_id": index,
            "shape": shape,
            "color": color,
            "size": size_name,
            "radius": SIZES[size_name],
            "center": center,
            "rotation": rng.uniform(-0.35, 0.35),
        })
    objects.sort(key=lambda obj: (obj["center"][1], obj["center"][0]))
    caption = make_caption(objects)
    return objects, caption, scene_attributes(objects)


def render_scene(objects: list[dict[str, Any]]) -> Image.Image:
    size = CANVAS_SIZE * OVERSAMPLE
    image = Image.new("RGB", (size, size), BACKGROUND)
    draw = ImageDraw.Draw(image)
    # Subtle non-semantic grid improves spatial reference without introducing text or external assets.
    grid_color = (33, 40, 52)
    for coordinate in (64, 128, 192):
        draw.line((coordinate * OVERSAMPLE, 0, coordinate * OVERSAMPLE, size), fill=grid_color, width=OVERSAMPLE)
        draw.line((0, coordinate * OVERSAMPLE, size, coordinate * OVERSAMPLE), fill=grid_color, width=OVERSAMPLE)
    for obj in objects:
        draw_shape(draw, obj, OVERSAMPLE)
    return image.resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--contact-sheet", type=Path, required=True)
    parser.add_argument("--count", type=int, default=384)
    parser.add_argument("--seed", default="agi-vs-t25-owned-scenes-v1")
    args = parser.parse_args()

    if args.count < 128:
        raise ValueError("The controlled pilot requires at least 128 records.")
    if args.image_dir.exists() and any(args.image_dir.iterdir()):
        raise RuntimeError("image directory must be empty to prevent mixed corpus state")
    args.image_dir.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.contact_sheet.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    captions: set[str] = set()
    scene_id = 0
    attempts = 0
    while len(records) < args.count:
        attempts += 1
        local_seed = int(hashlib.sha256(f"{args.seed}:scene:{scene_id}:{attempts}".encode("utf-8")).hexdigest()[:16], 16)
        objects, caption, attributes = make_scene(local_seed)
        if caption in captions:
            continue
        captions.add(caption)
        split = stable_split(args.seed, scene_id)
        asset_id = f"owned-scene-{scene_id:04d}"
        destination = args.image_dir / split / f"{asset_id}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        render_scene(objects).save(destination, format="PNG", optimize=True)
        records.append({
            "asset_id": asset_id,
            "scene_id": scene_id,
            "split": split,
            "relative_path": str(destination.relative_to(args.image_dir)),
            "sha256": sha256_file(destination),
            "width": CANVAS_SIZE,
            "height": CANVAS_SIZE,
            "generator": "scripts/generate_t25_owned_scenes.py",
            "generator_seed": args.seed,
            "scene_seed": local_seed,
            "objects": objects,
            "caption": caption,
            "attributes": attributes,
            "rights": "project_owned_procedural_output",
            "privacy_review": "pass_no_people_or_personal_data",
            "safety_review": "pass_geometric_non_sensitive_scene",
        })
        scene_id += 1

    records.sort(key=lambda record: record["asset_id"])
    split_counts = Counter(record["split"] for record in records)
    if not all(split_counts[split] > 0 for split in ("train", "dev", "held_out")):
        raise RuntimeError("deterministic split generation produced an empty split")

    manifest = {
        "schema_version": "1.0",
        "corpus_status": "project_owned_retained_pilot",
        "generator_version": "t25-owned-scenes-v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "selection": {
            "record_count": args.count,
            "seed": args.seed,
            "image_size": [CANVAS_SIZE, CANVAS_SIZE],
            "allowed_shapes": list(SHAPES),
            "allowed_colors": list(COLORS),
            "privacy_content_boundary": "geometric shapes only; no people, text in images, personal data, third-party artwork, brands, sexual content, or violence",
            "caption_policy": "deterministic captions generated from local scene specifications",
            "split_policy": "SHA-256 seeded 70/15/15 deterministic assignment before training",
        },
        "audit": {
            "split_counts": dict(sorted(split_counts.items())),
            "unique_caption_count": len(captions),
            "external_media_downloaded": False,
            "source_owner": "AGI-VS project",
        },
        "records": records,
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # A lightweight 6 × 4 representative preview is created for visual verification.
    preview_records = sorted(records, key=lambda record: hashlib.sha256(f"{args.seed}:preview:{record['asset_id']}".encode("utf-8")).hexdigest())[:24]
    tile = 128
    sheet = Image.new("RGB", (6 * tile, 4 * tile), (245, 245, 245))
    for index, record in enumerate(preview_records):
        with Image.open(args.image_dir / record["relative_path"]) as image:
            image.thumbnail((tile, tile))
            x = (index % 6) * tile
            y = (index // 6) * tile
            sheet.paste(image, (x, y))
    sheet.save(args.contact_sheet, format="PNG", optimize=True)

    summary = {
        "manifest_path": str(args.manifest),
        "manifest_sha256": manifest["manifest_sha256"],
        "record_count": len(records),
        "unique_caption_count": len(captions),
        "split_counts": dict(sorted(split_counts.items())),
        "external_media_downloaded": False,
        "contact_sheet": str(args.contact_sheet),
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
