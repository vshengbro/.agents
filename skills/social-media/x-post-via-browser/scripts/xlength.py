#!/usr/bin/env python3
"""X's own length rule, measured the way X measures it.

X does not count characters. It counts WEIGHTED characters, and the limit
is 280 of them. The rules come from twitter-text v3, the library the web
client uses to size the composer:

  * a URL counts as 23 characters, whatever its real length is, because X
    rewrites every address to a t.co link;
  * a character in the Latin and general-punctuation ranges counts 1;
  * every other character -- CJK, fullwidth forms, emoji -- counts 2.

So a Chinese reply is worth roughly half as many characters as an English
one of the same length, and the gap is invisible to a gate that counts
`len(copy)`. That gap is not theoretical: a copy of 168 Chinese characters
is 262 weighted characters and fits, and a copy of 186 is over the limit
and is refused by the site AFTER the composer has taken it -- which leaves
the text sitting in the composer for the next candidate to trip over.

Measuring the copy the way the site measures it is the whole point of this
module, so the gate refuses BEFORE anything is typed.

The emoji handling is an APPROXIMATION of twitter-text's grapheme
clustering: a ZWJ sequence is counted as one weighted character, while
twitter-text counts the whole cluster as two. It errs on the side of
counting MORE, because over-counting refuses a copy that might have fit
(trim it and send it) while under-counting lets a copy through that the
site refuses at the send button (the run then fails with a composer
nobody can clear).

Usage:
    python3 xlength.py FILE
    python3 xlength.py --text "the copy"
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# twitter-text v3: the limit, in weighted characters.
MAX_WEIGHTED = 280

# twitter-text v3: a URL is rewritten to a t.co link of this length.
URL_WEIGHT = 23

# twitter-text v3: the ranges whose characters weigh 1. Everything outside
# them weighs 2.
ONE_WEIGHT_RANGES = (
    (0x0000, 0x10FF),   # Latin, Latin-1, Latin Extended A and B, IPA
    (0x2000, 0x200D),   # general punctuation, first block
    (0x2010, 0x201F),   # general punctuation, second block
    (0x2022, 0x2027),   # bullets and quotes
)

# An address, the same span the gate already looks for.
URL_RE = re.compile(r"https?://\S+")

# The code points that take part in an emoji cluster.
EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
)
# The joiners and modifiers that continue a cluster rather than starting one.
ZWJ = 0x200D
VARIATION_SELECTOR = 0xFE0F
SKIN_TONE = (0x1F3FB, 0x1F3FF)


def _is_one_weight(code: int) -> bool:
    """Whether one character of this code point counts as one."""
    return any(lo <= code <= hi for lo, hi in ONE_WEIGHT_RANGES)


def _is_emoji(code: int) -> bool:
    return any(lo <= code <= hi for lo, hi in EMOJI_RANGES)


def weighted_length(text: str) -> int:
    """The length X counts, in weighted characters."""
    total = 0
    pos = 0
    for m in URL_RE.finditer(text):
        total += _plain_weight(text[pos:m.start()])
        total += URL_WEIGHT
        pos = m.end()
    total += _plain_weight(text[pos:])
    return total


def _plain_weight(text: str) -> int:
    """The weight of a span that holds no address."""
    total = 0
    i = 0
    length = len(text)
    while i < length:
        code = ord(text[i])
        if _is_emoji(code):
            # One cluster, whatever it is made of, counts as two.
            total += 2
            i += 1
            while i < length:
                nxt = ord(text[i])
                if (nxt == VARIATION_SELECTOR
                        or SKIN_TONE[0] <= nxt <= SKIN_TONE[1]):
                    i += 1
                    continue
                if nxt == ZWJ and i + 1 < length and _is_emoji(ord(text[i + 1])):
                    i += 2
                    continue
                break
            continue
        total += 1 if _is_one_weight(code) else 2
        i += 1
    return total


def main(argv: list[str]) -> int:
    text = None
    if len(argv) > 2 and argv[1] == "--text":
        text = argv[2]
    elif len(argv) > 1:
        text = Path(argv[1]).read_text(encoding="utf-8").strip()
    else:
        print(__doc__)
        return 2
    weight = weighted_length(text)
    print("raw=%d weighted=%d limit=%d%s"
          % (len(text), weight, MAX_WEIGHTED,
             " OVER" if weight > MAX_WEIGHTED else ""))
    return 1 if weight > MAX_WEIGHTED else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
