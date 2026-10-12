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

# ONE surface: headed, always.
#
# This used to be a parameter, defaulting to headless, because the two jobs
# had measured differently: replying needed headless, publishing measured
# better headed. The account owner has since ruled the headed surface the only
# one this skill uses, so the parameter and the headless branch are gone.
#
# What that ruling costs is recorded rather than deleted, because it is the
# reason the rule exists: on a HEADED window a reply click routes to a
# context-less /compose/post — the main composer, where typing publishes a
# standalone post where a reply was meant, and every gate then refuses.
# Re-measured on a clean /home, headed also mounted nothing at all:
# element.click() navigated with one editor and zero dialog editors, and a
# mouse press at the control's coordinates did the same. The reply leg may
# therefore need re-measuring on this surface before it is trusted again —
# it is blocked pending that, not working.
HEADED = "headed"
DEFAULT_MODE = HEADED


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


def launch() -> bool:
    """Start the real-profile copy HEADED, with no tab of its own.

    Headed is the only surface this skill uses, by the account owner's
    ruling. --headed is passed explicitly rather than relying on the
    launcher's own default, so the surface this skill runs on is stated by
    this file and cannot drift if the launcher's default changes.
    """
    if not os.path.exists(LAUNCH):
        print(f"launcher not found at {LAUNCH}")
        return False
    print(f"browser is down — launching via {LAUNCH} (headed)", flush=True)
    cmd = ["bash", LAUNCH, "--port", str(PORT), "--fresh", "--no-tab",
           "--headed"]
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
    # Headed, always. There is no mode argument to pass anymore: a headless
    # fallback here would put the reply leg back on a surface where a reply
    # publishes as a standalone post.
    for _ in range(20):
        if cdp_up():
            break
        if not launch():
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
