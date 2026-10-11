#!/usr/bin/env python3
"""Every environment-specific value this skill needs, in one place.

This module exists because the values used to live as literals scattered
across fourteen scripts: the debug port 9240, the account name, the launcher's
absolute path under one developer's home directory. Those made the skill
work on exactly one machine and exactly one account, and a copied skill failed
in a way that looked like a browser problem rather than a configuration one.

TWO RULES, and the second one is the one that bites:

1. NO ACCOUNT IS BAKED IN. handle_fallback() returns "" by default. A fallback
   handle exists only to survive a page that has not painted yet; when it is
   wrong, the account's own replies stop matching its own replies and its
   feed filters stop excluding its own posts — which is how a run replies to
   its own promotional posts. An empty fallback fails LOUDLY and safely, which
   beats a plausible name that is wrong on someone else's machine.

2. EVERY FUNCTION READS THE ENVIRONMENT AT CALL TIME. A module-level
   constant is frozen before a later `export` can take effect, and that
   staleness is exactly the bug class this skill already documents elsewhere
   (see org_repos.repo_re(), which builds its pattern lazily for the same
   reason). So nothing here is a constant: no PORT, no LAUNCH, no DEFAULT_*.
   Call the function.

Every value below has a working default. Setting an environment variable is
always optional, and none of them is required for the skill to run.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

# The port file the real-profile launcher writes. A module may change the port
# it launches on; reading the file means every script follows it without being
# told the new number.
PORT_FILE = Path("~/.hermes/state/chrome-real-profile.port").expanduser()

# Used only when nothing else says otherwise. Same number the launcher has
# always used, so an absent port file still points at the live browser.
DEFAULT_PORT = 9240

DEFAULT_SITE = "x.com"

# Roots searched for the real-profile launcher. The launcher ships with the
# skills repo and is registered into ~/.hermes/skills, so either may be the
# live copy and a glob finds whichever exists on this machine.
_LAUNCHER_ROOTS = ("~/.agents/skills", "~/.hermes/skills")
_LAUNCHER_SUFFIX = "chrome-real-profile-launch/scripts/run.sh"


def site() -> str:
    """The hostname to treat as the site. X_SITE, else x.com."""
    return (os.environ.get("X_SITE") or "").strip() or DEFAULT_SITE


def port() -> int:
    """The Chrome debugging port. X_PORT, else the launcher's port file."""
    raw = (os.environ.get("X_PORT") or "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass                      # fall through to the port file
    try:
        text = PORT_FILE.read_text().strip()
        if text:
            return int(text)
    except (OSError, ValueError):
        pass
    return DEFAULT_PORT


def launcher() -> str:
    """Path to the real-profile launcher's run.sh.

    X_LAUNCHER wins outright. Otherwise the skills repo and then the
    registered skills directory are globbed for the launcher, because which
    one is live depends on how this machine was set up and hardcoding a path
    made the skill fail everywhere else.

    Raises RuntimeError when it is absent: a missing launcher is a real
    setup problem, and silently returning a path that does not exist turns it
    into "could not start the browser" with no explanation.
    """
    explicit = (os.environ.get("X_LAUNCHER") or "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    for root in _LAUNCHER_ROOTS:
        base = Path(root).expanduser()
        if not base.is_dir():
            continue
        hits = sorted(base.glob(f"*/{_LAUNCHER_SUFFIX}")) + \
            sorted(base.glob(f"*/*/{_LAUNCHER_SUFFIX}"))
        for hit in hits:
            if hit.is_file():
                return str(hit)
    raise RuntimeError(
        f"real-profile launcher not found: looked for {_LAUNCHER_SUFFIX} under "
        + ", ".join(str(Path(r).expanduser()) for r in _LAUNCHER_ROOTS)
        + ". Set X_LAUNCHER to its run.sh.")


def handle_fallback() -> str:
    """The account to assume when the page cannot be read. X_HANDLE, else "".

    Empty on purpose — see the module docstring. Prefer handle.live(), which
    reads the real handle off the open tab; this is only the last resort, and
    an empty string makes the mismatch visible instead of silently wrong.
    """
    return (os.environ.get("X_HANDLE") or "").strip()


def state_dir() -> Path:
    """Where this skill keeps its own state. X_STATE_DIR, else under ~/.hermes.

    Created on demand: a script that only reads its state should not have to
    create the directory first, and one that writes it must not have to check.
    """
    raw = (os.environ.get("X_STATE_DIR") or "").strip()
    path = Path(raw).expanduser() if raw else \
        Path("~/.hermes/state/x-post").expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_site_tab(url: str) -> bool:
    """True when this URL is a tab on the configured site.

    Host EXACT match, so a link to x.com.evil.test is not the site. The
    point of this helper is that no script greps the literal "x.com" any
    more: pointing the skill at another host is one X_SITE away.
    """
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return host == site().lower().strip(".")


def _words(name: str) -> tuple[str, ...]:
    """Split a colon-or-comma separated env var into lowercased words."""
    raw = os.environ.get(name) or ""
    parts = raw.replace(":", ",").split(",")
    return tuple(w.strip().lower() for w in parts if w.strip())


# The vocabulary that makes a post worth engaging with. Kept here because a
# like and a reply must agree about what this account cares about, or the
# feed teaches two different things about it. X_TOPICS overrides it wholesale.
DEFAULT_TOPICS = (
    "rust", "cargo", "wasm", "webassembly", "compile", "compiler", "macro",
    "agent", "llm", "model", "token", "context", "prompt", "mcp", "tool",
    "inference", "type system", "static typing", "refactor", "debugging",
    "code", "programming", "developer",
    "编程", "模型", "编译", "工具", "宏", "上下文", "智能体", "推理", "代码",
)

# A keyword match is never a reason by itself: adult and scam posts stuff the
# same vocabulary (模型, token, code) into their text, and a promotional reply
# under one of those does real damage to the account. The very first dry-run
# target was an uncensored-image-model post caught by 模型 — a keyword match
# is never on its own enough to engage. X_BLOCK overrides it wholesale.
DEFAULT_BLOCK = (
    "少儿不宜", "成人内容", "未成年", "nsfw", "18+", "uncensored",
    "约炮", "onlyfans", "porn", "adult content", "博彩", "彩票",
    "刷单", "裸聊",
    # crypto shill threads match "token" without ever being about token
    # cost — conference booth posts, airdrops, pump talk
    "token2049", "airdrop", "波场", "币圈", "土狗", "百倍",
    "合约", "炒币", "跟单", "带单",
)


def topics() -> tuple[str, ...]:
    """Words that make a post worth engaging with. X_TOPICS overrides."""
    return _words("X_TOPICS") or DEFAULT_TOPICS


def blocklist() -> tuple[str, ...]:
    """Words that disqualify a post outright. X_BLOCK overrides."""
    return _words("X_BLOCK") or DEFAULT_BLOCK


def github_owners() -> tuple[str, ...]:
    """Owners to promote, from X_GITHUB_OWNERS. Empty by default.

    Empty means "derive them", not "promote anything" — see org_repos.py,
    where an owner set that resolves to nothing REFUSES the promotion rather
    than widening the gate. A hand-written allowlist goes stale the moment an
    account is renamed or gains an org, and the failure is silent.
    """
    return _words("X_GITHUB_OWNERS")


if __name__ == "__main__":
    # `python3 xconfig.py` prints what this machine resolved, which is the
    # fastest way to answer "why is it talking to port N / that account".
    print(f"site            {site()}")
    print(f"port            {port()}")
    print(f"handle_fallback {handle_fallback() or '(empty — read from the page)'}")
    print(f"state_dir       {state_dir()}")
    try:
        print(f"launcher        {launcher()}")
    except RuntimeError as exc:
        print(f"launcher        MISSING — {exc}")
    print(f"github_owners   {', '.join(github_owners()) or '(none — derived)'}")
    print(f"topics          {len(topics())} words")
    print(f"blocklist       {len(blocklist())} words")
