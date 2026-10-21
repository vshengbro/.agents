#!/usr/bin/env python3
"""Like exactly one post, by status id, and prove it.

THE PROOF IS THE BUTTON STATE, NOT THE CLICK

A click returns whether the click was dispatched, and the like count moves
for other reasons too -- it went 40, 41, 43 during a single run. What proves
a like landed is the button swapping: `like` gone, `unlike` present. So the
read BEFORE the click decides whether a click is needed at all, and the read
AFTER it is what counts.

That makes the operation idempotent: a post that is already liked reports
ALREADY_LIKED and is not clicked again, so a retry after an interrupted run
cannot toggle a like off.

Usage:
    xlike.py --candidates cand.json --index 3
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402
import xcandidates                                        # noqa: E402
from xcdp import Browser, sub                             # noqa: E402

# The article carrying this status id, with its like button state.
PROBE = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return JSON.stringify({err: 'no-article', nArts: arts.length});
  const like = art.querySelector("[data-testid='like']");
  const unlike = art.querySelector("[data-testid='unlike']");
  return JSON.stringify({
    found: true, nArts: arts.length,
    like: !!like, unlike: !!unlike,
    likeAria: like ? like.getAttribute('aria-label') : null,
    unlikeAria: unlike ? like ? null : (unlike.getAttribute('aria-label') || null) : null
  });
})()"""

CLICK = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return 'NO_ARTICLE';
  const b = art.querySelector("[data-testid='like']");
  if (!b) return 'NO_LIKE_BUTTON';
  if (art.querySelector("[data-testid='unlike']")) return 'ALREADY_LIKED';
  b.click();
  return 'CLICKED';
})()"""


async def like(sid: str, url: str | None = None) -> str:
    """Like one post. Returns the verdict, without the id.

    The verdict names the post by nothing at all: an id is a bare 19-digit
    number and the display layer replaces such numbers with a redaction
    token, so a verdict that carried one would read as a token to whoever
    reads it back.
    """
    target = url or ("https://%s/i/status/%s" % (xconfig.site(), sid))
    async with Browser() as b:
        tid, sess = await b.new_tab(target)
        try:
            await b.wait_for(sess, "document.querySelectorAll('article').length > 0",
                             timeout=40)
            pre = await b.ev(sess, sub(PROBE, SID=sid))
            if not isinstance(pre, str):
                return "NOT_CONFIRMED (probe failed: %s)" % str(pre)[:200]
            pd = json.loads(pre)
            if pd.get("err"):
                return "TARGET_NOT_ON_PAGE (%s)" % pd.get("err")
            if pd.get("unlike"):
                return "ALREADY_LIKED"
            if not pd.get("like"):
                return "NO_LIKE_BUTTON"
            clicked = await b.ev(sess, sub(CLICK, SID=sid))
            if clicked == "ALREADY_LIKED":
                return "ALREADY_LIKED"
            if clicked != "CLICKED":
                return "NOT_CONFIRMED (%s)" % clicked
            await asyncio.sleep(3.0)
            post = await b.ev(sess, sub(PROBE, SID=sid))
            if not isinstance(post, str):
                return "NOT_CONFIRMED (probe failed after the click)"
            pd = json.loads(post)
            if pd.get("unlike"):
                return "LIKED"
            return "NOT_CONFIRMED (state=%s)" % (
                "unlike" if pd.get("unlike") else "like")
        finally:
            await b.close_tab(tid)


def main(argv) -> int:
    path = None
    index = None
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--candidates":
            path = args[i + 1]; i += 2
        elif args[i] == "--index":
            index = int(args[i + 1]); i += 2
        else:
            print("unknown argument: %s" % args[i])
            return 2
    if not path or index is None:
        print(__doc__)
        return 2
    row = xcandidates.resolve(path, index)
    verdict = asyncio.run(like(row["sid"]))
    # The verdict names the candidate by INDEX, not by id: an id in a
    # transcript is redacted by the display layer.
    print("[%d] %s" % (index, verdict))
    return 0 if verdict.split()[0] in ("LIKED", "ALREADY_LIKED") else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
