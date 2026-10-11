#!/usr/bin/env python3
"""Shared plumbing for the x_*.py scripts: the verbs, not the actions.

The skill grew a family of scripts — quote, repost, edit, media, bookmark,
profile, thread, dm — and every one of them needs the same five things before
it can touch anything: the site tab, an activated target, the live account
handle, the owning article for a status id, and the button-state read that
decides whether an action actually happened. Each of those was got wrong at
least once by a script that had its own copy of it, so there is one copy here
and the verbs import it.

What the copies got wrong, and why this file is shaped the way it is:

  * A target that is not activated never mounts an editor. `visibilityState
    === "hidden"` is enough: the flow navigates to /compose/post, sits there
    with 0 dialogs and 0 editors, and reads as "the button does nothing".
    `Target.activateTarget` moves no pointer and takes no OS focus, which is
    why it is legal here and `Page.bringToFront` is not, and it runs at the
    top of every entry point rather than at the point of failure.

  * A status id is not a post. A quoted post, the post a reply answers, and a
    post inside a retweet all carry the target's status link, so
    `a[href*="/status/<id>"]` matches the WRONG article — which is how a run
    reported a stranger's text as this account's own. OWNING below matches the
    article whose OWN time link points at the id and which is not itself a
    quote container.

  * The click is not the event. `like_posts.py` uses a bare `element.click()`
    on the like control and it works; the reply control needs the full
    mousedown/mouseup/click sequence from `post_reply.py`, and even that
    measured as unreliable on this build. The two are not interchangeable, so
    `click_action` and `open_box` are separate functions and a caller has to
    say which one it means.

  * Templates end in both styles. `publish.py`'s EDITOR returns an object,
    `like_posts.py`'s STATE returns a JSON string, and the wrappers differ. A
    wrapper that unwrapped only one shape turned `{"opened":true}` into
    `{"_raw": '{"opened":true}'}`, so every question asked of it read as "no",
    and the reply box was reported NOT SENDING on every single run while it sat
    there focused and ready. `js()` here unwraps both.

Nothing here loads a page, clears a composer, takes the mouse or the OS
keyboard, or reads a credential. Scrolling is `window.scrollTo`, which is not
a navigation.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as C                                          # noqa: E402
import handle                                            # noqa: E402
import xconfig                                           # noqa: E402

DRAFT_CLS = "public-DraftEditor-content"

# Publish.py's member ceiling, not the 280 free-tier number. 280 was written
# into a gate once "to be safe" and it trimmed replies to a fifth of an answer
# before anyone checked what tier the account was on.
POST_LIMIT = 25000

# Error markers cdp.js returns instead of a value. A silent None is what made
# an earlier round conclude "the click did nothing" when the reply had simply
# been lost, so they are named here once and every wrapper strips them.
MARKERS = ("__js_error", "__socket_error", "__timeout", "__cdp_error")


# --- connection ---------------------------------------------------------

def no_browser(msg: str = "") -> str:
    """The message every entry point prints when there is nothing to drive."""
    host = xconfig.site()
    return (msg or
            "no %s tab — the browser is not running. Start it with "
            "ensure_browser.py %s (port %s) and open the tab yourself; this "
            "script loads no page, so it cannot open one."
            % (host, xconfig.port(), xconfig.port()))


def connect(require_visible: bool = True):
    """The site tab, activated, with the account handle read from it.

    Returns (Cdp, tab, handle) or (None, None, "") with the reason already
    printed. Nothing is typed before this returns ok.

    The handle comes from the nav bar, never from a constant: the account was
    renamed once and every hardcoded copy of the old name broke differently —
    reply verification stopped matching the account's own replies and the feed
    filters stopped excluding its own posts, so a run replied to its own
    promotional posts.
    """
    C.set_port(xconfig.port())
    tabs = [t for t in C.tabs("page") if xconfig.is_site_tab(t.get("url", ""))]
    if not tabs:
        print(no_browser(), flush=True)
        return None, None, ""
    tab = tabs[0]
    try:
        c = C.Cdp(tab["webSocketDebuggerUrl"])
    except Exception as exc:
        print("could not open a CDP session on %s: %s"
              % (tab.get("url", "")[:60], exc), flush=True)
        return None, None, ""

    # Required, not optional. A background target does not mount the editor.
    # This moves no pointer and takes no OS focus, which Page.bringToFront
    # would.
    try:
        c.send("Target.activateTarget", targetId=tab.get("id"), wait=8)
    except Exception:
        pass

    me = handle.live(c) or xconfig.handle_fallback()
    if require_visible:
        vis = c.js("document.visibilityState", wait=15, retries=3)
        if isinstance(vis, str) and vis and vis != "visible":
            # Try once more after a re-activate; a target activated during a
            # renderer swap can report hidden for a moment.
            try:
                c.send("Target.activateTarget", targetId=tab.get("id"), wait=8)
            except Exception:
                pass
            time.sleep(1.5)
            vis = c.js("document.visibilityState", wait=15, retries=3)
        if isinstance(vis, str) and vis and vis != "visible":
            print("the %s tab reports visibilityState=%s. Nothing is typed "
                  "into a hidden target — its editor never mounts. Bring the "
                  "window forward by hand and run again." % (xconfig.site(), vis),
                  flush=True)
            c.close()
            return None, None, ""
    return c, tab, me


# --- evaluation ---------------------------------------------------------

def js(c, tpl: str, **subs):
    """Evaluate a template, always handing back a dict.

    Never raises and never returns a bare string, because every caller here
    asks a structured question and a bare string has to stay visible as a
    failure instead of disappearing into a dict nobody checks. Both shapes are
    unwrapped: some templates end in JSON.stringify() and return a string,
    some return the object itself.
    """
    for k, v in subs.items():
        tpl = tpl.replace("__%s__" % k.upper(), json.dumps(v))
    try:
        r = c.js(tpl, wait=25, retries=5)
    except Exception as exc:
        return {"why": "evaluate failed: %s" % str(exc)[:120]}
    if isinstance(r, str):
        try:
            r = json.loads(r)
        except ValueError:
            return {"_raw": r[:160]}
    if isinstance(r, dict):
        return {k: v for k, v in r.items() if k not in MARKERS}
    return {"_raw": str(r)[:160]}


def js_raw(c, expr: str, wait: int = 25, retries: int = 5):
    """Evaluate a plain expression and return whatever it produced."""
    try:
        return c.js(expr, wait=wait, retries=retries)
    except Exception as exc:
        return {"why": "evaluate failed: %s" % str(exc)[:120]}


def canon(s: str) -> str:
    """Source and page text reduced to a comparable form.

    Whitespace goes everywhere and every URL span becomes one marker, for two
    measured reasons. X rewrites a URL as a t.co shortener, so the source's
    host is never on the page; and the renderer reflows the body, so a
    newline lands between two tokens that were space-separated in the source.
    What is left is the non-space characters, and those must match exactly —
    a dropped or mangled character cannot hide behind a space.
    """
    s = re.sub(r"\S*(?:https?://\S+|t\.co/\S+)", "\x00", s or "")
    return "".join(s.split())


def stray_linkifiers(text: str) -> list:
    """Dotted tokens X will turn into links even though they are not URLs.

    X linkifies any dotted token, and the span it replaces then reads back as a
    line break — a bare "crates.io" in a body split a sentence in two and it
    shipped twice before this check existed.
    """
    return [w for w in re.findall(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}", text or "")]


# The OWNING article for a status id: the one whose own time link points at
# that id and which is not itself a quote container. Matching "any status
# link" picks up a quoted post, the post a reply answers, or the inner post of
# a retweet — measured, and it is how a run reported a stranger's links for a
# post of this account's own. verify_post.py states the same rule.
ARTICLE = """(() => {
  const pick = (a) => {
    if (a.querySelector('[data-testid="quoteTweet"]')) return null;
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    return st ? a : null;
  };
  for (const a of document.querySelectorAll('article')) {
    const own = pick(a);
    if (!own) continue;
    const who = own.querySelector("a[href^='/']");
    // tweetText is a display layer and is CLIPPED: it stops mid-sentence and
    // carries no "show more" of its own, so its text is a PREFIX of the post.
    // Walking the subtree puts each link's own text back where the link sits.
    const walk = (n) => {
      let s = '';
      for (const k of n.childNodes) {
        if (k.nodeType === 3) s += k.textContent;
        else if (k.nodeName === 'BR') s += '\\n';
        else s += walk(k);
      }
      return s;
    };
    const box = own.querySelector('[data-testid="tweetText"]');
    let body = box ? walk(box) : (own.innerText || '');
    const full = own.innerText || '';
    const qt = own.querySelector('[data-testid="quoteTweet"]');
    return JSON.stringify({
      sid: __SID__,
      who: who ? who.getAttribute('href').split('/').pop() : '?',
      text: body,
      // A quote renders the quoted post inside the quoting one; the
      // attribution is a trailing "@handle · <text>" on X.
      has_quote: !!qt,
      quoted_who: qt ? ((qt.querySelector("a[href^='/']") || {}).getAttribute
              ? qt.querySelector("a[href^='/']").getAttribute('href')
                .split('/').pop() : '') : '',
      quoted_text: qt ? (qt.innerText || '').replace(/\\s+/g, ' ').trim() : '',
      time: (own.querySelector('time') || {}).dateTime || '',
      collapsed: /显示更多|Show more|顯示更多/.test(full.slice(0, 400)),
      testids: [...new Set([...own.querySelectorAll('[data-testid]')]
               .map(x => x.dataset.testid))]
    });
  }
  return 'NOT ON PAGE';
})()"""

# Every visible article by this account, with its own status id. This is the
# surface a sent post is verified on: post_reply.py's reply is invisible on
# the target's status page (the count moves, the article stays folded by
# ranking) and the timeline puts a new post at the TOP, so the caller scrolls
# to 0 first — which is a scroll, not a navigation.
MINE = """(() => {
  const walk = (n) => {
    let s = '';
    for (const k of n.childNodes) {
      if (k.nodeType === 3) s += k.textContent;
      else if (k.nodeName === 'BR') s += '\\n';
      else s += walk(k);
    }
    return s;
  };
  const out = [];
  for (const a of document.querySelectorAll('article')) {
    const who = a.querySelector("a[href^='/']");
    if (!who || who.getAttribute('href').split('/').pop() !== __WHO__) continue;
    const st = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href')));
    if (!st) continue;
    const box = a.querySelector('[data-testid="tweetText"]');
    out.push({sid: st.getAttribute('href').split('/').pop(),
              text: box ? walk(box) : '',
              has_quote: !!a.querySelector('[data-testid="quoteTweet"]'),
              quoted_who: (() => { const q =
                a.querySelector('[data-testid="quoteTweet"]'); if (!q) return '';
                const l = q.querySelector("a[href^='/']");
                return l ? l.getAttribute('href').split('/').pop() : ''; })()});
  }
  return JSON.stringify(out);
})()"""


def read_article(c, sid: str):
    """The owning article for `sid`, or {'why': ...}."""
    got = js_raw(c, ARTICLE.replace("__SID__", json.dumps(sid)), wait=30)
    if got == "NOT ON PAGE" or not isinstance(got, str):
        return {"why": "status %s is not on this page — open its thread "
                       "first, or scroll it into view" % sid}
    try:
        return json.loads(got)
    except ValueError:
        return {"why": "unreadable article: %s" % str(got)[:120]}


def scroll_to_top(c, tries: int = 3, pause: float = 2.5) -> None:
    """Back to the top of the timeline before reading it for a new post.

    A post that was just sent appears at the TOP, and a script that scrolled
    down to reach its target leaves the feed scrolled past the very post it
    was about to verify — one run sent a reply, scrolled up, found it, and
    reported NOT VERIFIED because the read happened first.
    """
    for _ in range(tries):
        js_raw(c, "window.scrollTo(0, 0); true", wait=20, retries=3)
        time.sleep(pause)


# --- action buttons -----------------------------------------------------

# A bare element.click() on the like control works and is what like_posts.py
# has always done. It is NOT what the reply control needs, so the two are kept
# apart rather than folded into one helper.
TOGGLE = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!own) continue;
    const btn = own.querySelector('[data-testid="__KIND__"]');
    if (!btn) return {clicked: false, why: 'no ' + '__KIND__' + ' control'};
    if (btn.offsetParent === null) return {clicked: false, why: 'control is hidden'};
    const box = btn.getBoundingClientRect();
    if (!box.width) return {clicked: false, why: 'control has no size'};
    if (box.top < 0 || box.top > window.innerHeight) {
      window.scrollTo(0, Math.max(0,
        window.scrollY + box.top - window.innerHeight / 2));
      return {clicked: false, why: 'control was off screen, scrolled to it'};
    }
    btn.click();
    return {clicked: true, was: btn.dataset.testid};
  }
  return {clicked: false, why: 'status not on page'};
})()"""

# The whole action row, read back. Presence of a control proves nothing — the
# like control exists whether the post is liked or not — so the state is the
# testid that is mounted afterwards, and every testid on the article comes
# back with it so a run that finds nothing can dump the real ones instead of
# guessing.
ACTION_STATE = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!own) continue;
    const testids = [...new Set([...own.querySelectorAll('[data-testid]')]
                   .map(x => x.dataset.testid))];
    const labels = [...own.querySelectorAll('[aria-label]')]
      .map(x => x.getAttribute('aria-label')).filter(Boolean);
    return JSON.stringify({sid: __SID__, testids: testids, labels: labels,
      has: (t) => testids.indexOf(t) >= 0});
  }
  return JSON.stringify({why: 'status not on page', testids: [], labels: []});
})()"""

# Which testid means "already on". Every entry whose "on" testid is not in any
# script in this skill is flagged in the report rather than presented as fact:
# a guessed testid that silently does nothing is worse than one marked unknown.
TOGGLE_KINDS = {
    "like":  {"off": ["like"],  "on": ["unlike"],
              "on_label": ("取消喜欢", "Undo like", "已喜欢")},
    "retweet": {"off": ["retweet"], "on": ["unretweet"],
                "on_label": ("取消转帖", "取消转发", "Undo repost")},
    "bookmark": {"off": ["bookmark"], "on": ["removeBookmark"],
                 "on_label": ("移除书签", "Remove bookmark", "已添加书签")},
}


def action_state(c, sid: str) -> dict:
    """Every control the owning article currently mounts, by testid."""
    return js(c, ACTION_STATE, sid=sid)


def is_on(state: dict, kind: str) -> bool:
    """True when the action is already in its "on" state.

    The testid is the signal; the aria-label is the fallback for the builds
    where the "on" control carries a different testid. Returns False when the
    surface said nothing at all, so a missing control can never read as "on".
    """
    spec = TOGGLE_KINDS[kind]
    have = state.get("testids") or []
    if any(t in have for t in spec["on"]):
        return True
    labels = state.get("labels") or []
    return any(any(w in (l or "") for w in spec["on_label"]) for l in labels)


def set_action(c, sid: str, kind: str, want_on: bool) -> dict:
    """Read the state, click only when it disagrees, read it again.

    Idempotent by construction: a second run on an already-bookmarked post
    reads `on` and returns `already` without clicking, because a toggle has
    no third state and clicking a satisfied button is how a re-run un-does the
    previous run.
    """
    before = action_state(c, sid)
    if before.get("why"):
        return {"ok": False, "why": before["why"]}
    on = is_on(before, kind)
    if on == want_on:
        return {"ok": True, "already": True, "on": on,
                "testids": before.get("testids") or []}
    t = js(c, TOGGLE, sid=sid, kind=kind)
    if not t.get("clicked"):
        return {"ok": False, "why": t.get("why") or t.get("_raw") or "no click"}
    after = before
    for _ in range(6):
        time.sleep(2.0)
        after = action_state(c, sid)
        if after.get("why"):
            return {"ok": False, "why": after["why"]}
        if is_on(after, kind) == want_on:
            return {"ok": True, "already": False, "on": want_on,
                    "testids": after.get("testids") or []}
    return {"ok": False,
            "why": "the control did not change state — testids on the article: "
                   "%s" % (after.get("testids") or [])}


# --- the overflow menu --------------------------------------------------

# `[data-testid="caret"]` is the post's overflow control; `[data-testid=
# "Dropdown"]` matches NOTHING on this build, measured, and a routine written
# against it reported "no Dropdown" on posts it had correctly located. The
# items are bare `[role="menuitem"]` with no wrapper at all.
CARET = """(() => {
  for (const a of document.querySelectorAll('article')) {
    const own = [...a.querySelectorAll("a[href*='/status/']")]
      .find(x => /\\/status\\//.test(x.getAttribute('href') || '')
                && !/\\/(analytics|photo|video|retweets|likes)/.test(
                      x.getAttribute('href'))
                && x.getAttribute('href').split('/').pop() === __SID__);
    if (!own) continue;
    const btn = own.querySelector('[data-testid="caret"]');
    if (!btn) return {opened: false, why: 'no caret on this post'};
    const box = btn.getBoundingClientRect();
    if (!box.width) return {opened: false, why: 'caret has no size'};
    if (box.top < 0 || box.top > window.innerHeight) {
      window.scrollTo(0, Math.max(0,
        window.scrollY + box.top - window.innerHeight / 2));
      return {opened: false, why: 'caret was off screen, scrolled to it'};
    }
    btn.click();
    return {opened: true};
  }
  return {opened: false, why: 'status not on page'};
})()"""

# Match the menu item on its FIRST character. A regex over the whole string
# missed the item with the item plainly visible, because the menu re-renders
# between the read and the click and the exact text is not stable across
# renders.
MENU_ITEM = """(() => {
  const items = [...document.querySelectorAll('[role="menuitem"]')]
    .filter(e => e.offsetParent);
  if (!items.length) return {clicked: false, why: 'the menu is not open',
    items: []};
  const texts = items.map(e => (e.innerText || '').trim());
  const want = __WANT__;
  const hit = texts.findIndex(t => want.some(w =>
    t.startsWith(w) || new RegExp('^' + w, 'i').test(t)));
  if (hit < 0) return {clicked: false, why: 'no such menu item', items: texts};
  items[hit].click();
  return {clicked: true, item: texts[hit]};
})()"""

# Every menu item currently on the page, for a run that found nothing and
# needs to say what the menu actually holds rather than reporting a lookup
# failure.
MENU_ITEMS = """(() => JSON.stringify(
  [...document.querySelectorAll('[role="menuitem"]')]
    .filter(e => e.offsetParent)
    .map(e => (e.innerText || '').replace(/\\s+/g, ' ').trim())))()"""


def menu_choose(c, prefixes) -> dict:
    """Click the first visible menuitem whose text starts with one of these."""
    return js(c, MENU_ITEM, want=list(prefixes))


def menu_items(c):
    return js_raw(c, MENU_ITEMS)


# --- composer boxes -----------------------------------------------------

# The visible Draft editors, and whether the one holding the text sits in a
# reply dialog. TWO nodes carry data-testid="tweetTextarea_0" and only one is
# the real editor, so the taller visible one is the one that holds the text.
EDITORS = """(() => {
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  return JSON.stringify({
    count: all.length,
    dialogs: dialogs.length,
    items: all.map(n => {
      let t = '';
      for (const k of n.childNodes) t += k.textContent || '';
      return {len: t.length, text: t,
              in_dialog: !!n.closest('[role="dialog"]'),
              focused: n === document.activeElement};
    })
  });
})()""" % json.dumps(DRAFT_CLS)

FOCUS_EDITOR = """(() => {
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  if (!all.length) return false;
  all.sort((a, b) => b.getBoundingClientRect().height
                    - a.getBoundingClientRect().height)[0].focus();
  return true;
})()""" % json.dumps(DRAFT_CLS)

# The send control, found by walking UP from the editor that holds the text.
# Taking the first enabled tweet button on the page sent through whatever
# composer happened to be on screen, and the inline composer mounts
# tweetButtonInline and often mounts no tweetButton at all — so either testid
# counts, but it must be the one inside this box.
SEND_IN_BOX = """(() => {
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf(%s) >= 0
                 && n.offsetParent !== null);
  const e = all.find(n => dialogs.some(d => d === n.closest('[role="dialog"]')))
          || all[0];
  if (!e) return {sent: false, why: 'no visible editor'};
  let scope = dialogs.find(d => d.contains(e)) || e.closest('form')
              || e.parentElement;
  while (scope && scope !== document.body) {
    const b = [...scope.querySelectorAll('button[data-testid]')]
      .find(x => /^tweetButton/.test(x.dataset.testid) && !x.disabled);
    if (b) { b.click(); return {sent: true, which: b.dataset.testid}; }
    scope = scope.parentElement;
  }
  return {sent: false, why: 'no enabled send button inside this box',
          buttons: [...document.querySelectorAll('button[data-testid]')]
            .map(x => x.dataset.testid).filter(t => /^tweetButton/.test(t))};
})()""" % json.dumps(DRAFT_CLS)

# Close a box through the control the page already shows. It is never used on
# a box holding anything but automation's own debris — clearing a composer is
# the thing the commit gate blocks, and it raises Chrome's unsaved-changes
# dialog, which then blocks every later CDP call until the user dismisses it.
CLOSE_BOX = """(() => {
  const dialogs = [...document.querySelectorAll('[role="dialog"]')]
    .filter(d => d.offsetParent !== null
                 && d.querySelector('[data-testid="tweetTextarea_0"]'));
  const d = dialogs[0];
  if (!d) return 'no dialog with an editor';
  const b = d.querySelector('[data-testid="app-bar-close"]');
  if (!b) return 'no close button';
  b.click();
  return 'closed';
})()"""

# Dialogs holding nothing editable are leftovers from an earlier run and they
# put the first dialog on the page in the wrong place. post_reply.py clears
# exactly these — the ones WITH an editor are never touched.
CLEAR_STALE_DIALOGS = """(() => {
  let n = 0;
  for (const d of document.querySelectorAll('[role="dialog"]')) {
    if (d.offsetParent === null) continue;
    if (d.querySelector('[contenteditable="true"]')) continue;
    const b = d.querySelector('[data-testid="app-bar-close"]');
    if (b) { b.click(); n++; } else d.remove();
  }
  return n;
})()"""


def editors(c) -> dict:
    """The visible Draft editors and what each one holds."""
    return js(c, EDITORS)


def the_editor(c, want_empty=None, want_dialog=None, tries=8, pause=1.6):
    """The Draft editor to work in, polled until it settles.

    `want_empty` picks a box that holds nothing and `want_dialog` insists it
    be inside a dialog — the two gates that stopped 643 characters of reply
    going into the main composer and publishing as a standalone post.
    """
    best = {}
    for _ in range(tries):
        st = editors(c)
        items = st.get("items") or []
        if items:
            best = st
            for it in items:
                if want_dialog and not it.get("in_dialog"):
                    continue
                if want_empty is not None and (it.get("len") or 0) != want_empty:
                    continue
                return it
        time.sleep(pause)
    return {}


# --- typing -------------------------------------------------------------

def type_body(c, text: str, existing: str = "", echo=print) -> None:
    """Type `text` into the focused editor, after whatever it already holds.

    Two paths, chosen by measurement and not by habit, because the difference
    is which characters survive:

      pure ASCII   one Input.insertText. It writes to the DOM without touching
                   the editor's own state, and the STANDALONE composer accepts
                   that — a 535-character post typed in one call published
                   whole, link card and all.
      anything else  per-character key events. The same insertText loses a CJK
                   body entirely: 5-, 48-, 190- and 597-character Chinese
                   probes all arrived as a single newline, every Han character
                   gone. Real key events update the editor's model.

    A fresh Draft block swallows the FIRST character of any sequence, whatever
    it is and however it is sent — measured four ways, including with the caret
    collapsed to the start. One throwaway ASCII space initialises the block.
    It is removed afterwards by collapsing a range onto that one block and
    pressing Delete FORWARD; Backspace at the end of a typed body eats the
    body's last character instead of the space.

    The removal is anchored on the SOURCE's own leading characters, never on a
    shape the editor also has: the linkified URL renders as link text, so a
    "any leaf starting with a space" pass finds the URL's own element and
    deletes it — measured, the URL was whole at the insert and read back with
    zero occurrences while the text behind it was untouched.
    """
    tail = text.lstrip()
    if tail and existing:
        c.send("Input.dispatchKeyEvent", type="char", text=" ")
        time.sleep(0.3)
    if all(ord(ch) < 128 for ch in text):
        c.send("Input.insertText", text=text, wait=40, retries=6)
        time.sleep(2.0)
        return
    for i, ch in enumerate(text):
        c.send("Input.dispatchKeyEvent", type="char", text=" ")
        if i == 0:
            time.sleep(0.3)
            continue
        if ch == "\n":
            c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13, text="\r")
            c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13)
            c.send("Input.dispatchKeyEvent", type="char", text=" ")
        elif ord(ch) < 0x80:
            c.send("Input.dispatchKeyEvent", type="keyDown", key=ch, text=ch)
            c.send("Input.dispatchKeyEvent", type="keyUp", key=ch)
        else:
            c.send("Input.dispatchKeyEvent", type="char", text=ch)
        time.sleep(0.012)
        if i % 25 == 24:
            time.sleep(0.4)
    time.sleep(1.0)


def remove_warmup(c, anchor: str, echo=print) -> None:
    """Delete the one leading space that initialised the block.

    ONE pass, and the block is located by the source's own text. A pass that
    loops on a condition the delete does not change keeps finding the same
    block, runs to its limit, and eats real characters — measured, 9 blocks
    against 8 warm-ups deleted one real character and the length check could
    not see it because the removed character and the trailing space cancelled.
    """
    anchor = anchor[:10]
    if not anchor:
        return
    moved = js_raw(c, """(() => {
      const all = [...document.querySelectorAll(
        '[data-testid="tweetTextarea_0"]')]
        .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                     && n.offsetParent !== null);
      const e = all.find(x => x === document.activeElement) || all[0];
      if (!e) return 'NO_EDITOR';
      const b = [...e.querySelectorAll('div')].find(x =>
        x.children.length === 0 &&
        (x.innerText || '').replace(/\\s+/g, ' ') === ' ' + %s);
      if (!b) return 'NO_WARMUP_BLOCK';
      const sel = window.getSelection();
      const r = document.createRange();
      r.selectNodeContents(b);
      r.collapse(true);
      sel.removeAllRanges();
      sel.addRange(r);
      return 'OK';
    })()""" % json.dumps(anchor), wait=25, retries=4)
    if moved == "OK":
        time.sleep(0.5)
        c.send("Input.dispatchKeyEvent", type="keyDown", key="Delete",
               code="Delete", windowsVirtualKeyCode=46)
        c.send("Input.dispatchKeyEvent", type="keyUp", key="Delete",
               code="Delete", windowsVirtualKeyCode=46)
        time.sleep(0.8)
    else:
        echo("  warm-up removal: %s (nothing to remove, or the block was not "
             "found)" % moved)


# --- per-feature state --------------------------------------------------

def state_file(name: str):
    """A per-feature state file, in the configured state directory.

    Named with an x_ prefix so a feature's file can never collide with one
    another feature's.
    """
    d = xconfig.state_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data) -> None:
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    except OSError as exc:
        print("could not save state to %s: %s" % (path, exc), flush=True)


def read_text_or_file(arg: str) -> str:
    """The argument as literal text, or as a file's contents when it is one."""
    if os.path.exists(arg):
        return open(arg, encoding="utf-8").read()
    return arg


def die(msg: str) -> int:
    """Print a refusal and exit non-zero.

    A run that did nothing must never exit 0: a script reported "no replies
    confirmed" and still exited 0, its completion notice was indistinguishable
    from a success, and every "completed normally" in a log had to be read
    against the output file instead of the exit code.
    """
    print(msg, flush=True)
    return 1