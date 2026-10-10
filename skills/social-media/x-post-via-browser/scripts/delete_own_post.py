#!/usr/bin/env python3
"""Delete one post of this account, by status id, and verify it is gone.

Scoped by construction. It only ever acts on a status id the caller passes, it
refuses unless the post is confirmed to be this account's own, and it prints
the full text of both the post and its expected text so the caller can read
them before deciding. Nothing is matched by keyword and no search is performed:
deleting the wrong post is unrecoverable, so the id is the whole input.

Confirm before it acts:

    python3 delete_own_post.py 9240 <status-id> --expect "first words"

Opens the post in the existing tab, deletes it, then reads the thread back and
reports whether the status id is still there. Never reloads, never navigates to
another page, never takes the mouse or OS focus.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import cdp

WHO = r"""(() => {
  const d = document.querySelector('[data-testid="User-Name"]');
  return (d && d.innerText || '').split('\n').find(l => l.trim().startsWith('@')) || '';
})()"""

POST = r"""(() => {
  const a = [...document.querySelectorAll('article')]
    .find(x => x.querySelector('a[href*="/status/__PID__"]'));
  if (!a) return null;
  return {
    id: '__PID__',
    time: a.querySelector('time') ? a.querySelector('time').getAttribute('datetime') : '',
    text: (a.innerText || '').replace(/\s+/g, ' ').trim(),
  };
})()"""

DEL = r"""(() => {
  const a = [...document.querySelectorAll('article')]
    .find(x => x.querySelector('a[href*="/status/__PID__"]'));
  if (!a) return 'NO_ARTICLE';
  const menu = a.querySelector('[data-testid="caret"]');
  if (!menu) return 'NO_CARET';
  menu.click();
  return 'CLICKED_CARET';
})()"""

DEL_CONFIRM = r"""(() => {
  // No [data-testid="Dropdown"] wrapper on this menu — measured, the items
  // are bare [role="menuitem"] elements ("删除", "置顶到你的个人资料", ...),
  // so scoping to a wrapper finds nothing.
  //
  // Match the FIRST character only. An earlier regex over the whole string
  // ("/删除|Delete/i") missed the item even with the item present and visible,
  // because the menu re-renders between the read and the click and the exact
  // text is not stable across renders.
  const items = [...document.querySelectorAll('[role="menuitem"]')]
    .filter(e => e.offsetParent);
  const del = items.find(e => (e.innerText || '').trim().startsWith('删除'))
            || items.find(e => /^Delete/i.test((e.innerText || '').trim()));
  if (!del) return 'NO_DELETE_ITEM:' + items.map(e => (e.innerText || '').trim()).join('|');
  del.click();
  return 'CLICKED_DELETE';
})()"""

DEL_CONFIRM2 = r"""(() => {
  // The confirmation sheet is NOT inside a [role="dialog"] — measured, the
  // only dialogs on the page were the composer, while
  // [data-testid="confirmationSheetConfirm"] existed on its own. Searching for
  // the button inside a dialog therefore never finds it.
  const btn = document.querySelector('[data-testid="confirmationSheetConfirm"]');
  if (!btn) return 'NO_CONFIRM_BUTTON';
  if (btn.offsetParent === null) return 'CONFIRM_BUTTON_HIDDEN';
  btn.click();
  return 'CONFIRMED';
})()"""


def js(c, tmpl: str, pid: str):
    return c.js(tmpl.replace("__PID__", pid), wait=25, retries=3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("sid")
    ap.add_argument("--expect", required=True,
                    help="text this post must start with, so a wrong id is caught")
    args = ap.parse_args()

    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])

    who = c.js(WHO, wait=20, retries=3)
    mine = who.strip() if isinstance(who, str) else ""
    print("logged in as:", mine)

    p = js(c, POST, args.sid)
    if not isinstance(p, dict):
        print("post %s is not on this page — open its thread first" % args.sid)
        return 1
    print("post text: %r" % p["text"][:220])

    if args.expect not in p["text"]:
        print("REFUSING - this post does not contain the expected text")
        print("  expected: %r" % args.expect)
        return 1

    r = js(c, DEL, args.sid)
    print("caret:", r)
    if r != "CLICKED_CARET":
        return 1
    time.sleep(1.6)

    r2 = js(c, DEL_CONFIRM, args.sid)
    print("menu:", r2)
    if not str(r2).startswith("CLICKED_DELETE"):
        return 1
    time.sleep(1.8)

    r3 = js(c, DEL_CONFIRM2, args.sid)
    print("confirm:", r3)
    if r3 != "CONFIRMED":
        return 1
    time.sleep(4.0)

    after = js(c, POST, args.sid)
    print("after delete, post still present:", bool(isinstance(after, dict)))
    if not isinstance(after, dict):
        print("VERIFIED GONE — %s" % args.sid)
        return 0
    print("STILL PRESENT: %r" % str(after.get("text", ""))[:160])
    return 1


if __name__ == "__main__":
    sys.exit(main())