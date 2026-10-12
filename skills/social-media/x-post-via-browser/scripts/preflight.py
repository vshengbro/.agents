#!/usr/bin/env python3
"""Read every precondition the publish path depends on, and refuse loudly.

Written after a measured run where four of these were quietly wrong and each
would have failed the publish in a way that read as something else: a
backgrounded tab that looks exactly like a working one, a composer testid
that matches nothing, a non-empty box that must never be cleared.

Everything here is a READ. It clicks nothing, types nothing and publishes
nothing, so it is safe to run against a signed-in account at any time — and
running it is cheaper than discovering the problem halfway through typing a
post.

Exit 0 means every precondition holds. Exit 1 names what does not, and the
run stops. A preflight that cannot fail is not a preflight.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cdp as C                                          # noqa: E402
import xconfig                                            # noqa: E402

STATE = """(() => {
  const vis = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.offsetParent !== null);
  let len = 0;
  for (const n of vis) for (const c of n.childNodes) len += (c.textContent||'').length;
  return JSON.stringify({
    visibility: document.visibilityState,
    url: location.pathname,
    editors_visible: vis.length,
    composer_len: len,
    buttons: [...document.querySelectorAll('button[data-testid]')]
      .filter(b => /tweetButton/.test(b.dataset.testid))
      .map(b => b.dataset.testid + (b.disabled ? ':DISABLED' : ':enabled')),
    compose_control: !!document.querySelector(
      '[data-testid="SideNav_NewTweet_Button"]'),
    compose_fallback: !!document.querySelector('a[href*="/compose/post"]')
  });
})()"""

ACTIVATE = ("document.visibilityState")


def js(c, tpl, wait=25, retries=5):
    r = c.js(tpl, wait=wait, retries=retries)
    if isinstance(r, str):
        try:
            return json.loads(r)
        except ValueError:
            return {"_raw": r[:200]}
    return r


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else xconfig.port()
    C.set_port(port)
    pages = [t for t in C.tabs("page") if xconfig.is_site_tab(t.get("url", ""))]
    if not pages:
        print("FAIL  no x.com tab — run ensure_browser.py first")
        return 1
    c = C.Cdp(pages[0]["webSocketDebuggerUrl"])

    # A hidden tab is the one failure that makes every later check lie, so it
    # is reported first and separately — and activateTarget is offered as the
    # remedy because it is the only write-ish step in the whole flow and it
    # moves no pointer and takes no OS focus.
    vis = c.js(ACTIVATE)
    print(f"visibility : {vis}   url: {c.js('location.pathname')}")
    if vis != "visible":
        print("FAIL  tab is hidden — the editor may never mount, and a hidden "
              "tab is indistinguishable from a working one.")
        print("      fix: Target.activateTarget on this target id, then re-run. "
              f"(target {pages[0]['id']})")
        c.close()
        return 1

    st = js(c, STATE)
    if "_raw" in st:
        print("FAIL  could not read the page:", st["_raw"])
        c.close()
        return 1

    print(f"editors    : {st['editors_visible']} visible, "
          f"composer {st['composer_len']} chars")
    print(f"buttons    : {st['buttons'] or 'none mounted'}")

    checks = [
        ("exactly one visible editor (two is the decoy pair)",
         st["editors_visible"] == 1),
        ("composer is empty (a non-empty one is refused, never cleared)",
         st["composer_len"] == 0),
        ("compose control found (SideNav_NewTweet_Button)",
         st["compose_control"] is True),
        ("a post button is mounted (only tweetButtonInline is reliable)",
         len(st["buttons"]) > 0),
    ]
    ok = True
    for label, good in checks:
        ok = ok and good
        print(f"{'PASS' if good else 'FAIL'}  {label}")
    if not st["compose_control"] and st["compose_fallback"]:
        print("      note: only the a[href*=\"/compose/post\"] fallback is "
              "present; the real testid is missing on this build.")
    c.close()
    print("\npreflight: " + ("all checks pass" if ok else "STOP — do not type"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())