#!/usr/bin/env python3
"""Build a bounded Open Images V7 record-review queue from a local metadata CSV.

This script is intentionally offline: it performs no network calls, does not fetch
media, does not compute embeddings, and does not authorize retention or training.
It only converts a manually supplied metadata extract into unreviewed manifest
entries that remain quarantined until later source-specific review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_TEMPLATE_FIELDS = [
    "source_record_id",
    "canonical_source_url",
    "source_creator_or_attribution_party",
    "title_if_supplied",
    "item_level_licence_evidence_url",
    "licence_evidence_capture_time",
    "annotation_type_and_version",
    "annotation_licence_evidence_url",
    "content_privacy_safety_review_status",
    "rights_caveat_review_status",
    "deduplication_review_status",
    "split_assignment",
    "removal_contact_or_source_procedure",
    "retention_expiry_or_review_date",
    "manifest_entry_checksum",
]


def normalized_entry_payload(entry: dict[str, Any]) -> str:
    """Return deterministic JSON excluding the checksum itself."""
    payload = {key: value for key, value in entry.items() if key != "manifest_entry_checksum"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def checksum(entry: dict[str, Any]) -> str:
    return hashlib.sha256(normalized_entry_payload(entry).encode("utf-8")).hexdigest()


def value(row: dict[str, str], *names: str) -> str:
    for name in names:
        candidate = (row.get(name) or "").strip()
        if candidate:
            return candidate
    return ""


def review_entry(row: dict[str, str], captured_at: str, review_date: str) -> dict[str, Any]:
    image_id = value(row, "ImageID", "image_id", "id")
    source_url = value(row, "OriginalURL", "original_url", "url")
    landing_url = value(row, "OriginalLandingURL", "original_landing_url", "landing_url")
    author = value(row, "Author", "author", "Creator", "creator")
    title = value(row, "Title", "title")
    licence = value(row, "License", "license", "Licence", "licence")

    entry: dict[str, Any] = {
        "source_record_id": image_id,
        "canonical_source_url": landing_url or source_url,
        "source_creator_or_attribution_party": author,
        "title_if_supplied": title,
        "item_level_licence_evidence_url": licence,
        "licence_evidence_capture_time": captured_at,
        "annotation_type_and_version": "Open Images V7 — candidate record; annotation selection unreviewed",
        "annotation_licence_evidence_url": "https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses",
        "content_privacy_safety_review_status": "unreviewed",
        "rights_caveat_review_status": "unreviewed",
        "deduplication_review_status": "unreviewed",
        "split_assignment": "unassigned",
        "removal_contact_or_source_procedure": "unreviewed",
        "retention_expiry_or_review_date": review_date,
        "review_queue_state": "unreviewed",
        "training_eligibility": "blocked",
        "media_downloaded": False,
        "embeddings_generated": False,
        "source_row_license_text": licence,
        "source_row_media_url": source_url,
        "manifest_entry_checksum": "",
    }
    entry["manifest_entry_checksum"] = checksum(entry)
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-csv", required=True, type=Path, help="Local manually supplied metadata CSV; no URL is accepted.")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON manifest path.")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum queue entries, capped at 1000.")
    parser.add_argument("--review-date", required=True, help="Review expiry or next-review date in ISO-8601 form.")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 1000:
        raise SystemExit("--limit must be between 1 and 1000; the T2.1 gate prohibits larger queues.")
    if not args.metadata_csv.is_file():
        raise SystemExit(f"Metadata CSV does not exist: {args.metadata_csv}")

    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    records: list[dict[str, Any]] = []
    skipped: dict[str, int] = {"missing_image_id": 0, "duplicate_image_id": 0}
    seen: set[str] = set()

    with args.metadata_csv.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        for row in reader:
            if len(records) >= args.limit:
                break
            entry = review_entry(row, captured_at, args.review_date)
            record_id = entry["source_record_id"]
            if not record_id:
                skipped["missing_image_id"] += 1
                continue
            if record_id in seen:
                skipped["duplicate_image_id"] += 1
                continue
            seen.add(record_id)
            records.append(entry)

    output = {
        "schema_version": "1.0",
        "manifest_status": "T2.1 bounded record review queue — no media retained, no training authorized",
        "program": "AGI-VS T2.1 Bounded Review Queue",
        "source": "Open Images V7",
        "hard_limits": {
            "maximum_review_queue_records": 1000,
            "queue_record_count": len(records),
            "bulk_download_permitted": False,
            "web_media_reconstruction_permitted": False,
            "retained_training_records": 0,
            "embedding_generation_permitted": False,
            "model_training_permitted": False,
        },
        "input_provenance": {
            "metadata_csv_path": str(args.metadata_csv),
            "metadata_csv_sha256": hashlib.sha256(args.metadata_csv.read_bytes()).hexdigest(),
            "captured_at": captured_at,
            "skipped_records": skipped,
        },
        "candidate_records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"queue_record_count": len(records), "output": str(args.output), "skipped_records": skipped}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
