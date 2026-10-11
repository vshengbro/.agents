#!/usr/bin/env python3
"""Edit one post of this account, in place, through the editor X offers.

Almost every run stops at the caret, and that is the honest answer rather than
a problem to work around. X only offers an edit item inside a short window
after publishing, so an edit requested minutes later has nothing to edit
through; the run says exactly that and exits non-zero instead of looping on
the menu hoping a retry finds one.

What the file had to get right, and what it is:

  * A status id is not a post. A quoted post, the post a reply answers, and
    the inner post of a retweet all carry the target's status link, so
    `a[href*="/status/<id>"]` matches the WRONG article — which is how an
    earlier round reported a stranger's text as this account's own. Every
    read here goes through xkit.read_article, which keeps the owning-article
    rule: the article whose OWN time link points at the id and which is not
    itself a quote container. The ownership gate is then a plain handle
    compare against the live account, so an edit can only ever be aimed at a
    post this account wrote.

  * The overflow menu's items are bare `[role="menuitem"]` with no wrapper —
    measured, `[data-testid="Dropdown"]` matches NOTHING on this build and a
    routine written against it reported "no Dropdown" on a post it had found.
    `[data-testid="caret"]` is VERIFIED (delete_own_post.py clicks it). The
    item's own TEXT — 编辑 / Edit — is UNVERIFIED in this skill: delete_own_post
    only ever proved 删除 / Delete, so the label here is a best guess and the
    failure path dumps the menu items it actually saw instead of saying
    "not found". That is also true of the second assumption: that the edit box
    mounts as a `[role="dialog"]` with a `tweetTextarea_0`. Both are flagged
    in the report rather than presented as fact.

  * An item is matched on its FIRST character. The menu re-renders between the
    read and the click, so a regex over the whole string missed an item that
    was plainly there and visible.

  * THE DEFAULT IS TO REFUSE, and that is the point of the file. X's edit box
    opens PRE-FILLED with the live published text, and the skill forbids
    clearing a composer — clearing raises Chrome's unsaved-changes dialog,
    which then blocks every later CDP call. So once ownership and `--expect`
    are proved, the run reports which post it is looking at and stops: the
    replacement is not typed. `--confirm-ready` exists so a human who has read
    that warning can still automate it, and it changes exactly one thing — a
    single select-all plus ONE Delete key event, which is a selection and one
    key, not a clearing loop. There is no Backspace loop here and no
    execCommand; the commit gate blocks both, and both were dead ends anyway
    (a delete loop keeps finding the same character and eats real text, and
    publish.py's own debris-clearer is the script that left a stray link in a
    published post).

  * The main composer is never used as a fallback. A missing edit box means X
    would not open one, and the composer on the same page would publish the
    replacement as a brand-new standalone post — the exact accident post_reply
    had with 643 characters.

  * The verify step is not a formality. X re-renders an edited post on its own
    schedule, so the read is retried; and the timeline CLIPS a long post
    behind 显示更多, so a correct edit can read as a mismatch. Both are
    reported as themselves rather than folded into a bare failure.

Dead ends kept out on purpose: no retry loop trying to force an editor open,
no falling back to the composer, no clearing the box, no closing it either
(xkit.CLOSE_BOX is for boxes holding nothing but automation's own debris, and
this one holds the user's published text).

    python3 x_edit.py <status_id> "<new text or file>" --expect "first words"
    python3 x_edit.py <status_id> body.md --expect "first words" --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit                                                 # noqa: E402

# A status id is a snowflake: digits and nothing else. Checking it here means
# a mistyped argument never reaches the page, and the caller learns it from
# this file instead of from a "not on page" that reads like a stale feed.
SID_RX = re.compile(r"\d{5,25}\Z")

# Select the whole contents of the edit box. This is a SELECTION: it moves the
# caret and marks the text, and the single Delete key event the caller sends
# afterwards is what removes it. Nothing is written to the DOM here, which is
# why it is not the composer clearing the commit gate blocks.
#
# Scoped exactly like xkit.SEND_IN_BOX — the editor inside the dialog that
# holds it — so a second editor on the page (two nodes carry
# data-testid="tweetTextarea_0", and only one is the real one) is never the
# thing that gets selected.
SELECT_ALL = """(() => {
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  const e = all.find(n => dialogs.some(d => d === n.closest('[role="dialog"]')))
          || all[0];
  if (!e) return 'NO_EDITOR';
  e.focus();
  const sel = window.getSelection();
  const r = document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges();
  sel.addRange(r);
  return 'SELECTED';
})()""" % json.dumps(xkit.DRAFT_CLS)

# The owning article's innerText — the same owning-article rule as
# xkit.read_article, so this cannot drift onto a quote container. Consulted
# only when read_article returned no body at all (an image-only or
# link-card-only post has no [data-testid="tweetText"]); it is chrome-heavy
# and is never allowed to override a body that WAS read.
INNER = """(() => {
  for (const a of document.querySelectorAll('article')) {
    if (a.querySelector('[data-testid="quoteTweet"]')) continue;
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!st) continue;
    return a.innerText || '';
  }
  return '';
})()"""

# The two refusal messages a caller may need to tell apart, written once.
# WINDOW: X never offered an editor, so nothing was opened. NO_BOX: the menu
# item was clicked and no box mounted behind it, which is a different failure
# and is the one worth looking at the page for.
WINDOW_MSG = ("EDIT WINDOW CLOSED - X did not offer an editor for %s; it can "
              "only be edited shortly after posting")
NO_BOX_MSG = ("NOT EDITING - no edit box opened (X only allows editing "
              "shortly after publishing)")

# The default answer, and the whole reason this file is safe to point at a
# production account. The edit box holds the live published text; the skill
# forbids clearing a composer; so the retype is handed to a human.
PRE_FILLED_MSG = (
    "NOT EDITING - this edit box is pre-filled with the live post text and "
    "the skill forbids clearing a composer, so the replacement is not typed "
    "automatically. Open the edit box yourself, select-all-replace by hand, "
    "and re-run with --confirm-ready, OR use delete+repost.")


def editor_text(c) -> str:
    """What the dialog editor holds, re-read fresh each time."""
    st = xkit.editors(c)
    items = [it for it in (st.get("items") or []) if it.get("in_dialog")]
    if not items:
        items = st.get("items") or []
    if not items:
        return ""
    # Two nodes carry the testid and only the taller visible one is real.
    return (items[0].get("text") or "")


def editor_len(c) -> int:
    st = xkit.editors(c)
    items = [it for it in (st.get("items") or []) if it.get("in_dialog")]
    items = items or (st.get("items") or [])
    if not items:
        return -1
    return int(items[0].get("len") or 0)


def opening_note(me: str, sid: str, cur: str) -> None:
    """Print the post this run is about to touch, before it touches anything."""
    print("editing post %s by @%s (%d characters on screen)"
          % (sid, me, len(cur)), flush=True)
    print("  current: %r" % cur[:200], flush=True)


def open_editor(c, sid: str):
    """Caret, then the edit item. Returns (ok, reason) and never retries a
    missing editor.

    The one retry here is a SCROLL: xkit.CARET reports `caret was off screen,
    scrolled to it` when the control is below the fold, exactly as
    xkit.TOGGLE does for the like control, and a second attempt after the
    scroll is the same single click. Nothing else is retried — an edit item
    X did not offer does not appear on the third look.
    """
    res = xkit.js(c, xkit.CARET, sid=sid)
    if not res.get("opened") and "off screen" in str(res.get("why") or ""):
        time.sleep(1.2)
        res = xkit.js(c, xkit.CARET, sid=sid)
    if not res.get("opened"):
        return False, "the overflow menu did not open (%s)" % (
            res.get("why") or res.get("_raw") or "no reason given")
    time.sleep(1.5)

    # UNVERIFIED label: delete_own_post.py proves 删除 / Delete on this menu,
    # not 编辑 / Edit. When the guess is wrong the items are printed, which
    # is what turns a dead end into a one-line fix.
    hit = xkit.menu_choose(c, ["编辑", "Edit"])
    if not hit.get("clicked"):
        seen = xkit.menu_items(c)
        return False, "the menu has no edit item; it offers: %s" % (
            seen if isinstance(seen, list) else (seen or "nothing readable"))
    time.sleep(1.8)
    return True, "clicked %r" % hit.get("item")


def verify(c, sid: str, me: str, text: str) -> tuple:
    """Read the account's own posts back and find the edited one.

    MINE is read with js_raw, NOT with xkit.js, and that is load-bearing.
    xkit.js unwraps a JSON OBJECT out of the answer's string form and hands it
    back as a dict; MINE ends in JSON.stringify() over an ARRAY, so it parses
    to a list, misses the `isinstance(r, dict)` branch and comes back as
    {_raw: '[{…}]'} — every row access on that returns nothing. Measured here:
    with xkit.js the verify loop found zero posts on a run whose edit had in
    fact been sent, and reported NOT VERIFIED. xkit.read_article parses its own
    string for the same reason, so this does the same.
    """
    want = xkit.canon(text)
    why = "the edited post was not among this account's posts in view"
    for _ in range(5):
        got = xkit.js_raw(c, xkit.MINE.replace("__WHO__", json.dumps(me)),
                          wait=25, retries=4)
        rows = []
        if isinstance(got, str):
            try:
                parsed = json.loads(got)
            except ValueError:
                parsed = None
            if isinstance(parsed, list):
                rows = parsed
            else:
                why = "could not read this account's posts back (%s)" % (
                    str(got)[:120])
        else:
            why = "could not read this account's posts back (%s)" % (
                got.get("why") or got.get("_raw") or "unreadable") \
                if isinstance(got, dict) else "unreadable answer"
        for row in rows:
            if row.get("sid") == sid and xkit.canon(row.get("text") or "") == want:
                return True, ""
        for row in rows:
            if row.get("sid") != sid:
                continue
            shown = row.get("text") or ""
            art = xkit.read_article(c, sid)
            if art.get("collapsed"):
                why = ("the timeline shows only %d of %d characters of it — X "
                       "clips a long post behind 显示更多, so a correct edit can "
                       "read as a mismatch here; expand it by hand and compare"
                       % (len(xkit.canon(shown)), len(want)))
            else:
                fg = xkit.canon(shown)
                i = next((n for n in range(min(len(fg), len(want)))
                          if fg[n] != want[n]), None)
                why = ("the post is on the page but reads %r"
                       % shown[:160])
                if i is not None:
                    why += "; first difference at %d: page %r, wanted %r" % (
                        i, fg[i:i + 30], want[i:i + 30])
                if "http" in shown or "\x00" in want:
                    why += (" (a body carrying a URL reads as a mismatch "
                            "because the page shows the link's display text, "
                            "not the URL)")
        time.sleep(4)
    return False, why


def run(c, args, text: str, me: str, state: dict) -> int:
    """Everything that touches the page. `state` records whether a send
    happened, so an abort after the send is never reported as "not editing"."""

    # --- gate 1: the status id is on the page -----------------------------
    art = xkit.read_article(c, args.sid)
    if art.get("why") or "who" not in art:
        print("NOT ON PAGE %s - %s" % (args.sid, art.get("why") or
                                       "no owning article here"), flush=True)
        return 1

    # --- gate 2: it is THIS account's post. -------------------------------
    # read_article already applied the owning-article rule, so this is the
    # one comparison that makes an edit safe: a stranger's id resolves to
    # their article and stops here, before the caret is even touched.
    if art.get("who") != me:
        return xkit.die("REFUSING - %s is not this account's post (page shows "
                        "@%s)" % (args.sid, art.get("who")))
    opening_note(me, args.sid, art.get("text") or "")

    # --- gate 3: it holds the text the caller named -----------------------
    # tweetText is a display layer and is CLIPPED — it stops mid-sentence and
    # carries no 显示更多 of its own — so read_article falls back to the
    # article's own innerText when there is no text box at all (an image-only
    # post). That fallback is the article's CHROME (display name, counters)
    # rather than a body, so --expect against it is weak; it is consulted only
    # when there is no text, never to override text that was read.
    cur = art.get("text") or ""
    if not cur.strip():
        fallback = xkit.js_raw(c, INNER.replace("__SID__", json.dumps(args.sid)),
                               wait=25, retries=4)
        if isinstance(fallback, str) and fallback.strip():
            cur = fallback
    if not (args.expect in cur
            or xkit.canon(args.expect) in xkit.canon(cur)):
        print("REFUSING - this post does not contain the expected text",
              flush=True)
        print("  expected: %r" % args.expect[:200], flush=True)
        print("  actual:   %r" % cur[:200], flush=True)
        return 1

    # --- the edit window ---------------------------------------------------
    ok, why = open_editor(c, args.sid)
    if not ok:
        print(WINDOW_MSG % args.sid, flush=True)
        print("  %s" % why, flush=True)
        return 1

    ed = xkit.the_editor(c, want_dialog=True)
    if not ed:
        st = xkit.editors(c)
        print(NO_BOX_MSG, flush=True)
        print("  editors on the page: %s" % (st.get("count") or 0),
              flush=True)
        print("  dialogs holding one: %s" % (st.get("dialogs") or 0),
              flush=True)
        return 1
    box = ed.get("text") or ""
    print("  edit box open: %d characters, in_dialog=%s"
          % (ed.get("len") or 0, ed.get("in_dialog")), flush=True)

    # --- the box must be holding the post the caller named ----------------
    # canon() strips whitespace and collapses every URL span to one marker, so
    # the reflow the renderer applies and the t.co rewrite cannot hide a
    # genuinely different post behind this compare.
    anchor = xkit.canon(args.expect)[:30]
    if not box.strip() or not xkit.canon(box).startswith(anchor):
        print("NOT EDITING - the edit box does not hold the post you named",
              flush=True)
        print("  box holds: %r" % box[:200], flush=True)
        print("  expected to start: %r" % args.expect[:200], flush=True)
        return 1

    if args.dry_run:
        # Nothing is typed and nothing is sent, so this is not an edit and
        # does not exit 0: a caller that cannot tell "nothing was done" from
        # "done" is the failure xkit.die() exists to prevent.
        print("NOT EDITING - dry run: ownership and --expect confirmed and the "
              "edit box holds the post you named; nothing was typed, nothing "
              "was sent. A dry run exits 1 because nothing was edited.",
              flush=True)
        return 1

    if not args.confirm_ready:
        print(PRE_FILLED_MSG, flush=True)
        return 1

    # --- the one clearing act this file is allowed ------------------------
    # Focus, select the whole box, ONE Delete forward. Not a loop: xkit's own
    # warm-up removal deletes once and checks, because a delete loop keeps
    # finding the same character and runs to its limit into real text.
    xkit.js(c, xkit.FOCUS_EDITOR)
    moved = xkit.js_raw(c, SELECT_ALL)
    if moved != "SELECTED":
        print("NOT EDITING - the edit box could not be selected (%s); it was "
              "left as it was" % (moved if isinstance(moved, str)
                                  else "evaluate failed"), flush=True)
        return 1
    time.sleep(0.6)
    c.send("Input.dispatchKeyEvent", type="keyDown", key="Delete",
           code="Delete", windowsVirtualKeyCode=46)
    c.send("Input.dispatchKeyEvent", type="keyUp", key="Delete",
           code="Delete", windowsVirtualKeyCode=46)
    time.sleep(1.0)

    left = editor_len(c)
    if left != 0:
        print("NOT EDITING - the edit box still holds %s characters after the "
              "single delete; nothing was typed on top of it, and it is left "
              "for you to look at" % (left,), flush=True)
        return 1

    # --- type --------------------------------------------------------------
    # `existing` is the text the box held, i.e. "this block has been used".
    # That is the flag that makes the ASCII path take the same warm-up pass as
    # the CJK path: a fresh Draft block swallows the FIRST character of any
    # sequence (measured four ways, including with the caret collapsed to the
    # start), and a block that was pre-filled and emptied is exactly that
    # shape. remove_warmup takes the one space back out, anchored on the
    # source's own leading characters.
    print("  typing %d characters (%s)"
          % (len(text), "not pure ASCII" if any(ord(ch) > 127 for ch in text)
             else "pure ASCII"), flush=True)
    xkit.type_body(c, text, existing=box)
    xkit.remove_warmup(c, text.lstrip())

    got = editor_text(c)
    if xkit.canon(got) != xkit.canon(text):
        print("NOT EDITING - text mismatch", flush=True)
        fg, ft = xkit.canon(got), xkit.canon(text)
        i = next((n for n in range(min(len(fg), len(ft))) if fg[n] != ft[n]),
                 None)
        print("  editor holds %d characters, source has %d"
              % (len(fg), len(ft)), flush=True)
        if i is None:
            print("  the lengths differ and the shared part is identical",
                  flush=True)
        else:
            lo = max(0, i - 30)
            print("  first difference at %d" % i, flush=True)
            print("    editor: %r" % fg[lo:i + 30], flush=True)
            print("    source: %r" % ft[lo:i + 30], flush=True)
        print("  the box was NOT closed and NOT sent; it is yours now",
              flush=True)
        return 1

    # --- send --------------------------------------------------------------
    res = xkit.js(c, xkit.SEND_IN_BOX)
    for _ in range(5):
        if res.get("sent"):
            break
        time.sleep(3.0)
        res = xkit.js(c, xkit.SEND_IN_BOX)
    c.close_composition("")
    if not res.get("sent"):
        print("NOT EDITING - the edit was not sent (%s)"
              % (res.get("why") or res.get("_raw") or "no send button"),
              flush=True)
        return 1
    state["sent"] = True
    print("  sent via %s" % res.get("which"), flush=True)

    # --- verify ------------------------------------------------------------
    # The box is not closed afterwards: it holds the user's published text,
    # and xkit.CLOSE_BOX is for boxes holding nothing but automation's debris.
    xkit.scroll_to_top(c)
    good, why = verify(c, args.sid, me, text)
    if good:
        print("VERIFIED edit %s" % args.sid, flush=True)
        return 0
    print("NOT VERIFIED edit %s" % args.sid, flush=True)
    print("  %s" % why, flush=True)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Edit one post of this account, by status id.")
    ap.add_argument("sid", help="status id of the post to edit")
    ap.add_argument("text", help="the new text, or a file holding it")
    ap.add_argument("--expect", required=True,
                    help="first words the EXISTING post must contain, so a "
                         "wrong id is caught before anything is touched")
    ap.add_argument("--confirm-ready", action="store_true",
                    help="read the warning first: selects the whole pre-filled "
                         "edit box and presses Delete ONCE before typing")
    ap.add_argument("--dry-run", action="store_true",
                    help="run every gate and open the edit box, then type and "
                         "send nothing (exits 1: nothing was edited)")
    args = ap.parse_args()

    # Argument gates first: a refusal that costs nothing should not cost a
    # browser connection, and a bad id should never reach the page.
    if not SID_RX.match(args.sid.strip()):
        return xkit.die("REFUSING - %r does not look like a status id"
                        % args.sid)
    args.sid = args.sid.strip()
    body = xkit.read_text_or_file(args.text)
    if not body.strip():
        return xkit.die("REFUSING - the new text is empty; an empty post is "
                        "not an edit (delete the post instead)")
    if len(body) > xkit.POST_LIMIT:
        return xkit.die("REFUSING - %d characters, over the %d limit"
                        % (len(body), xkit.POST_LIMIT))

    # The connect lives in xkit; the exception guard is here because a browser
    # that is not running answers the port with a refused connection, which
    # would otherwise reach the caller as a traceback. Nothing has been typed
    # at this point and nothing is claimed.
    try:
        c, tab, me = xkit.connect()
    except Exception as exc:
        print("  %s: %s" % (type(exc).__name__, str(exc)[:90]), flush=True)
        return xkit.die("REFUSING - cannot reach the browser to drive it.\n  %s"
                        % xkit.no_browser())
    if c is None:
        return 1                       # xkit printed why

    state = {"sent": False}
    try:
        return run(c, args, body, me, state)
    except Exception as exc:
        # An abort must not leave the caller guessing whether the post was
        # edited, so the line says which of the two it is.
        line = ("NOT VERIFIED edit %s" if state["sent"]
                else "NOT EDITING - ") % (args.sid if state["sent"] else "")
        return xkit.die("%saborted on %s: %s (the tab was left as it was; "
                        "nothing is claimed about the post)"
                        % (line, type(exc).__name__, str(exc)[:120]))
    finally:
        try:
            c.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
