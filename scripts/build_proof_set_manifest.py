#!/usr/bin/env python3
"""Build the fixed, metadata-only real-world proof-set manifest from selected Commons files."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any

import requests

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AGI-VS-real-world-proof-set/1.0 (fixed-manifest review; no media acquisition)"

SELECTED = (
    ("city_victoria_harbour", "city", "File:Victoria Harbour skyscrapers.jpg"),
    ("city_kaohsiung", "city", "File:Urban skyline of Kaohsiung, Taiwan at night.jpg"),
    ("animal_iguana", "animal", "File:Iguana de Venezuela.jpg"),
    ("animal_bird", "animal", "File:Bird at Wingham Wildlife Park.jpg"),
    ("house_quebec", "building", "File:House facade in Quebec city, Canada.jpg"),
    ("building_paulista", "building", "File:Building in Paulista Avenue 09.jpg"),
    ("landscape_utah_dunes", "landscape", "File:Utah Dunes Landscape - West Desert District.jpg"),
    ("vehicle_place_etoile", "vehicle", "File:Auto op de Place de l'Étoile, in de koplamp is de weerspiegeling van de Arc de T, Bestanddeelnr 191-0354.jpg"),
)


def clean_markup(value: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def allowed(license_short_name: str, usage_terms: str) -> bool:
    combined = f"{license_short_name} {usage_terms}".upper()
    return "CC0" in combined or "PUBLIC DOMAIN" in combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    records: list[dict[str, Any]] = []
    for asset_id, scene_class, title in SELECTED:
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1280,
        }
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        if len(pages) != 1:
            raise RuntimeError(f"Expected one source-page response for {title}")
        page = next(iter(pages.values()))
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata") or {}
        license_short_name = clean_markup((metadata.get("LicenseShortName") or {}).get("value"))
        usage_terms = clean_markup((metadata.get("UsageTerms") or {}).get("value"))
        delivery_url = info.get("thumburl")
        if not delivery_url or not allowed(license_short_name, usage_terms):
            raise RuntimeError(f"Source {title} failed delivery or CC0/public-domain eligibility")
        records.append({
            "asset_id": asset_id,
            "scene_class": scene_class,
            "source_file_title": page.get("title"),
            "source_page_url": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(str(page.get('title')).replace(' ', '_'), safe=':_(),-')}",
            "delivery_url": delivery_url,
            "original_delivery_url": info.get("url"),
            "source_width": info.get("width"),
            "source_height": info.get("height"),
            "mime": info.get("mime"),
            "license_short_name": license_short_name,
            "usage_terms": usage_terms,
            "artist": clean_markup((metadata.get("Artist") or {}).get("value")),
            "credit": clean_markup((metadata.get("Credit") or {}).get("value")),
            "licence_review": "pass_item_level_CC0_or_public_domain",
            "privacy_safety_visual_review": "pending_after_download",
            "media_downloaded": False,
        })

    manifest = {
        "schema_version": "1.0",
        "status": "approved_for_bounded_acquisition_pending_visual_review",
        "purpose": "frozen AGI-VS observation and performance benchmark; no training or semantic labelling",
        "source": "Wikimedia Commons fixed item-level proof set",
        "rights_policy": "only selected items with explicit CC0 or public-domain metadata are permitted",
        "proof_set_cap": 8,
        "records": records,
        "created_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_policy_urls": [
            "https://commons.wikimedia.org/wiki/Commons:Licensing",
            "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia",
            "https://commons.wikimedia.org/wiki/Commons:API/MediaWiki",
        ],
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    import hashlib
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"record_count": len(records), "manifest_sha256": manifest["manifest_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
