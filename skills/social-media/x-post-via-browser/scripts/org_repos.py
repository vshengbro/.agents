#!/usr/bin/env python3
"""The GitHub owners whose repositories this account is allowed to promote.

Both reply paths read this list. They disagreed once: the browser checked for
any github.com link at all, the API checked three names. A reply that carried
someone else's repository passed one and failed the other, which is the shape
of a rule that is only accidentally enforced.

The list is DERIVED, not written. owner_set() reads the real GitHub remotes
of every checkout under ~/code and keeps the owners those remotes actually
point at, so a rename — the account gained the org vshengbro while still
owning eastspire — cannot leave the gate refusing a link to this account's
own work. A hand-written list here goes stale on exactly that event, and the
failure is silent: the reply is refused and the post is burned, with nothing
on screen to say why.

Both orgs below are currently derived and live:
    crates-dev      ctares
    euv-dev         euv
    hyperlane-dev   hyperlane, hyperlane-mcp-upload, hyperlane-quick-start
    docs-pages      docs, pages
    eastspire       FrameworkBenchmarks, anent, web-frameworks
    vshengbro       vice-city-web

Adding an owner by hand is possible but unnecessary: it is picked up from the
remotes. A repository the account does not own is refused no matter which
org it is under.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

# Hand-written owner names. Kept as a FALLBACK for the case where ~/code is
# absent or unreadable; owner_set() below prefers what the real remotes say.
# The moment a checkout exists, these are advisory only — which is what stops
# a rename from silently refusing this account's own repository.
_OWNERS_FALLBACK = (
    "crates-dev",
    "euv-dev",
    "hyperlane-dev",
    "docs-pages",
    "eastspire",
    "vshengbro",
)

# Where this account's own repositories are checked out. Derived from the
# remotes, not from a list of project names.
CODE = Path(os.environ.get("HERMES_CODE_DIR", str(Path.home() / "code")))

# A repository with no push in this long is not a promotion target: it is
# being abandoned, and a post about it is a post about something dead.
STALE_DAYS = int(os.environ.get("HERMES_STALE_REPO_DAYS", "14"))

_OWNERS_CACHE: tuple[str, ...] | None = None


def _remote_url(d: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(d), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _checkouts() -> list[Path]:
    if not CODE.is_dir():
        return []
    return [d for d in sorted(CODE.iterdir()) if (d / ".git").exists()]


def owner_set(force: bool = False) -> tuple[str, ...]:
    """The GitHub owners this account actually has remotes under.

    Read from ~/code, so a renamed org or a newly added repository is picked up
    without editing this file. Falls back to the hand-written names only when
    no checkout can be read, so an empty ~/code cannot silently widen the gate
    to nothing at all.
    """
    global _OWNERS_CACHE
    if _OWNERS_CACHE is not None and not force:
        return _OWNERS_CACHE
    found: set[str] = set()
    for d in _checkouts():
        url = _remote_url(d)
        # A remote may embed a credential; only the owner is taken, and the
        # raw url is never returned or printed.
        m = re.search(r"github\.com[:/]([\w.-]+)/", url)
        if m:
            found.add(m.group(1))
    _OWNERS_CACHE = tuple(sorted(found)) if found else _OWNERS_FALLBACK
    return _OWNERS_CACHE


def repo_name() -> dict[str, str]:
    """Map owner -> repository name, read off the real remotes in CODE.

    Never raises: an unreadable remote or a missing checkout is skipped, so a
    broken directory cannot block a post.
    """
    out: dict[str, list[str]] = {}
    for d in _checkouts():
        url = _remote_url(d)
        m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$", url)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return {o: ", ".join(sorted(set(n))) for o, n in out.items()}


def last_push_days(repo_path: Path) -> float | None:
    """Days since this checkout's last push to origin/master, or None."""
    try:
        ts = subprocess.run(
            ["git", "-C", str(repo_path), "log", "-1", "--format=%ct",
             "origin/master"],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if not ts.isdigit():
            return None
        import time
        return (time.time() - int(ts)) / 86400.0
    except (OSError, subprocess.SubprocessError):
        return None


def promotion_targets() -> list[Path]:
    """Checkouts this account may write a promotion post about.

    Derived live: a checkout owned by one of owner_set() and pushed to
    recently. A repository whose last push is older than STALE_DAYS is being
    abandoned, so it is excluded rather than promoted.
    """
    owners = set(owner_set())
    hits = []
    for d in _checkouts():
        url = _remote_url(d)
        m = re.search(r"github\.com[:/]([\w.-]+)/", url)
        if not m or m.group(1) not in owners:
            continue
        days = last_push_days(d)
        if days is not None and days > STALE_DAYS:
            continue
        hits.append(d)
    return hits

# A repository URL the account is allowed to put in a post or a reply.
#
# Built AT CALL TIME, not at import: owner_set() reads ~/code, and a regex
# compiled at module load would freeze whatever the owners were before the
# first checkout was read — which is exactly the staleness this module exists
# to remove. Cached after the first build because the answer does not change
# within a run.
_REPO_RE: re.Pattern[str] | None = None


def repo_re() -> re.Pattern[str]:
    global _REPO_RE
    if _REPO_RE is None:
        _REPO_RE = re.compile(
            r"https://github\.com/(" + "|".join(
                re.escape(o) for o in owner_set()) + r")/[\w.-]+")
    return _REPO_RE


def find_repo(text: str) -> str | None:
    """Return the organisation repository in this text, or None.

    A bare github.com link to somewhere else is not a promotion of this
    account's work, and one that names no repository at all is not a
    promotion of anything.
    """
    m = repo_re().search(text or "")
    return m.group(0) if m else None


def check(text: str) -> str | None:
    """Return the repository if the text carries one, else a reason."""
    return find_repo(text) or (
        "no repository from this account's GitHub owners: "
        + ", ".join(owner_set()))
