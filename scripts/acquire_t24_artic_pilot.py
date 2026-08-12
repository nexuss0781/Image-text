#!/usr/bin/env python3
"""Acquire only an audited T2.4 Art Institute CC0 pilot allow-list.

The script refuses to run unless the metadata manifest audit passed. It downloads only the
exact IIIF URLs recorded in that manifest, validates media files, and writes a retained-media
manifest with a checksum for every asset. It never enumerates or discovers additional media.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import requests
from PIL import Image, UnidentifiedImageError


MAX_FILE_BYTES = 12 * 1024 * 1024
MIN_DIMENSION = 224


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--retained-manifest", type=Path, required=True)
    parser.add_argument("--download-log", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    audit_report = json.loads(args.audit_report.read_text(encoding="utf-8"))
    if audit_report.get("status") != "pass" or audit_report.get("hard_failures"):
        print("ERROR: metadata manifest audit did not pass; acquisition blocked.", file=sys.stderr)
        return 2

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != 200:
        print("ERROR: expected exact audited 200-record manifest; acquisition blocked.", file=sys.stderr)
        return 3
    if manifest.get("manifest_sha256") != audit_report.get("manifest_sha256"):
        print("ERROR: audit report does not match manifest hash; acquisition blocked.", file=sys.stderr)
        return 4

    if args.output_dir.exists():
        existing_files = [path for path in args.output_dir.rglob("*") if path.is_file()]
        if existing_files:
            print("ERROR: output directory is not empty; acquisition blocked to prevent mixed corpus state.", file=sys.stderr)
            return 5
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.retained_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.download_log.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    download_rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for record in sorted(records, key=lambda value: value["asset_id"]):
        asset_id = record["asset_id"]
        split = record["split"]
        destination = args.output_dir / split / f"{asset_id}.jpg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".part")
        try:
            response = session.get(record["iiif_url"], stream=True, timeout=args.timeout)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                raise RuntimeError(f"unexpected content type: {content_type or 'missing'}")
            downloaded = 0
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_FILE_BYTES:
                        raise RuntimeError(f"file exceeds {MAX_FILE_BYTES} byte cap")
                    handle.write(chunk)
            if downloaded == 0:
                raise RuntimeError("empty media response")
            try:
                with Image.open(temporary) as image:
                    image.verify()
                with Image.open(temporary) as image:
                    width, height = image.size
                    image_format = image.format
                    image_mode = image.mode
            except (UnidentifiedImageError, OSError) as exc:
                raise RuntimeError(f"invalid image file: {exc}") from exc
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise RuntimeError(f"image below {MIN_DIMENSION}px minimum: {width}x{height}")
            temporary.replace(destination)
            download_rows.append(
                {
                    "asset_id": asset_id,
                    "source_artwork_id": record["source_artwork_id"],
                    "split": split,
                    "source_iiif_url": record["iiif_url"],
                    "relative_path": str(destination.relative_to(args.output_dir)),
                    "sha256": sha256_file(destination),
                    "byte_count": downloaded,
                    "width": width,
                    "height": height,
                    "format": image_format,
                    "mode": image_mode,
                    "status": "downloaded_and_validated",
                }
            )
        except Exception as exc:  # noqa: BLE001 — record every failed asset deterministically.
            temporary.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            failures.append({"asset_id": asset_id, "error": str(exc)})

    download_rows.sort(key=lambda value: value["asset_id"])
    retained_manifest = {
        "schema_version": "1.0",
        "retention_status": "acquired_pending_image_level_review",
        "source_candidate_manifest_sha256": manifest["manifest_sha256"],
        "source_audit_report": str(args.audit_report),
        "asset_count_expected": len(records),
        "asset_count_downloaded": len(download_rows),
        "asset_count_failed": len(failures),
        "acquired_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "download_cap_bytes_per_asset": MAX_FILE_BYTES,
        "minimum_dimension": MIN_DIMENSION,
        "records": download_rows,
        "failures": failures,
    }
    canonical = json.dumps(retained_manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    retained_manifest["retained_manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.retained_manifest.write_text(json.dumps(retained_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.download_log.open("w", encoding="utf-8") as handle:
        for row in download_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        for failure in failures:
            handle.write(json.dumps({"status": "failed", **failure}, sort_keys=True) + "\n")

    if failures or len(download_rows) != len(records):
        print(
            f"ERROR: acquired {len(download_rows)} of {len(records)} audited assets; corpus is incomplete and training blocked.",
            file=sys.stderr,
        )
        return 6
    print(json.dumps({
        "status": "pass_pending_image_level_review",
        "retained_manifest_sha256": retained_manifest["retained_manifest_sha256"],
        "asset_count": len(download_rows),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
