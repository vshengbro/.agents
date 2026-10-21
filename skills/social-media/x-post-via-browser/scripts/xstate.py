#!/usr/bin/env python3
"""The state this skill keeps between runs, and the lock that serialises them.

THE STATE FILE IS NEVER WRITTEN IN PLACE.

A bare `open(path, "w")` truncates the moment it is called, so a write that
raises afterwards leaves a zero-byte file and every prior run's record gone.
The write here goes to a temporary file, is renamed over the target
atomically, and is read back before the call returns -- a state file that was
never verified is the same class of defect as an unverified post.

THE LOCK IS ADVISORY AND PER-PROCESS.

Two jobs on a schedule can overlap: the every-30-minutes job and the daily
one both drive the same browser and the same account, and a reply that lands
under the wrong post is the result. The lock makes the second run wait rather
than interleave.
"""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402


# --------------------------------------------------------------------------
# atomic json
# --------------------------------------------------------------------------

def write_json(path: Path, data, backup_suffix: str | None = None) -> None:
    """Write JSON atomically, optionally keeping the previous copy."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup_suffix and path.exists():
        shutil.copy2(path, str(path) + backup_suffix)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    # Read back: a write that reported success but produced nothing is the
    # failure this whole dance exists to prevent.
    with open(path, encoding="utf-8") as fh:
        json.load(fh)


def read_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


# --------------------------------------------------------------------------
# answered sids
# --------------------------------------------------------------------------

def answered_sids() -> list:
    """The parent post ids this account has already answered.

    The file is a dict with a `sids` list, but it has been a bare list in
    other versions; both are read, and the dict shape is what is written.
    """
    data = read_json(xconfig.answered_file(), {"sids": []})
    if isinstance(data, dict):
        sids = data.get("sids", [])
    elif isinstance(data, list):
        sids = data
    else:
        sids = []
    return [str(s) for s in sids]


def mark_answered(sid: str, backup_suffix: str | None = None) -> int:
    """Record a parent post id as answered.

    ONLY the parent's id is written. The reply's own id is deliberately NOT:
    a later run reads this file to decide what it may still answer, and the
    reply is not a thing it may answer.
    """
    sid = str(sid).strip()
    if not (len(sid) == 19 and sid.isdigit()):
        raise ValueError("not a status id: %r" % sid)
    path = xconfig.answered_file()
    data = read_json(path, {"sids": []})
    if not isinstance(data, dict):
        data = {"sids": []}
    sids = [str(s) for s in data.get("sids", [])]
    before = len(sids)
    if sid not in sids:
        sids.append(sid)
    write_json(path, {"sids": sids, "next": data.get("next", before)},
               backup_suffix=backup_suffix)
    after = len(answered_sids())
    return after


# --------------------------------------------------------------------------
# project state (what the promotion job has already published)
# --------------------------------------------------------------------------

def project_state() -> dict:
    return read_json(xconfig.project_state_file(), {})


def record_published(entry: dict) -> None:
    """Append one publication record to the project state."""
    state = project_state()
    posts = state.setdefault("posts", [])
    posts.append(entry)
    write_json(xconfig.project_state_file(), state)


def published_today() -> list:
    """The records written today, by local date."""
    today = time.strftime("%Y-%m-%d")
    return [p for p in project_state().get("posts", [])
            if str(p.get("date", "")) == today]


# --------------------------------------------------------------------------
# lock
# --------------------------------------------------------------------------

class Lock:
    """An advisory exclusive lock held for the life of the object.

    Usage:

        with Lock():
            ...drive the browser...

    A run that cannot take the lock waits, and says so on stderr, rather
    than interleaving with the run that holds it.
    """

    def __init__(self, path: Path | None = None, wait: float = 900.0,
                 poll: float = 2.0):
        self.path = Path(path or xconfig.lock_file())
        self.wait = wait
        self.poll = poll
        self._fh = None

    def __enter__(self) -> "Lock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+")
        deadline = time.time() + self.wait
        while True:
            try:
                fcntl.flock(self._fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.time() >= deadline:
                    self._fh.close()
                    self._fh = None
                    raise TimeoutError(
                        "another engagement run holds %s" % self.path)
                print("another engagement run holds the lock; waiting",
                      file=sys.stderr, flush=True)
                time.sleep(self.poll)
        self._fh.seek(0)
        self._fh.truncate()
        self._fh.write("%d %s\n" % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S")))
        self._fh.flush()
        return self

    def __exit__(self, *exc) -> None:
        if self._fh is not None:
            try:
                fcntl.flock(self._fh, fcntl.LOCK_UN)
            finally:
                self._fh.close()
                self._fh = None
