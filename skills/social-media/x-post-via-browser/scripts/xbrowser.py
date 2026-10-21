#!/usr/bin/env python3
"""Bring up the dedicated browser this skill drives, and tear it down again.

WHY A DEDICATED BROWSER AND NOT THE HARNESS ONE

The browser the tool harness launches runs with --headless=new, so it
identifies as HeadlessChrome, and Cloudflare answers that user agent with
403 on x.com. The one-line proof that it is the user agent and not the
network: the same URL answers 403 with a HeadlessChrome user agent and 200
with an ordinary one, from the same address in the same second.

Overriding the user agent fixes the 403, but the harness's own profile copy
carries only guest cookies -- no x.com session -- so the page redirects to
the login screen. The session lives in the USER's real Chrome profile, and
the only way to drive that session without taking over the user's own
browser window is to copy its cookies into a private profile and launch a
browser against THAT.

So this script:

  * copies x.com's cookies out of the real profile (read-only sqlite
    backup, so a running Chrome cannot lose a committed WAL page),
  * copies Local State, which holds the key material reference,
  * launches Chrome against the private copy with --remote-allow-origins=*,
  * records the port and the browser websocket endpoint in the state dir.

It NEVER writes to the user's real profile and never opens a window the user
can see: the copy is private and the launch is headless.

Usage:
    xbrowser.py up      # launch if needed, print the port and ws endpoint
    xbrowser.py status  # report what is running
    xbrowser.py down    # stop the browser this script started
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402

# The first port tried; the launcher walks up from here until one is free.
PORT_BASE = 9266

# How long to wait for the browser to answer.
READY_TIMEOUT = 45


def free_port(base: int = PORT_BASE) -> int:
    """The first free port at or above `base`."""
    for cand in range(base, base + 40):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", cand))
                return cand
            except OSError:
                continue
    raise SystemExit("no free port found at or above %d" % base)


def _http_json(port: int, path: str, timeout: float = 5):
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:%d%s" % (port, path), timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def running_port():
    """The port of a live browser, or None.

    The port file is consulted first, but it is only a hint: a stale file
    must not make the caller believe a browser is there. When there is no
    port file, the ports this skill launches on are probed, so a browser
    this skill started in an earlier session is ADOPTED rather than started
    a second time -- two browsers over one profile directory fight over the
    profile lock.
    """
    candidates = []
    try:
        candidates.append(xconfig.port())
    except Exception:
        pass
    for port in range(PORT_BASE, PORT_BASE + 40):
        if port not in candidates:
            candidates.append(port)
    for port in candidates:
        version = _http_json(port, "/json/version")
        if version and version.get("webSocketDebuggerUrl"):
            return port
    return None


def backup_cookies(src: Path, dst: Path) -> None:
    """Copy a live sqlite database consistently.

    A plain file copy of a database a running Chrome still holds can miss a
    committed page, because the recent writes live in the WAL. The online
    backup API reads through the WAL, so the copy is complete.
    """
    src_db = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    dst_db = sqlite3.connect(dst)
    try:
        with dst_db:
            src_db.backup(dst_db)
    finally:
        src_db.close()
        dst_db.close()


def session_cookie_rows(profile: Path):
    """The x.com session cookies in a profile, as (host, name, length)."""
    db = sqlite3.connect(profile / "Default" / "Cookies")
    try:
        return db.execute(
            "select host_key,name,length(encrypted_value) from cookies "
            "where name in ('auth_token','ct0','twid')").fetchall()
    finally:
        db.close()


def session_cookie_rows_present(profile: Path) -> bool:
    """Whether a profile copy already carries the session cookies."""
    if not (profile / "Default" / "Cookies").exists():
        return False
    try:
        rows = session_cookie_rows(profile)
    except sqlite3.Error:
        return False
    return any(r[1] == "auth_token" for r in rows)


def build_profile() -> Path:
    """Create the private profile copy with the session cookies in it."""
    real = xconfig.real_chrome_profile()
    private = xconfig.browser_dir()
    cookies = real / "Default" / "Cookies"
    if not cookies.exists():
        raise SystemExit(
            "no Chrome cookie database at %s -- open Chrome once so it exists"
            % cookies)
    # A live browser holds this profile open. Replacing it under a running
    # browser breaks that browser's session, so the copy is only rebuilt when
    # nothing is running against it.
    if private.exists() and session_cookie_rows_present(private):
        rows = session_cookie_rows(private)
        print("REUSING_EXISTING_PROFILE:", rows)
        return private
    if private.exists():
        shutil.rmtree(private)
    (private / "Default").mkdir(parents=True, exist_ok=True)

    backup_cookies(cookies, private / "Default" / "Cookies")

    # Local State carries the key material reference the browser needs to
    # decrypt the copied cookies.
    local_state = real / "Local State"
    if local_state.exists():
        shutil.copy2(local_state, private / "Local State")
    prefs = real / "Default" / "Preferences"
    if prefs.exists():
        shutil.copy2(prefs, private / "Default" / "Preferences")

    rows = session_cookie_rows(private)
    print("COPIED_AUTH_COOKIES:", rows)
    if not any(r[1] == "auth_token" for r in rows):
        raise SystemExit(
            "no auth_token in the copied cookies -- the session is not signed "
            "in; open Chrome and sign in to %s first" % xconfig.site())
    return private


def launch() -> int:
    """Start the browser and record where it can be reached."""
    private = build_profile()
    port = free_port()
    binary = xconfig.chrome_binary()
    if not os.path.exists(binary):
        raise SystemExit("Chrome not found at %s (set X_CHROME)" % binary)

    argv = [
        binary,
        "--user-data-dir=%s" % private,
        "--remote-debugging-port=%d" % port,
        # The websocket endpoint rejects any Origin the browser did not
        # expect, and a driver legitimately sends one.
        "--remote-allow-origins=*",
        "--no-first-run", "--no-default-browser-check",
        "--disable-background-networking", "--disable-component-update",
        "--disable-default-apps", "--disable-hang-monitor",
        "--disable-popup-blocking", "--disable-prompt-on-repost",
        "--disable-sync", "--disable-features=Translate",
        "--headless=new",
        "--window-size=1280,900",
        "about:blank",
    ]
    proxy = (os.environ.get("X_PROXY") or "").strip()
    if proxy:
        argv.insert(-1, "--proxy-server=%s" % proxy)

    log = xconfig.state_dir() / "browser.log"
    proc = subprocess.Popen(argv, stdout=open(log, "wb"),
                            stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    xconfig.pid_file().write_text(str(proc.pid))
    print("LAUNCHED_PID:", proc.pid, "PORT:", port)

    deadline = time.time() + READY_TIMEOUT
    while time.time() < deadline:
        if proc.poll() is not None:
            print("EXITED early; log tail:")
            print(log.read_text()[-1500:])
            return 1
        version = _http_json(port, "/json/version")
        if version and version.get("webSocketDebuggerUrl"):
            xconfig.port_file().write_text(str(port))
            xconfig.ws_file().write_text(version["webSocketDebuggerUrl"])
            print("READY:", version.get("Browser"))
            print("PORT:", port)
            print("WS:", version["webSocketDebuggerUrl"])
            return 0
        time.sleep(1)
    print("NOT READY; log tail:")
    print(log.read_text()[-2000:])
    return 2


def up() -> int:
    """Make sure a usable browser exists. Reuse one that is already up."""
    port = running_port()
    if port:
        version = _http_json(port, "/json/version") or {}
        ws = version.get("webSocketDebuggerUrl", "")
        if ws:
            xconfig.port_file().write_text(str(port))
            xconfig.ws_file().write_text(ws)
            print("REUSED port=%d browser=%s" % (port, version.get("Browser")))
            print("PORT:", port)
            print("WS:", ws)
            return 0
    return launch()


def status() -> int:
    """Report what is running, and whether it can be reached."""
    port = running_port()
    if not port:
        print("browser: DOWN (no live endpoint on the recorded port)")
        return 1
    version = _http_json(port, "/json/version") or {}
    tabs = _http_json(port, "/json/list") or []
    pages = [t for t in tabs if t.get("type") == "page"]
    x_pages = [t for t in pages if xconfig.site() in t.get("url", "")]
    print("browser:", version.get("Browser"))
    print("PORT:", port)
    print("targets=%d pages=%d %s_pages=%d" % (
        len(tabs), len(pages), xconfig.site(), len(x_pages)))
    for t in x_pages:
        print("  page:", t.get("url", "")[:90])
    print("WS:", version.get("webSocketDebuggerUrl", ""))
    return 0


def down() -> int:
    """Stop the browser this skill started. Nothing else is touched."""
    try:
        pid = int(xconfig.pid_file().read_text().strip())
    except (OSError, ValueError):
        print("no pid file; nothing to stop")
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
        print("sent SIGTERM to", pid)
    except ProcessLookupError:
        print("browser", pid, "already gone")
    except OSError as exc:
        print("could not stop", pid, exc)
        return 1
    for path in (xconfig.pid_file(), xconfig.port_file(), xconfig.ws_file()):
        try:
            path.unlink()
        except OSError:
            pass
    return 0


def main(argv) -> int:
    action = (argv[1] if len(argv) > 1 else "up").strip()
    if action == "up":
        return up()
    if action == "status":
        return status()
    if action == "down":
        return down()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
