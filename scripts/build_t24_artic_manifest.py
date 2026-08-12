#!/usr/bin/env python3
"""Build a finite metadata-only candidate manifest for the T2.4 Art Institute CC0 pilot.

This tool does not request IIIF images, thumbnails, manifests, or any other media. It only
queries the provider's documented artwork metadata API and writes a reviewable allow-list.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import requests

API_URL = "https://api.artic.edu/api/v1/artworks/search"
API_BASE = "https://api.artic.edu/api/v1/artworks"
IIIF_BASE = "https://www.artic.edu/iiif/2"
SOURCE_POLICY_URL = "https://www.artic.edu/collection-information/open-access/open-access-images"
SOURCE_IMAGE_LICENSING_URL = "https://www.artic.edu/collection-information/image-licensing"
SOURCE_TERMS_URL = "https://www.artic.edu/terms"

# Intentionally conservative metadata-only exclusions. An uncertain candidate is excluded.
FORBIDDEN_TERMS = (
    "portrait",
    "self-portrait",
    "person",
    "people",
    "human",
    "figure",
    "nude",
    "nudity",
    "naked",
    "erotic",
    "sexual",
    "sex",
    "violence",
    "violent",
    "battle",
    "war",
    "weapon",
    "sword",
    "gun",
    "rifle",
    "death",
    "dead",
    "murder",
    "execution",
    "blood",
    "skull",
    "trauma",
    "slavery",
    "enslaved",
    "colonial",
    "holocaust",
    "genocide",
    "racism",
    "racial",
    "anatomy",
    "body",
    "flesh",
    "christ",
    "saint",
    "buddha",
    "religious",
    "religion",
    "sacred",
    "prayer",
    "church",
    "mosque",
    "synagogue",
)

FIELDS = (
    "id,title,is_public_domain,image_id,department_title,classification_title,"
    "subject_titles,artist_title,date_display,api_link"
)


def stable_hash(seed: str, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def values_for_review(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("title", "department_title", "classification_title", "artist_title", "date_display"):
        value = record.get(key)
        if isinstance(value, str):
            values.append(value)
    subjects = record.get("subject_titles")
    if isinstance(subjects, list):
        values.extend(str(value) for value in subjects if isinstance(value, str))
    return normalize(" ".join(values))


def exclusion_reason(record: dict[str, Any], seen_titles: set[str]) -> str | None:
    artwork_id = record.get("id")
    title = record.get("title")
    classification = record.get("classification_title")
    department = record.get("department_title")
    image_id = record.get("image_id")

    if record.get("is_public_domain") is not True:
        return "public_domain_flag_not_true"
    if not isinstance(artwork_id, int):
        return "missing_stable_artwork_id"
    if not isinstance(image_id, str) or not image_id.strip():
        return "missing_image_reference"
    if not isinstance(title, str) or not title.strip():
        return "missing_title"
    if not isinstance(classification, str) or not classification.strip():
        return "missing_classification"
    if not isinstance(department, str) or not department.strip():
        return "missing_department"

    normalized_title = normalize(title)
    if normalized_title in seen_titles:
        return "duplicate_normalized_title"

    review_text = values_for_review(record)
    for term in FORBIDDEN_TERMS:
        if term in review_text:
            return f"metadata_safety_exclusion:{term}"
    return None


def target_text(record: dict[str, Any]) -> str:
    return (
        f"Title: {record['title']}. "
        f"Classification: {record['classification_title']}. "
        f"Department: {record['department_title']}."
    )


def select_diverse(candidates: list[dict[str, Any]], cap: int, seed: str) -> tuple[list[dict[str, Any]], list[str]]:
    by_category: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for candidate in candidates:
        by_category[normalize(candidate["classification_title"])].append(candidate)

    viable_categories = [
        category for category, records in by_category.items() if len(records) >= 5
    ]
    viable_categories.sort(key=lambda category: (-len(by_category[category]), category))
    selected_categories = viable_categories[:40]
    if len(selected_categories) < 20:
        selected_categories = sorted(by_category, key=lambda category: (-len(by_category[category]), category))[:40]

    category_records: dict[str, list[dict[str, Any]]] = {}
    for category in selected_categories:
        category_records[category] = sorted(
            by_category[category],
            key=lambda record: stable_hash(seed, str(record["source_artwork_id"])),
        )

    selection: list[dict[str, Any]] = []
    positions = {category: 0 for category in selected_categories}
    per_category_limit = max(1, (cap + max(1, len(selected_categories)) - 1) // max(1, len(selected_categories)) + 2)
    per_category_used: collections.Counter[str] = collections.Counter()

    while len(selection) < cap:
        progress = False
        for category in selected_categories:
            if len(selection) >= cap:
                break
            if per_category_used[category] >= per_category_limit:
                continue
            position = positions[category]
            records = category_records[category]
            if position >= len(records):
                continue
            selection.append(records[position])
            positions[category] += 1
            per_category_used[category] += 1
            progress = True
        if not progress:
            break

    # Preserve the initial category-balanced allocation, then fill any remaining
    # capacity from the already screened candidate pool in deterministic order.
    # This avoids rejecting eligible records solely because smaller categories
    # exhaust before the finite pilot cap is reached.
    selected_ids = {record["source_artwork_id"] for record in selection}
    if len(selection) < cap:
        for candidate in sorted(
            candidates,
            key=lambda record: stable_hash(f"{seed}:fill", str(record["source_artwork_id"])),
        ):
            if len(selection) >= cap:
                break
            if candidate["source_artwork_id"] in selected_ids:
                continue
            selection.append(candidate)
            selected_ids.add(candidate["source_artwork_id"])

    return selection, selected_categories


def split_records(records: Iterable[dict[str, Any]], seed: str) -> None:
    by_category: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        by_category[normalize(record["classification_title"])].append(record)

    for category, category_records in by_category.items():
        ordered = sorted(
            category_records,
            key=lambda record: stable_hash(f"{seed}:split", str(record["source_artwork_id"])),
        )
        count = len(ordered)
        train_count = max(1, round(count * 0.70))
        dev_count = max(1, round(count * 0.15)) if count >= 7 else 0
        if train_count + dev_count >= count:
            dev_count = max(0, count - train_count - 1)
        for index, record in enumerate(ordered):
            if index < train_count:
                record["split"] = "train"
            elif index < train_count + dev_count:
                record["split"] = "dev"
            else:
                record["split"] = "held_out"


def fetch_records(max_records: int, timeout: float) -> Iterable[dict[str, Any]]:
    session = requests.Session()
    page = 1
    reviewed = 0
    while reviewed < max_records:
        remaining = max_records - reviewed
        limit = min(100, remaining)
        params = {
            "query[term][is_public_domain]": "true",
            "fields": FIELDS,
            "limit": limit,
            "page": page,
        }
        response = session.get(API_URL, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        records = payload.get("data")
        if not isinstance(records, list) or not records:
            break
        for record in records:
            if isinstance(record, dict):
                yield record
                reviewed += 1
                if reviewed >= max_records:
                    break
        if len(records) < limit or reviewed >= max_records:
            break
        # The search endpoint exposes deterministic page numbers but does not always
        # return a next_url. Continue only within the explicit bounded record cap.
        page += 1
        time.sleep(0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Output JSON manifest path")
    parser.add_argument("--audit-log", type=Path, required=True, help="Output JSONL decision log path")
    parser.add_argument("--summary", type=Path, required=True, help="Output JSON summary path")
    parser.add_argument("--pilot-cap", type=int, default=300)
    parser.add_argument("--max-source-records", type=int, default=6000)
    parser.add_argument("--seed", default="agi-vs-t24-artic-cc0-v1")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    if args.pilot_cap <= 0 or args.max_source_records < args.pilot_cap:
        raise ValueError("pilot cap must be positive and no larger than max source records")

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.audit_log.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)

    seen_titles: set[str] = set()
    candidates: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    reason_counts: collections.Counter[str] = collections.Counter()

    for record in fetch_records(args.max_source_records, args.timeout):
        reason = exclusion_reason(record, seen_titles)
        record_id = record.get("id")
        if reason:
            reason_counts[reason] += 1
            decisions.append({"artwork_id": record_id, "decision": "exclude", "reason": reason})
            continue
        seen_titles.add(normalize(record["title"]))
        candidate = {
            "asset_id": f"artic-{record['id']}",
            "source_artwork_id": record["id"],
            "source_api_url": f"{API_BASE}/{record['id']}",
            "source_policy_url": SOURCE_POLICY_URL,
            "source_image_licensing_url": SOURCE_IMAGE_LICENSING_URL,
            "source_terms_url": SOURCE_TERMS_URL,
            "is_public_domain": True,
            "image_id": record["image_id"],
            "iiif_url": f"{IIIF_BASE}/{record['image_id']}/full/843,/0/default.jpg",
            "title": record["title"].strip(),
            "classification_title": record["classification_title"].strip(),
            "department_title": record["department_title"].strip(),
            "artist_title": (record.get("artist_title") or "").strip(),
            "date_display": (record.get("date_display") or "").strip(),
            "normalized_title": normalize(record["title"]),
            "text_target": target_text(record),
            "metadata_review": "pass",
            "media_acquired": False,
        }
        candidates.append(candidate)
        decisions.append({"artwork_id": record_id, "decision": "candidate", "reason": "metadata_pass"})

    selected, selected_categories = select_diverse(candidates, args.pilot_cap, args.seed)
    selected_ids = {record["source_artwork_id"] for record in selected}
    for decision in decisions:
        if decision["decision"] == "candidate" and decision["artwork_id"] not in selected_ids:
            decision["decision"] = "exclude"
            decision["reason"] = "not_selected_by_diversity_cap"
            reason_counts["not_selected_by_diversity_cap"] += 1

    split_records(selected, args.seed)
    selected.sort(key=lambda record: record["asset_id"])
    selected_category_count = len({normalize(record["classification_title"]) for record in selected})
    split_counts = collections.Counter(record["split"] for record in selected)

    manifest = {
        "schema_version": "1.0",
        "manifest_status": "metadata_only_candidate_allow_list_not_yet_acquired",
        "source": {
            "provider": "Art Institute of Chicago",
            "api_url": API_URL,
            "source_policy_url": SOURCE_POLICY_URL,
            "source_image_licensing_url": SOURCE_IMAGE_LICENSING_URL,
            "source_terms_url": SOURCE_TERMS_URL,
            "provider_contact": "image-requests@artic.edu",
        },
        "selection": {
            "seed": args.seed,
            "pilot_cap": args.pilot_cap,
            "max_source_records_reviewed": args.max_source_records,
            "api_fields": FIELDS.split(","),
            "public_domain_query": "query[term][is_public_domain]=true",
            "forbidden_metadata_terms": list(FORBIDDEN_TERMS),
            "diversity_strategy": "up_to_40_highest-coverage classification categories; deterministic round-robin with per-category cap",
            "text_target_policy": "title, classification, and department only; no raw description or biography text",
            "media_policy": "No image, thumbnail, IIIF manifest, or other media requested by this manifest-building run.",
        },
        "audit": {
            "source_records_reviewed": len(decisions),
            "metadata_candidates_before_diversity_cap": len(candidates),
            "selected_records": len(selected),
            "selected_classification_categories": selected_category_count,
            "selected_category_pool": selected_categories,
            "split_counts": dict(sorted(split_counts.items())),
            "exclusion_counts": dict(sorted(reason_counts.items())),
        },
        "records": selected,
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    manifest["created_utc"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.audit_log.open("w", encoding="utf-8") as handle:
        for decision in decisions:
            handle.write(json.dumps(decision, sort_keys=True) + "\n")
    summary = {
        "manifest_path": str(args.manifest),
        "manifest_sha256": manifest["manifest_sha256"],
        "source_records_reviewed": len(decisions),
        "selected_records": len(selected),
        "selected_classification_categories": selected_category_count,
        "split_counts": dict(sorted(split_counts.items())),
        "exclusion_counts": dict(sorted(reason_counts.items())),
        "media_requested": False,
        "created_utc": manifest["created_utc"],
    }
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if len(selected) < args.pilot_cap:
        print(
            f"ERROR: selected {len(selected)} records, below required pilot cap {args.pilot_cap}; no acquisition is authorized.",
            file=sys.stderr,
        )
        return 2
    if selected_category_count < 20:
        print(
            f"ERROR: selected {selected_category_count} classification categories, below minimum 20; no acquisition is authorized.",
            file=sys.stderr,
        )
        return 3
    if split_counts.get("held_out", 0) == 0 or split_counts.get("dev", 0) == 0:
        print("ERROR: required development or held-out split is empty; no acquisition is authorized.", file=sys.stderr)
        return 4

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
