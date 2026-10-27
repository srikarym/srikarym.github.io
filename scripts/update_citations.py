"""Fetch per-paper citation counts from Google Scholar and write citations.js.

Uses the SerpAPI Google Scholar Author API when SERPAPI_KEY is set (needed on
GitHub Actions, where Scholar blocks direct requests); otherwise scrapes the
public profile page directly.

Usage: [SERPAPI_KEY=...] python3 scripts/update_citations.py
"""
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

USER = "DVMnHboAAAAJ"
SCHOLAR_URL = ("https://scholar.google.com/citations?user={user}&hl=en"
               "&cstart={start}&pagesize=100&sortby=pubdate")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
OUT = pathlib.Path(__file__).resolve().parent.parent / "citations.js"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def counts_from_serpapi(key):
    counts = {}
    start = 0
    while True:
        query = urllib.parse.urlencode({
            "engine": "google_scholar_author", "author_id": USER, "hl": "en",
            "num": 100, "start": start, "api_key": key,
        })
        data = json.loads(get("https://serpapi.com/search.json?" + query))
        if "error" in data:
            sys.exit("SerpAPI error: " + data["error"])
        articles = data.get("articles", [])
        for art in articles:
            pid = art.get("citation_id", "").split(":")[-1]
            if pid:
                counts[pid] = (art.get("cited_by") or {}).get("value") or 0
        if len(articles) < 100:
            return counts
        start += 100


def counts_from_scholar():
    counts = {}
    start = 0
    while True:
        rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', get(SCHOLAR_URL.format(user=USER, start=start)), re.S)
        for row in rows:
            pid = re.search(r"citation_for_view=" + USER + r":([\w-]+)", row)
            cnt = re.search(r'class="gsc_a_ac gs_ibl"[^>]*>(\d*)<', row)
            if pid:
                counts[pid.group(1)] = int(cnt.group(1)) if cnt and cnt.group(1) else 0
        if len(rows) < 100:
            return counts
        start += 100


def main():
    key = os.environ.get("SERPAPI_KEY")
    counts = counts_from_serpapi(key) if key else counts_from_scholar()

    if not counts:
        # Scholar returned a captcha or changed its markup; keep the old file.
        sys.exit("No publications parsed from Google Scholar; citations.js left unchanged.")

    data = {"user": USER, "updated": datetime.date.today().isoformat(), "counts": counts}
    OUT.write_text("window.SCHOLAR_CITATIONS = " + json.dumps(data, indent=2, sort_keys=True) + ";\n")
    print(f"Wrote {len(counts)} citation counts to {OUT.name}")


if __name__ == "__main__":
    main()
