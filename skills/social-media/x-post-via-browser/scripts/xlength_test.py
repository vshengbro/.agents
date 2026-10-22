#!/usr/bin/env python3
"""The weighted length of a copy, measured the way X measures it.

Run directly:

    python3 xlength_test.py

X does not count characters; it counts WEIGHTED characters, and the limit
is 280 of them. The rules come from twitter-text v3 -- the library the web
client uses to size its composer -- and they are not what `len()` says:

  * a URL counts as 23 characters, whatever its real length is;
  * a character in the Latin and general-punctuation ranges counts 1;
  * every other character -- CJK, fullwidth forms -- counts 2.

The gate used to measure raw characters, so a Chinese reply of 186
characters passed the gate at 186 and the SITE refused it at 372. That
happened on 2026-10-22: the copy was written, the composer took it, and
the send was rejected with the text still sitting in the composer, where
the next candidate trips the "composer already holds text" refusal.

These cases pin the measurement against the vectors twitter-text itself
publishes, so a change to the counting cannot quietly drift.
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


xlength = _load("xlength")
xreply = _load("xreply")
xpost = _load("xpost")

# (name, text, expected weighted length)
#
# The expected values come from twitter-text v3's own configuration:
# maxWeightedTweetLength 280, scale 100, defaultWeight 200, transformedURL
# Length 23, and the four ranges whose characters weigh 100.
CASES = [
    ("an empty string weighs nothing", "", 0),
    ("a latin word weighs one per character", "hello", 5),
    ("a sentence of latin weighs one per character",
     "the quick brown fox", 19),
    ("a CJK character weighs two", "中", 2),
    ("a run of CJK weighs two per character", "中文测试", 8),
    ("latin and CJK weigh differently in the same string",
     "DeepSeek 部署", 8 + 1 + 4),
    ("an address weighs 23, whatever its length",
     "https://github.com/hyperlane-dev/hyperlane", 23),
    ("a long address still weighs 23",
     "https://github.com/hyperlane-dev/hyperlane-mcp-upload-and-more", 23),
    ("an address inside a sentence",
     "see https://github.com/vshengbro/euv now", 4 + 23 + 4),
    ("fullwidth punctuation weighs two", "（括号）", 8),
    ("the em dash is in the one-weight range", "a—b", 3),
    ("an emoji weighs two", "\U0001f600", 2),
    ("a ZWJ emoji sequence weighs two, not four",
     "\U0001f468‍\U0001f469", 2),
]


def main() -> int:
    failures = 0

    for name, text, expected in CASES:
        got = xlength.weighted_length(text)
        if got != expected:
            failures += 1
            print("FAIL xlength: %s -- expected %d, got %d"
                  % (name, expected, got))
        else:
            print("ok   xlength: %s" % name)

    # The limit itself, from the config.
    if xlength.MAX_WEIGHTED != 280:
        failures += 1
        print("FAIL xlength: the limit is %d, expected 280"
              % xlength.MAX_WEIGHTED)
    else:
        print("ok   xlength: the limit is 280")

    # The gate refuses a copy the site would refuse. Both posting scripts
    # carry the gate, so both are pinned against the same fixtures.
    #
    # The copy below is 186 raw characters of Chinese, which is 372
    # weighted -- past the limit in a way `len()` cannot see.
    over = "补" * 186
    under = "补" * 140
    # The post's copy ends with an address, which weighs 23 and is preceded
    # by a space that weighs 1, so the prose has 256 weighted characters
    # left: 128 Chinese ones.
    repo = "https://github.com/hyperlane-dev/hyperlane"
    for label, gate in (("xreply", xreply.gate_copy),
                        ("xpost", xpost.gate_copy)):
        # The no-repo gate is the reply's; the post's needs an address.
        if label == "xreply":
            refused = gate(over, None)
            allowed = gate(under, None)
        else:
            refused = gate(over + " " + repo, repo)
            allowed = gate("补" * 128 + " " + repo, repo)
        if not any("weighted length" in p for p in refused):
            failures += 1
            print("FAIL %s: the gate let through a copy of 372 weighted "
                  "characters (got: %s)" % (label, refused))
        else:
            print("ok   %s: the gate refuses 372 weighted characters" % label)
        if any("weighted length" in p for p in allowed):
            failures += 1
            print("FAIL %s: the gate refused a copy of 280 weighted "
                  "characters (got: %s)" % (label, allowed))
        else:
            print("ok   %s: the gate allows 280 weighted characters" % label)

    if failures:
        print("\n%d case(s) failed" % failures)
        return 1
    print("\nall %d weighted-length cases hold" % len(CASES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
