#!/usr/bin/env python3
"""Verify publish.py's type_keys() delivers a CJK body intact, without posting.

The publisher's text compare is the real gate, so this drives the same code
path the publisher uses and then applies the publisher's own comparison. It
never clicks send. The text it types is cleared afterwards, identified by a
marker unique to this run.

    python3 verify_type_keys.py 9240
"""
from __future__ import annotations

import sys
import time

import cdp
import publish as P

# A CJK body with the same shape as the real copy: several paragraphs, mixed
# ASCII identifiers, and a URL at the end preceded by one space.
BODY = (
    "探测中文输入路径 ZZPROBEZZ。\n\n"
    "这里有一段汉字正文，用来确认逐字符按键事件能不能完整送达。\n"
    "data-euv-id 是这次要验证的标识符。\n\n"
    "结论：如果 LEN 与 want 相等且 match=True，修复生效。 "
    "https://github.com/euv-dev/euv"
)

READ = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const empty = ed.filter(e => !(e.innerText || '').trim());
  const e = empty[0] || ed[ed.length - 1];
  return {'len': (e.innerText || '').length, 'text': (e.innerText || '')};
})()"""

CLEAR = r"""(() => {
  const ed = [...document.querySelectorAll('div[contenteditable="true"]')]
    .filter(e => e.offsetParent);
  const hit = ed.filter(e => (e.innerText || '').includes('ZZPROBEZZ'));
  if (!hit.length) return {'ok': false, 'why': 'no editor holds the marker'};
  const e = hit[0];
  const sel = window.getSelection(), r = document.createRange();
  r.selectNodeContents(e);
  sel.removeAllRanges(); sel.addRange(r);
  document.execCommand('delete');
  sel.removeAllRanges();
  return {'ok': (e.innerText || '').length < 40,
          'len': (e.innerText || '').length};
})()"""


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "9240"
    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])

    print("body: %d characters, %d non-ASCII"
          % (len(BODY), sum(1 for ch in BODY if ord(ch) > 127)))
    # Focus the real Draft editor FIRST, exactly as publish.py does. Typing
    # without this step measures nothing: key events go to whatever element
    # holds focus, and on this page that is nothing.
    st0 = P.focus_editor(c)
    if not isinstance(st0, dict) or not st0.get("focused"):
        print("could not focus the Draft editor: %r" % (st0,))
        return 1
    print("editor focused")
    P.type_keys(c, BODY)
    st = c.js(READ, wait=25, retries=3)
    if not isinstance(st, dict):
        print("could not read the editor: %r" % (st,))
        return 1
    got = st.get("text") or ""
    fg, ft = P.canon(got), P.canon(BODY)
    ok = fg == ft and len(fg) <= len(ft)
    print("LEN %s want %s exact=%s" % (st.get("len"), len(BODY), ok))
    if not ok:
        print("got : %r" % got[:120])
        print("want: %r" % BODY[:120])
    else:
        print("CJK body delivered intact through type_keys")

    cl = c.js(CLEAR, wait=20, retries=2)
    print("cleared:", cl)
    time.sleep(0.5)
    final = c.js(READ, wait=15, retries=2)
    print("final editor length:",
          final.get("len") if isinstance(final, dict) else final)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())