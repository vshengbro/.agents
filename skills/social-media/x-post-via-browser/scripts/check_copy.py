#!/usr/bin/env python3
"""Refuse a post copy that X will mangle before a character is typed.

The trap this exists for: X linkifies ANY dotted token, not only one it
recognises as a URL. A bare `crates.io` in the body became a t.co
shortener, and the span X replaced then read back as a line break — which
split one sentence in two and shipped TWO posts before it was caught here.
A version number like `0.28.12` is the same trap wearing a different hat.

So the check runs on the COPY, before typing, and publish.py runs it too.
This script exists to let a run decide before it starts rather than after it
has already opened a composer.

Offline by construction: it reads a JSON file and prints a verdict. No
browser, no network, no account.

    python3 check_copy.py x_copy_example.json [index]

Exit 0 clean, 1 refused, 2 usage error.
"""
from __future__ import annotations

import json
import re
import sys

URL = re.compile(r"https?://\S+")
# A dotted token: something, a dot, then letters. Deliberately generous —
# this over-reports rather than under-reports, because the cost of a false
# positive is a rewritten sentence and the cost of a miss is two posts.
DOTTED = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z]{2,}")
VERSION = re.compile(r"\b\d+\.\d+(?:\.\d+)?\b")


def check(text: str) -> list[str]:
    """Every reason this copy would be mangled, empty list when clean."""
    problems: list[str] = []
    urls = URL.findall(text or "")
    hosts = {u.split("://", 1)[1].split("/", 1)[0] for u in urls}

    stray = [w for w in DOTTED.findall(text or "") if w not in hosts]
    if stray:
        problems.append(
            f"dotted token(s) X will linkify, splitting the text: {stray}. "
            f"Write them without the dot, or make them the intended URL.")

    if VERSION.search(DOTTED.sub("", text or "")):
        problems.append(
            "version-number-shaped token present; X linkifies dotted tokens "
            "and the span reads back as a line break. Keep versions out of "
            "the body.")

    if not text or not text.strip():
        problems.append("copy is empty")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_copy.py <copy.json> [index]")
        return 2
    try:
        posts = json.load(open(sys.argv[1], encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read copy: {exc}")
        return 2
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    if not isinstance(posts, list) or not posts:
        print("copy must be a non-empty JSON list of strings")
        return 2
    if idx >= len(posts):
        print(f"index {idx} out of range ({len(posts)} posts)")
        return 2

    raw = posts[idx]
    text = raw["text"] if isinstance(raw, dict) else raw

    problems = check(text)
    urls = URL.findall(text)
    print(f"[{idx}] {len(text)} chars, {len(urls)} url(s)")
    for u in urls:
        print(f"     url: {u}")
    if problems:
        print("\nREFUSING:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\ncopy is clean — X will not linkify anything it should not")
    return 0


if __name__ == "__main__":
    sys.exit(main())