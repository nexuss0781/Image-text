#!/usr/bin/env python3
"""Audit T2.2 source-page review completeness without using any media or model data."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    review = json.loads(args.input.read_text(encoding="utf-8"))
    records = review.get("records", [])
    if not isinstance(records, list) or len(records) > 50:
        raise SystemExit("T2.2 input must contain no more than 50 review records.")

    http_statuses: Counter[str] = Counter()
    request_statuses: Counter[str] = Counter()
    missing_fields: Counter[str] = Counter()
    unresolved: Counter[str] = Counter()
    non_quarantined = 0
    eligible = 0
    media_downloaded = 0
    embeddings_generated = 0

    for record in records:
        page = record.get("source_page_review", {})
        request_statuses[str(page.get("request_status", "missing"))] += 1
        if "http_status" in page:
            http_statuses[str(page["http_status"])] += 1
        for field in ("source_record_id", "landing_url", "source_creator_or_attribution_party", "source_row_licence_url"):
            if not str(record.get(field) or "").strip():
                missing_fields[field] += 1
        for field in ("item_level_licence_verification", "privacy_safety_review", "removal_path_review"):
            if "unresolved" in str(record.get(field, "")):
                unresolved[field] += 1
        if record.get("review_decision") != "quarantined":
            non_quarantined += 1
        if record.get("training_eligibility") != "blocked":
            eligible += 1
        media_downloaded += int(bool(record.get("media_downloaded")))
        embeddings_generated += int(bool(record.get("embeddings_generated")))

    retention_ready = (
        len(records) > 0
        and not missing_fields
        and not unresolved
        and non_quarantined == 0
        and eligible == 0
        and media_downloaded == 0
        and embeddings_generated == 0
    )
    report: dict[str, Any] = {
        "audit_status": "PASS_BLOCKED_FOR_RETENTION",
        "sample_size": len(records),
        "sample_limit": 50,
        "request_status_counts": dict(sorted(request_statuses.items())),
        "http_status_counts": dict(sorted(http_statuses.items())),
        "missing_required_review_fields": dict(sorted(missing_fields.items())),
        "unresolved_control_counts": dict(sorted(unresolved.items())),
        "non_quarantined_records": non_quarantined,
        "training_eligible_records": eligible,
        "media_downloaded": media_downloaded,
        "embeddings_generated": embeddings_generated,
        "retention_ready": retention_ready,
        "retention_blockers": [
            "All records remain quarantined by design.",
            "Item-level licence verification remains unresolved.",
            "Privacy and safety review remains unresolved because no media was retained or inspected.",
            "Removal-path confirmation remains unresolved.",
            "Perceptual/text similarity deduplication was not performed.",
        ],
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
