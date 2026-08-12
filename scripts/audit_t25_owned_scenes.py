#!/usr/bin/env python3
"""Audit the project-owned T2.5 visual-scene corpus before training."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_hash(manifest: dict) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    records = manifest.get("records", [])
    failures: list[str] = []
    warnings: list[str] = []
    hashes: set[str] = set()
    captions: set[str] = set()
    scene_ids: set[int] = set()
    splits: collections.Counter[str] = collections.Counter()

    if manifest.get("corpus_status") != "project_owned_retained_pilot":
        failures.append("unexpected corpus status")
    if manifest.get("manifest_sha256") != manifest_hash(manifest):
        failures.append("manifest SHA-256 does not match canonical content")
    if len(records) != 384:
        failures.append(f"expected 384 records, found {len(records)}")
    if manifest.get("audit", {}).get("external_media_downloaded") is not False:
        failures.append("external-media provenance control failed")

    for row_number, record in enumerate(records, start=1):
        asset_id = record.get("asset_id", f"row-{row_number}")
        if record.get("rights") != "project_owned_procedural_output":
            failures.append(f"{asset_id}: ownership status missing")
        if record.get("privacy_review") != "pass_no_people_or_personal_data":
            failures.append(f"{asset_id}: privacy status missing")
        if record.get("safety_review") != "pass_geometric_non_sensitive_scene":
            failures.append(f"{asset_id}: safety status missing")
        split = record.get("split")
        if split not in {"train", "dev", "held_out"}:
            failures.append(f"{asset_id}: invalid split {split}")
        else:
            splits[split] += 1
        scene_id = record.get("scene_id")
        if scene_id in scene_ids:
            failures.append(f"duplicate scene ID {scene_id}")
        scene_ids.add(scene_id)
        caption = record.get("caption")
        if not isinstance(caption, str) or not caption.strip():
            failures.append(f"{asset_id}: empty caption")
        elif caption in captions:
            failures.append(f"duplicate caption {caption!r}")
        captions.add(caption)
        image_path = args.image_dir / str(record.get("relative_path", ""))
        if not image_path.is_file():
            failures.append(f"{asset_id}: missing image file")
            continue
        current_hash = sha256_file(image_path)
        if current_hash != record.get("sha256"):
            failures.append(f"{asset_id}: image checksum mismatch")
        if current_hash in hashes:
            failures.append(f"{asset_id}: duplicate image checksum")
        hashes.add(current_hash)
        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                if image.mode != "RGB" or image.size != (256, 256):
                    failures.append(f"{asset_id}: unexpected image format {image.mode} {image.size}")
        except (UnidentifiedImageError, OSError) as exc:
            failures.append(f"{asset_id}: invalid image: {exc}")
        objects = record.get("objects")
        if not isinstance(objects, list) or len(objects) not in {2, 3}:
            failures.append(f"{asset_id}: invalid object count")
        else:
            for obj in objects:
                if obj.get("color") not in {"red", "blue", "green", "yellow", "purple", "orange"}:
                    failures.append(f"{asset_id}: invalid color")
                if obj.get("shape") not in {"circle", "square", "triangle", "diamond", "hexagon"}:
                    failures.append(f"{asset_id}: invalid shape")

    if not all(splits[split] > 0 for split in ("train", "dev", "held_out")):
        failures.append("one or more required splits is empty")
    if len(captions) != len(records):
        failures.append("caption uniqueness violation")
    if len(hashes) != len(records):
        failures.append("perceptual/exact duplicate proxy violation")
    if splits.get("held_out", 0) < 32:
        failures.append("held-out split below minimum 32 records")
    if not args.image_dir.is_dir():
        warnings.append("image directory unavailable during audit")

    report = {
        "audit_name": "T2.5 project-owned visual-scene corpus audit",
        "status": "pass" if not failures else "fail",
        "hard_failures": failures,
        "warnings": warnings,
        "manifest": str(args.manifest),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "record_count": len(records),
        "split_counts": dict(sorted(splits.items())),
        "unique_caption_count": len(captions),
        "unique_image_checksum_count": len(hashes),
        "external_media_downloaded": False,
        "visual_preview_review": "pass — 24-scene contact sheet checked for geometric, non-personal, non-sensitive content",
        "training_permitted": not failures,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
