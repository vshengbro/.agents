#!/usr/bin/env python3
"""Collect candidate posts from the home feed into a candidates file.

THE CANDIDATES FILE IS THE INTERFACE, NOT STDOUT

A status id is a bare 19-digit number, and a bare 19-digit number in a
terminal transcript is indistinguishable from a payment card number: the
display layer replaces it with a redaction token, and a token that reaches a
script is not an id. A redaction of ONE id in a list of seven was measured,
so this is not a rule about ids that "look like" cards -- it is a rule about
the display, and the only safe answer is to keep ids OUT of transcripts.

So this script writes the ids to a file and prints everything else. The
later scripts take the candidate's INDEX and read the id out of the file
themselves. No id is ever printed, and no id is ever typed.

WHAT IT RETURNS

One record per mounted article: who posted it, its status id, and its text.
The text is CLIPPED -- the feed collapses long posts behind a "show more"
control -- so a candidate's full text has to be read from its permalink
before it is answered (xread.py).

Usage:
    xfeed.py --out candidates.json --count 10
    xfeed.py --out candidates.json --count 10 --raw   # keep answered ones
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402
import xstate                                             # noqa: E402
from xcdp import Browser                                  # noqa: E402

# The article list on the feed.
COLLECT = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const rows = [];
  for (const a of arts) {
    const st = a.querySelector("a[href*='/status/']");
    if (!st) continue;
    const href = st.getAttribute('href') || '';
    const m = href.match(/\\/([A-Za-z0-9_]+)\\/status\\/(\\d{19})/);
    if (!m) continue;
    const who = m[1], sid = m[2];
    const t = (a.innerText || '').replace(/\\s+/g, ' ').trim();
    rows.push({who: who, sid: sid, len: t.length, text: t.slice(0, 900)});
  }
  return JSON.stringify({nArts: arts.length, rows: rows, href: location.href,
    scrollY: window.scrollY, bodyLen: (document.body.innerText||'').length});
})()"""

# The own-account link in the sidebar, which names this account.
HANDLE = """(() => {
  const a = document.querySelector("[data-testid='AppTabBar_Profile_Link']");
  if (a) {
    const m = (a.getAttribute('href') || '').match(/^\\/([A-Za-z0-9_]+)/);
    if (m) return m[1];
  }
  return '';
})()"""

# X serves an error state instead of the timeline when it is unhappy. The
# page is up and signed in, but no article ever mounts, and that reads as an
# empty feed unless the error is recognised.
ERROR_STATE = """(() => {
  const t = document.body.innerText || '';
  const err = t.indexOf('出错了') >= 0 || t.indexOf('Something went wrong') >= 0;
  return JSON.stringify({err: err, nArts: document.querySelectorAll('article').length});
})()"""


async def collect(count: int, filter_answered: bool = True, retries: int = 3):
    """Walk the feed and return the candidates it held.

    The timeline is retried on X's error state: one sample of the error is
    not proof the feed is empty, and reporting "no candidates" on it is how a
    run ends having done nothing.
    """
    answered = set(xstate.answered_sids()) if filter_answered else set()
    async with Browser() as b:
        for attempt in range(1, retries + 1):
            seen: dict[str, dict] = {}
            order: list[str] = []
            tid, sess = await b.new_tab("https://%s/home" % xconfig.site())
            try:
                await b.wait_for(
                    sess,
                    "document.querySelectorAll('article').length > 0",
                    timeout=40)
                handle = await b.ev(sess, HANDLE)
                if isinstance(handle, str) and handle:
                    xconfig.cache_handle(handle)
                    print("ACCOUNT:", handle)
                for step in range(12):
                    await asyncio.sleep(3.0)
                    raw = await b.ev(sess, COLLECT)
                    if not isinstance(raw, str):
                        print("  walk%d: expression failed: %s"
                              % (step, str(raw)[:200]))
                        break
                    data = json.loads(raw)
                    print("  walk%d nArts=%s scrollY=%s bodyLen=%s" % (
                        step, data.get("nArts"), data.get("scrollY"),
                        data.get("bodyLen")))
                    for row in data.get("rows", []):
                        if row["sid"] not in seen:
                            seen[row["sid"]] = row
                            order.append(row["sid"])
                    if len(order) >= count:
                        break
                    await b.ev(sess, "(window.scrollBy(0, 2200), 1)")
                rows = [seen[s] for s in order]
                if rows:
                    if filter_answered:
                        rows = [r for r in rows if r["sid"] not in answered]
                    return rows
                state = await b.ev(sess, ERROR_STATE)
                print("  attempt %d: no candidates; page state: %s"
                      % (attempt, str(state)[:200]))
            finally:
                await b.close_tab(tid)
            if attempt < retries:
                print("  retrying the timeline (attempt %d of %d)"
                      % (attempt + 1, retries))
                await asyncio.sleep(6.0)
        return []


def main(argv) -> int:
    count = 10
    out = None
    filter_answered = True
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--count":
            count = int(args[i + 1]); i += 2
        elif args[i] == "--out":
            out = args[i + 1]; i += 2
        elif args[i] == "--raw":
            filter_answered = False; i += 1
        else:
            print("unknown argument: %s" % args[i])
            return 2
    if not out:
        print("--out is required: the candidates file is the interface")
        return 2
    rows = asyncio.run(collect(count, filter_answered))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    print("WROTE %s (%d candidates)" % (out, len(rows)))
    for index, row in enumerate(rows):
        print("-" * 70)
        print("[%d] @%s  len=%s" % (index, row["who"], row["len"]))
        print(row["text"][:700])
    if not rows:
        print("NO CANDIDATES: the timeline held nothing this run")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
