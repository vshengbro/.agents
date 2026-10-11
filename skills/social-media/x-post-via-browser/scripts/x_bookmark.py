#!/usr/bin/env python3
"""Bookmark a post, take the bookmark back, or read what this account saved.

The toggle itself is xkit's. This file is the twenty lines around it — which
article, which word, what the last line of the output is — and none of that is
a second copy of a read-decide-click-reread loop, because that loop is exactly
the kind of thing that gets written backwards. A bookmark that does not happen
is nearly invisible: the post is still there, the timeline shows no error, and
a run that clicked and never confirmed is indistinguishable from a run that
never clicked. So the click is not the event here either. The button state is
read before anything is pressed, pressed only when that state disagrees with
the goal, and read again afterwards.

What was measured on the way here, and what each thing costs:

  * Idempotence is the point, not a nicety. A toggle has no third state, so a
    re-run over a post that is already in the desired state must NOT click —
    that is how the previous run gets undone — and it must still exit 0,
    because ALREADY BOOKMARKED is the goal holding, not nothing happening. A
    second run and a first run leave the page in the same place, which is the
    only property that makes this safe to put in a queue that re-runs.

  * The two testids are UNVERIFIED on this build and are the reason this file
    can fail honestly instead of silently. `bookmark` (off) and
    `removeBookmark` (on) come from xkit.TOGGLE_KINDS and from the
    browser-automation reference notes; nothing in this skill has ever driven
    a bookmark control, so the first live run is the measurement. Like every
    other script here it is written so that being wrong is legible: the
    failure branch prints the article's REAL testids and aria-labels, and
    xkit.is_on falls back to the label (移除书签 / Remove bookmark /
    已添加书签) on a build where the "on" control carries a different testid.

  * A status id is not a post. xkit.read_article takes the article whose own
    time link carries the id and refuses a quote container, because a quoted
    post, the post a reply answers and the inner post of a retweet all carry
    the target's link — matching "any status link" is how a run once acted on
    a stranger's post. The id is checked against digits here before a browser
    is even asked for, so a typo never reaches the page and never reads as a
    stale feed.

  * --list does NOT open the saved view, and that is deliberate rather than
    incomplete. Reaching it means a navigation, a page load, and every page
    load makes the user confirm it in their own UI — the one rule this whole
    skill is gated on. So the caller opens Saved items by hand and this script
    reads whatever is on screen. When the surface is not a bookmarks view the
    run says so and exits 1 rather than reading the feed and calling it the
    saved list. That failure is worth keeping: a list of the wrong surface is
    worse than no list, because the caller cannot tell.

  * How the surface is recognised is half-measured. The route test is
    independent of any testid; the nav-link test is UNVERIFIED, because
    `AppTabBar_Bookmarks_Link` comes from the reference notes and no script
    here has read it. Two independent signals are accepted for that reason,
    and a second opinion that never mentions the unverified testid at all is
    included so that one renamed testid cannot turn this into a script that
    only works on the day it was written.

  * The read scrolls, it never navigates. window.scrollBy down a screen at a
    time, deduping on the status id because the virtual list re-renders and
    hands back the same articles after every step. The count it prints is the
    number of rows it ACTUALLY read, and zero is a real answer: an account
    with nothing saved is told so, and told it separately from a page that
    could not be read at all, because those two are indistinguishable from a
    single exit code and must never be indistinguishable in the output.

  * One scroll attempt on the toggle path, then stop — the same arrangement
    as x_repost.py, and for its reason: a target the virtual list has dropped
    is not in the document at all, so a second attempt returns the same
    answer while looking like patience.

A --dry-run prints the state it read and the state it would leave, and never
prints a BOOKMARKED or UNBOOKMARKED line — a caller that greps for those
words must not be able to find one in a run that changed nothing.

The lines a caller greps, each followed by the status id:

    BOOKMARKED  UNBOOKMARKED  ALREADY BOOKMARKED  ALREADY UNBOOKMARKED
    NOT BOOKMARKED  NOT UNBOOKMARKED  NOT ON PAGE
    BOOKMARKS <n>

  python3 x_bookmark.py <status-id> [--remove] [--dry-run]
  python3 x_bookmark.py --list 5
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit as X                                          # noqa: E402

# A status id is a snowflake: digits and nothing else. Checked before a browser
# is asked for, so a mistyped argument never reaches the page.
SID_RX = re.compile(r"\d{5,25}\Z")

# How far a --list read will scroll, and how long it lets each step settle.
# window.scrollBy moves the document and is NOT a navigation.
SCROLL_STEP = 0.9            # viewports per round
SCROLL_ROUNDS = 40           # ~36 viewports, then it gives up and says so
SETTLE = 1.6                 # seconds between rounds

# Whether this tab is the saved/bookmarks view at all, and on what evidence.
#
# UNVERIFIED, and it is the only unverified thing this file reaches for on its
# own: `AppTabBar_Bookmarks_Link` is the nav link's data-testid in the
# browser-automation reference notes, and nothing in this skill has read it.
# The ROUTE half of the test does not depend on that name and carries the
# decision on its own whenever the route matches; the nav-link half is a
# second opinion for a build that serves saved items from a route this regex
# does not know about. The third signal never mentions the unverified testid
# at all, so a rename there costs one opinion rather than the whole check.
SURFACE = """(() => {
  const path = location.pathname || '';
  // Path segments, not a hostname: X serves the saved list at /i/bookmarks.
  const route_hit = /\\/bookmarks|\\/saved/i.test(path);
  const found = [...document.querySelectorAll(
    '[data-testid="AppTabBar_Bookmarks_Link"]')];
  let link = null;
  for (const a of found) {
    const here = a.getAttribute('aria-current');
    const wrapped = !!a.closest('[aria-current="page"]');
    if (!link)
      link = {href: a.getAttribute('href') || '', aria_current: here || '',
              current: false};
    if (here === 'page' || wrapped) {
      link = {href: a.getAttribute('href') || '', aria_current: here || '',
              current: true};
      break;
    }
  }
  const current_links = [...document.querySelectorAll(
      'a[aria-current="page"][href*="/bookmarks"]')]
    .map(a => a.getAttribute('href') || '');
  return JSON.stringify({route: path, route_hit: route_hit, link: link,
                         nav_found: found.length,
                         current_links: current_links});
})()"""

# Every saved post rendered on screen, deduped by status id. The id comes from
# the post's OWN time link, so a saved quote reports the quoting post and a
# saved reply reports the reply — which is the same rule xkit.read_article
# applies on the toggle path, kept here because xkit's own template refuses a
# quote container outright and a list that drops every saved quote is a list
# with a hole in it that nobody can see.
READ_ROWS = """(() => {
  const out = [];
  const seen = new Set();
  for (const a of document.querySelectorAll('article')) {
    let href = '';
    const t = a.querySelector('time');
    if (t) {
      const own = t.closest("a[href*='/status/']");
      if (own) href = own.getAttribute('href') || '';
    }
    if (!href) {
      const alt = [...a.querySelectorAll("a[href*='/status/']")]
        .find(x => /\\/status\\/\\d+/.test(x.getAttribute('href') || '')
                  && !/\\/(analytics|photo|video|retweets|likes)/.test(
                        x.getAttribute('href')));
      href = alt ? alt.getAttribute('href') : '';
    }
    const m = href.match(/\\/status\\/(\\d+)/);
    const sid = m ? m[1] : '';
    if (!sid || seen.has(sid)) continue;
    seen.add(sid);
    const who = a.querySelector("a[href^='/']");
    const box = a.querySelector('[data-testid="tweetText"]');
    // innerText is undefined on a node Chrome is not rendering, and a saved
    // list mounts rows inside collapsed containers. One unreadable body must
    // cost one row's text, not the whole read — so it falls back to
    // textContent and then to empty, as xkit.ARTICLE does.
    const body = box ? ((box.innerText || box.textContent || '')
                       .replace(/\\s+/g, ' ').trim()) : '';
    out.push({sid: sid,
              who: who ? who.getAttribute('href').split('/').pop() : '?',
              text: body});
  }
  return JSON.stringify(out);
})()"""

# One step down the saved list. Reports whether the document actually moved, so
# the read can stop at the end of the list instead of grinding out its rounds.
SCROLL_DOWN = """(() => {
  const before = Math.round(window.scrollY);
  window.scrollBy(0, Math.round(window.innerHeight * __STEP__));
  const after = Math.round(window.scrollY);
  return JSON.stringify({moved: after > before, from: before, to: after,
                         height: Math.round(document.body.scrollHeight)});
})()"""


def testids_line(c, sid: str) -> str:
    """The article's real control testids, for a run that changed nothing.

    xkit.set_action already embeds them in its own failure text; this is the
    read for the failures that happen before it gets that far, so the run says
    what it saw rather than only what it did not find.
    """
    try:
        state = X.action_state(c, sid)
    except Exception as exc:
        return "  testids could not be read: %s" % str(exc)[:120]
    return "  testids on the article: %s" % (state.get("testids") or [])


def verdict(remove: bool) -> tuple:
    """The three terminal lines, as prefixes, for one direction.

    Built from one branch so the verdict a caller greps can never come from a
    different string than the exit code it controls.
    """
    if remove:
        return ("UNBOOKMARKED", "ALREADY UNBOOKMARKED", "NOT UNBOOKMARKED")
    return ("BOOKMARKED", "ALREADY BOOKMARKED", "NOT BOOKMARKED")


def is_bookmarks_view(surf: dict) -> bool:
    """True when the tab is showing the saved list, on any of three signals."""
    if surf.get("route_hit"):
        return True
    if (surf.get("link") or {}).get("current"):
        return True
    return any("/bookmarks" in (h or "")
               for h in (surf.get("current_links") or []))


def read_rows(c) -> "list | None":
    """Every saved post rendered right now, or None when the page said nothing.

    Read through js_raw and parsed here because the template ends in
    JSON.stringify: js() unwraps a JSON string into a dict, and the list
    inside that dict is not what the deduping loop below iterates over.
    """
    raw = X.js_raw(c, READ_ROWS, wait=25, retries=3)
    if not isinstance(raw, str):
        return None
    try:
        rows = json.loads(raw)
    except ValueError:
        return None
    return rows if isinstance(rows, list) else None


def collect(c, want: int) -> tuple:
    """Scroll-collect up to `want` saved posts.

    Returns (rows, readable, rounds, why). `readable` is False only when not
    one round produced a list, and that is the difference between "this
    account has saved nothing" and "the page could not be read": the two share
    an exit-code shape, so they must not share a line of output.

    A round that reads nothing does NOT re-read the same scroll position — it
    scrolls anyway. Retrying in place is what the first version of this loop
    did, and a single transient evaluate failure then burned the whole round
    budget on one screen and reported a short list as if that were all of it.
    Every row the collect has does not depend on any one round having worked.
    """
    rows: list = []
    seen: set = set()
    readable = False
    rounds = 0
    missed = 0
    stop_reason = "the saved list ran out"

    def absorb(got):
        for row in got:
            sid = (row or {}).get("sid") or ""
            if not sid or sid in seen:
                continue           # the virtual list re-renders behind us
            seen.add(sid)
            rows.append(row)

    for rnd in range(1, SCROLL_ROUNDS + 1):
        rounds = rnd
        got = read_rows(c)
        if got is None:
            missed += 1
        else:
            readable = True
            absorb(got)
        if len(rows) >= want:
            break
        step = X.js(c, SCROLL_DOWN, step=SCROLL_STEP)
        time.sleep(SETTLE)
        if step.get("why"):
            stop_reason = "the page stopped answering: %s" % step["why"]
            break
        if not step.get("moved"):
            # One more read after a scroll that did not move. The list mounts
            # rows from its own prefetch, and a post already queued is a real
            # row rather than a guess — so it is read, not inferred.
            last = read_rows(c)
            if last:
                readable = True
                absorb(last)
            break
    if len(rows) >= want:
        stop_reason = "%d saved posts read" % len(rows)
    elif missed:
        stop_reason = ("the list ran out with %d of %d reads not answering"
                       % (missed, rounds))
    return rows[:want], readable, rounds, stop_reason


def do_list(c, want: int) -> int:
    """Read the saved list the CALLER has already opened. Returns the exit code."""
    surf = X.js(c, SURFACE)
    route = surf.get("route") or "(unreadable)"
    if surf.get("why") or surf.get("_raw"):
        print("  the page would not say where it is: %s"
              % (surf.get("why") or surf.get("_raw")), flush=True)
        print("BOOKMARKS 0", flush=True)
        print("  nothing was read, and this is NOT the same answer as an "
              "empty saved list", flush=True)
        return 1

    # The nav link is the one object here that may arrive as anything at all —
    # xkit.js hands back a dict, but a template that returned a bare string
    # would arrive as a str. Narrowed once, so the reporting below cannot ask
    # a string for a key.
    raw_link = surf.get("link")
    raw_link = raw_link if isinstance(raw_link, dict) else {}
    link = {"href": str(raw_link.get("href") or ""),
            "current": bool(raw_link.get("current"))}
    if not is_bookmarks_view(surf):
        print("  route: %s" % route, flush=True)
        print("  bookmarks nav link: %s"
              % ("found, marked current (%s)" % (link.get("href") or "-")
                 if link.get("current") else
                 "found, not marked current" if surf.get("nav_found")
                 else "not on this page"), flush=True)
        print("NOT THE BOOKMARKS VIEW - open Saved items yourself and re-run; "
              "this script loads no page", flush=True)
        return 1

    print("  bookmarks surface confirmed — route %s, nav link %s"
          % (route, "marked current" if link.get("current")
             else "not marked current, route carried it"), flush=True)

    rows, readable, rounds, why = collect(c, want)
    if not readable:
        print("  the saved view could not be read in %d reads (%s)"
              % (rounds, why), flush=True)
        print("BOOKMARKS 0", flush=True)
        print("  nothing was read, and this is NOT the same answer as an "
              "empty saved list", flush=True)
        return 1

    for row in rows:
        print("  %s @%s: %s" % (row.get("sid"), row.get("who") or "?",
                                (row.get("text") or "")[:140]), flush=True)
    print("SAVED_JSON %s" % json.dumps(rows, ensure_ascii=False), flush=True)
    print("BOOKMARKS %d" % len(rows), flush=True)
    if rows:
        print("  read %d saved posts in %d reads; %s" % (len(rows), rounds, why),
              flush=True)
    else:
        print("  the surface WAS a bookmarks view and it holds no saved posts "
              "— a real empty answer, not a read that failed", flush=True)
    return 0


def do_toggle(c, sid: str, remove: bool, dry_run: bool) -> int:
    """Bookmark or unbookmark `sid`. Returns the process exit code."""
    done, already_line, fail_line = verdict(remove)
    want_on = not remove

    art = X.read_article(c, sid)
    if art.get("why"):
        # One scroll, once. See the module docstring: a target the virtual list
        # has dropped is not in the document at all, so this buys one window of
        # feed refresh and not more. window.scrollTo is not a navigation.
        X.js_raw(c, "window.scrollTo(0, 0); true", wait=20, retries=3)
        time.sleep(2.5)
        art = X.read_article(c, sid)
    if art.get("why"):
        print("NOT ON PAGE %s" % sid, flush=True)
        print("  open that post's thread and scroll it into view, then run "
              "again — this script loads no page, so it cannot bring a post "
              "here", flush=True)
        return 1

    print("  @%s %s — %s"
          % (art.get("who") or "?", sid,
             (art.get("text") or "")[:140].replace("\n", " ")), flush=True)

    if dry_run:
        # Read the same state the toggle would read and click nothing. The
        # verdict lines are deliberately absent from here: a dry run must not
        # put BOOKMARKED or UNBOOKMARKED anywhere a grep can find one.
        state = X.action_state(c, sid)
        on = X.is_on(state, "bookmark")
        print("DRY RUN %s — nothing clicked" % sid, flush=True)
        print("  current state: %s" % ("bookmarked" if on else "not bookmarked"),
              flush=True)
        print("  target state:  %s" % ("bookmarked" if want_on
                                       else "not bookmarked"), flush=True)
        print(testids_line(c, sid), flush=True)
        print("  would %s" % ("unbookmark" if remove else "bookmark"),
              flush=True)
        print("  UNVERIFIED here: the control is read as %r when on and %r "
              "when off (xkit.TOGGLE_KINDS['bookmark']), falling back to "
              "移除书签 / Remove bookmark / 已添加书签 on the label. Nothing in "
              "this skill has driven a bookmark control yet, so the testids "
              "printed above are what a first run is really measuring."
              % (X.TOGGLE_KINDS["bookmark"]["on"][0],
                 X.TOGGLE_KINDS["bookmark"]["off"][0]), flush=True)
        return 0

    # Idempotent by construction: the helper reads the row, clicks only when it
    # disagrees with want_on, reads again, and reports what it saw.
    res = X.set_action(c, sid, "bookmark", want_on=want_on)

    if res.get("ok"):
        print("%s %s" % (already_line if res.get("already") else done, sid),
              flush=True)
        if res.get("already"):
            print("  the control already read that way, so nothing was "
                  "clicked — a toggle has no third state", flush=True)
        return 0

    print("%s %s" % (fail_line, sid), flush=True)
    print("  %s" % (res.get("why") or "the control did not change state"),
          flush=True)
    if not res.get("testids"):
        print(testids_line(c, sid), flush=True)
    print("  UNVERIFIED here: if neither the 'on' nor the 'off' testid is in "
          "that list, the real control name is the aria-label to match — this "
          "skill has never driven a bookmark control, and a run that lists "
          "what it saw is worth more than one that says 'not found'",
          flush=True)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bookmark or unbookmark a post, or read the saved list "
                    "the caller has already opened.")
    ap.add_argument("sid", nargs="?",
                    help="status id of the post to bookmark or unbookmark")
    ap.add_argument("--remove", action="store_true",
                    help="take the bookmark back instead of making it")
    ap.add_argument("--list", dest="list_n", type=int, metavar="N",
                    help="read up to N posts from the saved view the caller "
                         "has already opened; this script loads no page")
    ap.add_argument("--dry-run", action="store_true",
                    help="read the bookmark state and report it; click "
                         "nothing")
    args = ap.parse_args()

    # Argument gates first: a refusal that costs nothing should not cost a
    # browser connection, and a bad id should never reach the page.
    if args.list_n is not None:
        if args.list_n < 1:
            return X.die("REFUSING - --list wants a positive count, not %d"
                         % args.list_n)
        if args.sid:
            print("  --list wins over the status id: reading the saved view, "
                  "not touching %s" % args.sid, flush=True)
    elif not args.sid:
        return X.die("REFUSING - nothing to do: give a status id, or --list N "
                     "with the saved view already open")
    else:
        if not SID_RX.match(args.sid.strip()):
            return X.die("REFUSING - %r does not look like a status id"
                         % args.sid)
        args.sid = args.sid.strip()

    try:
        c, tab, me = X.connect()
    except Exception as exc:
        # connect() reads the tab list over HTTP first, and a browser that is
        # not running answers that with a refused connection rather than an
        # empty list. Unhandled it is a traceback on the most ordinary
        # invocation there is.
        print(X.no_browser(), flush=True)
        print("  (%s)" % str(exc)[:120], flush=True)
        return 1
    if c is None:
        return 1                     # connect already printed the reason

    try:
        if args.list_n is not None:
            return do_list(c, args.list_n)
        return do_toggle(c, args.sid, args.remove, args.dry_run)
    except Exception as exc:
        # The state after an unexpected error is UNKNOWN, which is not ok, and
        # a run that exits 0 on an unconfirmed click is the exact defect this
        # file exists to prevent. Say which of the two it is instead.
        if args.list_n is not None:
            print("  the read ended early: %s" % str(exc)[:160], flush=True)
            print("BOOKMARKS 0", flush=True)
            print("  nothing is claimed about the saved list", flush=True)
            return 1
        line = verdict(args.remove)[2]
        print("%s %s" % (line, args.sid), flush=True)
        print("  the run ended early: %s" % str(exc)[:160], flush=True)
        print(testids_line(c, args.sid), flush=True)
        return 1
    finally:
        try:
            c.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())