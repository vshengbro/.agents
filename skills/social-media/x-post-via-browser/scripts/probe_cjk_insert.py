#!/usr/bin/env python3
"""Probe: does one Input.insertText drop CJK, and at what length?

The publisher sends a whole post body in one insertText and a 597-character
Chinese body came back holding only its 30-character ASCII URL. The reply path
sends one key event per character and Chinese replies land fine, so the two
paths differ. This measures the boundary instead of guessing at it.

Read-only apart from text typed into the composer, which is cleared only
through clear_own_composer.py afterwards. No navigation, no reload, no mouse.

    python3 probe_cjk_insert.py 9240
"""
from __future__ import annotations

import json
import sys
import time

import cdp

# Bind to the EMPTY editor, never to the last one in DOM order. This page
# mounts more than one composer and one of them holds text this script did not
# type — typing into it and then clearing it would destroy it. Pick an editor
# with no text in it; refuse if there is none.
FOCUS = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const empty = ed.filter(e => !(e.innerText || '').trim());
  const e = empty[0];
  if (!e) return {'ok': false, 'why': 'no empty editor to type into',
                  'n': ed.length};
  e.focus();
  return {'ok': true, 'n_editors': ed.length, 'used_empty': empty.length};
})()"""

READ = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const empty = ed.filter(e => !(e.innerText || '').trim());
  const e = empty[0] || ed[ed.length - 1];
  return {'len': (e.innerText || '').length, 'text': (e.innerText || '')};
})()"""

# Clear only the editor this probe typed into: the one that was empty.
CLEAR = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const dirty = ed.filter(e => (e.innerText || '').includes('探测') ||
                                (e.innerText || '').includes('PROBEABC') ||
                                (e.innerText || '').includes('probe ') ||
                                (e.innerText || '').includes('探测'));
  const e = dirty[0];
  if (!e) return {'ok': false, 'why': 'no editor holds probe text'};
  const sel = window.getSelection(), r = document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges(); sel.addRange(r);
  document.execCommand('delete');
  sel.removeAllRanges();
  return {'ok': true, 'len': (e.innerText || '').length};
})()"""

CASES = [
    ("ascii short", "PROBEABC abcdefghij"),
    ("cjk short", "探测中文短"),
    ("cjk medium", "探测中文中等长度" * 6),
    ("cjk long", "探测中文较长的一段内容用来测试长度阈值" * 10),
    ("mixed", "probe " + "中文混合" * 20 + " https://github.com/euv-dev/euv"),
]


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "9240"
    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])

    print(f"{'case':14s} {'want':>5s} {'got':>5s}  verdict")
    for name, body in CASES:
        f = c.js(FOCUS, wait=20, retries=3)
        if not isinstance(f, dict) or not f.get("ok"):
            print("  cannot focus an editor:", f)
            return 1
        c.js(CLEAR, wait=15, retries=2)
        time.sleep(0.4)
        c.send("Input.insertText", text=body, wait=40, retries=4)
        time.sleep(1.6)
        st = c.js(READ, wait=20, retries=3)
        got = st.get("text", "") if isinstance(st, dict) else ""
        exact = got.strip() == body.strip()
        print(f"{name:14s} {len(body):>5d} {len(got):>5d}  "
              f"{'exact' if exact else 'LOSS'}"
              + ("" if exact else f"  kept={got[:24]!r}"))
        c.js(CLEAR, wait=15, retries=2)
        time.sleep(0.3)
    return 0


if __name__ == "__main__":
    sys.exit(main())