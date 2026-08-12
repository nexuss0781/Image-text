#!/usr/bin/env python3
"""Discover item-level licensed Wikimedia Commons proof-image candidates without media download."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Any

import requests

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AGI-VS-real-world-proof-set/1.0 (rights-review; no media acquisition)"

QUERIES = {
    "city": "city skyline filetype:bitmap",
    "city_alternate": "urban skyline filetype:bitmap",
    "animal": "elephant wildlife filetype:bitmap",
    "animal_alternate": "bird wildlife filetype:bitmap",
    "house": "house architecture filetype:bitmap",
    "house_alternate": "cottage house filetype:bitmap",
    "landscape": "mountain landscape filetype:bitmap",
    "vehicle": "car road landscape filetype:bitmap",
}


def clean_markup(value: str | None) -> str:
    if not value:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def safe_license(short_name: str, usage_terms: str) -> bool:
    combined = f"{short_name} {usage_terms}".upper()
    # Accept CC0, PD, or attribution-only CC BY. Exclude ShareAlike to avoid
    # imposing a downstream repository licensing question on a proof benchmark.
    return (
        "CC0" in combined
        or "PUBLIC DOMAIN" in combined
        or ("CC BY" in combined and "SA" not in combined and "NC" not in combined and "ND" not in combined)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-query", type=int, default=20)
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    candidates: list[dict[str, Any]] = []
    query_audit: list[dict[str, Any]] = []

    for scene_class, query in QUERIES.items():
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": args.per_query,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1024,
        }
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        pages = payload.get("query", {}).get("pages", {})
        reviewed = 0
        eligible = 0
        for page in pages.values():
            reviewed += 1
            info = (page.get("imageinfo") or [{}])[0]
            metadata = info.get("extmetadata") or {}
            licence_short_name = clean_markup((metadata.get("LicenseShortName") or {}).get("value"))
            usage_terms = clean_markup((metadata.get("UsageTerms") or {}).get("value"))
            candidate = {
                "scene_class": scene_class,
                "search_query": query,
                "title": page.get("title"),
                "page_id": page.get("pageid"),
                "source_page_url": f"https://commons.wikimedia.org/wiki/{str(page.get('title', '')).replace(' ', '_')}",
                "delivery_url": info.get("thumburl"),
                "original_delivery_url": info.get("url"),
                "width": info.get("width"),
                "height": info.get("height"),
                "mime": info.get("mime"),
                "license_short_name": licence_short_name,
                "usage_terms": usage_terms,
                "artist": clean_markup((metadata.get("Artist") or {}).get("value")),
                "credit": clean_markup((metadata.get("Credit") or {}).get("value")),
                "attribution_required": "CC BY" in f"{licence_short_name} {usage_terms}".upper(),
                "eligible_by_license": safe_license(licence_short_name, usage_terms),
                "media_downloaded": False,
            }
            candidates.append(candidate)
            eligible += int(candidate["eligible_by_license"] and bool(candidate["delivery_url"]))
        query_audit.append({"scene_class": scene_class, "query": query, "reviewed": reviewed, "delivery_and_license_eligible": eligible})

    payload = {
        "status": "metadata_only_candidate_review",
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": "Wikimedia Commons Action API",
        "source_policy_urls": [
            "https://commons.wikimedia.org/wiki/Commons:Licensing",
            "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia",
            "https://commons.wikimedia.org/wiki/Commons:API/MediaWiki",
        ],
        "allowed_license_rule": "CC0, explicit public domain, or CC BY without SA/NC/ND; final item-level source evidence and visual review still required",
        "query_audit": query_audit,
        "candidates": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"query_audit": query_audit, "candidate_count": len(candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
