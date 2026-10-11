"""Fetch every source listed in data/sources.csv into data/raw/.

Wikipedia pages are fetched through the MediaWiki API (TextExtracts, plain text with
``== Section ==`` markers) together with the revision id, so the exact text version is
recorded. Nothing here is committed except what the licence allows (see data/sources.csv).

Usage:
    uv run python scripts/fetch_data.py            # fetch all
    uv run python scripts/fetch_data.py --only ko  # one language
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "data" / "sources.csv"
RAW_WIKI = REPO / "data" / "raw" / "wiki"
USER_AGENT = "bearing-rag-bench/0.1 (research project; https://github.com/Juunary/bearing-rag-bench)"


def fetch_wikipedia(lang: str, title: str) -> dict:
    params = {
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
        "prop": "extracts|revisions|info",
        "explaintext": "1", "exsectionformat": "wiki",
        "rvprop": "ids|timestamp", "inprop": "url",
        "titles": title,
    }
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    page = data["query"]["pages"][0]
    if page.get("missing"):
        raise RuntimeError(f"{lang}:{title} is missing")
    rev = page["revisions"][0]
    return {
        "lang": lang,
        "title": page["title"],              # canonical title after redirect
        "requested_title": title,
        "pageid": page["pageid"],
        "revid": rev["revid"],
        "rev_timestamp": rev["timestamp"],
        "url": page["fullurl"],
        "text": page["extract"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="language code filter")
    ap.add_argument("--force", action="store_true", help="re-fetch even if the raw file exists")
    args = ap.parse_args()

    RAW_WIKI.mkdir(parents=True, exist_ok=True)
    with open(SOURCES, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    n_ok = n_skip = 0
    for row in rows:
        if args.only and row["lang"] != args.only:
            continue
        if row["source_type"] != "wikipedia":
            print(f"skip {row['doc_id']}: source_type {row['source_type']} not handled", file=sys.stderr)
            continue
        out = RAW_WIKI / f"{row['doc_id']}.json"
        if out.exists() and not args.force:
            n_skip += 1
            continue
        page = fetch_wikipedia(row["lang"], row["title"])
        page["doc_id"] = row["doc_id"]
        page["license"] = row["license"]
        page["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        out.write_text(json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{row['doc_id']:34} rev={page['revid']} chars={len(page['text'])}")
        n_ok += 1
        time.sleep(0.5)   # be polite to the API
    print(f"fetched {n_ok}, skipped {n_skip} (already present)")


if __name__ == "__main__":
    main()
