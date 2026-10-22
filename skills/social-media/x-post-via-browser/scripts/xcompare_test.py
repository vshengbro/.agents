#!/usr/bin/env python3
"""Fixtures for the landed-text comparison, in both posting scripts.

Run directly:

    python3 xcompare_test.py

A trailing address lands as a CARD, and the card is not part of the post's
own text, so the landed text carries NO url span while the source copy
carries one. A comparison that leaves a marker where the span was makes
the two differ by exactly one character, and a reply that landed
perfectly reads as a mismatch. That false negative cost a real reply on
2026-10-22: the reply was on the site, with the card naming the
repository and the t.co resolving to it, and the run still reported it as
rejected.

These cases pin the behaviour that fixes it: the url span is removed from
BOTH sides, so the two compare as prose, and the address is proved
separately by the card and the t.co.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    """Import a sibling script by path, without putting it on sys.path."""
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


xreply = _load("xreply")
xpost = _load("xpost")

REPO = "https://github.com/hyperlane-dev/hyperlane"

PROSE = ("补个 Rust 侧细节：rustls-webpki 0.103.16 把 8 个泄露中间 CA 的 SPKI 硬编码进 distrust 列表，"
         "链验证命中即报 CertDistrusted；webpki-roots 1.0.10 摘掉了 emSign ECC Root CA - G3。"
         "Rust 栈只需 cargo update 后重编译，不必动系统证书库。hyperlane 的 http-request 用编译进二进制的 "
         "webpki-roots，系统升级 ca-certificates 无效，得升依赖重编译")
SOURCE = PROSE + " " + REPO

# (name, landed, source, repo, expected)
CASES = [
    ("card case: the landed text carries no url span",
     PROSE, SOURCE, REPO, True),
    ("card case with the t.co still inline in the text",
     PROSE + " https://t.co/qRQPuijJhB", SOURCE, REPO, True),
    ("the prose was mangled",
     PROSE.replace("编译进二进制的", ""), SOURCE, REPO, False),
    ("the prose lost a clause",
     PROSE.replace("Rust 栈只需 cargo update 后重编译，不必动系统证书库。", ""),
     SOURCE, REPO, False),
    ("a no-repo reply, whole text",
     PROSE, PROSE, None, True),
    ("a no-repo reply with a mangled prose",
     PROSE.replace("得升依赖重编译", ""), PROSE, None, False),
    ("the token in front of the url survives",
     "看 " + PROSE, "看 " + PROSE + " " + REPO, REPO, True),
]

# The landing read's readiness gate, in both posting scripts.
#
# A post's own text mounts BEFORE its link card. A read that stops on the
# text alone reads a half-hydrated post, and it calls a link that landed
# with its card a lost one -- which is what a run did to a perfectly
# landed reply on 2026-10-22: the reply was up, with the card naming the
# repository and the t.co resolving to it, and the run still reported it
# as rejected.
#
# These cases pin the gate that stops the read from judging the address
# before the card has hydrated.
#
# (name, landing read, expected)
READY_CASES = [
    ("the card and the t.co are both there",
     {"hasCard": True, "tco": ["https://t.co/abc"]}, True),
    ("the card has not hydrated yet",
     {"hasCard": False, "tco": []}, False),
    ("the card is there but the t.co is not",
     {"hasCard": True, "tco": []}, False),
    ("the t.co is there but the card is not",
     {"hasCard": False, "tco": ["https://t.co/abc"]}, False),
    ("nothing has rendered yet",
     {}, False),
]


def main() -> int:
    failures = 0

    for name, landed, source, repo, expected in CASES:
        got, detail = xreply.compare_prose(landed, source, repo)
        if got != expected:
            failures += 1
            print("FAIL xreply: %s -- expected %s, got %s (%s)"
                  % (name, expected, got, detail))
        else:
            print("ok   xreply: %s" % name)

    # The standalone-post script carries the same comparison, so the same
    # fixtures apply to it.
    for name, landed, source, repo, expected in CASES:
        got = xpost.canon(landed) == xpost.canon(source)
        if got != expected:
            failures += 1
            print("FAIL xpost:  %s -- expected %s, got %s" % (name, expected, got))
        else:
            print("ok   xpost:  %s" % name)

    # The readiness gate lives in both posting scripts, so both are pinned
    # against the same fixtures.
    for name, landing, expected in READY_CASES:
        got = xreply.link_ready(landing)
        if got != expected:
            failures += 1
            print("FAIL xreply: link_ready -- %s -- expected %s, got %s"
                  % (name, expected, got))
        else:
            print("ok   xreply: link_ready -- %s" % name)

    for name, landing, expected in READY_CASES:
        got = xpost.link_ready(landing)
        if got != expected:
            failures += 1
            print("FAIL xpost:  link_ready -- %s -- expected %s, got %s"
                  % (name, expected, got))
        else:
            print("ok   xpost:  link_ready -- %s" % name)

    if failures:
        print("\n%d case(s) failed" % failures)
        return 1
    print("\nall %d comparison cases and %d readiness cases hold in both scripts"
          % (len(CASES), len(READY_CASES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
