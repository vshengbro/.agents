#!/usr/bin/env python3
"""Clear the X composer back to empty, in place — but only OUR text.

The composer is the user's surface and clearing it is normally forbidden. This
script exists for one case: the composer holds text that a previous AUTOMATED
run typed and then abandoned — the publisher refused that text after it was
already typed (a separator rule, a control off screen) and left it behind. That
text was never the user's. Leaving it blocks every later attempt forever, so
the rule meant to protect the user's draft becomes the reason the task can
never finish.

Two guards, because the cost of being wrong is the user's own unsent words:

1. The editor is chosen BY ITS TEXT, never by position. X mounts more than one
   contenteditable (a draft box, a reply box, a quote box); picking by index
   clears whichever happens to be last in DOM order. Measured on this page: two
   composers, neither holding our text — an index-based clear would have wiped
   an unrelated one.

2. The text must match what the caller says this run typed. No match, or more
   than one match, refuses and exits non-zero without touching anything.

Never reloads, never navigates, never opens a tab, never takes the mouse or OS
focus. Never returns 0 unless it verified afterwards that our text is gone.

    python3 clear_own_composer.py 9240 --contains "euv 是一个声明式"
"""
from __future__ import annotations

import argparse
import json
import sys

import cdp

# cdp.Cdp.js() evaluates a bare expression string with no parameter binding, so
# the needle is spliced in as a JSON string literal. json.dumps is what makes
# that safe: it escapes quotes, backslashes and newlines, so a needle cannot
# terminate the literal and inject into the expression.
READ = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  return ed.map(e => ({
    'len': (e.innerText || '').length,
    // The FULL text, not a slice: verifying "our needle is gone" against a
    // truncated read reports NOT CLEARED for a composer that is actually empty
    // whenever the needle happens to sit past the cut. Measured: a 31-char
    // composer holding a 30-char URL was refused as un-cleared.
    'text': (e.innerText || ''),
  }));
})()"""

SELECT = r"""(() => {
  const NEEDLE = __NEEDLE__;
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const hit = ed.filter(e => (e.innerText || '').includes(NEEDLE));
  return {'editors': ed.length, 'matched': hit.length};
})()"""

# One execCommand('delete') clears a block but stops at the next boundary:
# measured 371 -> 1, so the caller loops rather than believing one pass.
#
# The pass reports ok only when the editor is empty of EVERYTHING. Reporting
# 'still has the needle' instead is what caused a false "cleared" verdict: an
# editor reduced to a single newline still .includes(needle)==false, so the
# loop's retry check treated it as gone while 1 character remained. The check
# must be "is this editor empty", never "does this editor still match".
CLEAR = r"""(() => {
  const NEEDLE = __NEEDLE__;
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const hit = ed.filter(e => (e.innerText || '').includes(NEEDLE));
  if (!hit.length) return {'ok': false, 'why': 'no editor holds that text'};
  if (hit.length > 1)
    return {'ok': false, 'why': hit.length + ' editors hold it — refusing'};
  const e = hit[0];
  const sel = window.getSelection();
  const r = document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges();
  sel.addRange(r);
  const before = (e.innerText || '').length;
  const ok = document.execCommand('delete');
  sel.removeAllRanges();
  const after = (e.innerText || '').length;
  return {'ok': after === 0, 'before': before, 'after': after,
          'exec': ok, 'rest': (e.innerText || '').slice(0, 80)};
})()"""


def _js(c, tmpl: str, needle: str):
    return c.js(tmpl.replace("__NEEDLE__", json.dumps(needle)),
                wait=20, retries=3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("port")
    ap.add_argument("--contains", required=True,
                    help="text this automated run typed and abandoned")
    args = ap.parse_args()

    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])

    editors = c.js(READ, wait=20, retries=3)
    if not isinstance(editors, list):
        print("could not read the composers: %r" % (editors,))
        return 1
    if not any(e.get("len") for e in editors):
        print("every composer is already empty — nothing to clear")
        return 0

    probe = _js(c, SELECT, args.contains)
    if not isinstance(probe, dict):
        print("could not probe the composers: %r" % (probe,))
        return 1
    matched, total = probe.get("matched", 0), probe.get("editors", 0)
    if matched == 0:
        print("REFUSING - no composer holds the text this run abandoned.")
        print("  %d composer(s) visible:" % total)
        for e in editors:
            if e.get("len"):
                print("    %4d chars | %r" % (e["len"], e.get("text", "")[:60]))
        return 1
    if matched > 1:
        print("REFUSING - %d composers hold that text; not guessing" % matched)
        return 1

    passes = 0
    for i in range(12):
        res = _js(c, CLEAR, args.contains)
        if not isinstance(res, dict):
            print("clear pass %d returned nothing usable" % (i + 1))
            return 1
        passes += 1
        if res.get("ok"):
            break
        # Residue left. Re-select by the REMAINDER the last pass reported,
        # never by the original needle: once the editor is a single newline it
        # no longer contains the needle, and re-matching by needle reported a
        # cleared composer that still held a character.
        rest = res.get("rest") or ""
        if not rest.strip():
            break                       # whitespace only — effectively empty
        res = _js(c, CLEAR, rest)
        if not isinstance(res, dict) or not res.get("ok"):
            print("clear pass %d stopped: %r" % (i + 1, res))
            break
        passes += 1
        if res.get("ok"):
            break

    final = c.js(READ, wait=15, retries=2)
    if not isinstance(final, list):
        print("could not verify: %r" % (final,))
        return 1
    rest = [e for e in final
            if e.get("len") and args.contains in (e.get("text") or "")]
    if rest:
        print("NOT CLEARED - our text remains in %d composer(s)" % len(rest))
        return 1
    print("VERIFIED cleared in %d pass(es) — our text is gone" % passes)
    return 0


if __name__ == "__main__":
    sys.exit(main())