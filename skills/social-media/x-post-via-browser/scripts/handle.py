#!/usr/bin/env python3
"""The logged-in handle, read live from the page.

An account gets renamed, and every script that hardcoded the name broke in a
different way: reply verification stopped matching the account's own replies,
and the feed filters stopped excluding the account's own posts, so one run
replied to its own promotional posts. The nav bar's profile link always
carries the current handle, so read it.

The fallback is NOT a name. It is empty unless X_HANDLE sets one, on purpose:

  an empty fallback fails loudly — the comparison simply matches nothing and
  the caller reports zero of its own posts, which is visible;
  a wrong fallback fails silently — the account's own posts look like a
  stranger's and get filtered, liked or replied to as if they were someone
  else's, and nothing on screen says why.

So this module never names an account. Set X_HANDLE only on a machine where
the page genuinely cannot be read, and expect it to be wrong the first time
the account is renamed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                           # noqa: E402


def fallback() -> str:
    """The configured fallback handle, read at CALL time. Empty by default."""
    return xconfig.handle_fallback()


# Kept under the old name because callers use it as a value; a function is
# called through FALLBACK() below. Anyone importing FALLBACK directly should
# switch to fallback() so a later `export X_HANDLE=...` can take effect.
PROFILE_HANDLE = """(() => {
  const a = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  if (!a) return '';
  return (a.getAttribute('href') || '').replace(/^\\//, '');
})()"""


def live(c) -> str:
    """Current handle from the open tab, else the configured fallback.

    Resolved per call rather than at import: the fallback can be set by an
    export that happens after this module loads, and a constant read at import
    would miss it.
    """
    fb = fallback()
    try:
        r = c.js(PROFILE_HANDLE, wait=15, retries=3)
        h = (r or "").strip().strip('"').strip().lstrip("/")
        return h or fb
    except Exception:
        return fb
