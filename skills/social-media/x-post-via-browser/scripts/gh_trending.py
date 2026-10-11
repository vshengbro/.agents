#!/usr/bin/env python3
"""GitHub's trending repositories for the last 24 hours, read live.

A promotion post has to name a repository that is genuinely hot RIGHT NOW, and
"genuinely hot right now" is a fact about github.com/trending, not something an
agent should remember. The trending page is public, needs no token, and returns
the daily window on every load — so this is the read command a cron prompt
names, rather than a list of repositories typed into the prompt once.

Output is JSON: [{full_name, url, description, language, stars_today, stars, mine}]

`mine` is derived from org_repos.owner_set() at CALL TIME, so the account's own
work is marked without a second hardcoded list going stale after a rename.

  python3 gh_trending.py
  python3 gh_trending.py --since daily --lang rust --limit 5
  python3 gh_trending.py --community        # drop the account's own repos
  python3 gh_trending.py --self-test

Read-only: it fetches one public page over HTTPS and prints. It does not touch
the browser, the composer, or any credential.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
TRENDING = "https://github.com/trending"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _text(html: str) -> str:
    return _WS.sub(" ", _TAG.sub(" ", html)).strip()


def _int(text: str) -> int:
    m = re.search(r"([\d,]+)", text or "")
    return int(m.group(1).replace(",", "")) if m else 0


def fetch(since: str = "daily", lang: str | None = None,
          timeout: int = 30) -> str:
    """The trending page's HTML. One GET; no auth, no cookies."""
    url = f"{TRENDING}?since={urllib.parse.quote(since)}"
    if lang:
        url += f"&language={urllib.parse.quote(lang)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode(
        "utf-8", "replace")


def parse(html: str, mine_owners: set[str] | None = None) -> list[dict]:
    """Every repository in one trending row, in page order.

    The page has no stable class or id per row beyond `Box-row`, so the row is
    located by that and the fields inside it by the structure GitHub has used
    unchanged for years: an <h2> holding owner/repo, a description <p>, a
    language item, the total star count and "N stars today".
    """
    owners = mine_owners if mine_owners is not None else _owners()
    out: list[dict] = []
    for row in re.findall(r'<article class="Box-row".*?</article>', html, re.S):
        h2 = re.search(r"<h2.*?</h2>", row, re.S)
        if not h2:
            continue
        name = _text(h2.group(0)).replace("/", " ").replace("  ", " ").strip()
        parts = name.split()
        if len(parts) < 2:
            continue
        full_name = f"{parts[0]}/{parts[1]}"
        desc = ""
        dp = re.search(r'<p class="col-9[^"]*">(.*?)</p>', row, re.S)
        if dp:
            desc = _text(dp.group(1))
        # The language is a <span itemprop="programmingLanguage">; accept a
        # <li> of the same itemprop too, so a markup move is a wider match
        # rather than a silently empty language on every row.
        li = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)</',
                       row, re.S)
        lang = _text(li.group(1)) if li else ""
        st = re.search(r'stargazers"[^>]*>(.*?)</a>', row, re.S)
        today = re.search(r"([\d,]+)\s*stars?\s*(?:today|this week|this month)",
                          _text(row), re.I)
        out.append({
            "full_name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": desc,
            "language": lang,
            "stars": _int(_text(st.group(1))) if st else 0,
            "stars_today": _int(today.group(1)) if today else 0,
            "mine": parts[0] in owners,
        })
    return out


def _owners() -> set[str]:
    """This account's GitHub owners, read live. Never raises."""
    try:
        import org_repos
        return set(org_repos.owner_set(force=True))
    except Exception:
        return set()


def self_test() -> int:
    """Prove the parser reads a row rather than trusting that it does."""
    sample = """
    <article class="Box-row">
      <h2><a href="/foo/bar">foo / bar</a></h2>
      <p class="col-9 color-fg-muted my-1 pr-4">
        A tiny &amp; fast <thing> for &lt;devs&gt;
      </p>
      <ul><span itemprop="programmingLanguage">Rust</span></ul>
      <a href="/foo/bar/stargazers">1,234</a>
      <span class="d-inline-block float-sm-right">987 stars today</span>
    </article>
    """
    got = parse(sample, mine_owners={"foo"})
    if len(got) != 1:
        print(f"self-test FAILED: 1 row parsed as {len(got)}")
        return 1
    r = got[0]
    for key, want in (("full_name", "foo/bar"), ("language", "Rust"),
                      ("stars", 1234), ("stars_today", 987), ("mine", True)):
        if r[key] != want:
            print(f"self-test FAILED: {key} is {r[key]!r}, wanted {want!r}")
            return 1
    if r["url"] != "https://github.com/foo/bar":
        print(f"self-test FAILED: url {r['url']!r}")
        return 1
    print("self-test OK: one row -> "
          f"{r['full_name']} {r['language']} +{r['stars_today']} today, mine={r['mine']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--since", default="daily",
                    choices=("daily", "weekly", "monthly"))
    ap.add_argument("--lang", help="GitHub's language filter, e.g. rust")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--community", action="store_true",
                    help="drop this account's own repositories")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    try:
        rows = parse(fetch(args.since, args.lang))
    except (urllib.error.URLError, OSError) as e:
        print(f"trending fetch failed: {e}", flush=True)
        return 1
    if args.community:
        rows = [r for r in rows if not r["mine"]]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("trending returned no rows — do NOT write copy from memory; "
              "skip today's promotion and report it", flush=True)
        return 1
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
