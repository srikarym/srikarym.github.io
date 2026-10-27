"""Fetch per-paper citation counts from Google Scholar and write citations.js.

Usage: python3 scripts/update_citations.py
"""
import datetime
import json
import pathlib
import re
import sys
import urllib.request

USER = "DVMnHboAAAAJ"
URL = ("https://scholar.google.com/citations?user={user}&hl=en"
       "&cstart={start}&pagesize=100&sortby=pubdate")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
OUT = pathlib.Path(__file__).resolve().parent.parent / "citations.js"


def fetch(start):
    req = urllib.request.Request(URL.format(user=USER, start=start), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    counts = {}
    start = 0
    while True:
        rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', fetch(start), re.S)
        for row in rows:
            pid = re.search(r"citation_for_view=" + USER + r":([\w-]+)", row)
            cnt = re.search(r'class="gsc_a_ac gs_ibl"[^>]*>(\d*)<', row)
            if pid:
                counts[pid.group(1)] = int(cnt.group(1)) if cnt and cnt.group(1) else 0
        if len(rows) < 100:
            break
        start += 100

    if not counts:
        # Scholar returned a captcha or changed its markup; keep the old file.
        sys.exit("No publications parsed from Google Scholar; citations.js left unchanged.")

    data = {"user": USER, "updated": datetime.date.today().isoformat(), "counts": counts}
    OUT.write_text("window.SCHOLAR_CITATIONS = " + json.dumps(data, indent=2, sort_keys=True) + ";\n")
    print(f"Wrote {len(counts)} citation counts to {OUT.name}")


if __name__ == "__main__":
    main()
