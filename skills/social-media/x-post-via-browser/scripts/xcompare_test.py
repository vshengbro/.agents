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


# The address's proof.
#
# The landed post carries a card, and the card's TITLE is the target
# page's own title -- so it names the repository only for a bare
# repository address. A pull request address ends in its NUMBER, and no
# title contains a number, so the check that looked for the address's
# last path segment in the card's title read FALSE on a post that had
# landed perfectly: on 2026-10-22 a standalone post carrying a pull
# request address was up, with its card and its t.co, and the run
# reported it as unproven.
#
# The redirect is the proof. These cases pin it.
#
# (name, t.co list, address that was sent, card title, resolver, expected)
ADDRESS_CASES = [
    ("a pull request address, proved by the redirect",
     ["https://t.co/abc"], "https://github.com/zai-org/zcode-plugins/pull/112",
     "feat(zcode-context-insight): add plugin by bowenliang123 ·...",
     {"https://t.co/abc": "https://github.com/zai-org/zcode-plugins/pull/112"},
     True),
    ("the same address, with a trailing slash on the redirect",
     ["https://t.co/abc"], "https://github.com/zai-org/zcode-plugins/pull/112",
     "feat(zcode-context-insight): add plugin by bowenliang123 ·...",
     {"https://t.co/abc": "https://github.com/zai-org/zcode-plugins/pull/112/"},
     True),
    ("a bare repository address, proved by the redirect",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     "GitHub - hyperlane-dev/hyperlane: a Rust HTTP framework",
     {"https://t.co/abc": "https://github.com/hyperlane-dev/hyperlane"},
     True),
    ("the redirect points somewhere else",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     "GitHub - someone/else: a different repository",
     {"https://t.co/abc": "https://github.com/someone/else"},
     False),
    ("the redirect cannot be read, and the card names the repository",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     "GitHub - hyperlane-dev/hyperlane: a Rust HTTP framework",
     {}, True),
    ("the redirect cannot be read, and the card names nothing",
     ["https://t.co/abc"], "https://github.com/zai-org/zcode-plugins/pull/112",
     "feat(zcode-context-insight): add plugin by bowenliang123 ·...",
     {}, False),
    ("a pull request address, proved by the redirect, with the card "
     "naming nothing at all",
     ["https://t.co/abc"], "https://github.com/zai-org/zcode-plugins/pull/112",
     "",
     {"https://t.co/abc": "https://github.com/zai-org/zcode-plugins/pull/112"},
     True),
]


# The reply script's proof of the same address.
#
# It answers with THREE states, not two: the link points at the address
# that was sent, the link points somewhere else, or the redirect could
# not be read. The third is neither a proof nor a refutation, so it is
# reported and left to the caller -- a network that cannot read a public
# redirect is not evidence that the post is wrong.
#
# (name, t.co list, address that was sent, resolver table, expected)
REPLY_ADDRESS_CASES = [
    ("the link points at the address that was sent",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     {"https://t.co/abc": "https://github.com/hyperlane-dev/hyperlane"}, True),
    ("the link points at a pull request address",
     ["https://t.co/abc"], "https://github.com/zai-org/zcode-plugins/pull/112",
     {"https://t.co/abc": "https://github.com/zai-org/zcode-plugins/pull/112"},
     True),
    ("the link points somewhere else",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     {"https://t.co/abc": "https://github.com/someone/else"}, False),
    ("the redirect cannot be read",
     ["https://t.co/abc"], "https://github.com/hyperlane-dev/hyperlane",
     {}, None),
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

    # The address's proof. The resolver is a lookup table, so the cases
    # run without a network and pin the COMPARISON, which is the part
    # that was wrong.
    for name, tco, repo, card_text, table, expected in ADDRESS_CASES:
        def resolver(short, _table=table):
            return _table.get(short, "")
        got, why = xpost.address_proved(tco, repo, card_text,
                                        resolver=resolver)
        if got != expected:
            failures += 1
            print("FAIL xpost:  address_proved -- %s -- expected %s, got %s (%s)"
                  % (name, expected, got, why))
        else:
            print("ok   xpost:  address_proved -- %s" % name)

    # The reply script proves the address the same way, and an unreadable
    # redirect is neither a proof nor a refutation: it is reported and
    # left to the caller.
    for name, tco, repo, table, expected in REPLY_ADDRESS_CASES:
        def resolver(short, _table=table):
            return _table.get(short, "")
        got, why = xreply.address_points_at(tco, repo, resolver=resolver)
        if got != expected:
            failures += 1
            print("FAIL xreply: address_points_at -- %s -- expected %s, got %s (%s)"
                  % (name, expected, got, why))
        else:
            print("ok   xreply: address_points_at -- %s" % name)

    if failures:
        print("\n%d case(s) failed" % failures)
        return 1
    print("\nall %d comparison cases and %d readiness cases hold in both scripts"
          % (len(CASES), len(READY_CASES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
