#!/usr/bin/env python3
"""Read a profile on X, and change one social-graph edge on it.

One handle in, one profile out; at most one edge changed, and only on a
profile the page has itself proved it is on. Nothing is navigated to and no
tab is opened, so the caller has the profile in front of it already — as
with every other script here, a page load makes the user confirm it in their
UI, and that is a cost this file never pays.

Three rules do the work, and each is there because the alternative was
measured going wrong on this account:

  * EVERY WRITE NEEDS --confirm, and without it this script prints a refusal
    and exits non-zero BEFORE it connects to anything — a refusal that costs
    a browser connection has already cost too much. There is no --force and
    no environment variable that buys the click. It exists because an
    unconfirmed follow, block or mute lands on a REAL PERSON's account the
    moment it is clicked, and neither a notification nor a later run is a
    quiet undo: the person is told, the block is real, and the only way back
    is a second unrequested write. A mistake that needs another mistake to
    repair is not one to automate by accident.

  * A SOCIAL-GRAPH WRITE TARGETS ANOTHER PERSON'S ACCOUNT, which is why the
    bar here is higher than for this account's own posts. Deleting or
    editing a post of this account's own is a repair to a thing this account
    owns, and x_edit.py's whole difficulty is the editor refusing to open.
    Blocking, muting or following a stranger is an act performed ON them:
    visible to them, not undoable by editing anything here, and — for a
    block — a wall built in both directions. So the handle is asserted
    before any click, and this account's own handle is refused outright.
    A write that mis-aims at the logged-in account has no victim and a real
    consequence, which is strictly worse than a refusal.

  * THE HANDLE ASSERTION IS A GATE, NOT A WARNING. Before anything is
    clicked, the handle the PAGE shows is read back and compared,
    case-insensitively, with the handle the caller named; a mismatch aborts
    and prints both. It exists because of a MEASURED incident: a stale log
    once matched one topic's post with a handle belonging to a completely
    different post, so acting on the account named in the log rather than
    the one on screen is a real failure mode in this skill, not a
    hypothetical one. Every other script here is scoped by a status id,
    which cannot be silently wrong in that particular way — a quoted post
    carries the target's link and the scope still resolves to the right
    article. A profile is scoped by a STRING A CALLER TYPED, so the page
    has to be the authority and the argument is only the question.

VERIFIED in this skill, and relied on here:

    [data-testid="caret"]       exists and clicks (delete_own_post.py)
    [role="menuitem"]           the overflow menu's items are BARE elements
                                with NO wrapper; [data-testid="Dropdown"]
                                matches NOTHING on this build, measured,
                                and a routine scoped to it reported "no
                                Dropdown" on a menu it had opened
    first-character matching    the menu re-renders between the read and
                                the click, so its exact text is not stable
                                across renders and an item must be matched
                                on its FIRST character — a whole-string
                                regex missed 删除 while it was plainly
                                visible
    [data-testid="User-Name"]   carries the display name and an @handle
                                line (delete_own_post.py reads it)

UNVERIFIED, and no script in this skill has driven any of them:

    [data-testid="follow"] / [data-testid="unfollow"]
                                the follow control's state-bearing testids,
                                taken from the browser-automation notes and
                                not seen on this build. Nothing here has
                                ever clicked a follow button.
    the profile link's href shape used by the assertion
                                three selectors are tried and each reports
                                its own value, so a wrong guess shows up as
                                an empty field and not as a silent pass
    屏蔽/Block, 取消屏蔽/Unblock, 静音/Mute, 取消静音/Unmute
                                as menu-item labels. delete_own_post.py
                                proves only 删除 / Delete on this menu, so
                                every label here is a first guess.
    [data-testid="UserDescription"] for the bio, the aria-labels on the
    [data-testid="UserCell"],     counter links, and the UserCell rows the
                                followers/following read collects from.

Every failure branch prints the real testids, labels and menu items it
saw instead of "not found", which is what turns each UNVERIFIED entry above
into a measurement on the first run that meets it — the same reason
x_edit.py dumps the menu it found.

DEAD END kept out on purpose, and worth naming: a block and a mute both
raise a CONFIRMATION SHEET. delete_own_post.py measured
[data-testid="confirmationSheetConfirm"] standing on its own, NOT inside a
[role="dialog"], so a dialog-scoped lookup never finds it. This file does
not click it. Confirming that sheet is a second write on another person's
account that no caller asked for, and a script that quietly performs the
step it could not name is the exact defect the other gates here exist to
prevent. The sheet is detected, reported, and left for a human; the run
then says NOT BLOCKED, which is true.

    python3 x_profile.py <handle>                        read the profile
    python3 x_profile.py <handle> --followers 50         read the list
    python3 x_profile.py <handle> --follow --confirm     follow it
    python3 x_profile.py <handle> --unfollow --confirm   take it back
    python3 x_profile.py <handle> --block --confirm      block it
    python3 x_profile.py <handle> --mute --dry-run       read, change nothing
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

# A handle is letters, digits and underscore, and nothing else. Checked
# before the page is touched, because a mistyped handle that reaches the
# browser costs a connection and teaches the caller nothing.
HANDLE_RX = re.compile(r"\A[A-Za-z0-9_]+\Z")

# The first path segment is not a profile. Without this list a read of the
# home tab resolves to "home" and the handle assertion fires on a perfectly
# good page; with it, the answer is "there is no handle here", which says
# the real thing.
NOT_A_PROFILE = {"home", "search", "explore", "notifications", "messages",
                 "settings", "compose", "i", "login", "logout", "intent",
                 "share", "about", "tos", "privacy", "help"}

# One entry per action, and every terminal line this file can print is built
# here rather than at the print sites — so the string a caller greps can
# never come from a different branch than the exit code it controls.
#
# `button` is the follow control's UNVERIFIED state-bearing testid: the one
# that is expected to be mounted once the goal HOLDS. `menu` is the pair of
# UNVERIFIED labels, [what is already there, what to click].
#
# ALREADY is the verb, not a separate string. x_repost.py prints "ALREADY
# NOT REPOSTED" because "unreposted" is not a word; here every verb has a
# past tense, so ALREADY UNFOLLOWED is readable and greppable on the same
# line as UNFOLLOWED.
ACTIONS = {
    "follow":   {"verb": "FOLLOWED",   "button": "unfollow"},
    "unfollow": {"verb": "UNFOLLOWED", "button": "follow"},
    "block":    {"verb": "BLOCKED",
                 "menu": ("取消屏蔽", "Unblock"), "click": ("屏蔽", "Block")},
    "unblock":  {"verb": "UNBLOCKED",
                 "menu": ("屏蔽", "Block"), "click": ("取消屏蔽", "Unblock")},
    "mute":     {"verb": "MUTED",
                 "menu": ("取消静音", "Unmute"), "click": ("静音", "Mute")},
    "unmute":   {"verb": "UNMUTED",
                 "menu": ("静音", "Mute"), "click": ("取消静音", "Unmute")},
}

# --- what the page says --------------------------------------------------

# The profile, in one read: the handle the assertion needs, the display name,
# the bio, the counters, and the follow control's current state. Counting the
# header caret as "the caret NOT inside an article" is deliberate — every
# post in the timeline below carries one of its own, and taking the first
# caret on the page gets a post's menu, not the profile's. The caret
# TESTID is verified; this scoping to it is not, and it is flagged in the
# report.
PROFILE = """(() => {
  const lines = (n) => (((n && n.innerText) || '').split('\\n')
                        .map(l => l.trim()).filter(Boolean));
  const txt = (n) => (n && (n.innerText || '') || '').replace(/\\s+/g, ' ').trim();
  const one = (sel) => document.querySelector(sel);

  // VERIFIED shape: delete_own_post.py reads the @handle out of this node.
  const ul = lines(one('[data-testid="User-Name"]'));
  const un_handle = (ul.find(l => l[0] === '@') || '').replace(/^@/, '');

  // UNVERIFIED href shapes, each named so an empty one is visible instead
  // of indistinguishable from a profile that has no such link.
  const href = (sel) => {
    const a = one(sel);
    return a ? (a.getAttribute('href') || '') : '';
  };

  // UNVERIFIED: the follow control's state-bearing testid pair. Every one
  // found on the page comes back, so a run that changes nothing prints what
  // it actually saw instead of a guess.
  const follow_testids = [...new Set(
    [...document.querySelectorAll(
      '[data-testid^="follow"], [data-testid^="unfollow"]')]
      .map(b => b.dataset.testid))];
  const follow_btn = one('[data-testid="follow"]');
  const unfollow_btn = one('[data-testid="unfollow"]');

  const counts = {};
  for (const a of document.querySelectorAll('a[href]')) {
    const h = (a.getAttribute('href') || '');
    const val = (a.getAttribute('aria-label') || '') + ' ' + txt(a);
    if (/\\/followers$/.test(h) && !counts.followers) counts.followers = val;
    if (/\\/following$/.test(h) && !counts.following) counts.following = val;
  }

  const carets = [...document.querySelectorAll('[data-testid="caret"]')];
  return JSON.stringify({
    user_name_handle: un_handle,
    display: ul.find(l => l[0] !== '@' && !/joined|加入|注册/i.test(l)) || '',
    user_name_lines: ul.slice(0, 6),
    link_handles: {
      UserName_link: href('[data-testid="User-Name"] a[href^="/"]'),
      avatar: href('[data-testid="UserAvatar-Container-unknown"]'),
      header_link: href('[data-testid="primaryColumn"] a[href^="/"]'),
    },
    route: location.pathname || '',
    bio: txt(one('[data-testid="UserDescription"]')),
    counts: counts,
    follow_state: unfollow_btn ? 'unfollow' : (follow_btn ? 'follow' : ''),
    follow_testids: follow_testids,
    header_carets: carets.filter(b => !b.closest('article')
                                  && b.offsetParent).length,
    post_carets: carets.filter(b => b.closest('article')
                                && b.offsetParent).length
  });
})()"""

# The profile header's overflow caret. Unverified by this skill as a PROFILE
# caret: delete_own_post.py proved the testid on a post, and nothing here has
# opened a profile's. The scroll is a scrollIntoView, which is not a
# navigation, and a caret below the fold clicks on nothing.
HEADER_CARET = """(() => {
  const all = [...document.querySelectorAll('[data-testid="caret"]')];
  const hdr = all.filter(b => !b.closest('article') && b.offsetParent);
  if (!hdr.length) return {opened: false, why: 'no caret outside any article',
    carets: all.length};
  const btn = hdr[0];
  const box = btn.getBoundingClientRect();
  if (!box.width) return {opened: false, why: 'the header caret has no size'};
  if (box.top < 0 || box.top > window.innerHeight) {
    btn.scrollIntoView({block: 'center', behavior: 'instant'});
    return {opened: false, why: 'the header caret was off screen, scrolled',
            carets: all.length};
  }
  btn.click();
  return {opened: true, carets: all.length};
})()"""

# The follow control. A bare element.click(), which is what xkit.TOGGLE and
# delete_own_post.py's caret both do; the reply control's mousedown/mouseup
# pair is not interchangeable with it and is not used here.
FOLLOW_CLICK = """(() => {
  const want = __WANT__;
  const btn = document.querySelector('[data-testid="' + want + '"]');
  if (!btn) return {clicked: false, why: 'no [' + want + '] control here'};
  const box = btn.getBoundingClientRect();
  if (!box.width) return {clicked: false, why: 'the follow control has no size'};
  if (box.top < 0 || box.top > window.innerHeight) {
    btn.scrollIntoView({block: 'center', behavior: 'instant'});
    return {clicked: false, why: 'the follow control was off screen, scrolled'};
  }
  btn.click();
  return {clicked: true, was: want};
})()"""

# delete_own_post.py measured this testid on the delete sheet, standing on
# its own rather than inside a dialog. Read, never clicked — see the module
# docstring on why this file stops here.
SHEET = """(() => {
  const b = document.querySelector('[data-testid="confirmationSheetConfirm"]');
  return (b && b.offsetParent) ? 'SHEET' : 'NO_SHEET';
})()"""

# Whether the document moved. x_bookmark's --list measures this rather than
# comparing against scrollHeight: a virtual list grows its own scrollHeight as
# it prefetches, so a bottom-of-page guess is wrong exactly when the list has
# more to give. window.scrollBy moves the document and is NOT a navigation.
SCROLL_DOWN = """(() => {
  const before = Math.round(window.scrollY);
  window.scrollBy(0, Math.round(window.innerHeight * 0.9));
  const after = Math.round(window.scrollY);
  return JSON.stringify({moved: after > before, from: before, to: after});
})()"""

# A row of a followers/following view. [data-testid="UserCell"] is
# UNVERIFIED here and is tried first; the fallback walks a[href^="/"] whose
# own text starts with @ and which holds no further profile link, so a
# suggested-accounts strip cannot contribute a row. Which of the two was
# used comes back as `via`.
ROWS = """(() => {
  const cells = [...document.querySelectorAll('[data-testid="UserCell"]')]
      .filter(n => n.offsetParent);
  const scope = cells.length ? cells
      : [...document.querySelectorAll('a[href^="/"]')].filter(a => {
          const t = (a.innerText || '').trim();
          return t[0] === '@' && !a.querySelector('a[href^="/"]');
        });
  const out = [];
  const seen = new Set();
  for (const n of scope) {
    const a = (n.querySelector ? n.querySelector('a[href^="/"]') : n);
    if (!a) continue;
    const h = (a.getAttribute('href') || '').replace(/^\\//, '').split('/')[0];
    if (!/^[A-Za-z0-9_]{1,20}$/.test(h) || seen.has(h)) continue;
    seen.add(h);
    out.push(h);
  }
  return JSON.stringify({
    rows: out,
    via: cells.length ? '[data-testid="UserCell"]' : 'a[href^="/"]'
  });
})()"""


def norm_handle(raw: str) -> tuple:
    """(display, compare) for a handle the caller typed. Never repairs one.

    A leading @ is stripped because people write it and X accepts it; a typo
    is refused instead of corrected, because the correction would be a
    DIFFERENT PERSON'S ACCOUNT and this file acts on other people's accounts.
    Returns (None, None) when the handle is not a handle.
    """
    show = (raw or "").strip()
    bare = show[1:] if show.startswith("@") else show
    if not HANDLE_RX.match(bare):
        return None, None
    return bare, bare.lower()


def handle_from_href(href: str) -> str:
    """The handle a profile link's href names, or ''."""
    m = re.match(r"\A/@?([A-Za-z0-9_]+)", (href or "").lstrip("/"))
    return m.group(1) if m else ""


def handle_from_route(path: str) -> str:
    """The handle the URL's first segment names, or '' if it names no one."""
    seg = [s for s in (path or "").split("/") if s]
    if not seg or seg[0].lower() in NOT_A_PROFILE:
        return ""
    bare = seg[0].lstrip("@")
    return bare if HANDLE_RX.match(bare) else ""


def page_handles(page: dict) -> list:
    """(source, handle) for every handle the PAGE gives, best source first.

    The User-Name element leads because delete_own_post.py VERIFIED that it
    carries an @handle line. The three href selectors and the URL follow, and
    each is returned by NAME so a wrong guess is visible in the abort.
    """
    out = []
    un = (page.get("user_name_handle") or "").strip().lstrip("@")
    if un:
        out.append(('[data-testid="User-Name"]', un))
    for name, href in sorted((page.get("link_handles") or {}).items()):
        h = handle_from_href(href)
        if h:
            out.append((name, h))
    route = handle_from_route(page.get("route") or "")
    if route:
        out.append(("location.pathname", route))
    return out


def sources_line(page: dict, found: list) -> str:
    """Every candidate the page offered, so an abort names all of them."""
    links = page.get("link_handles") or {}
    bits = ["User-Name=%s" % (page.get("user_name_handle") or "(empty)")]
    for name in sorted(links):
        bits.append("%s=%s" % (name, links[name] or "(empty)"))
    bits.append("route=%s" % (page.get("route") or "(empty)"))
    return "  handle sources: %s" % "  ".join(bits)


def read_profile(c) -> dict:
    """The PROFILE read, parsed. xkit.js handles both return shapes."""
    return X.js(c, PROFILE)


def assert_handle(page: dict, want: str) -> int:
    """Refuse unless the page's own handle IS the handle asked about.

    EVERY candidate must agree, not just the first: a page that names the
    account two different ways is not evidence of anything, and the safe
    direction to be wrong in is the one where nothing is clicked. Returns 0
    when the assertion holds.
    """
    found = page_handles(page)
    if not found:
        print(sources_line(page, found), flush=True)
        return X.die("ABORT - the page names no handle, so there is nothing "
                     "to assert @%s against; open that profile and run "
                     "again" % want)
    actual = found[0][1]
    disagree = [f for f in found if f[1].lower() != want.lower()]
    if disagree:
        print("ABORT - asked about @%s but the page shows @%s"
              % (want, actual), flush=True)
        print("  disagrees: %s says @%s" % (disagree[0][0], disagree[0][1]),
              flush=True)
        print(sources_line(page, found), flush=True)
        print("  nothing was clicked.", flush=True)
        return 1
    return 0


def show_profile(page: dict, handle: str) -> None:
    """The profile's own fields, in the order a reader wants them."""
    print("  handle      @%s" % handle, flush=True)
    if page.get("display"):
        print("  display     %s" % page.get("display"), flush=True)
    if page.get("bio"):
        print("  bio         %s" % (page.get("bio") or "")[:160], flush=True)
    for key, label in (("followers", "followers"),
                       ("following", "following")):
        val = (page.get("counts") or {}).get(key)
        if val:
            print("  %-11s %s" % (label, " ".join(val.split())), flush=True)
    print("  follow ctl  %s%s" % (page.get("follow_state") or "(none found)",
          "  testids=%s" % (page.get("follow_testids") or []) if
          page.get("follow_testids") else ""), flush=True)
    print("  carets      %d in the header, %d in posts"
          % (page.get("header_carets") or 0, page.get("post_carets") or 0),
          flush=True)


def first_char_hit(text: str, prefixes) -> bool:
    """Match a menu label on its FIRST character, per the measured rule."""
    t = (text or "").strip()
    return bool(t) and any(t[0] == p[0] for p in prefixes)


def confirm_sheet_up(c) -> bool:
    """True when a confirmation sheet is showing. Detected, never clicked."""
    return X.js_raw(c, SHEET, wait=15, retries=2) == "SHEET"


def open_menu(c, tries: int = 3) -> tuple:
    """Open the profile's overflow menu and read what it offers.

    Returns (items, ok, why). The menu is deliberately left OPEN: the caller
    may be about to click one of the items, and closing it means a second
    open whose re-render would invalidate the labels just read.
    """
    last = {}
    for _ in range(tries):
        r = X.js(c, HEADER_CARET)
        if r.get("opened"):
            items = X.menu_items(c)
            if isinstance(items, list):
                return items, True, ""
            return [], False, ("the menu opened but its items did not "
                               "answer: %s" % str(items)[:100])
        last = r
        if "scrolled" in str(r.get("why") or ""):
            time.sleep(1.2)          # the one retry worth making: the caret
            continue                 # was below the fold, and the scroll
        break                        # moved it
    return [], False, str(last.get("why") or "the overflow menu did not open")


def close_menu(c) -> None:
    """Click the caret again to drop a menu this run opened and left.

    Tidying, not part of any write: nothing here is asserted about the
    result, because a menu left open on the user's screen is untidy but
    harmless and a second unguarded click on an account's menu is not.
    """
    X.js(c, HEADER_CARET)


def menu_write(c, action: str) -> dict:
    """Read the menu, click only when the state disagrees with the goal.

    The same idempotence xkit.set_action gives a post: a re-run on an
    already-blocked account reads the 取消屏蔽 item, reports ALREADY and
    clicks nothing, because a menu item clicked twice is how the previous
    run gets undone.
    """
    spec = ACTIONS[action]
    items, ok, why = open_menu(c)
    if not ok:
        return {"ok": False, "why": why}
    if not items:
        return {"ok": False, "why": "the overflow menu is open but holds no "
                                    "readable items"}
    if any(first_char_hit(it, spec["menu"]) for it in items):
        close_menu(c)
        return {"ok": True, "already": True, "items": items}
    hit = X.menu_choose(c, list(spec["click"]))
    if not hit.get("clicked"):
        close_menu(c)
        return {"ok": False, "items": items,
                "why": "the menu has no item starting %s" %
                       "/".join(spec["click"])}
    return {"ok": True, "already": False, "clicked": hit.get("item"),
            "items": items}


def menu_read(c, action: str) -> tuple:
    """Re-read the menu after a click. (holds, items, why)."""
    if confirm_sheet_up(c):
        return False, [], ("a confirmation sheet is standing on the page — "
                           "nothing further was clicked; confirm or dismiss "
                           "it yourself, then re-read the profile")
    items, ok, why = open_menu(c)
    if not ok:
        return False, [], why
    holds = any(first_char_hit(it, ACTIONS[action]["menu"]) for it in items)
    close_menu(c)
    return holds, items, ""


def follow_write(c, action: str) -> dict:
    """Read the follow control, click only when it disagrees with the goal."""
    spec = ACTIONS[action]
    page = read_profile(c)
    now = page.get("follow_state") or ""
    if not now:
        return {"ok": False, "why": "no [data-testid=\"follow\"] or "
                                    "[data-testid=\"unfollow\"] control on "
                                    "this profile (UNVERIFIED pair)",
                "testids": page.get("follow_testids") or []}
    if now == spec["button"]:
        return {"ok": True, "already": True, "state": now}
    res = X.js(c, FOLLOW_CLICK, want=now)
    if not res.get("clicked"):
        return {"ok": False, "why": res.get("why") or "no click",
                "testids": page.get("follow_testids") or []}
    after = page
    for _ in range(6):
        time.sleep(2.0)
        after = read_profile(c)
        if (after.get("follow_state") or "") == spec["button"]:
            return {"ok": True, "already": False, "state": after["follow_state"]}
    return {"ok": False, "testids": after.get("follow_testids") or [],
            "why": "the control still reads %s after the click" %
                   (after.get("follow_state") or "(nothing)")}


def run_write(c, args, me: str) -> int:
    """Everything a write touches. The assertion gates every click."""
    action = args.action
    spec = ACTIONS[action]
    verb = spec["verb"]

    page = read_profile(c)
    if page.get("_raw") and not page.get("route"):
        return X.die("NOT %s - the profile could not be read: %s"
                     % (verb, page.get("_raw")))
    rc = assert_handle(page, args.handle)
    if rc:
        return rc
    handle = page_handles(page)[0][1]
    print("  asserting against @%s" % handle, flush=True)
    print(sources_line(page, []), flush=True)

    # This account's own handle. A social-graph edge pointed at the logged-in
    # account has no victim and a real consequence, so it is refused even
    # though every other part of the run passed.
    if me and me.lower() == handle.lower():
        return X.die("ABORT - @%s is this account; refusing to "
                     "follow/block/mute yourself" % handle)
    if not me:
        print("  note: this account's own handle could not be read, so the "
              "self-edge check did not run", flush=True)

    if args.dry_run:
        if action in ("follow", "unfollow"):
            now = page.get("follow_state") or ""
            holds = (now == spec["button"])
        else:
            items, ok, why = open_menu(c)
            holds = ok and any(first_char_hit(it, spec["menu"]) for it in items)
            close_menu(c)
        print("DRY RUN %s @%s — nothing was clicked; %s"
              % (action.upper(), handle,
                 "the goal already holds" if holds else
                 "the goal does not hold yet"), flush=True)
        if action not in ("follow", "unfollow"):
            print("  the overflow menu was opened to read its labels and "
                  "dropped again; nothing inside it was clicked", flush=True)
        else:
            print("  follow control testids: %s"
                  % (page.get("follow_testids") or []), flush=True)
        return 0

    print("  %s @%s — confirmed" % (action.upper(), handle), flush=True)
    res = (follow_write(c, action) if action in ("follow", "unfollow")
           else menu_write(c, action))

    if res.get("ok"):
        if res.get("already"):
            print("ALREADY %s @%s" % (verb, handle), flush=True)
        else:
            print("%s @%s" % (verb, handle), flush=True)
        return 0

    print("NOT %s @%s" % (verb, handle), flush=True)
    print("  %s" % (res.get("why") or "the control did not change state"),
          flush=True)
    if res.get("testids"):
        print("  follow control testids seen: %s" % res["testids"], flush=True)
    if res.get("items"):
        print("  menu items seen: %s" % res["items"], flush=True)
    return 1


def _read_rows(c):
    """The open list's rows as a dict, or None when the page does not answer.

    ROWS ends in JSON.stringify(), so the answer is a STRING. Parsed here
    rather than handed to xkit.js, which unwraps a JSON OBJECT and would
    hand an array back as {_raw: '[…]'} — x_edit.py records that exact trap
    costing it a verification.
    """
    got = X.js_raw(c, ROWS, wait=25, retries=4)
    if isinstance(got, dict):
        return got if got.get("rows") is not None else None
    if isinstance(got, str):
        try:
            parsed = json.loads(got)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def read_list(c, kind: str, want: int) -> tuple:
    """Up to `want` handles from a followers/following view ALREADY OPEN.

    Collection is by scrollBy, which is a scroll and not a navigation — this
    file loads no page, so the caller has to have the list open, exactly as
    with x_bookmark's --list. Returns (rows, via, why).
    """
    rows, seen, via = [], set(), ""
    for _ in range(60):
        parsed = _read_rows(c)
        if parsed is None:
            return [], via, ("the %s view did not answer" % kind)
        via = via or (parsed.get("via") or "")
        for h in parsed.get("rows") or []:
            if h not in seen:
                seen.add(h)
                rows.append(h)
        if len(rows) >= want:
            return rows[:want], via, ""
        # Stop on a scroll that did not MOVE, not on a guess at the bottom of
        # the page: x_bookmark's --list measures the same way, because a
        # virtual list grows its own scrollHeight while it prefetches and a
        # bottom-of-page test then fires exactly when there is more to read.
        # One more read after a still scroll, for the same reason it takes one
        # — rows already queued are real rows rather than a guess.
        step = X.js(c, SCROLL_DOWN)
        time.sleep(2.2)
        if not step.get("moved"):
            last = _read_rows(c)
            if last:
                for h in last.get("rows") or []:
                    if h not in seen:
                        seen.add(h)
                        rows.append(h)
            break
    return rows[:want], via, ""


def run_list(c, args, page: dict) -> int:
    """--followers / --following. Reads the open list; navigates nowhere."""
    kind = "followers" if args.followers else "following"
    handle = page_handles(page)[0][1]
    want = args.followers or args.following
    rows, via, why = read_list(c, kind, want)
    if not rows:
        print("NO %s - %s" % (kind.upper(), why or "no rows were readable"),
              flush=True)
        print("  open the profile's %s tab yourself and run again — this "
              "script loads no page, so it cannot bring the list here"
              % kind, flush=True)
        return 1
    for h in rows:
        print("@%s" % h, flush=True)
    print("%s %d" % (kind.upper(), len(rows)), flush=True)
    print("  read from %s for @%s" % (via or "an unnamed surface", handle),
          flush=True)
    if len(rows) < want:
        print("  asked for %d, the list gave %d before it stopped growing"
              % (want, len(rows)), flush=True)
    return 0


def run_read(c, args) -> int:
    """The plain read: assert, report, print the terminal line."""
    page = read_profile(c)
    if page.get("_raw") and not page.get("route"):
        return X.die("NOT READABLE - the profile could not be read: %s"
                     % page.get("_raw"))
    rc = assert_handle(page, args.handle)
    if rc:
        return rc
    show_profile(page, page_handles(page)[0][1])
    print(sources_line(page, []), flush=True)
    print("PROFILE @%s" % page_handles(page)[0][1], flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read an X profile, or change one social-graph edge on it.")
    ap.add_argument("handle", help="handle WITHOUT the leading @")
    for flag, helptext in (
            ("follow", "follow this account"),
            ("unfollow", "take the follow back"),
            ("block", "block this account"),
            ("unblock", "lift the block"),
            ("mute", "mute this account"),
            ("unmute", "unmute this account")):
        ap.add_argument("--" + flag, action="store_true", help=helptext)
    ap.add_argument("--followers", type=int, metavar="N",
                    help="read N handles from the OPEN followers list")
    ap.add_argument("--following", type=int, metavar="N",
                    help="read N handles from the OPEN following list")
    ap.add_argument("--confirm", action="store_true",
                    help="required for every write: this acts on ANOTHER "
                         "PERSON's account and cannot be quietly undone")
    ap.add_argument("--dry-run", action="store_true",
                    help="run every gate and report the state; click nothing")
    args = ap.parse_args()

    # Argument gates first, all of them, and none of them after this line
    # touches a browser. A refusal that costs nothing should cost nothing.
    chosen = [f for f in ("follow", "unfollow", "block", "unblock",
                          "mute", "unmute") if getattr(args, f)]
    if len(chosen) > 1:
        return X.die("REFUSING - pick exactly one action (got: %s)"
                     % ", ".join("--" + c for c in chosen))

    display, want = norm_handle(args.handle)
    if display is None:
        return X.die("REFUSING - %s is not a valid handle" % args.handle)

    lists = [k for k in ("followers", "following")
             if getattr(args, k) is not None]
    if len(lists) > 1:
        return X.die("REFUSING - pick one list to read (got: --%s and --%s)"
                     % (lists[0], lists[1]))
    for k in lists:
        if getattr(args, k) < 1:
            return X.die("REFUSING - --%s needs a positive N, got %s"
                         % (k, getattr(args, k)))

    if chosen:
        # The confirm gate sits BEFORE the connect: an unconfirmed write on a
        # real person must cost no more than printing a line.
        if not args.confirm:
            return X.die("REFUSING - %s @%s needs --confirm; this acts on "
                         "ANOTHER PERSON's account"
                         % (chosen[0], display))
        args.action = chosen[0]
        if lists:
            print("note: --%s is ignored while an action is given"
                  % lists[0], flush=True)
    elif args.confirm:
        print("note: --confirm given with no write to confirm", flush=True)

    try:
        c, tab, me = X.connect()
    except Exception as exc:
        # xkit.connect catches its own misses, but the port lookup under it
        # raises when nothing is listening, and a driver traceback is not a
        # message a caller can act on. xkit.no_browser() is the house wording.
        print("  %s: %s" % (type(exc).__name__, str(exc)[:90]), flush=True)
        return X.die("REFUSING - cannot reach the browser to drive it.\n  %s"
                     % X.no_browser())
    if c is None:
        return 1                     # connect already printed why

    try:
        if chosen:
            return run_write(c, args, me)
        if lists:
            page = read_profile(c)
            rc = assert_handle(page, display)
            if rc:
                return rc
            return run_list(c, args, page)
        return run_read(c, args)
    except Exception as exc:
        # The state after an unexpected error is UNKNOWN, which is not ok, so
        # the line names the action that may or may not have landed.
        verb = ACTIONS[args.action]["verb"] if getattr(args, "action", None) \
            else "READ"
        return X.die("NOT %s @%s - the run ended early: %s (nothing is "
                     "claimed about the account; the tab was left as it was)"
                     % (verb, display, str(exc)[:140]))
    finally:
        try:
            c.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())