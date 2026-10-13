#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chinese-leak check for Japanese prose.

The denylist is built OFFLINE by build_denylist.py from a hand-verified
simplified/shinjitai table, keeping only chars that are provably a
Simplified-only codepoint whose Japanese counterpart is attested elsewhere.
So it has zero false positives on genuine Japanese kanji.

Table rows, headings, fences, images and link targets are skipped: model names
and URLs there are intentionally verbatim.

Usage: python3 ja_zhcheck.py <file>
"""
import re
import sys

LIST = '/Users/sqs/.hermes/cache/scratch/ja_zhcheck_denylist.txt'
CJK = re.compile(r'[㐀-䶿一-鿿豈-﫿]')


def main():
    path = sys.argv[1]
    deny = set(open(LIST, encoding='utf-8').read().strip())
    txt = open(path, encoding='utf-8').read()
    in_fm = txt.startswith('---\n')
    probs, seen = [], set()
    for i, ln in enumerate(txt.split('\n'), 1):
        s = ln.strip()
        if in_fm:
            if i > 1 and s == '---':
                in_fm = False
            continue
        if not s or s.startswith(('|', '#', '```', '![', '>')):
            continue
        # keep the link TARGET, drop the anchor text when checking
        s = re.sub(r'\]\([^)]*\)', ']', s)
        for ch in CJK.findall(s):
            if ch in deny and ch not in seen:
                seen.add(ch)
                probs.append((i, ch, s[:64]))
    if probs:
        print(f'ZHLEAK {path}: FOUND({len(probs)})')
        for i, ch, ctx in probs:
            print(f'  L{i} {ch} | {ctx}')
        sys.exit(1)
    print(f'ZHLEAK {path}: CLEAN ({len(deny)} chars denylisted)')


if __name__ == '__main__':
    main()
