#!/usr/bin/env python3
"""Send a direct message, or read the recent DM list, on the page already open.

A DM IS THE LEAST REVERSIBLE WRITE THIS SKILL PERFORMS. A reply, a quote, a
repost and a bookmark all land on the account's own timeline, where an author
can delete them and where a mistake is visible to whoever watches. A DM lands
in a NAMED PERSON'S INBOX, on a surface they read in private, with no public
undo and no way for the account to take it back. That is why sending one sits
behind --confirm alongside the social-graph writes rather than running on the
confidence of a well-formed argument: the gate is not about the message being
risky, it is about the destination being a human being who did not ask to be
part of a batch job.

Three refusals are decided from the ARGS ALONE, before connect() is called and
before a single byte crosses to the browser, because each of them is a
property of what was typed rather than of what is on screen:

  * Sending without --confirm costs nothing to detect and must cost nothing
    to refuse. Checked after the argument shape and the handle's shape, and
    before the browser is even asked whether it is running.
  * A handle carrying anything outside [A-Za-z0-9_] is not a handle. It is a
    URL, a mention with trailing punctuation, a copy-paste of a profile link,
    or a second handle pasted in by mistake — and each of those would be sent
    as a literal string into a box rather than rejected.
  * A body X will linkify is refused before typing, for the reason every
    other verb here refuses one: X rewrites a dotted token into a link span,
    and the span then reads back as a line break, so a body that reads
    correctly here ships with a sentence split in two. A DM has no public
    edit affordance, so there is no "fix it after".

--list REQUIRES THE CALLER TO ALREADY HAVE THE MESSAGES VIEW OPEN. Opening it
is a page load, and this skill forbids every page load: each one makes the
user confirm it in their own UI, which is a dialog they did not ask for in
the middle of a run they were told would be silent. The same rule shapes the
send path — the conversation with the target must already be on screen, and
this script will not open one, click the nav link, or type a handle into a
search box to start one. So the messages surface is DETECTED, never created,
and a run on the wrong page says so and stops. That is the whole difference
between a verb and a crawler.

THE HANDLE ASSERTION EXISTS BECAUSE A STALE LOG ONCE MATCHED ONE POST WITH A
HANDLE FROM A COMPLETELY DIFFERENT POST. The queue named a topic, a later
scraper re-read the timeline, and a run carried a handle forward from an
entry that had nothing to do with the message being sent. On a public post
that produces a wrong-but-public reply, which is embarrassing. In a DM it
produces a private message in a stranger's inbox about something they were
never part of, which is a different class of harm entirely. So the handle is
re-read from the conversation's OWN header immediately before typing, and a
mismatch aborts without a character being entered. A header that cannot be
read at all is treated as a mismatch: an unverified conversation is not a
conversation we are willing to send into.

Four selectors in this file are UNVERIFIED and are the least-verified in the
whole set, because no script in this skill has ever opened a DM surface:

  * the messages/DM nav link testid,
  * the conversation-list row container,
  * the DM composer's editor testid — the inline DM box may not reuse
    tweetTextarea_0 at all, and may be a bare [contenteditable="true"] or a
    [role="textbox"] instead,
  * the DM send control's testid or aria-label.

They are written so that being wrong is legible rather than silent: every
failure branch prints the testids, roles and aria-labels the page REALLY
carries, because a run that lists what it saw is what turns these four notes
into measurements, and "not found" is worth nothing to the next writer. The
verified ones are reused unchanged from files that have run: tweetTextarea_0
with public-DraftEditor-content, role="dialog", app-bar-close, and the walk
UP from the editor to its own send button.

The composer search is deliberately three-deep and in priority order — the
Draft editor first, then any visible contenteditable or role=textbox, then
one inside a dialog — because the DM box is expected to be INLINE rather than
in a modal. The send control is looked up by scoping UP from whichever box
was chosen, exactly as post_reply.py binds a reply box's own button: taking
the first enabled tweet button on the page sent through whatever composer
happened to be on screen, and in a DM that is the difference between messaging
one person and messaging whoever else is open.

Nothing here loads a page, opens a tab, clears a composer, takes the pointer
or the OS keyboard, or touches the clipboard. Scrolling for --list is
scrollBy, which moves the document and is not a navigation.

The lines a caller greps, each on its own:

    SENT dm HANDLE SID        (SID is the literal "no-id" when the DOM
                               exposes no message id, said plainly rather
                               than invented)
    NOT SENT dm HANDLE
    CONVERSATIONS N

plus the REFUSING / NOT THE MESSAGES VIEW / ABORT / NO CONVERSATION /
NO DM BOX lines, which are refusals and never successes.

  python3 x_dm.py <handle> <text_or_file> --confirm
  python3 x_dm.py --list 10
  python3 x_dm.py <handle> <text_or_file> --confirm --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xkit                                                # noqa: E402

# The marker put on the composer this run picked, so the focus read, the
# re-read and the send lookup all address the SAME node the search chose.
# post_reply.py sets window.__seenEditors for the same reason: the selection
# is re-derived identically in every template that needs it, and a template
# that re-derived it slightly differently would act on a different box.
BOX_MARK = "data-xdm-box"

# What every failure branch prints, so a run that changed nothing still says
# what it looked at. Presence of a control proves nothing about whether it
# worked, and a run that reports "not found" without the real names sends the
# next writer back to guessing.
SURFACE = """(() => {
  const vis = (n) => n.offsetParent !== null;
  const cap = (a, n) => a.slice(0, n);
  return JSON.stringify({
    path: location.pathname,
    title: (document.title || '').slice(0, 80),
    testids: cap([...new Set([...document.querySelectorAll('[data-testid]')]
      .map(x => x.dataset.testid).filter(Boolean))], 60),
    labels: cap([...new Set([...document.querySelectorAll('[aria-label]')]
      .map(x => x.getAttribute('aria-label')).filter(Boolean))], 40),
    roles: cap([...new Set([...document.querySelectorAll('[role]')]
      .map(x => x.getAttribute('role')).filter(Boolean))], 25),
    editables: [...document.querySelectorAll('[contenteditable="true"]')]
      .filter(vis).length,
    textboxes: [...document.querySelectorAll('[role="textbox"]')]
      .filter(vis).length,
    dialogs: [...document.querySelectorAll('[role="dialog"]')]
      .filter(vis).length
  });
})()"""

# Every bare-profile link on the page, with its own vertical position. This
# is deliberately shape-based (a link to "/name" and nothing else) rather than
# testid-based: no testid for a profile link inside a DM header has been
# verified, and the href shape has been stable on every surface in this skill.
WHO_LINKS = """(() => JSON.stringify(
  [...document.querySelectorAll('a[href^="/"]')]
    .filter(a => /^\\/[A-Za-z0-9_]{1,15}$/.test(a.getAttribute('href') || ''))
    .map(a => ({h: (a.getAttribute('href') || '').slice(1),
                top: Math.round(a.getBoundingClientRect().top)}))))()"""

# The handles in the topmost band of the page, which on the messages view is
# the conversation header. A band rather than a fixed selector: the header is
# the highest-scoring cluster of profile links, and taking a band around the
# highest one keeps the assertion honest when the user has scrolled.
HEADER_WHO = """(() => {
  const links = __LINKS__;
  if (!links.length) return JSON.stringify({ok: false,
    why: 'no profile link on the page at all'});
  const top = Math.min.apply(null, links.map(x => x.top));
  const band = [...new Set(links.filter(x => x.top <= top + 160)
                                 .map(x => x.h))];
  return JSON.stringify({ok: true, top: top, handles: band});
})()"""

# The conversation list, read by URL shape: a DM cell links to
# /messages/<conversation-id>. The row's own body is found by walking up
# until the ancestor says more than the anchor does — a container testid for
# a conversation cell is UNVERIFIED, so nothing here depends on one.
CONV_ROWS = """(() => {
  const seen = new Set(); const out = [];
  for (const a of document.querySelectorAll('a[href^="/messages/"]')) {
    const m = (a.getAttribute('href') || '').match(/^\\/messages\\/(\\d+)/);
    if (!m || seen.has(m[1])) continue;
    seen.add(m[1]);
    let cell = a, txt = (a.innerText || '').replace(/\\s+/g, ' ').trim();
    for (let i = 0; i < 6 && cell.parentElement; i++) {
      cell = cell.parentElement;
      const t = (cell.innerText || '').replace(/\\s+/g, ' ').trim();
      if (t.length > txt.length + 3) txt = t;
    }
    const handle = [...cell.querySelectorAll('a[href^="/"]')]
      .map(x => (x.getAttribute('href') || '').slice(1))
      .find(x => /^[A-Za-z0-9_]{1,15}$/.test(x))
      || (txt.startsWith('@') && /^[@A-Za-z0-9_]{1,16}$/
          .test(txt.split(/\\s+/)[0])
          ? txt.split(/\\s+/)[0].slice(1) : '');
    let preview = txt.replace(handle, '').replace(/^@/, '').trim();
    preview = preview.replace(/^\\d+[smhd]?$/, '').trim();
    out.push({cid: m[1], handle: handle, preview: preview.slice(0, 120)});
  }
  return JSON.stringify(out);
})()"""

# scrollBy, not a navigation. The window first; when the window itself does
# not scroll, the tallest scrolling ancestor is tried, because the messages
# list lives inside its own scroll container on some viewports.
SCROLL_BY = """(() => {
  const y = __Y__;
  window.scrollBy(0, y);
  if (window.scrollY > 0) return 'window';
  let best = null, most = 0;
  for (const n of document.querySelectorAll('div')) {
    if (n.scrollHeight - n.clientHeight > most
        && n.clientHeight > 200) { best = n; most = n.scrollHeight - n.clientHeight; }
  }
  if (!best) return 'nothing scrolls';
  best.scrollTop += y;
  return 'container';
})()"""

# The DM composer, in the three priority orders the flow tries. The Draft
# editor testid is VERIFIED (post_reply.py and x_quote.py both type into one);
# the generic contenteditable / role=textbox arms exist because an inline DM
# box has never been confirmed to reuse it.
PICK_BOX = """(() => {
  const vis = (n) => n.offsetParent !== null;
  for (const n of document.querySelectorAll('[%s]')) n.removeAttribute('%s');
  const clean = (n) => {
    let t = '';
    for (const k of n.childNodes) t += k.textContent || '';
    return t;
  };
  // (a) the Draft editor — verified testid, and the shape a DM box is
  // expected to have if it reuses the compose editor at all.
  let hit = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className
                 && n.className.indexOf('public-DraftEditor-content') >= 0
                 && vis(n))[0] || null;
  let kind = 'draft';
  // (b) any visible contenteditable or role=textbox in the messages view.
  if (!hit) {
    hit = [...document.querySelectorAll(
      '[contenteditable="true"], [role="textbox"]')].filter(vis)[0] || null;
    kind = 'editable';
  }
  // (c) one inside a dialog, for the modal DM surface.
  if (!hit) {
    const d = [...document.querySelectorAll('[role="dialog"]')].filter(vis)
      .filter(x => x.querySelector('[contenteditable="true"], [role="textbox"]'))[0];
    hit = d ? d.querySelector('[contenteditable="true"], [role="textbox"]') : null;
    kind = 'dialog';
  }
  if (!hit) return JSON.stringify({ok: false,
    why: 'no visible editor, contenteditable or textbox on this page'});
  hit.setAttribute('%s', '1');
  const t = clean(hit);
  return JSON.stringify({ok: true, kind: kind, len: t.length, text: t,
    in_dialog: !!hit.closest('[role="dialog"]'),
    testid: hit.getAttribute('data-testid') || '',
    role: hit.getAttribute('role') || '',
    aria: hit.getAttribute('aria-label') || '',
    focused: hit === document.activeElement});
})()"""

# Re-read the marked box. The text is taken from the child NODES, not
# innerText, for the reason xkit.EDITORS does it: Draft keeps its own hidden
# text nodes and innerText reports them.
BOX_STATE = """(() => {
  const e = document.querySelector('[%s]');
  if (!e) return JSON.stringify({ok: false, why: 'the box is no longer marked'});
  let t = '';
  for (const k of e.childNodes) t += k.textContent || '';
  return JSON.stringify({ok: true, len: t.length, text: t,
    focused: e === document.activeElement,
    in_dialog: !!e.closest('[role="dialog"]'),
    testid: e.getAttribute('data-testid') || '',
    role: e.getAttribute('role') || ''});
})()"""

# In-page focus, never OS focus and never a click: el.focus() moves the
# document's own caret and takes nothing from the user.
FOCUS_BOX = """(() => {
  const e = document.querySelector('[%s]');
  if (!e) return 'NO_BOX';
  e.focus();
  return e === document.activeElement ? 'FOCUSED' : 'FOCUS_REFUSED';
})()"""

# The send control, scoped UP from the marked box. Identical walk to
# post_reply.py's: the dialog that holds it, else its own form, else its
# parent, each step outwards, and never the first enabled button on the page.
# The aria-label / testid arm is the UNVERIFIED one — a DM composer may carry
# no tweetButton at all, in which case the only way to find its send control
# is by what it is called.
SEND_UP = """(() => {
  const e = document.querySelector('[%s]');
  if (!e) return JSON.stringify({sent: false, why: 'the box is no longer marked'});
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null && d.contains(e));
  let scope = dialogs[0] || e.closest('form') || e.parentElement;
  const seen = [];
  while (scope && scope !== document.body) {
    const btns = [...scope.querySelectorAll('button[data-testid], button')];
    const hit = btns.find(x => /^tweetButton/.test(x.dataset.testid || '')
                              && !x.disabled)
             || btns.find(x => {
                  const t = ((x.dataset.testid || '') + ' '
                             + (x.getAttribute('aria-label') || '')).toLowerCase();
                  return !x.disabled && /(send|发送|发送消息|发送讯息)/.test(t)
                         && x.offsetParent !== null; });
    if (hit) { hit.click(); return JSON.stringify({sent: true,
      which: hit.dataset.testid || null,
      aria: hit.getAttribute('aria-label') || null}); }
    seen.push(...btns.map(x => x.dataset.testid || null).filter(Boolean));
    scope = scope.parentElement;
  }
  return JSON.stringify({sent: false,
    why: 'no send control inside the box itself',
    seen_testids: [...new Set(seen)].slice(0, 30)});
})()"""

# The sent message, read back out of the thread. The composer is EXCLUDED,
# and that exclusion is the whole point: a send that silently failed leaves
# the text sitting in the box, and a verify that searched the page without
# excluding the box would read that draft as the message having landed.
THREAD_HITS = """(() => {
  const want = __WANT__;
  const norm = (s) => (s || '').replace(/\\s+/g, '');
  const boxes = [...document.querySelectorAll('[%s]')];
  const inBox = (n) => boxes.some(b => b === n || b.contains(n));
  const cands = [...new Set([...document.querySelectorAll(
    '[data-testid="messageEntry"], [data-testid^="message"], '
    + '[data-testid="cellInnerDiv"]')])];
  const rows = cands.filter(n => n.offsetParent !== null && !inBox(n));
  for (const n of rows) {
    const t = norm(n.innerText);
    if (!t) continue;
    if (norm(t).indexOf(want) < 0) continue;
    const st = [...n.querySelectorAll("a[href*='/status/']")]
      .map(a => (a.getAttribute('href') || ''))
      .find(h => /\\/status\\/(\\d+)/.test(h) && !/\\/(analytics|photo|video)/
        .test(h));
    const mid = [...n.querySelectorAll("[id]")].map(x => x.id)
      .find(i => /^(msg|dm|message)[-_]/i.test(i)) || '';
    return JSON.stringify({ok: true, text: n.innerText.replace(/\\s+/g, ' ').trim(),
      sid: st ? st.match(/\\/status\\/(\\d+)/)[1] : '', mid: mid,
      testids: [...new Set([...n.querySelectorAll('[data-testid]')]
        .map(x => x.dataset.testid))].slice(0, 20)});
  }
  return JSON.stringify({ok: false, candidates: rows.length,
    testids: [...new Set([...document.querySelectorAll('[data-testid]')]
      .map(x => x.dataset.testid).filter(Boolean))].slice(0, 60)});
})()"""

UNMARK = """(() => {
  for (const n of document.querySelectorAll('[%s]')) n.removeAttribute('%s');
  return 'unmarked';
})()"""


def rows(raw) -> list:
    """A list-returning template's answer as a list, or [].

    xkit.js() unwraps a JSON string into a DICT, and a list inside that dict
    is not what a caller iterates over — the mismatch reads as "nothing on the
    page" rather than as a bug, which is how a verified send gets reported as
    a failure. So the list templates go through js_raw and are parsed here.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return []
    return raw if isinstance(raw, list) else []


def obj(raw) -> dict:
    """A dict-returning template's answer, or {'why': ...} when it is not.

    Every template here ends in JSON.stringify, so the answer arrives as a
    STRING; xkit.js() unwraps that string into a dict, but js_raw() does not,
    and a string that is never parsed reads as a total failure of the read
    rather than as the bug it is. So parse it here.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return {"why": "unreadable page answer: %s" % raw[:80]}
    return raw if isinstance(raw, dict) else {"why": "unreadable page answer"}


def stop(c, msg: str, code: int = 1) -> int:
    """Print the last line, close the session, return the exit code.

    Everything this script refuses or fails at ends here, so there is one
    place that closes the socket and one place that decides the status. The
    message goes last: the final line of the output is what a cron log is read
    for, and a run that did nothing must never exit 0.
    """
    print(msg, flush=True)
    if c is not None:
        try:
            c.close()
        except Exception:
            pass
    return code


def normalise(raw: str) -> str:
    """The handle without its leading '@', or '' when it is not a handle."""
    h = (raw or "").strip().lstrip("@")
    return h if re.fullmatch(r"[A-Za-z0-9_]{1,15}", h) else ""


def who_links(c) -> list:
    """Every bare-profile link on the page, with its vertical position."""
    return rows(xkit.js_raw(c, WHO_LINKS, wait=25, retries=4))


def surface_line(c) -> str:
    """What the page really carries, for a run that changed nothing."""
    s = obj(xkit.js_raw(c, SURFACE, wait=25, retries=4))
    if s.get("why") or not s.get("testids"):
        return "  the page could not be read: %s" % (s.get("why") or "nothing")
    return ("  path=%s  editables=%s textboxes=%s dialogs=%s\n"
            "  testids: %s\n  aria-labels: %s\n  roles: %s"
            % (s.get("path"), s.get("editables"), s.get("textboxes"),
               s.get("dialogs"), s.get("testids"), s.get("labels"),
               s.get("roles")))


def messages_surface(c) -> bool:
    """True when this page is a messages/DM surface.

    The route is the signal because it is the only part of this file's
    detection that is not a guess about markup: /messages is what the app
    calls its DM surface everywhere else too. The DOM arms underneath are
    belt and braces for the builds that render a DM view on another route.
    """
    p = obj(xkit.js_raw(c, SURFACE, wait=25, retries=4))
    if p.get("why"):
        return False
    if str(p.get("path") or "").startswith("/messages"):
        return True
    tids = set(p.get("testids") or [])
    return bool(tids & {"messageEntry", "primaryColumn"}) and bool(
        str(p.get("path") or "").startswith("/i/"))


# --- --list ---------------------------------------------------------------

def do_list(c, want: int) -> int:
    """Read up to `want` conversations off the open list. Exit code."""
    if not messages_surface(c):
        print("NOT THE MESSAGES VIEW - open Messages yourself and re-run; "
              "this script loads no page", flush=True)
        print(surface_line(c), flush=True)
        return stop(c, "NOT THE MESSAGES VIEW - open Messages yourself and "
                       "re-run; this script loads no page")

    found: dict = {}
    for round_ in range(6):
        for row in rows(xkit.js_raw(c, CONV_ROWS, wait=25, retries=4)):
            cid = row.get("cid")
            if cid and cid not in found:
                found[cid] = row
            if len(found) >= want:
                break
        if len(found) >= want:
            break
        if round_ == 5:
            break
        # scrollBy moves the document and is not a navigation. Stopping on a
        # "nothing scrolls" answer matters: an infinite loop on a list that
        # does not scroll reads as patience and is not.
        moved = xkit.js_raw(c, SCROLL_BY.replace("__Y__", json.dumps(900)),
                            wait=20, retries=3)
        time.sleep(2.0)
        if moved == "nothing scrolls":
            break

    out = list(found.values())[:want]
    if not out:
        print("  no conversation rows could be read from this surface",
              flush=True)
        print(surface_line(c), flush=True)
        return stop(c, "CONVERSATIONS 0")

    for row in out:
        print("@%s  %s" % (row.get("handle") or "?",
                           (row.get("preview") or "").replace("\n", " ")[:90]),
              flush=True)
    if len(found) < want:
        print("  the list yielded %d of the %d asked for; scrolling stopped "
              "where the surface stopped" % (len(found), want), flush=True)
    print("CONVERSATIONS %d" % len(out), flush=True)
    try:
        c.close()
    except Exception:
        pass
    return 0


# --- sending --------------------------------------------------------------

def assert_conversation(c, want: str) -> dict:
    """The handle in the conversation's own header, checked against `want`.

    This is the stale-log guard and it runs BEFORE a character is typed. A
    header that cannot be read is reported as a failure rather than skipped:
    an unreadable conversation is not one this script will send into.
    """
    links = who_links(c)
    if not links:
        return {"ok": False, "why": "no conversation header on this page",
                "actual": "?"}
    band = obj(xkit.js_raw(
        c, HEADER_WHO.replace("__LINKS__", json.dumps(links)),
        wait=25, retries=4))
    handles = [h for h in (band.get("handles") or []) if h]
    if not handles:
        return {"ok": False, "why": "the header names no readable handle",
                "actual": "?"}
    match = [h for h in handles if h.lower() == want.lower()]
    return {"ok": bool(match), "actual": handles[0], "handles": handles,
            "why": "" if match else
            "the header names %s" % ", ".join("@" + h for h in handles[:4])}


def pick_box(c) -> dict:
    """The DM composer, marked for the focus, read and send passes."""
    return obj(xkit.js_raw(c, PICK_BOX.replace("%s", BOX_MARK), wait=25,
                           retries=4))


def box_state(c) -> dict:
    """What the marked box holds right now."""
    return obj(xkit.js_raw(c, BOX_STATE.replace("%s", BOX_MARK), wait=25,
                           retries=4))


def unmark(c) -> None:
    """Drop the marker, so nothing later addresses this run's box."""
    try:
        xkit.js_raw(c, UNMARK.replace("%s", BOX_MARK), wait=15, retries=2)
    except Exception:
        pass


def do_send(c, me: str, handle: str, text: str, confirm: bool,
            dry_run: bool) -> int:
    """The whole send path. Returns the process exit code."""
    if me and handle.lower() == me.lower():
        return stop(c, "REFUSING - that is this account; not sending a DM to "
                       "yourself")

    assertion = assert_conversation(c, handle)
    if not assertion.get("ok"):
        # Not a match, AND not readable, take the same branch: no character
        # is entered until the header says whose conversation this is.
        print("ABORT - asked about @%s but this conversation is with @%s"
              % (handle, assertion.get("actual") or "?"), flush=True)
        if assertion.get("why"):
            print("  %s" % assertion["why"], flush=True)
        print(surface_line(c), flush=True)
        return stop(c, "ABORT - asked about @%s but this conversation is with "
                       "@%s" % (handle, assertion.get("actual") or "?"))

    print("  conversation assertion: header says @%s, asked about @%s"
          % (assertion.get("actual"), handle), flush=True)

    box = pick_box(c)
    if not box.get("ok"):
        print("NO DM BOX", flush=True)
        print("  %s" % (box.get("why") or "nothing to type into"), flush=True)
        print(surface_line(c), flush=True)
        return stop(c, "NO DM BOX - no composer on this page; nothing typed")

    print("  DM box: kind=%s testid=%r role=%r in_dialog=%s len=%s"
          % (box.get("kind"), box.get("testid") or "", box.get("role") or "",
             box.get("in_dialog"), box.get("len")), flush=True)

    if (box.get("len") or 0) != 0:
        # Never cleared. Clearing raises Chrome's unsaved-changes dialog,
        # which then blocks every later CDP call — and the draft in a DM box
        # is the user's own words, not automation's debris.
        if box.get("in_dialog"):
            print("  the DM box already holds %s characters; closing this "
                  "dialog and re-checking, that draft is not ours to clear"
                  % box.get("len"), flush=True)
            xkit.js(c, xkit.CLOSE_BOX)
            time.sleep(2.5)
            unmark(c)
            box = pick_box(c)
        else:
            return stop(c, "REFUSING - the DM box already holds text; that "
                           "draft is not ours to clear")
        if not box.get("ok") or (box.get("len") or 0) != 0:
            unmark(c)
            print(surface_line(c), flush=True)
            return stop(c, "REFUSING - no empty DM box; that draft is not "
                           "ours to clear")

    if dry_run:
        # No send line is printed here on purpose: a dry run must not put
        # "SENT dm" anywhere a grepping caller could read it as a send.
        print("DRY RUN dm %s - nothing typed, nothing sent (--confirm %s)"
              % (handle, "given" if confirm else "NOT given"), flush=True)
        print("  would type %d characters into the %s box and verify the "
              "thread afterwards" % (len(text), box.get("kind")), flush=True)
        unmark(c)
        try:
            c.close()
        except Exception:
            pass
        return 0

    focus = xkit.js_raw(c, FOCUS_BOX.replace("%s", BOX_MARK), wait=20, retries=3)
    if focus != "FOCUSED":
        # The Draft editor has its own focus helper, already used by every
        # other verb in this skill; try it before giving up on a box that
        # carries the verified testid.
        if box.get("kind") == "draft":
            focus = ("FOCUSED" if xkit.js_raw(c, xkit.FOCUS_EDITOR, wait=20,
                                              retries=3) else "FOCUS_REFUSED")
        if focus != "FOCUSED":
            unmark(c)
            return stop(c, "NOT SENDING - the DM box would not take focus "
                           "(%s)" % focus)

    print("  typing %d characters" % len(text), flush=True)
    xkit.type_body(c, text)
    xkit.remove_warmup(c, text.lstrip())

    held = box_state(c)
    got, want = xkit.canon(held.get("text") or ""), xkit.canon(text)
    if got != want:
        print("  the box does not hold what was typed:", flush=True)
        print("    got %d characters, source has %d" % (len(got), len(want)),
              flush=True)
        for i, (a, b) in enumerate(zip(got, want)):
            if a != b:
                print("    first difference at %d: got %r want %r"
                      % (i, a, b), flush=True)
                break
        else:
            print("    one is a prefix of the other — nothing was invented, "
                  "but something was lost", flush=True)
        unmark(c)
        return stop(c, "NOT SENDING - text mismatch")

    # canon() drops whitespace, so it cannot see a warm-up space that
    # remove_warmup failed to delete on a non-Draft box. The raw head is
    # printed so that residue is visible rather than assumed away.
    print("  LEN %s want %s exact=True head=%r"
          % (held.get("len"), len(text), (held.get("text") or "")[:4]),
          flush=True)

    res = obj(xkit.js_raw(c, SEND_UP.replace("%s", BOX_MARK), wait=25,
                          retries=3))
    for _ in range(6):
        if res.get("sent"):
            break
        time.sleep(3)
        res = obj(xkit.js_raw(c, SEND_UP.replace("%s", BOX_MARK), wait=25,
                              retries=3))
    c.close_composition("")        # never leave a composition open behind
    unmark(c)
    print("  SEND %s" % res, flush=True)
    if not res.get("sent"):
        print("  testids met on the way up: %s" % (res.get("seen_testids") or []),
              flush=True)
        return stop(c, "NOT SENT dm %s" % handle)

    # Read the conversation back. The composer is excluded from THREAD_HITS,
    # so a send that did nothing cannot be read as a send that did.
    prefix = xkit.canon(text)[:40]
    time.sleep(5)
    hit = {}
    for _ in range(5):
        got_row = obj(xkit.js_raw(
            c, THREAD_HITS.replace("__WANT__", json.dumps(prefix)),
            wait=30, retries=3))
        if got_row.get("ok"):
            hit = got_row
            break
        time.sleep(4)
    if not hit:
        diag = obj(xkit.js_raw(c, THREAD_HITS.replace(
            "__WANT__", json.dumps("@@@no-such-message@@@")),
            wait=20, retries=2))
        print("  the thread carried no message with this text after 5 reads",
              flush=True)
        print("  message-shaped nodes read: %s; testids on the page: %s"
              % (diag.get("candidates"), diag.get("testids") or []),
              flush=True)
        return stop(c, "NOT SENT dm %s" % handle)

    sid = hit.get("sid") or hit.get("mid") or ""
    if not sid:
        # Said plainly rather than invented: a caller that greps the SENT line
        # must be able to trust that field, and a made-up id would be read as
        # evidence the send is verified on a surface it was not verified on.
        print("  the message is in the thread but the DOM exposes no id for "
              "it (no /status/ link and no message id attribute)", flush=True)
        sid = "no-id"
    print("  VERIFIED dm to @%s (%s) in the thread" % (handle, sid), flush=True)
    try:
        c.close()
    except Exception:
        pass
    print("SENT dm %s %s" % (handle, sid), flush=True)
    return 0


# --- entry point ----------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Send a DM, or read the recent DM list, on the open page.")
    ap.add_argument("handle", nargs="?",
                    help="target handle, with or without a leading @")
    ap.add_argument("text", nargs="?", metavar="TEXT_OR_FILE",
                    help="the message, or the path to a file holding it")
    ap.add_argument("--list", type=int, metavar="N", default=0,
                    help="read up to N recent conversations instead of sending")
    ap.add_argument("--confirm", action="store_true",
                    help="required to send: a DM lands in a real inbox")
    ap.add_argument("--dry-run", action="store_true",
                    help="report the plan and change nothing")
    args = ap.parse_args()

    # Every gate below is decided from the arguments alone. connect() is not
    # called until they all pass, so a refused run costs no browser
    # round-trip and cannot have touched the page.
    #
    # A handle on its own is not a request to do anything: `x_dm.py someone`
    # names a target and supplies no message, and falling through to the
    # browser for it costs a round-trip and then fails inside connect() with
    # a message about the browser rather than about the missing text.
    sending = args.text is not None and args.handle is not None
    if not sending and not args.list:
        return stop(None, "REFUSING - give a handle and text to send, or "
                          "--list N to read")

    handle = ""
    if args.handle is not None:
        handle = normalise(args.handle)
        if not handle:
            return stop(None, "REFUSING - %s is not a valid handle"
                        % args.handle)

    if args.list and args.list < 1:
        return stop(None, "REFUSING - --list takes a count of 1 or more")

    text = ""
    if sending:
        if not args.confirm:
            return stop(None, "REFUSING - sending a DM to @%s needs "
                              "--confirm; a message lands in a real person's "
                              "inbox and cannot be recalled" % handle)
        # `sending` is true only when both positionals are present; the
        # assertion restates that in the form a reader (and a type checker)
        # can check, rather than relying on the boolean above.
        assert args.text is not None
        text = xkit.read_text_or_file(args.text)
        stray = xkit.stray_linkifiers(text)
        if stray:
            return stop(None, "REFUSING - %s will be linkified and read back "
                              "broken" % ", ".join(sorted(set(stray))))
        if not text.strip():
            return stop(None, "REFUSING - the message is empty")
        if len(text) > xkit.POST_LIMIT:
            return stop(None, "REFUSING - %d characters, over the %d limit"
                        % (len(text), xkit.POST_LIMIT))

    try:
        c, _tab, me = xkit.connect()
    except Exception as exc:
        # connect() reads the tab list over HTTP first, and a browser that is
        # not running answers with a connection error rather than an empty
        # list. Unhandled it is a traceback on the most ordinary invocation
        # there is — the browser closed, or never opened.
        print(xkit.no_browser(), flush=True)
        print("  (reading the tab list failed: %s)" % str(exc)[:80],
              flush=True)
        return 1
    if c is None:
        return 1

    try:
        if args.list:
            return do_list(c, args.list)
        if not args.dry_run:
            print("  sending a %d-character DM to @%s" % (len(text), handle),
                  flush=True)
        return do_send(c, me, handle, text, args.confirm, args.dry_run)
    except Exception as exc:
        # The state after an unexpected error is UNKNOWN, which is not sent.
        # A driver traceback is not a message a caller can act on, so the
        # verdict line is printed and the reason follows it.
        unmark(c)
        if args.list:
            return stop(c, "CONVERSATIONS 0")
        print("  the run ended early: %s" % str(exc)[:160], flush=True)
        return stop(c, "NOT SENT dm %s" % handle)
    finally:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
