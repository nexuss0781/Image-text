#!/usr/bin/env python3
"""Acquire only the fixed real-world proof images recorded in Proofs/proof_set_manifest.json."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import requests
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 12 * 1024 * 1024
MIN_DIMENSION = 256
USER_AGENT = "AGI-VS-real-world-proof-set/1.0 (bounded proof acquisition)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    records = manifest.get("records")
    if manifest.get("status") != "approved_for_bounded_acquisition_pending_visual_review" or not isinstance(records, list) or len(records) != 8:
        print("ERROR: fixed eight-record approved manifest is required; acquisition blocked.", file=sys.stderr)
        return 2
    if any(record.get("licence_review") != "pass_item_level_CC0_or_public_domain" for record in records):
        print("ERROR: source licence review is incomplete; acquisition blocked.", file=sys.stderr)
    if args.image_dir.exists() and any(args.image_dir.iterdir()):
        print("ERROR: proof image directory is not empty; acquisition blocked to prevent mixed evidence.", file=sys.stderr)
        return 3
    args.image_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    acquired: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for record in records:
        asset_id = record["asset_id"]
        destination = args.image_dir / f"{asset_id}.jpg"
        temporary = destination.with_suffix(".part")
        try:
            response = session.get(record["delivery_url"], stream=True, timeout=60)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                raise RuntimeError(f"unexpected Content-Type {content_type or 'missing'}")
            byte_count = 0
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    byte_count += len(chunk)
                    if byte_count > MAX_BYTES:
                        raise RuntimeError("response exceeded fixed byte limit")
                    handle.write(chunk)
            with Image.open(temporary) as image:
                image.verify()
            with Image.open(temporary) as image:
                width, height = image.size
                image_format = image.format
                image_mode = image.mode
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise RuntimeError(f"image dimensions {width}x{height} are below {MIN_DIMENSION}px")
            temporary.replace(destination)
            acquired.append({
                "asset_id": asset_id,
                "scene_class": record["scene_class"],
                "source_file_title": record["source_file_title"],
                "source_page_url": record["source_page_url"],
                "delivery_url": record["delivery_url"],
                "license_short_name": record["license_short_name"],
                "usage_terms": record["usage_terms"],
                "artist": record["artist"],
                "relative_path": str(destination),
                "sha256": sha256_file(destination),
                "byte_count": byte_count,
                "width": width,
                "height": height,
                "format": image_format,
                "mode": image_mode,
                "status": "acquired_pending_visual_review",
            })
        except Exception as exc:  # noqa: BLE001 — retain exact failure reason for review.
            temporary.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            failures.append({"asset_id": asset_id, "error": str(exc)})

    output = {
        "schema_version": "1.0",
        "status": "acquired_pending_visual_review" if not failures and len(acquired) == 8 else "incomplete_acquisition_training_and_benchmark_blocked",
        "source_manifest_sha256": manifest.get("manifest_sha256"),
        "acquired_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "asset_count_expected": len(records),
        "asset_count_acquired": len(acquired),
        "records": acquired,
        "failures": failures,
        "core_training_or_modification": False,
    }
    canonical = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    output["acquisition_manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "acquired": len(acquired), "failed": len(failures)}, sort_keys=True))
    return 0 if output["status"] == "acquired_pending_visual_review" else 4


if __name__ == "__main__":
    raise SystemExit(main())
