#!/usr/bin/env python3
"""Create and review a deterministic, metadata-only T2.2 source-page sample.

The script reads the locally quarantined T2.1 manifest, selects no more than 50
records deterministically, requests only their landing-page HTML with bounded reads,
and saves no page HTML or media. It never requests media URLs, thumbnails,
annotations, embeddings, or model resources. Every record remains quarantined.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

ALLOWED_LANDING_HOST_SUFFIXES = ("flickr.com",)
MAX_SAMPLE = 50
MAX_HTML_BYTES = 131072
REQUEST_TIMEOUT_SECONDS = 3
MAX_WORKERS = 5
USER_AGENT = "AGI-VS-T2.2-source-review/1.0 (metadata-only; no-media-fetch)"


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.parts.append(data)

    def title(self) -> str:
        return " ".join(" ".join(self.parts).split())[:500]


def stable_sample(records: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    sorted_records = sorted(
        records,
        key=lambda entry: hashlib.sha256(str(entry.get("source_record_id", "")).encode("utf-8")).hexdigest(),
    )
    return sorted_records[:count]


def safe_landing_url(entry: dict[str, Any]) -> str:
    raw = str(entry.get("canonical_source_url") or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        return ""
    if not any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_LANDING_HOST_SUFFIXES):
        return ""
    return raw


def inspect_page(url: str) -> dict[str, Any]:
    if not url:
        return {"request_status": "blocked_invalid_or_unapproved_host"}
    try:
        with requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            stream=True,
        ) as response:
            content_type = response.headers.get("content-type", "")
            body = b""
            if "html" in content_type.lower():
                for chunk in response.iter_content(chunk_size=16384):
                    body += chunk
                    if len(body) >= MAX_HTML_BYTES:
                        body = body[:MAX_HTML_BYTES]
                        break
            parser = TitleParser()
            parser.feed(body.decode(response.encoding or "utf-8", errors="replace"))
            final_host = (urlparse(response.url).hostname or "").lower()
            return {
                "request_status": "completed",
                "http_status": response.status_code,
                "content_type": content_type,
                "final_url": response.url,
                "final_host_allowed": any(final_host == suffix or final_host.endswith("." + suffix) for suffix in ALLOWED_LANDING_HOST_SUFFIXES),
                "page_title": parser.title(),
                "html_bytes_inspected": len(body),
            }
    except requests.RequestException as error:
        return {"request_status": "request_error", "error_type": type(error).__name__, "error": str(error)[:300]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Ignored local audited T2.1 manifest.")
    parser.add_argument("--output", required=True, type=Path, help="Ignored raw T2.2 review log.")
    parser.add_argument("--summary", required=True, type=Path, help="Aggregate T2.2 evidence JSON.")
    parser.add_argument("--sample-size", type=int, default=50)
    args = parser.parse_args()

    if not 1 <= args.sample_size <= MAX_SAMPLE:
        raise SystemExit("--sample-size must be between 1 and 50.")
    source = json.loads(args.input.read_text(encoding="utf-8"))
    candidates = source.get("candidate_records", [])
    if not isinstance(candidates, list) or not candidates:
        raise SystemExit("Input must contain a non-empty candidate_records list.")
    if source.get("hard_limits", {}).get("model_training_permitted") is not False:
        raise SystemExit("Input manifest must explicitly prohibit model training.")

    sample = stable_sample(candidates, args.sample_size)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    records: list[dict[str, Any]] = []
    statuses: dict[str, int] = {}
    http_statuses: dict[str, int] = {}

    landing_urls = [safe_landing_url(candidate) for candidate in sample]
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        page_results = list(executor.map(inspect_page, landing_urls))

    for candidate, landing_url, page in zip(sample, landing_urls, page_results, strict=True):
        request_status = str(page.get("request_status", "unknown"))
        statuses[request_status] = statuses.get(request_status, 0) + 1
        if "http_status" in page:
            code = str(page["http_status"])
            http_statuses[code] = http_statuses.get(code, 0) + 1
        records.append(
            {
                "source_record_id": candidate.get("source_record_id"),
                "landing_url": landing_url,
                "source_creator_or_attribution_party": candidate.get("source_creator_or_attribution_party"),
                "title_if_supplied": candidate.get("title_if_supplied"),
                "source_row_licence_url": candidate.get("source_row_license_text"),
                "source_page_review": page,
                "item_level_licence_verification": "unresolved_requires_human_terms_review",
                "privacy_safety_review": "unresolved_no_media_retrieved",
                "removal_path_review": "unresolved_requires_source_process_review",
                "review_decision": "quarantined",
                "media_downloaded": False,
                "embeddings_generated": False,
                "training_eligibility": "blocked",
                "reviewed_at": timestamp,
            }
        )

    raw_log = {
        "status": "T2.2 bounded source-page review; all records remain quarantined",
        "sample_size": len(records),
        "source_manifest_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "reviewed_at": timestamp,
        "media_downloaded": 0,
        "embeddings_generated": 0,
        "retained_training_records": 0,
        "model_training_permitted": False,
        "records": records,
    }
    summary = {
        "audit_status": "PASS_WITH_ALL_RECORDS_QUARANTINED",
        "sample_size": len(records),
        "sample_limit": MAX_SAMPLE,
        "request_status_counts": dict(sorted(statuses.items())),
        "http_status_counts": dict(sorted(http_statuses.items())),
        "media_downloaded": 0,
        "embeddings_generated": 0,
        "retained_training_records": 0,
        "training_eligible_records": 0,
        "quarantined_records": len(records),
        "unresolved_controls": [
            "item-level licence verification",
            "privacy and safety review without retained media",
            "rights-caveat review",
            "removal procedure confirmation",
            "perceptual and text similarity deduplication",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(raw_log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
