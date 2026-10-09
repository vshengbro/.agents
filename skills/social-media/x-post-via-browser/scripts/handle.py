#!/usr/bin/env python3
"""The logged-in X handle, read live from the page.

The account was renamed (eastspire_sheng -> vshengbro) and every script that
hardcoded the old name broke in a different way: reply verification stopped
matching the account's own replies, and the feed filters stopped excluding
the account's own posts, so one run replied to its own promotional posts.
The nav bar's profile link always carries the current handle, so read it;
the constant below is only the fallback for a page that has not painted yet.
"""

FALLBACK = "vshengbro"

PROFILE_HANDLE = """(() => {
  const a = document.querySelector('[data-testid="AppTabBar_Profile_Link"]');
  if (!a) return '';
  return (a.getAttribute('href') || '').replace(/^\\//, '');
})()"""


def live(c) -> str:
    """Current handle from the open tab, or FALLBACK when unreadable."""
    try:
        r = c.js(PROFILE_HANDLE, wait=15, retries=3)
        h = (r or "").strip().strip('"').strip().lstrip("/")
        return h or FALLBACK
    except Exception:
        return FALLBACK
