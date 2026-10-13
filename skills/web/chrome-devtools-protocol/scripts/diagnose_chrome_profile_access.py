#!/usr/bin/env python3
"""Decide WHY a Chrome/Chromium profile directory is unreadable: TCC or a real lock.

A privacy grant and a running browser produce the same `PermissionError`,
so any code that only inspects the exception text will confidently tell the
user to quit a browser that was never the problem. This probe separates them
mechanically.

Usage:
    python3 diagnose_chrome_profile_access.py [chrome|chromium|brave|edge]

Exit codes:
    0  readable (or genuinely absent)
    1  denied by a privacy grant (TCC) -- user must grant Full Disk Access
    2  a real lock: the browser holds the profile, quitting it will help
"""

from __future__ import annotations

import errno
import os
import subprocess
import sys

# (key, relative path under ~) siblings swept to locate the denial boundary.
SIBLINGS = (
    "Library/Application Support/Google",
    "Library/Application Support/Google/Chrome",
    "Library/Application Support/Google/Chrome/Default",
    "Library/Application Support/Google/Chrome/Default/Network",
    "Library/Application Support/Google/Chrome for Testing",
    "Library/Preferences",
    "Library/Safari",
    "Library/Application Support/Firefox",
    "Library/Application Support/com.apple.sharedfilelist",
)

APP_DATA_SIBLINGS = ("Library/Application Support/Firefox", "Library/Safari",
                     "Library/Application Support/com.apple.sharedfilelist")

PROFILES = {
    "chrome": "Library/Application Support/Google/Chrome",
    "chromium": "Library/Application Support/Chromium",
    "brave": "Library/Application Support/BraveSoftware/Brave-Browser",
    "edge": "Library/Application Support/Microsoft Edge",
}

# Chromium-family process names, used to report whether a browser is running.
BROWSER_BINARIES = ("chrome", "chromium", "brave", "msedge", "google chrome")


def read_result(path: str) -> tuple[str, str]:
    """(status, detail) for probing one path. Never raises."""
    if not os.path.exists(path):
        return "absent", "path does not exist"
    if not os.path.isdir(path):
        return "file", "regular file"
    try:
        return "readable", f"{len(os.listdir(path))} entries"
    except OSError as e:
        if e.errno == errno.EPERM:
            return "denied-EPERM", "TCC privacy denial (errno 1)"
        if e.errno == errno.EACCES:
            return "denied-EACCES", "Unix permissions (errno 13)"
        return "error", f"{type(e).__name__}: {e}"


def ancestor_chain(pid: int = None, depth: int = 8) -> list[str]:
    """Process ancestry as 'pid -> ppid : comm' lines, to name the grant holder."""
    if pid is None:
        pid = os.getpid()
    lines: list[str] = []
    for _ in range(depth):
        try:
            out = subprocess.run(["ps", "-o", "ppid=", "-p", str(pid)],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            break
        parent = out.strip()
        if not parent or parent == "1":
            break
        try:
            comm = subprocess.run(["ps", "-o", "comm=", "-p", parent],
                                  capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            comm = "?"
        lines.append(f"{pid} -> {parent} : {comm}")
        pid = parent
    return lines


def browsers_running(profile: str) -> list[str]:
    """Chromium-family processes whose cmdline references this user-data-dir."""
    hits: list[str] = []
    try:
        out = subprocess.run(["ps", "-Ao", "pid=,command="], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return hits
    for line in out.splitlines():
        low = line.lower()
        if not any(b in low for b in BROWSER_BINARIES):
            continue
        # A lock only exists when a process actually holds THIS dir.
        if profile.lower() in low or f"--user-data-dir={profile}".lower() in low:
            hits.append(line.strip()[:160])
    return hits


def main() -> int:
    key = (sys.argv[1] if len(sys.argv) > 1 else "chrome").lower()
    if key not in PROFILES:
        print(f"unknown browser {key!r}; choose one of {', '.join(PROFILES)}")
        return 0
    home = os.path.expanduser("~")
    profile = os.path.join(home, PROFILES[key])

    print(f"== target: {key} ==")
    print(f"profile dir: {profile}")
    print()

    print("== why: real lock vs privacy denial ==")
    singleton = {n: os.path.exists(os.path.join(profile, n))
                 for n in ("SingletonLock", "SingletonSocket", "SingletonCookie")}
    print("singleton markers:", ", ".join(f"{n}={'present' if v else 'absent'}"
                                           for n, v in singleton.items()))
    status, detail = read_result(profile)
    print(f"directory read: {status} ({detail})")
    print()

    print("== boundary sweep (which app-data dirs are denied) ==")
    statuses: dict[str, str] = {}
    for rel in SIBLINGS:
        st, det = read_result(os.path.join(home, rel))
        statuses[rel] = st
        print(f"  {st:14} {rel}  [{det}]")
    print()

    print("== processes holding this profile ==")
    running = browsers_running(profile)
    if running:
        for line in running:
            print(f"  {line}")
    else:
        print("  (none)")
    print()

    print("== process ancestry (the app that must be granted) ==")
    for line in ancestor_chain():
        print(f"  {line}")
    print()

    # Decide. EPERM on the profile + other app-data dirs denied = TCC.
    app_data_denied = [rel for rel in APP_DATA_SIBLINGS if statuses.get(rel) == "denied-EPERM"]
    if status == "denied-EPERM" and app_data_denied:
        print("VERDICT: privacy grant (TCC), NOT a browser lock.")
        print("  Quitting the browser will NOT help. Grant Full Disk Drive Access")
        print("  to the ancestor app named above, then fully quit and relaunch it.")
        return 1
    if status == "denied-EPERM" and singleton.get("SingletonLock"):
        print("VERDICT: the browser holds a real profile lock.")
        print("  Quitting the browser should release it.")
        return 2
    if status == "denied-EPERM":
        print("VERDICT: EPERM denial with no lock and no app-data pattern --")
        print("  re-check the ancestry above; the grant holder may be unidentified.")
        return 1
    if status == "absent":
        print("VERDICT: profile absent. Launch the browser once, then re-probe.")
        return 0

    print("VERDICT: readable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
