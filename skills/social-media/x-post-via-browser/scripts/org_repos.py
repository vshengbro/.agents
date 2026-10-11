#!/usr/bin/env python3
"""The GitHub owners whose repositories this account is allowed to promote.

Both reply paths read this list. They disagreed once: the browser checked for
any github.com link at all, the API checked three names. A reply that carried
someone else's repository passed one and failed the other, which is the shape
of a rule that is only accidentally enforced.

The list is DERIVED, not written. owner_set() reads the real GitHub remotes of
every checkout under the code directory and keeps the owners those remotes
actually point at, so a rename — an account gaining an org while still owning
the old one — cannot leave the gate refusing a link to this account's own work.
A hand-written list here goes stale on exactly that event, and the failure is
silent: the reply is refused and the post is burned, with nothing on screen to
say why. There is no hand-written list. There is no list to edit.

WHEN NOTHING CAN BE DERIVED, IT REFUSES. An owner set that resolves to nothing
is not "promote anything", and it is emphatically not an empty alternation
compiled into a pattern that then matches whatever else it is handed. It is a
refusal with a reason attached, and both reply paths print that reason. Narrow
is safe; wide and silent is the one failure this module exists to prevent, so
X_GITHUB_OWNERS is the only override and it is explicit whenever it is used.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                           # noqa: E402

# A repository with no push in this long is not a promotion target: it is
# being abandoned, and a post about it is a post about something dead.
_DEFAULT_STALE_DAYS = 14

_OWNERS_CACHE: tuple[str, ...] | None = None

# (owner, repo) from a github remote. Three separator forms are in use on this
# machine and all three have to work: scp-style `git@github.com:owner/repo.git`,
# https `https://github.com/owner/repo`, and SSH-over-443
# `ssh://git@ssh.github.com:443/owner/repo.git`. The port is consumed by an
# explicit `:\d+` before the separator is taken, because otherwise `[:/]` reads
# "443" as the owner and hands the gate an owner nobody owns — and the first
# two forms then stop matching entirely, which is a gate that refuses the
# account's own repository with no error anywhere.
_REMOTE_RE = re.compile(r"github\.com(?::\d+)?[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")

# A pattern that cannot match any string at all. This is what the gate becomes
# when no owner resolves: not the empty alternation (which compiles to a real
# URL pattern with a blank owner segment and can still match), but something
# with no way to succeed.
_NEVER = re.compile(r"(?!)")


def code_dir() -> Path:
    """Where this account's own repositories are checked out.

    HERMES_CODE_DIR, else ~/code. Read at CALL time for the same reason every
    other value here is read: a module-level Path is frozen before a later
    export can change it, and whoever sets it is normally a cron wrapper that
    runs after the import chain has already started.
    """
    raw = (os.environ.get("HERMES_CODE_DIR") or "").strip()
    return Path(raw).expanduser() if raw else Path.home() / "code"


def stale_days() -> int:
    """Days without a push past which a checkout stops being a target."""
    raw = (os.environ.get("HERMES_STALE_REPO_DAYS") or "").strip()
    try:
        return int(raw) if raw else _DEFAULT_STALE_DAYS
    except ValueError:
        return _DEFAULT_STALE_DAYS


def _remote_url(d: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(d), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _checkouts() -> list[Path]:
    base = code_dir()
    if not base.is_dir():
        return []
    return [d for d in sorted(base.iterdir()) if (d / ".git").exists()]


def _owner_repo(url: str) -> tuple[str, str] | None:
    """(owner, repository) for a github remote, or None.

    A remote may embed a credential; only the owner and repository are taken
    out, and the raw url is never returned or printed anywhere.
    """
    m = _REMOTE_RE.search(url or "")
    return (m.group(1), m.group(2)) if m else None


def owner_set(force: bool = False) -> tuple[str, ...]:
    """The GitHub owners this account actually has remotes under.

    X_GITHUB_OWNERS wins outright when it is set, and that is the ONLY hand-
    written path in. Otherwise the owners are derived from the real remotes of
    every checkout under code_dir(), so a renamed org or a newly added
    repository is picked up without editing this file.

    Returns () when neither source yields anything, and () here is a REFUSAL
    rather than a wildcard — see owner_reason() for the wording, and note that
    repo_re() becomes unmatchable and check() refuses rather than matches. A
    caller that needs to know which of the two happened asks owner_reason(),
    which is "" only when owners really resolved.
    """
    global _OWNERS_CACHE
    if _OWNERS_CACHE is not None and not force:
        return _OWNERS_CACHE
    env = xconfig.github_owners()
    if env:
        _OWNERS_CACHE = env
        return _OWNERS_CACHE
    found: set[str] = set()
    for d in _checkouts():
        hit = _owner_repo(_remote_url(d))
        if hit:
            found.add(hit[0])
    _OWNERS_CACHE = tuple(sorted(found))
    return _OWNERS_CACHE


def owner_reason() -> str:
    """Why promotion is refused, or "" when owners really resolved.

    The refusal has to name WHICH of the two things is wrong — no readable
    checkout to derive from, or nothing in it with a github remote — because
    from the outside "the gate closed" and "the gate was never opened" look
    identical, and one of them is a setup problem the user can fix.
    """
    if owner_set():
        return ""
    where = code_dir()
    if xconfig.github_owners():
        return ""                       # unreachable: owners were resolved
    if not where.is_dir():
        return (f"no GitHub owners resolved: {where} is not a readable "
                f"directory and X_GITHUB_OWNERS is unset — refusing to "
                f"promote anything rather than widening the gate")
    if not _checkouts():
        return (f"no GitHub owners resolved: {where} holds no git checkout "
                f"and X_GITHUB_OWNERS is unset — refusing to promote "
                f"anything rather than widening the gate")
    return (f"no GitHub owners resolved: no checkout under {where} has a "
            f"github.com origin remote and X_GITHUB_OWNERS is unset — "
            f"refusing to promote anything rather than widening the gate")


def repo_name() -> dict[str, str]:
    """Map owner -> repository name, read off the real remotes in code_dir().

    Never raises: an unreadable remote or a missing checkout is skipped, so a
    broken directory cannot block a post.
    """
    out: dict[str, list[str]] = {}
    for d in _checkouts():
        hit = _owner_repo(_remote_url(d))
        if hit:
            out.setdefault(hit[0], []).append(hit[1])
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
        return (time.time() - int(ts)) / 86400.0
    except (OSError, subprocess.SubprocessError):
        return None


def promotion_targets() -> list[Path]:
    """Checkouts this account may write a promotion post about.

    Derived live: a checkout owned by one of owner_set() and pushed to
    recently. A repository whose last push is older than stale_days() is being
    abandoned, so it is excluded rather than promoted. With no owners resolved
    this returns nothing at all — the narrow answer, never the wide one.
    """
    owners = set(owner_set())
    if not owners:
        return []
    hits = []
    for d in _checkouts():
        hit = _owner_repo(_remote_url(d))
        if not hit or hit[0] not in owners:
            continue
        days = last_push_days(d)
        if days is not None and days > stale_days():
            continue
        hits.append(d)
    return hits


# A repository URL the account is allowed to put in a post or a reply.
#
# Built AT CALL TIME, not at import: owner_set() reads real remotes, and a
# regex compiled at module load would freeze whatever the owners were before
# the first checkout was read — which is exactly the staleness this module
# exists to remove. Keyed on the owner tuple it was built from, so a forced
# refresh of the owners refreshes the pattern with them.
_REPO_RE: re.Pattern[str] | None = None
_REPO_RE_OWNERS: tuple[str, ...] | None = None


def repo_re() -> re.Pattern[str]:
    global _REPO_RE, _REPO_RE_OWNERS
    owners = owner_set()
    if _REPO_RE is not None and _REPO_RE_OWNERS == owners:
        return _REPO_RE
    _REPO_RE_OWNERS = owners
    if not owners:
        _REPO_RE = _NEVER
    else:
        _REPO_RE = re.compile(
            r"https://github\.com/(" + "|".join(
                re.escape(o) for o in owners) + r")/[\w.-]+")
    return _REPO_RE


def find_repo(text: str) -> str | None:
    """Return this account's repository in this text, or None.

    A bare github.com link to somewhere else is not a promotion of this
    account's work, and one that names no repository at all is not a
    promotion of anything. When no owner resolved, nothing matches — see
    owner_reason(), which says why, because "no match" on its own reads as
    "the copy has no link" and the real problem is setup.
    """
    if not owner_set():
        return None
    m = repo_re().search(text or "")
    return m.group(0) if m else None


def check(text: str) -> str | None:
    """Return the repository if the text carries one, else the reason."""
    if not owner_set():
        return owner_reason()
    return find_repo(text) or (
        "no repository from this account's GitHub owners: "
        + ", ".join(owner_set()))