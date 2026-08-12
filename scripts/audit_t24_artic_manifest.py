#!/usr/bin/env python3
"""Fail-closed audit for the T2.4 Art Institute CC0 metadata-only candidate manifest."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path


def manifest_hash(manifest: dict) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    unsigned.pop("created_utc", None)
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    audit_decisions = [
        json.loads(line)
        for line in args.audit_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    failures: list[str] = []
    warnings: list[str] = []
    records = manifest.get("records")
    audit = manifest.get("audit", {})
    selection = manifest.get("selection", {})

    if manifest.get("manifest_status") != "metadata_only_candidate_allow_list_not_yet_acquired":
        failures.append("manifest status is not metadata-only candidate allow-list")
    if not isinstance(records, list):
        failures.append("records is not a list")
        records = []
    if len(records) != 200:
        failures.append(f"expected exactly 200 selected records, found {len(records)}")
    if selection.get("pilot_cap") != 200:
        failures.append("selection pilot cap is not 200")
    if selection.get("max_source_records_reviewed") != 1000:
        failures.append("source review cap is not the declared 1000 records")
    if audit.get("source_records_reviewed") != 1000:
        failures.append("audit source-record count differs from declared bounded review")
    if audit.get("selected_records") != len(records):
        failures.append("audit selected-record count does not match manifest")
    if manifest.get("manifest_sha256") != manifest_hash(manifest):
        failures.append("manifest SHA-256 does not match canonical manifest contents")

    required_fields = {
        "asset_id", "source_artwork_id", "source_api_url", "source_policy_url",
        "source_image_licensing_url", "source_terms_url", "is_public_domain",
        "image_id", "iiif_url", "title", "classification_title", "department_title",
        "normalized_title", "text_target", "metadata_review", "media_acquired", "split",
    }
    ids: set[str] = set()
    source_ids: set[int] = set()
    titles: set[str] = set()
    splits: collections.Counter[str] = collections.Counter()
    categories: set[str] = set()

    for row_number, record in enumerate(records, start=1):
        missing = sorted(field for field in required_fields if field not in record)
        if missing:
            failures.append(f"record {row_number} missing fields: {', '.join(missing)}")
            continue
        if record["asset_id"] in ids:
            failures.append(f"duplicate asset_id: {record['asset_id']}")
        ids.add(record["asset_id"])
        if record["source_artwork_id"] in source_ids:
            failures.append(f"duplicate source artwork ID: {record['source_artwork_id']}")
        source_ids.add(record["source_artwork_id"])
        if record["normalized_title"] in titles:
            failures.append(f"duplicate normalized title: {record['normalized_title']}")
        titles.add(record["normalized_title"])
        if record["is_public_domain"] is not True:
            failures.append(f"non-public-domain record present: {record['asset_id']}")
        if record["metadata_review"] != "pass":
            failures.append(f"non-passing metadata review: {record['asset_id']}")
        if record["media_acquired"] is not False:
            failures.append(f"media-acquired flag unexpectedly true: {record['asset_id']}")
        if not record["source_api_url"].endswith(f"/{record['source_artwork_id']}"):
            failures.append(f"source API URL mismatch: {record['asset_id']}")
        if record["image_id"] not in record["iiif_url"]:
            failures.append(f"IIIF URL does not contain image ID: {record['asset_id']}")
        if not all(isinstance(record[field], str) and record[field].strip() for field in ("title", "classification_title", "department_title", "text_target")):
            failures.append(f"missing target text field: {record['asset_id']}")
        split = record["split"]
        if split not in {"train", "dev", "held_out"}:
            failures.append(f"invalid split {split}: {record['asset_id']}")
        splits[split] += 1
        categories.add(record["classification_title"].strip().lower())

    if not splits.get("train") or not splits.get("dev") or not splits.get("held_out"):
        failures.append("one or more required splits are empty")
    if len(categories) < 20:
        failures.append(f"fewer than 20 classification categories: {len(categories)}")
    if len(audit_decisions) != 1000:
        failures.append(f"audit log contains {len(audit_decisions)} decisions, expected 1000")
    selected_artwork_ids = {record["source_artwork_id"] for record in records}
    candidate_decision_ids = {
        decision.get("artwork_id")
        for decision in audit_decisions
        if decision.get("decision") == "candidate"
    }
    if candidate_decision_ids != selected_artwork_ids:
        failures.append("audit-log candidate decisions do not exactly match selected manifest IDs")
    if not audit.get("exclusion_counts"):
        warnings.append("no exclusion counts recorded")

    report = {
        "audit_name": "T2.4 Art Institute CC0 manifest audit",
        "manifest": str(args.manifest),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "status": "pass" if not failures else "fail",
        "hard_failures": failures,
        "warnings": warnings,
        "selected_record_count": len(records),
        "source_records_reviewed": audit.get("source_records_reviewed"),
        "split_counts": dict(sorted(splits.items())),
        "classification_category_count": len(categories),
        "media_requested_or_acquired": False,
        "next_action": "media acquisition permitted only for exact manifest IDs if status is pass",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
