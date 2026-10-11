#!/usr/bin/env python3
"""Quote a post through the quote box that its own quote control opens.

The path is the one a person takes: find the post on the open page, click the
quote control on that post, type into the box that appears, send, and find the
new post in the timeline afterwards. Clicking the control opens the box in
place, so this loads no page, opens no tab, takes no pointer and takes no OS
keyboard — which is why the commit gate allows the file at all. Every verb it
needs is xkit's; nothing here has its own copy of the editor read, the send
control, the canon or the state files.

Two testids in this file are UNVERIFIED, and they are the two this script was
written against without a measurement in front of it. `quote` is the quote
control and `quoteTweet` is the quoted-post container: both come from the
browser-automation reference notes, and nothing in this skill had ever clicked
one, so the first live run is the measurement. They are written so that being
wrong is legible instead of silent — the click reports every testid and
aria-label the article really carries when the control is not found, rather
than only saying it is missing.

What was measured on the way here, and what each of those cost:

  * Falling back to the main composer when the box did not open published the
    whole commentary as a standalone post — 643 characters, on a run that
    meant to quote somebody. So there is no fallback at all: the editor must
    come back from inside a dialog, and a quote box that does not open is NOT
    SENDING, not a reason to type into the composer that was already there.

  * scrollIntoView was measured to invalidate the node it was asked to bring
    into view, so the click that followed aimed at a detached element and the
    control reported itself off screen while sitting in the middle of the
    viewport. The scroll here is window.scrollTo on the article's own ABSOLUTE
    offset — its rect plus window.scrollY — which moves the document and
    leaves the node attached.

  * A box left holding a draft from an earlier run would have this commentary
    appended to somebody else's sentence and the post would carry their words.
    It is never cleared: clearing a composer raises Chrome's unsaved-changes
    dialog and that modal then blocks every later CDP call, so a non-empty box
    is closed through the control the page already shows and a fresh one is
    opened. Twice, and then it gives up.

  * The bare click and the full mousedown/mouseup/click sequence are kept
    apart on purpose, in that order. like_posts.py's bare element.click() is
    what a like control needs and it works; post_reply.py measured that the
    reply control needs the pair first. Nothing has been measured on a quote
    control, so the cheap act goes first and the sequence is the fallback.

  * Nothing counts as sent until the new post is found in the timeline under
    this account, carrying this commentary's prefix AND a quote container. The
    id reported on success is the NEW post's own status id, never the id that
    was passed in: reporting the quoted post back reads as "the post I quoted
    is mine", which is the failure this skill keeps making in other shapes.

  python3 x_quote.py <status_id> <commentary_or_file> [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit                                                # noqa: E402

# UNVERIFIED. The quote control's data-testid, from the browser-automation
# reference notes. No script in this skill has clicked one, so a run that
# cannot find this control says so and dumps what the article does carry
# instead of reporting a lookup failure and stopping there.
QUOTE_TESTID = "quote"

# UNVERIFIED as a POSTING dependency, though it is not new: xkit.ARTICLE and
# xkit.MINE already read this container, so the read side has precedent. What
# has never happened is this account quoting a post and the container being
# asserted on the result, so the verification treats a missing or unreadable
# container as "cannot confirm" rather than as a fact about the page.
QUOTE_CONTAINER_TESTID = "quoteTweet"

# The OWNING article for a status id, as a step toward a control on it: the
# one whose own time link carries the id and which is not itself a quote
# container. This is xkit.ARTICLE's pick restated, because these templates
# need the NODE and xkit.ARTICLE returns a description of the article.
OWNING = """\
  const pick = (a) => {
    if (a.querySelector('[data-testid="quoteTweet"]')) return null;
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    return st ? a : null;
  };"""

# Bring the target into view with window.scrollTo on the article's absolute
# offset, never scrollIntoView (measured to invalidate the node). The article
# is placed a third of the way down rather than at the top, because the
# control this script wants sits in the action row at the BOTTOM of a post and
# a long post would push it below the fold. A scroll is not a navigation.
SCROLL_TO = """(() => {
  %s
  for (const a of document.querySelectorAll('article')) {
    const own = pick(a);
    if (!own) continue;
    const r = own.getBoundingClientRect();
    const to = Math.max(0, Math.round(r.top + window.scrollY)
                            - Math.round(window.innerHeight / 3));
    window.scrollTo(0, to);
    return JSON.stringify({moved: true, was_top: Math.round(r.top),
                           scrolled_to: to, vh: window.innerHeight});
  }
  return JSON.stringify({moved: false, why: 'the status is not on this page'});
})()""" % OWNING

# Probe or click the quote control, in one template so the owning pick and the
# "is it on screen" arithmetic exist once. Three modes, one string:
#   probe     read the control and change nothing (--dry-run)
#   bare      btn.click()
#   sequence  mousedown/mouseup/click dispatched ON THE ELEMENT, never at
#             coordinates: element.click() fires only `click`, and X's
#             controls act on the pair — post_reply.py measured the reply
#             control opening nothing under a bare click.
QUOTE_POINT = """(() => {
  %s
  for (const a of document.querySelectorAll('article')) {
    const own = pick(a);
    if (!own) continue;
    const btn = own.querySelector('[data-testid=%s]');
    if (!btn)
      return {clicked: false, why: 'no quote control on this post',
              testids: [...new Set([...own.querySelectorAll('[data-testid]')]
                       .map(x => x.dataset.testid))],
              labels: [...own.querySelectorAll('[aria-label]')]
                .map(x => x.getAttribute('aria-label')).filter(Boolean)};
    if (btn.offsetParent === null)
      return {clicked: false, why: 'the quote control is hidden'};
    const box = btn.getBoundingClientRect();
    if (!box.width)
      return {clicked: false, why: 'the quote control has no size'};
    if (box.top < 0 || box.top > window.innerHeight) {
      // Its coordinates are in hand, so move the document to it and let the
      // caller click again rather than reporting a failure that a scroll
      // would fix — this is xkit.TOGGLE's arrangement.
      window.scrollTo(0, Math.max(0, window.scrollY + box.top
                                        - Math.round(window.innerHeight / 2)));
      return {clicked: false, why: 'off screen, scrolled to it',
              top: Math.round(box.top)};
    }
    if (__MODE__ === 'probe')
      return {clicked: false, probe: true, testid: btn.dataset.testid,
              top: Math.round(box.top),
              label: btn.getAttribute('aria-label') || ''};
    if (__MODE__ === 'bare') {
      btn.click();
      return {clicked: true, mode: 'bare', testid: btn.dataset.testid};
    }
    const at = {bubbles: true, cancelable: true, view: window,
                clientX: box.left + box.width / 2,
                clientY: box.top + box.height / 2, button: 0};
    btn.dispatchEvent(new MouseEvent('mousedown', at));
    btn.dispatchEvent(new MouseEvent('mouseup', at));
    btn.dispatchEvent(new MouseEvent('click', at));
    return {clicked: true, mode: 'sequence', testid: btn.dataset.testid};
  }
  return {clicked: false, why: 'the status is not on this page'};
})()""" % (OWNING, json.dumps(QUOTE_TESTID))

# The facts about the NEW post that decide whether it verified. This cannot be
# xkit.read_article: ARTICLE refuses any article that CONTAINS a quote
# container, and a quote post is exactly that — read back the shared way, the
# post this script just published reports as "not on page" while it is
# sitting right there in the timeline. So the owning rule is repeated with
# that one exclusion dropped, and nothing else changed.
QUOTE_STATE = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!st) continue;
    // UNVERIFIED as a posting result: see QUOTE_CONTAINER_TESTID above.
    const qt = a.querySelector('[data-testid="quoteTweet"]');
    const l = qt ? qt.querySelector("a[href^='/']") : null;
    const full = a.innerText || '';
    return JSON.stringify({
      sid: __SID__,
      has_quote: !!qt,
      quoted_who: l ? l.getAttribute('href').split('/').pop() : '',
      quoted_text: qt ? (qt.innerText || '').replace(/\\s+/g, ' ').trim() : '',
      // A quote long enough to be truncated sits behind 显示更多, and
      // expanding it is out of scope here; the state is reported so a run
      // that cannot see the full body says why instead of guessing.
      collapsed: /显示更多|Show more|顯示更多/.test(full.slice(0, 400)),
      testids: [...new Set([...a.querySelectorAll('[data-testid]')]
                 .map(x => x.dataset.testid))]
    });
  }
  return JSON.stringify({why: 'the new post is not on this page'});
})()"""


def stop(c, msg: str, code: int = 1) -> int:
    """Print the line a caller greps for, close the session, return the code.

    Every refusal and every failure ends here, so there is one place that
    closes the socket and one place that decides the exit status. The message
    is printed last, after whatever diagnosis led to it: the last line of this
    script's output is what a cron log is read for, and a run that did nothing
    must never exit 0.
    """
    print(msg, flush=True)
    if c is not None:
        try:
            c.close()
        except Exception:
            pass
    return code


def open_quote_box(c, sid: str) -> dict:
    """Open the quote box, bare click first and the event pair second.

    One click per style, then a real wait for the dialog: clicking the control
    again while the box is still deciding is how two boxes open, and the
    second one is the one that would end up holding the text. Roughly eight
    seconds per style, which is the window the bare click is given before the
    sequence is tried.
    """
    last = {}
    for mode in ("bare", "sequence"):
        got = xkit.js(c, QUOTE_POINT, sid=sid, mode=mode)
        last = got
        if not got.get("clicked"):
            time.sleep(2.0)
            continue
        # A "keep your draft" prompt can mount over the box right after the
        # click, and the first dialog on the page is then the wrong one
        # (measured on the reply path). It is closed here; CLEAR_STALE_DIALOGS
        # only touches dialogs with no editable in them, so the quote box and
        # anything the user typed are not what it acts on.
        xkit.js_raw(c, xkit.CLEAR_STALE_DIALOGS, wait=20, retries=3)
        time.sleep(1.0)
        box = xkit.the_editor(c, want_dialog=True, tries=5, pause=1.6)
        if box:
            return {"opened": True, "mode": mode, "box": box}
        time.sleep(2.0)
    return {"opened": False,
            "why": last.get("why") or "the quote box did not open",
            "testids": last.get("testids") or [],
            "labels": last.get("labels") or []}


def mine_rows(c, me: str) -> list:
    """This account's own articles, read live from the timeline.

    Read through js_raw and parsed here because xkit.MINE ends in
    JSON.stringify: js() unwraps a JSON string into a dict, and a list inside
    that dict is not what this loop iterates over.
    """
    raw = xkit.js_raw(c, xkit.MINE.replace("__WHO__", json.dumps(me)),
                      wait=30, retries=4)
    if not isinstance(raw, str):
        return []
    try:
        rows = json.loads(raw)
    except ValueError:
        return []
    return rows if isinstance(rows, list) else []


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Quote one post through the quote box its control opens.")
    ap.add_argument("sid", help="the status id to quote")
    ap.add_argument("text", metavar="TEXT_OR_FILE",
                    help="the commentary, or the path to a file holding it")
    ap.add_argument("--dry-run", action="store_true",
                    help="read the target and report what would be "
                         "clicked; nothing is clicked, typed or sent")
    args = ap.parse_args()

    sid = str(args.sid).strip()
    if not sid.isdigit():
        return stop(None, "NOT SENDING - %r is not a status id" % args.sid)

    text = xkit.read_text_or_file(args.text)

    # Both refusals are decided from the text alone, so they are made before
    # the browser is even asked for: a body that would ship broken is refused
    # whether or not anything is running, and no control has been clicked.
    stray = xkit.stray_linkifiers(text)
    if stray:
        return stop(None, "REFUSING - %s will be linkified and read back broken"
                    % ", ".join(sorted(set(stray))))
    if len(text) > xkit.POST_LIMIT:
        return stop(None, "REFUSING - %d characters, over the %d limit"
                    % (len(text), xkit.POST_LIMIT))

    try:
        c, _tab, me = xkit.connect()
    except Exception as exc:
        # connect() reads the tab list over HTTP first, and a browser that is
        # not running answers that with a connection error rather than an
        # empty list. Unhandled it is a traceback on the most ordinary
        # invocation there is — the browser closed, or never opened.
        print(xkit.no_browser(), flush=True)
        print("  (reading the tab list failed: %s)" % str(exc)[:80], flush=True)
        return 1
    if c is None:
        return 1

    print("  quoting %s with %d characters%s"
          % (sid, len(text),
             " (dry run — nothing is clicked, typed or sent)"
             if args.dry_run else ""), flush=True)

    pos = xkit.js(c, SCROLL_TO, sid=sid)
    if pos.get("why"):
        return stop(c, "NOT ON THE PAGE - %s" % pos["why"])
    # A scroll needs to settle before a control is aimed at it: the virtual
    # list re-renders, and a click into the old position reads as leaving the
    # box.
    time.sleep(2.0)
    print("  scrolled to %s (article top was %s, viewport %s)"
          % (pos.get("scrolled_to"), pos.get("was_top"), pos.get("vh")),
          flush=True)

    # Read the target so the quoted author is known BEFORE anything is sent —
    # the verification compares the new post's container against this, and a
    # post the page renders only as somebody else's quoted container is not
    # its OWNING article at all: quote it from its own status page.
    target = xkit.read_article(c, sid)
    if target.get("why"):
        return stop(c, "NOT ON THE PAGE - %s" % target["why"])
    target_who = target.get("who") or ""
    print("  target @%s: %s" % (target_who, (target.get("text") or "")[:110]),
          flush=True)

    if args.dry_run:
        probe = xkit.js(c, QUOTE_POINT, sid=sid, mode="probe")
        if not probe.get("testid"):
            print("  no %r control on this post" % QUOTE_TESTID, flush=True)
            print("  testids on the article: %s" % (probe.get("testids") or []),
                  flush=True)
            print("  aria-labels: %s" % (probe.get("labels") or []),
                  flush=True)
            return stop(c, "DRY RUN - the quote control is not on this post")
        print("  quote control %r at top %s (%s)"
              % (probe.get("testid"), probe.get("top"),
                 probe.get("label") or "no label"), flush=True)
        return stop(c, "DRY RUN - the box would open here; nothing clicked, "
                       "typed or sent", 0)

    # Dialogs holding nothing editable are leftovers from an earlier run and
    # they put the first dialog on the page in the wrong place. The ones WITH
    # an editor are never touched.
    xkit.js_raw(c, xkit.CLEAR_STALE_DIALOGS, wait=20, retries=3)
    time.sleep(1.0)

    opened = open_quote_box(c, sid)
    if not opened.get("opened"):
        print("  opened with: %s" % opened.get("mode", "neither style"),
              flush=True)
        print("  %s" % opened.get("why"), flush=True)
        print("  testids on the article: %s" % (opened.get("testids") or []),
              flush=True)
        print("  aria-labels: %s" % (opened.get("labels") or []), flush=True)
        print("  UNVERIFIED: the quote control's data-testid is %r here and "
              "no script in this skill has clicked one. If an aria-label "
              "above names the control, that is the testid this file "
              "needs." % QUOTE_TESTID, flush=True)
        # No fallback to the main composer. Measured: 643 characters of reply
        # published as a standalone post that way.
        return stop(c, "NOT SENDING - the quote box did not open")
    print("  quote box open (%s click), in_dialog=%s"
          % (opened.get("mode"), (opened.get("box") or {}).get("in_dialog")),
          flush=True)

    box = opened.get("box") or {}
    if (box.get("len") or 0) != 0:
        # Never cleared: that raises Chrome's unsaved-changes dialog, which
        # then blocks every later CDP call. Closed through the control the
        # page shows, then opened again — a new quote box starts empty.
        print("  quote box already holds %s characters, reopening a clean one"
              % box.get("len"), flush=True)
        xkit.js(c, xkit.CLOSE_BOX)
        time.sleep(2.0)
        again = open_quote_box(c, sid)
        if not again.get("opened"):
            return stop(c, "NOT SENDING - no empty quote box could be opened, "
                           "and the existing draft is not ours to touch")
        box = again.get("box") or {}
        if (box.get("len") or 0) != 0:
            return stop(c, "NOT SENDING - the reopened quote box still holds "
                           "%s characters" % box.get("len"))
        print("  clean quote box open", flush=True)

    if not xkit.js_raw(c, xkit.FOCUS_EDITOR, wait=20, retries=3):
        return stop(c, "NOT SENDING - the quote box's editor would not take "
                       "focus")
    print("  typing %d characters" % len(text), flush=True)
    xkit.type_body(c, text)
    xkit.remove_warmup(c, text.lstrip())

    held = xkit.the_editor(c, want_dialog=True, tries=4, pause=1.2) or {}
    fg, ft = xkit.canon(held.get("text") or ""), xkit.canon(text)
    if fg != ft:
        print("  the box does not hold what was typed:", flush=True)
        print("    got %d characters, source has %d" % (len(fg), len(ft)),
              flush=True)
        for i, (x, y) in enumerate(zip(fg, ft)):
            if x != y:
                print("    first difference at %d: got %r want %r"
                      % (i, x, y), flush=True)
                break
        else:
            print("    one is a prefix of the other — nothing was invented, "
                  "but something was lost", flush=True)
        return stop(c, "NOT SENDING - the quote box does not hold the source")

    res = xkit.js(c, xkit.SEND_IN_BOX)
    for _ in range(8):
        if res.get("sent"):
            break
        time.sleep(3)
        res = xkit.js(c, xkit.SEND_IN_BOX)
    c.close_composition("")       # never leave a composition open behind
    print("  SEND %s" % res, flush=True)
    if not res.get("sent"):
        return stop(c, "NOT SENDING - %s"
                    % (res.get("why") or res.get("buttons") or "no send"))

    time.sleep(6)
    # A post that has just been sent appears at the TOP of the timeline, and
    # this script scrolled down to reach its target, so the feed is left
    # scrolled past the very post it is about to verify (measured, on a
    # reply: sent, scrolled up, found it, and reported NOT VERIFIED because
    # the read happened first). A scroll is not a navigation.
    xkit.scroll_to_top(c)

    prefix = xkit.canon(text)[:60]
    hit = {}
    for _ in range(6):
        for row in mine_rows(c, me):
            if not (row.get("sid") and row.get("has_quote")):
                continue
            # An empty commentary canonicalises to an empty prefix, which
            # every row starts with; there the container and the author are
            # the whole of the evidence, so both are printed below.
            if prefix and not xkit.canon(row.get("text") or "").startswith(
                    prefix):
                continue
            hit = row
            break
        if hit:
            break
        time.sleep(5)
    if not hit:
        print("  no post by @%s in the timeline carries %r with a quote "
              "container after 6 reads" % (me, prefix[:40]), flush=True)
        return stop(c, "NOT VERIFIED %s" % sid)

    new_sid = hit.get("sid") or ""
    state = xkit.js(c, QUOTE_STATE, sid=new_sid)
    print("  candidate %s: has_quote=%s quoted_who=%s collapsed=%s"
          % (new_sid, state.get("has_quote"), state.get("quoted_who") or "-",
             state.get("collapsed")), flush=True)
    if state.get("why"):
        return stop(c, "NOT VERIFIED %s" % sid)
    if not state.get("has_quote"):
        print("  the article carries no quote container, so it is not the "
              "quote this run made", flush=True)
        return stop(c, "NOT VERIFIED %s" % sid)
    who = (state.get("quoted_who") or "").strip()
    if who and target_who and who != target_who:
        # Unreadable author is a best effort and does not fail the run; a
        # readable author that is NOT the target is a contradiction, and
        # reporting success over it is the failure this skill has made before
        # in other shapes.
        print("  the quote container names @%s and the target was @%s"
              % (who, target_who), flush=True)
        return stop(c, "NOT VERIFIED %s" % sid)
    if not who:
        print("  the quote container names no author — the text prefix and "
              "the container are what matched", flush=True)
    if state.get("collapsed"):
        print("  the new post is collapsed on the timeline; not expanded "
              "(out of scope), the prefix and the container are what matched",
              flush=True)
    print("VERIFIED quote by @%s %s" % (me, new_sid), flush=True)
    try:
        c.close()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())