#!/usr/bin/env python3
"""Empty the focused Draft editor completely, by block, and verify.

document.execCommand('delete') clears ONE block and stops at the next
boundary, so a multi-paragraph composer keeps everything after the first
block. Measured here: a 74-character two-paragraph body came back as 172
characters containing fragments of the PREVIOUS attempt. Every comparison
after that was measuring a mix of two bodies, which is how "insertText drops
CJK" and "key events garble" both looked true when neither was.

So: delete repeatedly until the editor is empty, verifying between passes, and
refuse to report success on anything else. This only ever touches the focused
Draft editor, never a reply box holding someone else's draft.

    python3 empty_draft_editor.py 9240
"""
from __future__ import annotations

import sys
import time

import cdp

ONE_PASS = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent && (e.innerText || '').length);
  const e = ed.find(x => x === document.activeElement) || ed[0];
  if (!e) return {'found': false};
  e.focus();
  const sel = window.getSelection(), r = document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges(); sel.addRange(r);
  document.execCommand('delete');
  sel.removeAllRanges();
  return {'found': true, 'len': (e.innerText || '').length};
})()"""

STATE = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  return ed.map(e => ({
    'len': (e.innerText || '').length,
    'blocks': e.querySelectorAll('[data-block="true"]').length,
    'focused': e === document.activeElement,
  }));
})()"""


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "9240"
    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])

    for i in range(15):
        st = c.js(STATE, wait=20, retries=3)
        if not isinstance(st, list):
            print("could not read the editors: %r" % (st,))
            return 1
        dirty = [e for e in st if e.get("len")]
        if not dirty:
            print("VERIFIED empty — every composer is blank")
            return 0
        res = c.js(ONE_PASS, wait=20, retries=3)
        if not isinstance(res, dict) or not res.get("found"):
            print("no editable composer to clear: %r" % (res,))
            return 1
        print("  pass %d: %d chars, %d blocks -> %d"
              % (i + 1, dirty[0]["len"], dirty[0]["blocks"], res["len"]))
        time.sleep(0.35)

    st = c.js(STATE, wait=20, retries=2)
    print("NOT EMPTY after 15 passes: %r" % (st,))
    return 1


if __name__ == "__main__":
    sys.exit(main())