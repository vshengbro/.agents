#!/usr/bin/env python3
"""Repost a status, or take the repost back, through the control it has.

A repost is the one verb in this skill whose failures are silent. A like that
does not happen leaves a post unliked; a repost that goes the wrong way leaves
the timeline with one fewer count and nothing in any log to say who took it
back. So the click is not the event here either: the button state is read
first, and nothing is clicked unless that state disagrees with the goal.
xkit.set_action does the whole read-decide-click-reread loop, and the point of
this file is to be the twenty lines around it — which article, which word, what
to print — rather than a second copy of a toggle that is easy to get backwards.

Three things are inherited from xkit rather than re-established, and each of
them is load-bearing:

  * The OWNING article, not any status link. xkit.read_article takes the
    article whose own time link carries the id and refuses a quote container,
    because a quoted post, the post a reply answers and the inner post of a
    retweet all carry the target's link — matching "any status link" is how a
    run once acted on a stranger's post. The consequence is worth stating: an
    id that exists only inside a quote reads as not on the page here, which is
    the safe direction to be wrong in.

  * A bare element.click() on the action row. That is what like_posts.py has
    always done and it works; xkit keeps it in a helper separate from the
    reply control's mousedown/mouseup pair precisely because the two are not
    interchangeable. So this script names the kind and reads the state, and
    never dispatches a click of its own.

  * One scroll attempt, then stop. A target the virtual list has dropped is
    not recovered by scrolling — the article is not in the document at all —
    so a second attempt returns the same answer while looking like patience.

What is NOT measured: the `retweet` and `unretweet` testids. Every other
script here has driven the like control and nothing in this skill has ever
driven a repost, so that pair comes from the browser-automation reference notes
and no run has seen it on this build. xkit.TOGGLE_KINDS carries the same pair
and xkit.is_on falls back to the aria-label (取消转帖 / 取消转发 / Undo repost)
when the testid does not match. That is exactly why the failure branch prints
the article's real testids instead of a guess: the first run against the live
page is what turns this pair from a note into a measurement, and a failure
that lists what it saw is worth more than a failure that says "not found".

ALREADY is a success and exits 0. A toggle has no third state, so a re-run
that clicked a satisfied control is how the previous run gets undone, and the
exit code has to say the goal holds rather than that nothing happened.

The lines a caller greps, each followed by the status id:

    REPOSTED  UNREPOSTED  ALREADY REPOSTED  ALREADY NOT REPOSTED
    NOT REPOSTED  NOT UNREPOSTED

  python3 x_repost.py <status-id> [--undo] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit as X                                          # noqa: E402


def labels(undo: bool) -> tuple:
    """The three terminal lines, as prefixes, for one direction.

    Built from one branch so the verdict a caller greps can never come from a
    different string than the exit code it controls.
    """
    if undo:
        return ("UNREPOSTED", "ALREADY NOT REPOSTED", "NOT UNREPOSTED")
    return ("REPOSTED", "ALREADY REPOSTED", "NOT REPOSTED")


def owning_article(c, sid: str) -> dict:
    """xkit.read_article, or {'why': ...} when the id is not mounted here."""
    return X.read_article(c, sid)


def testids_line(c, sid: str) -> str:
    """The article's real control testids, for a run that changed nothing.

    xkit.set_action already embeds them in its own failure text; this is the
    read for the failures that happen BEFORE it gets that far, so the run
    still says what it saw instead of only saying what it did not find.
    """
    try:
        state = X.action_state(c, sid)
    except Exception as exc:
        return "  testids could not be read: %s" % str(exc)[:120]
    return "  testids on the article: %s" % (state.get("testids") or [])


def run(c, sid: str, undo: bool, dry_run: bool) -> int:
    """Repost or unrepost `sid`. Returns the process exit code."""
    done, already_line, fail_line = labels(undo)
    want_on = not undo

    art = owning_article(c, sid)
    if art.get("why"):
        # One scroll, once. See the module docstring: a target the list has
        # dropped is not in the document, so this buys one window of feed
        # refresh and not more. window.scrollTo is not a navigation.
        X.js_raw(c, "window.scrollTo(0, 0); true", wait=20, retries=3)
        time.sleep(2.5)
        art = owning_article(c, sid)
    if art.get("why"):
        print("NOT ON PAGE %s" % sid, flush=True)
        print("  open that post's thread and scroll it into view, then run "
              "again — this script loads no page, so it cannot bring a post "
              "here", flush=True)
        return 1

    print("  @%s %s — %s" % (art.get("who") or "?", sid,
                             (art.get("text") or "")[:140].replace("\n", " ")),
          flush=True)

    if dry_run:
        # Read the same state the toggle would read, and click nothing. The
        # verdicts above are deliberately not printed here: a dry run must
        # not put REPOSTED or UNREPOSTED on the line for a caller to grep.
        state = X.action_state(c, sid)
        on = X.is_on(state, "retweet")
        print("DRY RUN %s — nothing clicked; the repost control currently "
              "reads %s" % (sid, "reposted" if on else "not reposted"),
              flush=True)
        print(testids_line(c, sid), flush=True)
        print("  would %s" % ("unrepost" if undo else "repost"), flush=True)
        return 0

    # Idempotent by construction: the helper reads the row, clicks only when
    # it disagrees with want_on, reads again, and reports what it saw.
    res = X.set_action(c, sid, "retweet", want_on=want_on)

    if res.get("ok"):
        print("%s %s" % (already_line if res.get("already") else done, sid),
              flush=True)
        return 0

    print("%s %s" % (fail_line, sid), flush=True)
    print("  %s" % (res.get("why") or "the control did not change state"),
          flush=True)
    if not res.get("testids"):
        print(testids_line(c, sid), flush=True)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sid", help="status id of the post to repost")
    ap.add_argument("--undo", action="store_true",
                    help="take the repost back instead of making it")
    ap.add_argument("--dry-run", action="store_true",
                    help="read the button state and report it; click nothing")
    args = ap.parse_args()

    try:
        c, tab, me = X.connect()
    except Exception as exc:
        # xkit.connect catches its own misses, but the port lookup under it
        # raises when nothing is listening — and a driver traceback is not a
        # message a caller can act on. xkit.no_browser() is the house wording.
        print(X.no_browser(), flush=True)
        print("  (%s)" % str(exc)[:120], flush=True)
        return 1
    if c is None:
        return 1                 # connect already printed the reason

    try:
        return run(c, args.sid, args.undo, args.dry_run)
    except Exception as exc:
        # The state after an unexpected error is UNKNOWN, which is not ok, and
        # a run that exits 0 on an unconfirmed click is the exact defect this
        # file exists to prevent. Say so plainly instead of exiting quietly.
        print("%s %s" % (labels(args.undo)[2], args.sid), flush=True)
        print("  the run ended early: %s" % str(exc)[:160], flush=True)
        print(testids_line(c, args.sid), flush=True)
        return 1
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
