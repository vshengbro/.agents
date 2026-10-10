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
import fcntl
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

# The vocabulary that makes a post worth engaging with. Shared with
# like_posts.py on purpose: a like and a reply should agree about what this
# account cares about, or the feed learns two different things about it.
TOPICS = ("rust", "cargo", "wasm", "webassembly", "compile", "compiler",
          "macro", "agent", "llm", "model", "token", "context", "prompt",
          "mcp", "tool", "inference", "type system", "static typing",
          "refactor", "debugging", "code", "programming", "developer",
          "编程", "模型", "编译", "工具", "宏", "上下文", "智能体", "推理", "代码")

# A keyword match is never a reason by itself: adult and scam posts stuff the
# same vocabulary (模型, token, code) into their text, and a promotional reply
# under one of those does real damage to the account. Measured 2026-10-09:
# the very first dry-run target was an uncensored-image-model post caught by
# 模型. Skip the whole post on any of these, whatever else it says.
BLOCK = ("少儿不宜", "成人内容", "未成年", "nsfw", "18+", "uncensored",
         "约炮", "onlyfans", "porn", "adult content", "博彩", "彩票",
         "刷单", "裸聊",
         # crypto shill threads match "token" without ever being about token
         # cost — TOKEN2049 booth posts, airdrops, pump talk
         "token2049", "airdrop", "波场", "币圈", "土狗", "百倍",
         "合约", "炒币", "跟单", "带单")

sys.path.insert(0, str(HERE))
import cdp as C                                          # noqa: E402
import handle                                            # noqa: E402

# Status ids this account has already consumed a reply on, persisted across
# runs: the 30-minute job and the nightly job share this file, so a post that
# was answered at 14:00 is not answered again at 14:30 just because the feed
# still shows it. The same file rotates the reply text: a 30-minute cadence
# would otherwise send 01.txt to every post, and 48 copies of one text in a
# day is the exact pattern spam detection exists for. Sids sort
# chronologically as equal-length strings, so the cap keeps the recent ones.
STATE = Path(os.environ.get(
    "X_ENGAGE_STATE",
    os.path.expanduser(
        "~/.hermes/cron/output/x-engagement/answered_sids.json")))


def load_state() -> tuple:
    """(answered sids, next reply-text index); tolerates the legacy list form."""
    try:
        raw = json.loads(STATE.read_text())
    except Exception:
        return set(), 0
    if isinstance(raw, list):
        return set(raw), 0
    if isinstance(raw, dict):
        return set(raw.get("sids") or []), int(raw.get("next") or 0)
    return set(), 0


def save_state(done: set, next_idx: int) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(
            {"sids": sorted(done)[-5000:], "next": next_idx}))
    except OSError as exc:
        print("could not save the engagement state:", exc, flush=True)

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


def js(c, tpl):
    r = c.js(tpl, wait=25, retries=5)
    return json.loads(r) if isinstance(r, str) else r


def collect(c, me, done, want, rounds=10):
    """Up to `want` candidate posts from the live feed, same filters as the
    classic reply loop. Scrolling is how new posts are reached; a scroll is
    not a navigation, so the skill's rules still stand."""
    out = []
    seen = set(done)
    for _ in range(rounds):
        if len(out) >= want:
            break
        rows = js(c, READ)
        if not isinstance(rows, list):
            break
        for r in rows:
            if (r.get("who") != me and r.get("text")
                    and any(w in r["text"].lower() for w in TOPICS)
                    and not any(w in r["text"].lower() for w in BLOCK)
                    and r.get("sid") and r["sid"] not in seen):
                seen.add(r["sid"])
                out.append(r)
                if len(out) >= want:
                    break
        if len(out) < want:
            c.js("window.scrollBy(0, 2200); true", wait=20, retries=3)
            time.sleep(3.5)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("port", nargs="?", default="9240")
    ap.add_argument("--likes", type=int, default=12)
    ap.add_argument("--suggest", type=int, default=0, metavar="N",
                    help="print up to N candidate posts as JSON and exit — "
                         "the caller composes the reply live and sends it "
                         "with --reply-to; nothing is sent or marked here")
    ap.add_argument("--reply-to", metavar="SID",
                    help="reply to this status id with the text in --file")
    ap.add_argument("--file", metavar="PATH",
                    help="reply text file for --reply-to (composed by the "
                         "caller, never from a pre-written pool)")
    ap.add_argument("--allow-no-repo", action="store_true",
                    help="forwarded to post_reply.py for opinion replies "
                         "that carry no repository link")
    args = ap.parse_args()
    port = args.port

    C.set_port(int(port))

    # The 30-minute job and the long nightly job can be scheduled on top of
    # each other, and two runs driving one tab at once is how a reply lands
    # under the wrong post. A skipped run is a correct outcome — the next
    # tick is 30 minutes away — so the lock is non-blocking.
    STATE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(STATE.parent / "engage.lock", "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another engagement run holds the lock — skipping this run",
              flush=True)
        return 0

    # --reply-to: send one caller-composed reply and record it. Everything
    # mechanical — the owned-repository gate, the exact-text compare, the
    # landing verification — stays in post_reply.py; this mode only adds the
    # cross-run bookkeeping.
    #
    # Marking happens AFTER the send, and only when the send verified. It used
    # to happen before, on the theory that a failed send has still consumed the
    # post's one answer — which is true of the POST but not of the CANDIDATE.
    # Measured: a run with a stale owner allowlist refused every link-bearing
    # reply, and each refusal burned a sid, so 7 candidates were permanently
    # skipped and never answered even after the allowlist was fixed. A refusal
    # is a bug in this pipeline, not an editorial decision, so it must leave the
    # candidate retryable.
    if args.reply_to:
        sid = args.reply_to
        if not args.file or not os.path.exists(args.file):
            print("--reply-to needs --file pointing at the composed text",
                  flush=True)
            return 1
        done, _ = load_state()
        if sid in done:
            print(f"REFUSING - {sid} is already answered (state file)",
                  flush=True)
            return 1
        cmd = [sys.executable, str(REPLY), port, sid, args.file]
        if args.allow_no_repo:
            cmd.append("--allow-no-repo")
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        tail = (rc.stdout + rc.stderr).strip().splitlines()[-12:]
        for line in tail:
            print("  " + line, flush=True)
        ok = any("VERIFIED reply by" in ln for ln in tail)
        if ok:
            done.add(sid)
            save_state(done, 0)
        else:
            # Deliberately NOT marked: leave it for a later batch. Say so
            # loudly, because a silent retry loop on one post wastes the run.
            print(f"  NOT MARKED - {sid} stays available for a later batch",
                  flush=True)
        print(f"engage_once: {'VERIFIED' if ok else 'NOT VERIFIED'} {sid}",
              flush=True)
        return 0 if ok else 1

    tabs = [t for t in C.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first", flush=True)
        return 1
    c = C.Cdp(tabs[0]["webSocketDebuggerUrl"])
    me = handle.live(c)

    # 1. back to the feed, so likes and replies both read a live timeline
    print("home:", c.js(GO_HOME, wait=25, retries=4), flush=True)
    time.sleep(6)
    c.js("window.scrollTo(0, 0); true", wait=20, retries=3)
    time.sleep(2)

    # --suggest: hand the caller live candidates and stop. Nothing is marked
    # or sent — the mark lands only when a composed reply is actually sent
    # through --reply-to, so a post the caller declines is not burned.
    if args.suggest:
        done, _ = load_state()
        cands = collect(c, me, done, args.suggest)
        print("candidates:", json.dumps(cands, ensure_ascii=False), flush=True)
        c.close()
        return 0

    # 2. likes, through the script that records the button state after each
    if args.likes:
        rc = subprocess.run([sys.executable, str(LIKE), port, str(args.likes)],
                            capture_output=True, text=True, timeout=900)
        for line in (rc.stdout + rc.stderr).strip().splitlines()[-14:]:
            print("  " + line, flush=True)

    # No --suggest and no --reply-to: likes only. Replies are composed live
    # by the caller and sent through --reply-to; the pre-written pool loop
    # was removed the day canned content was forbidden, so a bare run cannot
    # accidentally ship a file someone wrote weeks ago.
    print("\nengagement: likes done; no reply requested (use --suggest to "
          "collect candidates, --reply-to to send a composed reply)",
          flush=True)
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
