#!/usr/bin/env python3
"""Work the home feed: like what is worth liking, reply to what is worth answering.

A cron job runs this after the posts go out. It reads the feed LIVE — the
timeline replaces posts continuously, so a target id saved by an earlier scroll
names something that is no longer on screen, and this script never uses one.

Three jobs, in this order, because they share the page:

  1. return to the home feed (click the tab already on screen)
  2. like posts about the same work: Rust, agents, context cost, compilers
  3. reply, up to --replies times, each one bound to the post it answers

Scrolling is how new posts are reached. A scroll is not a navigation, so the
skill's rules still stand: no page load, no clearing, no mouse, no clipboard.

Every reply must carry a repository this account owns, or it is refused
before anything is typed — a reply that names someone else's project is not
promotion of this account's work. So the reply body must come from a directory
of replies that were written for this purpose; a reply is generated here, not
composed live, because the file is what the promotion rule is checked against.

  python3 engage_feed.py 9240 [--likes 12] [--replies 36] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIKE = HERE / "like_posts.py"
REPLY = HERE / "post_reply.py"
WHOSE = HERE / "whose_posts.py"
REPLY_DIR = Path(os.environ.get(
    "X_REPLY_DIR", str(HERE.parent / "replies")))

# The vocabulary that makes a post worth engaging with. Shared with
# like_posts.py on purpose: a like and a reply should agree about what this
# account cares about, or the feed learns two different things about it.
TOPICS = ("rust", "cargo", "wasm", "webassembly", "compile", "compiler",
          "macro", "agent", "llm", "model", "token", "context", "prompt",
          "mcp", "tool", "inference", "type system", "static typing",
          "refactor", "debugging", "code", "programming", "developer",
          "编程", "模型", "编译", "工具", "宏", "上下文", "智能体", "推理", "代码")

sys.path.insert(0, str(HERE))
import cdp as C                                          # noqa: E402

READ = """(() => {
  const out = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => x.getAttribute('href').split('/').pop()
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (!own) continue;
    const sid = own.getAttribute('href').split('/').pop();
    if (seen.has(sid)) continue;
    seen.add(sid);
    const who = a.querySelector("a[href^='/']");
    const box = a.querySelector('[data-testid="tweetText"]');
    out.push({sid: sid,
              who: who ? who.getAttribute('href').split('/').pop() : '?',
              text: box ? box.innerText.replace(/\\s+/g, ' ').trim() : ''});
  }
  return JSON.stringify(out);
})()"""

# The home tab is a link that is already on screen. Clicking it is what a person
# does to go back to the feed; location.assign would be a navigation, which the
# skill forbids and which makes the user confirm it in their UI.
GO_HOME = """(() => {
  const tab = document.querySelector('[data-testid="AppTabBar_Home_Link"]');
  if (!tab) return 'NO_HOME_TAB';
  tab.click();
  return 'CLICKED_HOME';
})()"""

AT_TOP = "(window.scrollY < 40 ? 'TOP' : 'SCROLLED ' + window.scrollY)"
COUNT = """(() => {
  const seen = new Set();
  for (const a of document.querySelectorAll('article')) {
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => x.getAttribute('href').split('/').pop()
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (st) seen.add(st.getAttribute('href').split('/').pop());
  }
  return JSON.stringify({n: seen.size, y: Math.round(window.scrollY)});
})()"""


def js(c, tpl):
    r = c.js(tpl, wait=25, retries=5)
    return json.loads(r) if isinstance(r, str) else r


def replies_available() -> list[Path]:
    return sorted(REPLY_DIR.glob("*.txt")) if REPLY_DIR.exists() else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("port", nargs="?", default="9240")
    ap.add_argument("--likes", type=int, default=12)
    ap.add_argument("--replies", type=int, default=36)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    port = args.port

    files = replies_available()
    if len(files) < args.replies and not args.dry_run:
        print(f"only {len(files)} replies written, asked for {args.replies} — "
              f"the queue is shorter than the target. Writing a reply per post "
              f"that arrives on its own is the only honest way to fill it.")
    if not files and not args.dry_run:
        print("no reply directory — nothing to say. See the skill for what a "
              "reply must carry before one may be written.")
        return 1

    C.set_port(int(port))
    tabs = [t for t in C.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first", flush=True)
        return 1
    c = C.Cdp(tabs[0]["webSocketDebuggerUrl"])

    # 1. back to the feed, so likes and replies both read a live timeline
    print("home:", c.js(GO_HOME, wait=25, retries=4), flush=True)
    time.sleep(6)
    c.js("window.scrollTo(0, 0); true", wait=20, retries=3)
    time.sleep(2)

    # 2. likes, through the script that records the button state after each
    if args.likes:
        rc = subprocess.run([sys.executable, str(LIKE), port, str(args.likes)],
                            capture_output=True, text=True, timeout=900)
        for line in (rc.stdout + rc.stderr).strip().splitlines()[-14:]:
            print("  " + line, flush=True)

    # 3. replies, one per post, each read live and bound to its target
    #
    # `done` is what makes this one reply per post rather than three replies to
    # the same one. The feed is virtualised: a post stays in the DOM at the
    # same offset long after the loop has scrolled past it, so the same first
    # matching article comes back into view on every pass and three of four
    # replies went to the same target. Remember the status ids this run has
    # already answered and skip them.
    liked, replied, said = 0, 0, 0
    done: set[str] = set()
    stalls = 0
    while replied < args.replies and said < len(files) and stalls < 4:
        rows = js(c, READ)
        if not isinstance(rows, list):
            print("could not read the feed:", str(rows)[:120], flush=True)
            break
        target = next((r for r in rows
                       if r.get("who") != "eastspire_sheng" and r.get("text")
                       and any(w in r["text"].lower() for w in TOPICS)
                       and r.get("sid") and r["sid"] not in done), None)
        if not target:
            # Nothing new worth answering in view: scroll for more, and give up
            # rather than loop — the feed may simply have run out for now.
            before = js(c, COUNT)
            c.js("window.scrollBy(0, 2200); true", wait=20, retries=3)
            time.sleep(3.5)
            after = js(c, COUNT)
            grew = False
            if isinstance(before, dict) and isinstance(after, dict):
                # n is a count, never a string; a string here means the read
                # failed and comparing it to an int would raise instead of
                # counting as "no growth".
                n0, n1 = before.get("n"), after.get("n")
                grew = (isinstance(n0, int) and isinstance(n1, int)
                        and n1 > n0)
            if not grew:
                stalls += 1
            continue

        body_file = files[said]
        said += 1
        # Mark the target before typing, not after: a reply that fails to
        # verify has still consumed the post's one answer, and re-picking it
        # would spend the next reply text on the same target.
        done.add(target["sid"])
        print(f"\nreply {replied + 1}/{args.replies} -> "
              f"@{target['who']} {target['sid']} "
              f"[{body_file.name}]", flush=True)
        print(f"  {target['text'][:100]}", flush=True)
        if args.dry_run:
            replied += 1
            continue

        # post_reply.py refuses a reply that names a repository this account
        # does not own, and refuses to send unless the text in the reply box
        # matches the file. Its own words are the result; do not work around
        # a refusal.
        rc = subprocess.run(
            [sys.executable, str(REPLY), port, target["sid"], str(body_file)],
            capture_output=True, text=True, timeout=900)
        tail = (rc.stdout + rc.stderr).strip().splitlines()[-12:]
        for line in tail:
            print("  " + line, flush=True)
        if any("VERIFIED reply by" in ln for ln in tail):
            replied += 1
            stalls = 0
            c.js("window.scrollTo(0, 0); true", wait=20, retries=3)
            time.sleep(2)
        else:
            print("  not verified — not counted", flush=True)
            stalls += 1

    print(f"\nengagement: {replied}/{args.replies} replies, "
          f"{said} reply texts considered", flush=True)
    c.close()
    return 0 if replied >= args.replies else 1


if __name__ == "__main__":
    sys.exit(main())
