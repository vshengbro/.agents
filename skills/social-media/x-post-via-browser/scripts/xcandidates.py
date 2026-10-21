#!/usr/bin/env python3
"""Resolve a candidate from a candidates file.

WHY THE INDEX AND NOT THE ID

A status id is a bare 19-digit number, and the terminal display layer
replaces such numbers with a redaction token -- one id in a list of seven
was redacted, so the rule is not "ids that look like cards" but "bare 19-digit
numbers in a transcript". A redacted token that reaches a script is not an
id, and a run that reads its own output cannot tell the difference.

So the caller names a candidate by its INDEX and this module reads the id
out of the file. The id never appears in a command line, in a transcript,
or in a report.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_candidates(path: str | Path) -> list:
    """The candidates in a candidates file."""
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    if not isinstance(rows, list):
        raise ValueError("%s does not hold a list of candidates" % path)
    return rows


def resolve(path: str | Path, index: int) -> dict:
    """One candidate, by index.

    Raises IndexError with the count in the message when the index is out of
    range, so a caller that passes the wrong index sees WHY rather than a
    KeyError on an id.
    """
    rows = load_candidates(path)
    if not rows:
        raise IndexError("%s holds no candidates" % path)
    if not (0 <= index < len(rows)):
        raise IndexError(
            "candidate index %d is out of range: %s holds %d"
            % (index, path, len(rows)))
    row = rows[index]
    sid = str(row.get("sid", ""))
    if not (len(sid) == 19 and sid.isdigit()):
        raise ValueError("candidate %d has no usable status id" % index)
    return row


def describe(row: dict, index: int) -> str:
    """One candidate, described without its id."""
    return "[%d] @%s  len=%s" % (index, row.get("who", "?"), row.get("len", "?"))
