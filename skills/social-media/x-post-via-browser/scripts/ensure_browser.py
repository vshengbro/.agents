#!/usr/bin/env python3
"""Make sure a usable x.com tab exists, starting what is missing.

Three states, three actions, and nothing more:

  browser down          launch it through the real-profile launcher
  up but no x.com tab   open ONE tab at the composer
  up with an x.com tab  do nothing at all

The launcher is chrome-real-profile-launch/scripts/run.sh, not a raw
`Google Chrome --remote-debugging-port`, because the copy of the profile is
what carries the login. --no-tab is passed to it so the launcher does not open
a page of its own; this script decides what the one tab shows.

Opening a tab is a page load, and a page load makes the user confirm it in
their UI. That is why this is a separate script with a single narrow job and
the commit gate exempts only THIS FILE: every other script in the skill stays
forbidden from loading a page, so "the publisher opened a tab" remains a
defect rather than a shortcut.

  python3 ensure_browser.py [port]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                           # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else xconfig.port()
LAUNCH = xconfig.launcher()
COMPOSE = f"https://{xconfig.site()}/compose/post"

# The surface is a PARAMETER, not a constant, because the two jobs need
# different ones and the measurements that decided that are not a single
# answer: replying needs headless, and publishing measured better headed. See
# launch() for the evidence. Hardcoding either one here forces the other job
# onto the wrong surface.
HEADED = "headed"
HEADLESS = "headless"
DEFAULT_MODE = HEADLESS


def cdp_up() -> bool:
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/json/version", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def x_tabs() -> list[dict]:
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/json/list", timeout=8) as r:
            out = json.load(r)
    except Exception:
        return []
    return [t for t in out
            if t.get("type") == "page" and xconfig.is_site_tab(t.get("url", ""))]


def launch(mode: str = DEFAULT_MODE) -> bool:
    """Start the real-profile copy on the named surface, with no tab of its own.

    `mode` is "headed" or "headless" and is a parameter because the two jobs
    measured DIFFERENTLY. Neither surface is right everywhere, and the
    evidence is worth keeping in full:

    REPLYING needs headless. A HEADED window's reply click routes to a
    context-less /compose/post — the main composer, where typing publishes a
    standalone post where a reply was meant, and every gate then refuses —
    while the headless copy opens the real reply dialog with its parent
    context. Re-measured, headed mounted nothing at all on a clean /home:
    element.click() navigated to /compose/post with one editor and zero
    dialog editors, a full mouse press at the control's coordinates did the
    same, and focus+Enter focused nothing (`data-testid` came back None). The
    identical probe on headless mounted a dialog editor on element.click()
    with focus landing on tweetTextarea_0.

    PUBLISHING measured better headed: headless is also where the composer's
    input path misbehaves — a URL arriving as `https://github.c`, Chinese
    bodies losing whole stretches.

    So callers pass the mode their job needs and this file stops being the
    place where that decision is made by accident. Defaulting to headless is
    the safer of the two: headed can publish where a reply was meant, and that
    mistake is not undoable from the timeline.
    """
    if not os.path.exists(LAUNCH):
        print(f"launcher not found at {LAUNCH}")
        return False
    headed = mode == HEADED
    print(f"browser is down — launching via {LAUNCH} ({mode})", flush=True)
    # --headed is passed ONLY when asked for: the launcher defaults to
    # headless, so omitting it must not silently mean "headed".
    cmd = ["bash", LAUNCH, "--port", str(PORT), "--fresh", "--no-tab"]
    if headed:
        cmd.append("--headed")
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
    tail = (p.stdout + p.stderr).strip().splitlines()[-6:]
    for line in tail:
        print("  " + line)
    return cdp_up()


def open_compose_tab() -> bool:
    """Open exactly one tab at the composer.

    /json/new is a GET, which is the documented way to ask the browser for a
    tab. It is a page load — the one this script exists to perform.
    """
    url = f"http://127.0.0.1:{PORT}/json/new?{COMPOSE}"
    req = urllib.request.Request(url, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            json.load(r)
    except urllib.error.HTTPError as e:
        if e.code not in (405, 501):
            print(f"  open failed: HTTP {e.code}")
            return False
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
                json.load(r)
        except Exception as e:
            print(f"  open failed: {e}")
            return False
    except Exception as e:
        print(f"  open failed: {e}")
        return False
    return True


def main() -> int:
    # The surface this run brings the browser up on: --headed when asked for
    # (publishing, which measured better headed), headless otherwise.
    mode = HEADED if "--headed" in sys.argv[1:] else DEFAULT_MODE
    for _ in range(20):
        if cdp_up():
            break
        if not launch(mode):
            print("could not start the browser")
            return 1
        time.sleep(3)

    for _ in range(20):
        tabs = x_tabs()
        if tabs:
            print(f"ready — {len(tabs)} {xconfig.site()} tab(s) open, "
                  f"using {tabs[0]['url'][:60]}")
            return 0
        print(f"browser is up but has no {xconfig.site()} tab — opening one "
              f"at the composer", flush=True)
        if not open_compose_tab():
            return 1
        # X needs a moment before the Draft editor is queryable; a tab that is
        # opened and immediately driven returns "no visible Draft editor" and
        # looks like a failure rather than a page that has not painted yet.
        for _ in range(10):
            time.sleep(3)
            if x_tabs():
                break
    print(f"{xconfig.site()} tab is not reachable")
    return 1


if __name__ == "__main__":
    sys.exit(main())
