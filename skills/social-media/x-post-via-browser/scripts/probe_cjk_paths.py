#!/usr/bin/env python3
"""Find an input path that delivers a CJK body into X's Draft editor intact.

Measured on this composer, both obvious paths lose Han characters:

  Input.insertText, whole body   597 chars -> only the 30-char ASCII URL
  Input.insertText, clean editor  74 chars -> 0 characters
  one key event per character      74 chars -> 56, three Han dropped

So try the remaining shapes and report what each actually delivers, measured
rather than assumed: insertText per paragraph, insertText with a wait between
paragraphs, and char events in small batches. The winner is the one that
matches the source exactly; a run that matches nothing reports that instead of
naming a winner.

Only the focused Draft editor is typed into, and it is emptied afterwards.
No navigation, no reload, no mouse.

    python3 probe_cjk_paths.py 9240
"""
from __future__ import annotations

import subprocess
import sys
import time

import cdp
import publish as P

BODY = ("中文输入路径探测第一段。\n\n"
        "第二段含 ASCII 与 data-euv-id。 https://github.com/euv-dev/euv")

READ = r"""(() => {
  const all = [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(n => n.className && n.className.indexOf('public-DraftEditor') >= 0
                 && n.offsetParent !== null);
  const e = all.find(x => x === document.activeElement) || all[0];
  return (e && (e.innerText || '')) || '';
})()"""


def read(c) -> str:
    return c.js(READ, wait=20, retries=3) or ""


def empty(port: str) -> None:
    subprocess.run([sys.executable, "empty_draft_editor.py", port],
                   capture_output=True)


def per_paragraph(c) -> None:
    parts = BODY.split("\n\n")
    for i, p in enumerate(parts):
        if i:
            c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13, text="\r")
            c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13)
            time.sleep(0.3)
        c.send("Input.insertText", text=p, wait=30, retries=4)
        time.sleep(0.8)


def per_paragraph_slow(c) -> None:
    parts = BODY.split("\n\n")
    for i, p in enumerate(parts):
        if i:
            c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13, text="\r")
            c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                   code="Enter", windowsVirtualKeyCode=13)
            time.sleep(1.5)
        c.send("Input.insertText", text=p, wait=40, retries=5)
        time.sleep(2.5)


def char_batches(c) -> None:
    text = BODY
    i = 0
    while i < len(text):
        chunk = text[i:i + 8]
        for ch in chunk:
            if ch == "\n":
                c.send("Input.dispatchKeyEvent", type="keyDown", key="Enter",
                       code="Enter", windowsVirtualKeyCode=13, text="\r")
                c.send("Input.dispatchKeyEvent", type="keyUp", key="Enter",
                       code="Enter", windowsVirtualKeyCode=13)
            elif ord(ch) < 0x80:
                c.send("Input.dispatchKeyEvent", type="keyDown", key=ch, text=ch)
                c.send("Input.dispatchKeyEvent", type="keyUp", key=ch)
            else:
                c.send("Input.dispatchKeyEvent", type="char", text=ch)
        time.sleep(0.5)
        i += 8


PATHS = [
    ("insertText per paragraph", per_paragraph),
    ("insertText per paragraph, slow", per_paragraph_slow),
    ("char events in batches of 8", char_batches),
]


def main() -> int:
    port = sys.argv[1] if len(sys.argv) > 1 else "9240"
    tabs = [t for t in cdp.tabs("page") if "x.com" in t.get("url", "")]
    if not tabs:
        print("no x.com tab — run ensure_browser.py first")
        return 1
    c = cdp.Cdp(tabs[0]["webSocketDebuggerUrl"])
    fg, ft = P.canon(BODY), P.canon(BODY)
    print("source: %d chars" % len(BODY))
    winners = []
    for name, fn in PATHS:
        empty(port)
        P.focus_editor(c)
        time.sleep(0.5)
        fn(c)
        time.sleep(1.5)
        got = read(c)
        ok = P.canon(got) == fg
        print("%-32s %3d chars  %s" % (name, len(got),
                                        "EXACT" if ok else "loss"))
        if not ok:
            print("    got: %r" % got[:90])
        else:
            winners.append(name)
    empty(port)
    print("\nexact paths: %s" % (winners or "NONE — no input path is exact"))
    return 0 if winners else 1


if __name__ == "__main__":
    sys.exit(main())