#!/usr/bin/env python3
"""Bind reviewed browser-saved proof copies to their fixed item-level source manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--review-log", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    records = source_manifest.get("records", [])
    review_log = args.review_log.read_text(encoding="utf-8")
    failures: list[str] = []
    output_records: list[dict] = []
    source_ids = {record.get("asset_id") for record in records}
    actual_ids = {path.stem for path in args.image_dir.glob("*.webp")}
    if len(records) != 8 or len(source_ids) != 8:
        failures.append("fixed eight-record source manifest requirement failed")
    if actual_ids != source_ids:
        failures.append(f"local proof-copy set differs from source manifest: expected={sorted(source_ids)}, actual={sorted(actual_ids)}")

    for record in records:
        asset_id = record["asset_id"]
        image_path = args.image_dir / f"{asset_id}.webp"
        if f"| `{asset_id}` " not in review_log or "**Pass**" not in next((line for line in review_log.splitlines() if f"| `{asset_id}` " in line), ""):
            failures.append(f"{asset_id}: no passing visual-review entry")
            continue
        if not image_path.is_file():
            failures.append(f"{asset_id}: missing local proof copy")
            continue
        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                width, height = image.size
                image_format = image.format
                image_mode = image.mode
        except (UnidentifiedImageError, OSError) as exc:
            failures.append(f"{asset_id}: invalid image {exc}")
            continue
        if width < 256 or height < 256 or image_mode not in {"RGB", "RGBA"}:
            failures.append(f"{asset_id}: unsupported proof-copy image contract {width}x{height} {image_mode}")
            continue
        output_records.append({
            "asset_id": asset_id,
            "scene_class": record["scene_class"],
            "source_file_title": record["source_file_title"],
            "source_page_url": record["source_page_url"],
            "delivery_url": record["delivery_url"],
            "license_short_name": record["license_short_name"],
            "usage_terms": record["usage_terms"],
            "artist": record["artist"],
            "local_copy": str(image_path),
            "local_copy_format": image_format,
            "local_copy_sha256": sha256_file(image_path),
            "width": width,
            "height": height,
            "mode": image_mode,
            "acquisition_route": "normal browser delivery path; locally saved WebP proof copy",
            "rights_review": "pass_item_level_CC0_or_public_domain",
            "privacy_safety_visual_review": "pass_no_discernible_people_faces_or_sensitive_content",
        })

    output = {
        "schema_version": "1.0",
        "status": "pass" if not failures else "fail",
        "source_manifest_sha256": source_manifest.get("manifest_sha256"),
        "review_log": str(args.review_log),
        "record_count": len(output_records),
        "core_training_or_modification": False,
        "records": output_records,
        "hard_failures": failures,
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
    }
    canonical = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    output["acquisition_manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "records": len(output_records), "failures": failures}, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
