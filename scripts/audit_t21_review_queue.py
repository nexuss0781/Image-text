#!/usr/bin/env python3
"""Audit a T2.1 record-review queue without reading, downloading, or processing media.

All queue records remain blocked because record-level licence verification, privacy/safety
review, and perceptual/text duplicate checks require additional approved review work.
The audit assigns reproducible proposed split labels but grants no training eligibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def canonical_payload(entry: dict[str, Any]) -> str:
    data = {key: value for key, value in entry.items() if key != "manifest_entry_checksum"}
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def entry_checksum(entry: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(entry).encode("utf-8")).hexdigest()


def proposed_split(record_id: str) -> str:
    bucket = int(hashlib.sha256(record_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 10:
        return "proposed_held_out"
    if bucket < 20:
        return "proposed_development"
    return "proposed_training"


def missing_fields(entry: dict[str, Any]) -> list[str]:
    required = {
        "source_record_id": entry.get("source_record_id"),
        "canonical_source_url": entry.get("canonical_source_url"),
        "source_creator_or_attribution_party": entry.get("source_creator_or_attribution_party"),
        "item_level_licence_evidence_url": entry.get("item_level_licence_evidence_url"),
        "source_row_media_url": entry.get("source_row_media_url"),
    }
    return [name for name, field in required.items() if not str(field or "").strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    records = data.get("candidate_records", [])
    if not isinstance(records, list) or len(records) > 1000:
        raise SystemExit("Review queue must be a list of no more than 1,000 records.")
    if data.get("hard_limits", {}).get("bulk_download_permitted") is not False:
        raise SystemExit("Input manifest violates the no-bulk-download hard limit.")
    if data.get("hard_limits", {}).get("model_training_permitted") is not False:
        raise SystemExit("Input manifest violates the no-training hard limit.")

    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_by_field: Counter[str] = Counter()
    licence_values: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    audited: list[dict[str, Any]] = []
    audit_time = datetime.now(UTC).replace(microsecond=0).isoformat()

    for original in records:
        entry = dict(original)
        record_id = str(entry.get("source_record_id") or "")
        if record_id in seen_ids:
            duplicate_ids.append(record_id)
        seen_ids.add(record_id)
        for field in missing_fields(entry):
            missing_by_field[field] += 1
        licence_values[str(entry.get("source_row_license_text") or "<missing>")] += 1

        split = proposed_split(record_id) if record_id else "unassigned"
        split_counts[split] += 1
        entry["split_assignment"] = split
        entry["exact_record_id_duplicate_check"] = "failed_duplicate" if record_id in duplicate_ids else "passed"
        entry["metadata_provenance_status"] = "incomplete" if missing_fields(entry) else "metadata_complete_pending_item_verification"
        entry["content_privacy_safety_review_status"] = "requires_human_review_no_media_processed"
        entry["rights_caveat_review_status"] = "requires_human_review_no_item_level_verification"
        entry["deduplication_review_status"] = "exact_id_checked_media_and_text_similarity_unassessed"
        entry["removal_contact_or_source_procedure"] = "source_procedure_pending_human_review"
        entry["review_queue_state"] = "quarantined_pending_human_review"
        entry["training_eligibility"] = "blocked"
        entry["media_downloaded"] = False
        entry["embeddings_generated"] = False
        entry["audit_timestamp"] = audit_time
        entry["manifest_entry_checksum"] = ""
        entry["manifest_entry_checksum"] = entry_checksum(entry)
        audited.append(entry)

    output = {
        "schema_version": "1.0",
        "manifest_status": "T2.1 audited review queue — all records quarantined; no media retained or training authorized",
        "program": data.get("program"),
        "source": data.get("source"),
        "hard_limits": {
            "maximum_review_queue_records": 1000,
            "queue_record_count": len(audited),
            "bulk_download_permitted": False,
            "web_media_reconstruction_permitted": False,
            "retained_training_records": 0,
            "embedding_generation_permitted": False,
            "model_training_permitted": False,
        },
        "input_manifest_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "audit_timestamp": audit_time,
        "candidate_records": audited,
    }
    report = {
        "audit_status": "PASS_WITH_ALL_RECORDS_QUARANTINED",
        "queue_record_count": len(audited),
        "hard_limit_pass": len(audited) <= 1000,
        "unique_record_id_count": len(seen_ids),
        "duplicate_record_id_count": len(set(duplicate_ids)),
        "missing_required_metadata_fields": dict(sorted(missing_by_field.items())),
        "source_row_licence_values": dict(sorted(licence_values.items())),
        "proposed_split_counts": dict(sorted(split_counts.items())),
        "media_downloaded": 0,
        "embeddings_generated": 0,
        "retained_training_records": 0,
        "training_eligible_records": 0,
        "quarantined_records": len(audited),
        "unresolved_controls": [
            "per-record source and licence verification",
            "privacy and sensitive-content review",
            "rights-caveat review",
            "perceptual and text similarity deduplication",
            "removal procedure confirmation",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
