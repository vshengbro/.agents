#!/usr/bin/env python3
"""Today's trending GitHub repositories, read live.

THE LIST IS NEVER READ FROM MEMORY

Yesterday's list is yesterday's list. The list is fetched on every run, and
a run that cannot fetch it publishes no community post rather than publishing
yesterday's.

THE PARSER IS CHECKED AGAINST THE PAGE

A hand-rolled trending parser that matches `<a href="/owner/repo"` returns
ZERO rows against a live, fully populated page: the anchor carries its
attributes before href, and the heading carries a class list. It fails
silently and reads exactly like "trending returned no rows". So the number
of articles on the page is counted and printed next to the number parsed, and
a page with articles but no parsed rows is reported as a PARSER BUG, not as
an empty list.

OWNERSHIP COMES FROM LIVE GIT REMOTES

Never from a flag of a script whose ownership import is wrapped in a
try/except that returns an empty set: that marks every row as not-owned,
including the account's own repositories.

Usage:
    xtrending.py --limit 8
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402

# The heading holds a class list and the anchor carries extra attributes
# before its href, so the pattern allows for both.
ROW = re.compile(r'<h2[^>]*>\s*<a\b[^>]*\bhref="/([^"#?]+)"', re.S)
ARTICLE = re.compile(r'<article class="Box-row".*?</article>', re.S)
LANG = re.compile(r'itemprop="programmingLanguage">([^<]+)<')
TODAY = re.compile(r"([\d,]+)\s*stars?\s*today")
STARS = re.compile(r'href="/[^"]+/stargazers"[^>]*>\s*(?:<svg.*?</svg>)?\s*([\d,]+)', re.S)


def opener():
    """An opener that honours the proxy environment.

    urllib does not traverse this machine's TUN interface the way curl does,
    so a request that works from curl fails with an SSL error from urllib
    unless the proxy is named explicitly.
    """
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    if proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener()


def owned_repos() -> set:
    """The repositories this account owns, from the live git remotes.

    Read from the checkouts rather than written down: a hand-written list
    goes stale on exactly the event that matters, and the failure is silent.
    """
    owned = set()
    base = xconfig.code_dir()
    if not base.is_dir():
        return owned
    for entry in sorted(os.listdir(base)):
        d = base / entry
        if not (d / ".git").exists():
            continue
        try:
            url = subprocess.run(
                ["git", "-C", str(d), "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            continue
        if not url:
            continue
        m = re.search(r"github\.com(?::\d+)?[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
                      url)
        if m:
            owned.add("%s/%s" % (m.group(1).lower(), m.group(2).lower()))
    return owned


def fetch(limit: int):
    """The trending list, read live."""
    req = urllib.request.Request(
        "https://github.com/trending?since=daily",
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "Safari/605.1.15"})
    html = opener().open(req, timeout=25).read().decode("utf-8", "replace")
    articles = ARTICLE.findall(html)
    rows = []
    for art in articles:
        m = ROW.search(art)
        if not m:
            continue
        full = re.sub(r"\s+", "", m.group(1))
        lang = LANG.search(art)
        today = TODAY.search(art)
        stars = STARS.search(art)
        rows.append({
            "full_name": full,
            "url": "https://github.com/" + full,
            "language": lang.group(1) if lang else "",
            "stars": stars.group(1) if stars else "",
            "stars_today": today.group(1) if today else "",
        })
    return rows[:limit], len(articles)


def main(argv) -> int:
    limit = 8
    out = None
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--limit":
            limit = int(args[i + 1]); i += 2
        elif args[i] == "--out":
            out = args[i + 1]; i += 2
        else:
            print("unknown argument: %s" % args[i])
            return 2
    try:
        rows, n_articles = fetch(limit)
    except Exception as exc:
        print("TRENDING FETCH FAILED: %s" % exc)
        return 1
    owned = owned_repos()
    print("read_at:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("articles_on_page: %d | parsed: %d | owned_remotes: %d"
          % (n_articles, len(rows), len(owned)))
    if n_articles and not rows:
        print("PARSER BUG: the page holds %d articles but none parsed -- fix "
              "the anchor pattern; do NOT report this as an empty list"
              % n_articles)
        return 1
    if not rows:
        print("NO TRENDING ROWS")
        return 1
    for row in rows:
        row["mine"] = row["full_name"].lower() in owned
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    print("--- not owned (verified from the live remotes) ---")
    print([r["full_name"] for r in rows if not r["mine"]])
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        print("saved:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
