#!/usr/bin/env python3
"""Every environment-specific value this skill needs, in one place.

Two rules, and the second one is the one that bites:

1. NO ACCOUNT IS BAKED IN. The handle is discovered from the live page and
   cached under the state directory; a remembered handle is wrong on any other
   machine and silently mis-attributes replies.

2. EVERY FUNCTION READS THE ENVIRONMENT AT CALL TIME. A module-level
   constant is frozen before a later export takes effect, and that staleness
   is exactly the bug class this skill already documents (the port file moves,
   the state directory moves). So nothing here is a constant: call the
   function.

Every value below has a working default. Setting an environment variable is
always optional, and none of them is required for the skill to run.
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# runtime shim
# --------------------------------------------------------------------------

_RUNTIME_OK = os.environ.get("X_RUNTIME_OK") == "1"


def ensure_runtime(module: str = "websockets") -> None:
    """Re-exec under an interpreter that has `module` importable.

    A cron shell resolves `python3` by PATH, and the interpreter it lands on
    is not guaranteed to carry the third-party modules this skill drives the
    browser with. Failing at import time turns a working script into an
    ImportError with no explanation, so the interpreter is chosen here
    instead: the first candidate that can import the module wins.

    The re-exec sets X_RUNTIME_OK so a candidate that somehow still fails
    cannot loop.
    """
    global _RUNTIME_OK
    if _RUNTIME_OK:
        return
    try:
        __import__(module)
        _RUNTIME_OK = True
        return
    except ImportError:
        pass
    candidates = []
    explicit = (os.environ.get("X_PYTHON") or "").strip()
    if explicit:
        candidates.append(explicit)
    candidates += [
        "/usr/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
    ]
    candidates += sorted(glob.glob(os.path.expanduser(
        "~/.hermes/installs/*/environments/*/venv/bin/python3")))
    here = os.path.realpath(sys.executable)
    for cand in candidates:
        if not cand or not os.path.isfile(cand):
            continue
        if os.path.realpath(cand) == here:
            continue
        try:
            probe = subprocess.run([cand, "-c", "import %s" % module],
                                  capture_output=True, timeout=20)
        except Exception:
            continue
        if probe.returncode == 0:
            env = dict(os.environ)
            env["X_RUNTIME_OK"] = "1"
            os.execve(cand, [cand, os.path.abspath(sys.argv[0])] + sys.argv[1:], env)
    raise SystemExit(
        "no interpreter with %r found; set X_PYTHON to one that has it" % module)


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

def state_dir() -> Path:
    """Where this skill keeps its own state. X_STATE_DIR, else under ~/.hermes.

    NOT the scratch directory: the daily cleanup removes scratch files older
    than a day, and a browser port file that disappears between two runs of
    the same job is a job that cannot find its own browser.
    """
    raw = (os.environ.get("X_STATE_DIR") or "").strip()
    base = Path(raw).expanduser() if raw else Path.home() / ".hermes" / "state" / "x-post"
    base.mkdir(parents=True, exist_ok=True)
    return base


def browser_dir() -> Path:
    """The dedicated browser's private profile copy. Under the state dir.

    The user's real Chrome profile is never used as a --user-data-dir: the
    cookies are copied out of it, and the copy lives here.
    """
    d = state_dir() / "browser-profile"
    d.mkdir(parents=True, exist_ok=True)
    return d


def port_file() -> Path:
    return state_dir() / "browser.port"


def ws_file() -> Path:
    return state_dir() / "browser.ws"


def pid_file() -> Path:
    return state_dir() / "browser.pid"


def handle_file() -> Path:
    return state_dir() / "handle"


def answered_file() -> Path:
    """The set of parent post ids this account has already answered."""
    return state_dir() / "answered_sids.json"


def project_state_file() -> Path:
    """What the promotion job has already published, so it does not repeat."""
    return state_dir() / "project_state.json"


def lock_file() -> Path:
    """The advisory lock every posting run holds while it drives the browser."""
    return state_dir() / "engage.lock"


def code_dir() -> Path:
    """Where this account's own repositories are checked out.

    HERMES_CODE_DIR, else ~/code. Read at CALL time for the same reason every
    other value here is read.
    """
    raw = (os.environ.get("HERMES_CODE_DIR") or "").strip()
    return Path(raw).expanduser() if raw else Path.home() / "code"


def real_chrome_profile() -> Path:
    """The user's own Chrome profile, read-only source of the session cookies."""
    raw = (os.environ.get("X_CHROME_PROFILE") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"


def chrome_binary() -> str:
    """The Chrome to launch. X_CHROME, else the standard install path."""
    raw = (os.environ.get("X_CHROME") or "").strip()
    if raw:
        return raw
    return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def site() -> str:
    """The hostname to treat as the site. X_SITE, else x.com."""
    return (os.environ.get("X_SITE") or "").strip() or "x.com"


def port() -> int:
    """The dedicated browser's debugging port.

    X_PORT wins, then the port file the launcher wrote, then the default.
    Never hardcode the port in a prompt: the launcher takes the first free
    port from a base upward, so a number written into a prompt is wrong the
    moment two runs overlap.
    """
    raw = (os.environ.get("X_PORT") or "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    try:
        text = port_file().read_text().strip()
        if text:
            return int(text)
    except (OSError, ValueError):
        pass
    return 9266


def ws_url() -> str:
    """The browser-level websocket endpoint.

    X_WS wins, then the file the launcher wrote. A /json/version probe can
    answer while the websocket path is what actually works, so this is read
    from the file rather than derived from the port.
    """
    raw = (os.environ.get("X_WS") or "").strip()
    if raw:
        return raw
    try:
        text = ws_file().read_text().strip()
        if text:
            return text
    except OSError:
        pass
    raise RuntimeError(
        "no browser websocket endpoint: run xbrowser.py first "
        "(it writes %s)" % ws_file())


def handle() -> str:
    """This account's own handle, as discovered from the live page.

    X_HANDLE wins; then the cached value; then the empty string. An empty
    handle makes a mismatch visible instead of silently wrong.
    """
    raw = (os.environ.get("X_HANDLE") or "").strip()
    if raw:
        return raw
    try:
        text = handle_file().read_text().strip()
        if text:
            return text
    except OSError:
        pass
    return ""


def cache_handle(value: str) -> None:
    """Remember the discovered handle for the rest of the run."""
    value = (value or "").strip().lstrip("@")
    if value:
        handle_file().write_text(value + "\n")
