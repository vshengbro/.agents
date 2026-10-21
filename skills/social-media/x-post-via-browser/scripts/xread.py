#!/usr/bin/env python3
"""Read a candidate's FULL post text from its permalink.

THE FEED CLIPS THE POST, AND THE CLIPPED HALF IS USUALLY THE POINT

The feed collapses a long post behind a "show more" control. What survives
can be the numbers while the argument, the admission or the conclusion sits
in the hidden half, and a reply written from the clipped half is a
restatement of the post -- which the task forbids.

So the full text is read here, from the permalink, where nothing is clipped.
The text is printed; the status id is not.

Usage:
    xread.py --candidates cand.json --index 3
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402
import xcandidates                                        # noqa: E402
from xcdp import Browser                                  # noqa: E402

READ = """(() => {
  const arts = [...document.querySelectorAll('article')];
  if (!arts.length) return JSON.stringify({err: 'no-article'});
  const art = arts[0];
  const links = [...art.querySelectorAll("a[href*='/status/']")].map(a => a.getAttribute('href'));
  const text = art.innerText || '';
  return JSON.stringify({len: text.length, text: text, links: links.slice(0, 6)});
})()"""


async def read(who: str, sid: str) -> dict:
    """The full text of one post."""
    url = "https://%s/%s/status/%s" % (xconfig.site(), who, sid)
    async with Browser() as b:
        tid, sess = await b.new_tab(url)
        try:
            for _ in range(12):
                await asyncio.sleep(2.5)
                raw = await b.ev(sess, READ)
                if not isinstance(raw, str):
                    continue
                try:
                    data = json.loads(raw)
                except ValueError:
                    continue
                if data.get("text"):
                    return data
            return {"err": "the post never mounted"}
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
    data = asyncio.run(read(row["who"], row["sid"]))
    if data.get("err"):
        print("FAILED: %s" % data["err"])
        return 1
    print("POST @%s (%d chars)" % (row["who"], data.get("len", 0)))
    print("-" * 70)
    print(data.get("text", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
