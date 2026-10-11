#!/usr/bin/env python3
"""Publish a thread on X: post 0 through the main composer, post N as a reply to
post N-1, and verify every one of them off the timeline before the next starts.

A thread that stops halfway has ALREADY put posts on a real account, so this
script's first obligation is to tell the caller exactly which index failed and
how many landed. A half-posted thread that reads as a finished one is the one
outcome with no repair: the posts cannot be un-sent as a set, and the caller
cannot tell from the output that the tail is missing. So the run STOPS at the
first unverified post, prints `THREAD PARTIAL landed/total stopped at post N`,
and exits 1. `landed` counts everything on the account, including posts a
previous run left behind, because that is the number the caller has to reason
about — not the number this process typed.

The second obligation is the one the resume state exists for. X has no delete-
and-redo for a thread: re-running a finished script would double-post. Every
index is therefore recorded in a state file ONLY after that post has been read
back off the timeline, and a re-run skips every index already in it. A state
entry is a verified post, never a typed one.

Shape of the run, and why each part is where it is:

  * VALIDATE EVERYTHING FIRST. `publish.py` checks one post's copy and then
    types it, so a bad entry at index 3 of a thread would leave posts 0-2
    already shipped when the refusal came. Here the whole array is checked —
    shape, emptiness, per-entry type, linkifiable tokens, length ceiling —
    before a single browser call is made. The linkify refusal is the sharpest
    case: X turns any dotted token into a link span, the span reads back as a
    line break, and the post ships with the sentence cut in two (measured, a
    bare "crates.io" did exactly that, twice).

  * POST 0 GOES OUT ON ITS OWN; EVERY LATER POST IS A REPLY. A thread is the
    conversation X builds from the reply control on the previous post's
    OWNING article. It is NOT built by opening the composer five times.

  * THE MAIN COMPOSER IS NEVER USED AS A FALLBACK FOR A REPLY. Measured: 643
    characters of reply text went into the standalone post box and published as
    a new post — the text is on the account, the thread is not, and the caller's
    post 1 is now an orphan top-level post. So when a reply box is wanted and
    cannot be opened, this script stops. It does not type into the composer.
    (A step-5 reading that says the main composer also covers "any index
    reached without a reply box" is deliberately NOT implemented; it contradicts
    the measured failure above, and the measured failure is the tie-breaker.)

  * CHAINING VIA THE REPLY CONTROL IS UNVERIFIED. See the comment on
    REPLY_POINT below.

  * NOTHING IS EVER CLEARED. A box that already holds text is closed with the
    control the page shows and a fresh one is opened; the draft is never
    emptied, because clearing raises Chrome's unsaved-changes dialog, which
    then blocks every later CDP call until a human dismisses it.

  * THE COMPARE IS `publish.py`'s, EXPRESSED THROUGH `xkit.canon`, NOT
    IMPORTED. The semantics that decide a post — whitespace removed everywhere
    so the Draft editor's hidden text nodes cannot fail a correct body, every
    URL span collapsed to one marker so the t.co rewrite cannot fail it, and
    the surviving non-space characters required to match exactly — are
    xkit's, and this file calls them rather than restating them. What IS
    duplicated from `publish.py` is its canon/compare PAIR around them, and
    the duplication is deliberate: importing `publish.py` runs its module body,
    and it is being edited in parallel by another worker, so an import would
    couple this file's compare to edits in flight. Importing `post_reply.py`
    is avoided for the same reason plus size; the reply control's click
    sequence and the dialog gate are re-expressed below in ~20 lines.

  * `xkit.MINE` RETURNS A JSON ARRAY, SO IT IS READ WITH `js_raw`, NOT `js`.
    `js()` unwraps dicts and parses JSON strings, and a LIST is neither: it
    comes back as `{"_raw": "[...]"}` and every comparison against it reads as
    no match. That is not hypothetical — a wrapper shaped that way reports NOT
    VERIFIED on every post that in fact landed.

  python3 x_thread.py thread.json                 # publish the whole thread
  python3 x_thread.py thread.json --dry-run       # validate + print the plan
  python3 x_thread.py thread.json --start-from 3  # resume a half-posted thread
  python3 x_thread.py thread.json --state /tmp/x.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xconfig                                            # noqa: E402
import xkit                                               # noqa: E402

# The URL token, counted for the plan and nothing else. xkit.canon does the
# deciding; this is here so --dry-run can print how many links a post carries
# before anyone types it.
URL_RE = re.compile(r"https?://\S+")

# Verification budget: how many reads of the timeline, and how far apart. A
# post that has just been sent appears at the TOP, and the read that follows
# it is racing the feed's own re-render, not the network.
VERIFY_TRIES = 6
VERIFY_PAUSE = 5.0

# A clipped row is matched on this many characters. tweetText is a display
# layer: behind 显示更多 it stops mid-sentence and carries no "show more" of its
# own, so a long post legitimately reads back as a prefix. Sixty characters is
# long enough that a prefix match is not a coincidence, and the clipped case is
# reported as clipped rather than quietly counted as a pass.
CLIP_CHARS = 60

# How many times a box that holds text is closed and reopened before the run
# gives up on it.
BOX_ROUNDS = 3

STATE_NAME = "x_thread_state.json"


class Refusal(Exception):
    """A reason the run must not start, printed without a traceback."""


def echo(msg: str = "") -> None:
    print(msg, flush=True)


# --- the input file -----------------------------------------------------

def load_posts(path: str) -> list:
    """The thread's texts, or a Refusal naming what is wrong with the file.

    Two shapes are accepted: a JSON array of strings, and a JSON array of
    objects with a "text" key — the second is the shape `x_copy_example.json`
    is written in, so a copy file is a thread file without being converted.
    Anything else is rejected by name rather than coerced: a list of dicts
    without a usable text would otherwise publish "[object Object]" or, worse,
    an empty post that counts as landed.
    """
    p = Path(path).expanduser()
    if not p.exists():
        raise Refusal("no such file: %s" % p)
    if p.is_dir():
        raise Refusal("%s is a directory — the thread is a JSON file" % p)
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise Refusal("could not read %s: %s" % (p, exc))
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise Refusal("%s is not JSON: %s" % (p, exc))

    if not isinstance(data, list):
        raise Refusal("%s holds %s, not a JSON array. A thread is an array of "
                      "strings, or of objects with a \"text\" key."
                      % (p, type(data).__name__))
    if not data:
        raise Refusal("EMPTY THREAD: %s holds no posts. Nothing to publish."
                      % p)

    texts = []
    for i, item in enumerate(data):
        if isinstance(item, str):
            texts.append(item)
            continue
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            texts.append(item["text"])
            continue
        if isinstance(item, dict):
            raise Refusal('BAD ENTRY %d: {"text": ...} expected, got a dict '
                          'whose "text" is %r' % (i, item.get("text")))
        raise Refusal("BAD ENTRY %d: %r" % (i, item))
    return texts


def check_all(texts: list) -> list:
    """Every reason the WHOLE thread must not be started, in index order.

    Returns a list of refusal lines; empty means publishable. Nothing here
    touches a browser, which is what makes a bad entry at index 3 safe: the
    refusal arrives before post 0 exists.
    """
    problems = []
    for i, t in enumerate(texts):
        if not t.strip():
            problems.append("BAD ENTRY %d: %r is empty. An empty post cannot "
                            "be sent, and counting one as sent would leave the "
                            "caller believing it landed." % (i, t))
            continue
        if len(t) > xkit.POST_LIMIT:
            problems.append(
                "REFUSING: post %d is %d characters, over the %d ceiling. "
                "Split it into two posts — the tail becomes post %d."
                % (i, len(t), xkit.POST_LIMIT, i + 1))
        stray = xkit.stray_linkifiers(t)
        if stray:
            problems.append(
                "REFUSING: post %d carries %s, which X linkifies into a span "
                "that reads back as a line break — the sentence ships cut in "
                "two. Rewrite the copy without the dotted token."
                % (i, ", ".join(repr(s) for s in stray)))
    return problems


def print_plan(path: str, texts: list) -> None:
    echo("%s" % path)
    echo("%d post(s)" % len(texts))
    echo()
    for i, t in enumerate(texts):
        echo("  [%d] %5d chars, %d url(s)" % (i, len(t),
                                              len(URL_RE.findall(t))))
        echo("      %r" % (t[:60] + ("..." if len(t) > 60 else "")))
    echo()
    echo("dry run — validated, nothing typed, nothing published")


# --- opening a box -----------------------------------------------------

# The compose controls publish.py clicks, in its own order and by its own rule:
# one combined selector, first VISIBLE match. Re-expressed rather than imported
# — importing publish.py runs its module body, and it is being edited in
# parallel. Opening a composer by clicking what is already on screen is also
# the only way to open one at all: no navigation, no reload, no new tab.
COMPOSE_CONTROL = """(() => {
  const btn = [...document.querySelectorAll(
    '[data-testid="SideNav_NewTweetButton"], a[href*="/compose/post"], '
    + '[data-testid="appTabBarPostBtn"]')]
    .filter(e => e.offsetParent !== null)[0];
  if (!btn) return {clicked: null, why: 'no visible compose control'};
  btn.click();
  return {clicked: btn.dataset.testid
          || (btn.getAttribute('href') || 'compose control')};
})()"""

# Open the reply box on the OWNING article of a status id.
#
# UNVERIFIED FOR THREAD CHAINING. This control is verified only as a plain
# reply control: post_reply.py drives it against a post by somebody else and
# the reply lands under it. That is NOT the same measurement. On this build X
# may mount a DEDICATED control for "continue this thread" — a different
# testid on the same article, or the same control changing behaviour when the
# target is this account's own post — and nothing here has ever been run
# against that. So the click is synthesised (element.click() alone fires
# `click` and X's controls act on the mousedown/mouseup pair), the box it
# opens is required to be an EMPTY DIALOG editor, and the result is verified
# off the timeline before the next post starts. If a build offers a dedicated
# continue-thread control, this selector has to be re-measured first.
#
# The owner rule is xkit.ARTICLE's, not post_reply.py's looser one: an article
# whose OWN time link points at the id, with quote containers skipped. Matching
# any status link picks up a quoted post, the post a reply answers, or the
# inner post of a retweet — measured, and it is how a run once reported a
# stranger's links for a post of this account's own.
REPLY_POINT = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!own) continue;
    if (own.querySelector('[data-testid="quoteTweet"]')) return {
      opened: false, why: 'the article for this id is a quote container'};
    const btn = own.querySelector('[data-testid="reply"]');
    if (!btn) return {opened: false, why: 'no reply control on this article'};
    const box = btn.getBoundingClientRect();
    if (!box.width) return {opened: false, why: 'reply control has no size'};
    if (box.top < 0 || box.top > window.innerHeight) {
      return {opened: false, why: 'reply control is off screen',
              top: Math.round(box.top)};
    }
    const at = {bubbles: true, cancelable: true, view: window,
                clientX: box.left + box.width / 2,
                clientY: box.top + box.height / 2, button: 0};
    btn.dispatchEvent(new MouseEvent('mousedown', at));
    btn.dispatchEvent(new MouseEvent('mouseup', at));
    btn.dispatchEvent(new MouseEvent('click', at));
    return {opened: true, top: Math.round(box.top)};
  }
  return {opened: false,
          why: 'status ' + __SID__ + ' is not on this page — it was just '
               + 'verified, so it should be at the top of the timeline'};
})()"""


def empty_main_box(c, idx: int):
    """A visible, EMPTY Draft editor on the main composer, or None.

    An editor already on the page is used rather than a second composer
    opened on top of it. A box holding text is never emptied: it is closed
    through the control the page shows, and a fresh one is opened, which is
    the same recovery post_reply.py uses for a reply box.
    """
    ed = xkit.the_editor(c, tries=3)
    for _ in range(BOX_ROUNDS):
        if not ed:
            opened = xkit.js(c, COMPOSE_CONTROL)
            if not opened.get("clicked"):
                echo("  no compose control on this page (%s) — open the "
                     "composer yourself and re-run with --start-from %d"
                     % (opened.get("why") or "none visible", idx))
                return None
            echo("  opened the composer with %s" % opened.get("clicked"))
            ed = xkit.the_editor(c, tries=12)
        if not ed:
            echo("  the composer control was clicked but no editor appeared")
            return None
        if (ed.get("len") or 0) == 0:
            return ed
        echo("  the composer already holds %d characters — closing it, NOT "
             "clearing it, and opening a fresh one"
             % (ed.get("len") or 0))
        xkit.js(c, xkit.CLOSE_BOX)
        time.sleep(2.0)
        ed = None
    return None


def empty_reply_box(c, sid: str, idx: int):
    """An EMPTY Draft editor inside a dialog opened from `sid`, or None.

    `want_dialog` is the gate that stopped 643 characters of reply going into
    the standalone post box, so it is not optional and there is no fallback:
    a reply that cannot open a reply box is not sent from anywhere else.
    """
    ed = None
    for _ in range(BOX_ROUNDS):
        pt = xkit.js(c, REPLY_POINT, sid=sid)
        if not pt.get("opened"):
            echo("  reply control on %s did not open a box: %s"
                 % (sid, pt.get("why") or pt.get("_raw") or "unknown"))
            echo("  NOT SENDING post %d — the main composer is NOT used as a "
                 "fallback for a reply: measured, 643 characters of reply text "
                 "went into it and published as a standalone post." % idx)
            return None
        ed = xkit.the_editor(c, want_dialog=True, tries=12)
        if not ed:
            echo("  the reply control was clicked but no dialog editor "
                 "appeared")
            return None
        if (ed.get("len") or 0) == 0:
            return ed
        echo("  the reply box already holds %d characters — closing it, NOT "
             "clearing it, and opening a fresh one" % (ed.get("len") or 0))
        xkit.js(c, xkit.CLOSE_BOX)
        time.sleep(2.0)
        ed = None
    return None


# --- typing and the compare -------------------------------------------

def type_and_compare(c, text: str, idx: int) -> bool:
    """Type into the focused editor and require the read-back to match.

    The compare is xkit.canon on both sides, which is publish.py's compare with
    its real reason stated: whitespace goes everywhere (the Draft editor keeps
    hidden text nodes of its own, and X drops a space at a Latin/CJK boundary
    while typing) and every URL span becomes one marker (X rewrites the URL to
    t.co, so the source's host is never on the page). What is left, the
    non-space characters, must match exactly — a dropped character cannot hide
    behind a space.

    Every visible editor is read, not just the first: two nodes carry
    data-testid="tweetTextarea_0" and only one is the real editor, so a single
    read can come back from the empty decoy and report a mismatch on a body
    that is correct. Accepting the match from ANY visible editor still gates on
    the exact normalized compare.
    """
    xkit.js(c, xkit.FOCUS_EDITOR)
    xkit.type_body(c, text)
    xkit.remove_warmup(c, text.lstrip())
    c.close_composition("")       # never leave an open composition behind

    want = xkit.canon(text)
    best = ""
    seen = 0
    for _ in range(6):
        st = xkit.editors(c)
        items = st.get("items") or []
        seen = len(items)
        for it in items:
            got = it.get("text") or ""
            if xkit.canon(got) == want:
                return True
            if len(got) > len(best):
                best = got
        time.sleep(1.5)
    echo("  editors read: %s, longest %d chars, source %d chars"
         % (seen, len(best), len(text)))
    echo("  got : %r" % xkit.canon(best)[:120])
    echo("  want: %r" % want[:120])
    return False


# --- verification ------------------------------------------------------

def read_mine(c, me: str) -> list:
    """This account's visible posts, each with its own status id.

    `js_raw`, not `js`: MINE ends in JSON.stringify of an ARRAY, and xkit.js
    unwraps dicts only — a list comes back as {"_raw": "[...]"} and every
    match against it fails. The substitute is done here rather than through
    js()'s keyword machinery for the same reason: the array is parsed on this
    side of the call, once.
    """
    raw = xkit.js_raw(c, xkit.MINE.replace("__WHO__", json.dumps(me or "")),
                      wait=25, retries=4)
    if isinstance(raw, str):
        try:
            rows = json.loads(raw)
        except ValueError:
            return []
    elif isinstance(raw, list):
        rows = raw
    else:
        return []
    return [r for r in rows if isinstance(r, dict)]


def verify_post(c, me: str, text: str):
    """(sid, clipped) for the post carrying this text, or (None, False).

    Read off the TIMELINE, not off the box that sent it. A box that closed is
    not evidence, and the timeline is the only surface where a post is this
    account's own post. Scrolling to the top first is part of the read: a post
    that has just been sent appears at the TOP, and a flow that scrolled down
    to reach a target leaves the feed past the very post it is verifying —
    measured, a run sent a reply, scrolled up, found it, and reported NOT
    VERIFIED because the read happened first.
    """
    want = xkit.canon(text)
    head = want[:CLIP_CHARS]
    xkit.scroll_to_top(c)
    for attempt in range(VERIFY_TRIES):
        for row in read_mine(c, me):
            got = xkit.canon(row.get("text") or "")
            if not got:
                continue
            if got == want:
                return row.get("sid") or "", False
            if head and got.startswith(head):
                return row.get("sid") or "", True
        if attempt + 1 < VERIFY_TRIES:
            time.sleep(VERIFY_PAUSE)
    return None, False


# --- the run -----------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(
        description="Publish a thread: post 0 on its own, the rest as replies.")
    ap.add_argument("path", help="JSON array of strings, or of {\"text\": ...}")
    ap.add_argument("--start-from", type=int, default=0, metavar="N",
                    help="begin at index N (default 0) — resume a "
                         "half-posted thread")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate the file and print the plan; publish "
                         "nothing")
    ap.add_argument("--state", default=None, metavar="PATH",
                    help="resume state file (default %s)" % STATE_NAME)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # --- everything above the browser ---------------------------------
    try:
        texts = load_posts(args.path)
    except Refusal as exc:
        echo(str(exc))
        return 1
    problems = check_all(texts)
    if problems:
        for p in problems:
            echo(p)
        echo("THREAD REFUSED: %d post(s) would mispublish. Nothing was typed "
             "and nothing was published." % len(problems))
        return 1
    total = len(texts)
    if args.start_from < 0 or args.start_from >= total:
        echo("--start-from %d is outside this thread (0..%d). Nothing to do."
             % (args.start_from, total - 1))
        return 1
    if args.dry_run:
        print_plan(args.path, texts)
        return 0

    state_path = Path(args.state).expanduser() if args.state \
        else xkit.state_file(STATE_NAME)
    raw_state = xkit.load_json(state_path, {})
    if not isinstance(raw_state, dict):
        raw_state = {}
    published = {}
    for k, v in raw_state.items():
        try:
            published[int(k)] = v
        except (TypeError, ValueError):
            continue

    echo("THREAD %d post(s) from %s" % (total, args.path))
    echo("  state file %s" % state_path)
    if published:
        echo("  already published, never re-posted: %s"
             % ", ".join("post %d = %s" % (i, published[i])
                         for i in sorted(published)))

    # --- browser ------------------------------------------------------
    # connect() reports a browser it can reach but that has no site tab, and
    # it raises outright when nothing is listening on the port at all —
    # urllib's URLError escapes from the tab listing. Both are the same fact
    # to this script (there is nothing to drive), and both must print the
    # message rather than a traceback: a run that did nothing must exit 1
    # with a line a caller can read, not a stack.
    try:
        c, _tab, me = xkit.connect()
    except Exception as exc:
        echo(xkit.no_browser("could not reach the browser on port %s (%s)."
                             % (xconfig.port(), str(exc)[:90])))
        echo("THREAD PARTIAL %d/%d stopped at post %d"
             % (len(published), total, args.start_from))
        return 1
    if c is None:
        echo("THREAD PARTIAL %d/%d stopped at post %d"
             % (len(published), total, args.start_from))
        return 1
    if not me:
        echo("this account's handle could not be read off the open %s tab, and "
             "a post cannot be verified without it. Nothing was typed."
             % xconfig.site())
        c.close()
        echo("THREAD PARTIAL %d/%d stopped at post %d"
             % (len(published), total, args.start_from))
        return 1

    echo("  posting as @%s" % me)
    idx = args.start_from
    while idx < total:
        if idx in published:
            echo("  post %d already published as %s — skipping" %
                 (idx, published[idx]))
            idx += 1
            continue
        text = texts[idx]
        echo("post %d: %d chars, %d url(s)"
             % (idx, len(text), len(URL_RE.findall(text))))

        if idx == 0:
            # Stale dialogs that hold nothing editable put the first dialog on
            # the page in the wrong place. This never touches a dialog that
            # has an editor in it.
            xkit.js(c, xkit.CLEAR_STALE_DIALOGS)
            ed = empty_main_box(c, idx)
            what = "the main composer"
        else:
            prev = published.get(idx - 1)
            if not prev:
                echo("cannot chain post %d: no status id for post %d, so there "
                     "is no post to reply to. Re-run with --start-from 0 and "
                     "the state file, which carries the ids this run verified."
                     % (idx, idx - 1))
                echo("THREAD PARTIAL %d/%d stopped at post %d"
                     % (len(published), total, idx))
                c.close()
                return 1
            ed = empty_reply_box(c, prev, idx)
            what = "the reply box on post %d (%s)" % (idx - 1, prev)

        if not ed:
            echo("NOT SENDING post %d: no empty box could be opened" % idx)
            echo("THREAD PARTIAL %d/%d stopped at post %d"
                 % (len(published), total, idx))
            c.close()
            return 1
        echo("  box: %s, empty, in_dialog=%s" % (what, ed.get("in_dialog")))

        if not type_and_compare(c, text, idx):
            echo("NOT SENDING post %d: text mismatch" % idx)
            echo("THREAD PARTIAL %d/%d stopped at post %d"
                 % (len(published), total, idx))
            c.close()
            return 1

        res = xkit.js(c, xkit.SEND_IN_BOX)
        for _ in range(8):
            if res.get("sent"):
                break
            time.sleep(3)
            res = xkit.js(c, xkit.SEND_IN_BOX)
        c.close_composition("")       # the send button may have opened one
        if not res.get("sent"):
            echo("  the send control did not fire: %s"
                 % (res.get("why") or res.get("_raw") or "unknown"))
            echo("THREAD PARTIAL %d/%d stopped at post %d"
                 % (len(published), total, idx))
            c.close()
            return 1
        echo("  SENT via %s" % res.get("which"))

        time.sleep(5)
        sid, clipped = verify_post(c, me, text)
        if not sid:
            echo("NOT VERIFIED post %d" % idx)
            echo("THREAD PARTIAL %d/%d stopped at post %d"
                 % (len(published), total, idx))
            c.close()
            return 1
        if clipped:
            echo("VERIFIED post %d %s (clipped — the timeline shows only a "
                 "prefix of this body, so the match is on the first %d "
                 "characters)" % (idx, sid, CLIP_CHARS))
        else:
            echo("VERIFIED post %d %s" % (idx, sid))
        # Recorded only now: a state entry is a VERIFIED post, so a re-run
        # never repeats one and never skips one that might have landed.
        published[idx] = sid
        xkit.save_json(state_path, {str(k): v for k, v in published.items()})
        idx += 1

    c.close()
    echo("THREAD COMPLETE %d/%d" % (len(published), total))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        echo("THREAD PARTIAL — interrupted by the operator")
        sys.exit(1)