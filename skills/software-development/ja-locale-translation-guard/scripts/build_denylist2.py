#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit the Chinese-leak denylist.

Rule: a char is a Chinese leak iff it has NO evidence of being a Japanese
word in IPADIC.  Evidence = it occurs in a multi-character dictionary surface
(実装, 独立, 国家) or a standalone one-character surface (国, 会, 性能).

The only noise is 固有名詞 junk, which admits 厂商/效果/效範.  Those surfaces
are proper nouns; we drop a char if ALL of its evidence consists solely of
names.  IPADIC marks names by containing 范/範/氏/君/etc -- simpler: require
the evidence word to be a plausible Japanese compound, which we approximate
by excluding a small hand-list of the exact junk surfaces we have observed.

Usage: python3 build_denylist2.py
"""
import glob
import pickle
import re
import sys

HERE = '/Users/sqs/.hermes/cache/scratch/'
CJK = re.compile(r'[一-鿿]')

cand = set(open(HERE + 'ja_zhcheck_candidates.txt', encoding='utf-8').read().strip())
d = pickle.load(open(HERE + 'ja_ipadic_index.pkl', 'rb'))
multi, single = d['multi'], d['single']

# Surfaces that are proper nouns / Chinese proper nouns rather than Japanese.
JUNK_SURF = re.compile(r'效範|厂商|效果|电网|网络')


def jp_evidence(c):
    hits = [w for w in multi.get(c, []) if not JUNK_SURF.search(w)]
    if hits:
        return True
    return bool(single.get(c))


# A char attested in real Japanese prose is Japanese even if IPADIC is thin.
# "Real Japanese prose" = a line that is not a leftover untranslated Chinese
# comment.  Heuristic: Japanese lines carry kana; a line of pure hanzi is
# Chinese left untranslated (as in hyperlane/quick-start/directory.md comments).
# So we only credit a corpus occurrence when its line contains kana, or when
# the char is also a standalone IPADIC word.
corpus = set()
for f in glob.glob('/Users/sqs/code/docs/docs/ja/**/*.md', recursive=True):
    if f.endswith('essay/public/2026/07-08.md'):
        continue          # our own file must never excuse a leak
    for ln in open(f, encoding='utf-8').read().split('\n'):
        if re.search(r'[぀-ヿ]', ln):
            corpus |= set(CJK.findall(ln))

lex = {c for c in cand if jp_evidence(c)}
# No corpus fallback: IPADIC alone is authoritative.  Every Simplified-only
# glyph (录/动/师) has a DIFFERENT shinjitai codepoint (録/動/師), so a
# Simplified char can never appear inside a genuine Japanese word.  Corpus
# evidence therefore only ever comes from untranslated Chinese or from typos,
# and crediting it would wrongly re-admit exactly the chars we must catch.
keep = sorted(cand - lex)

must = '厂效够网马鸟龙这说门车长东开关间还为见风书问吗师层务异录动'
miss = [c for c in must if c not in keep]
mustnot = '国会体性能格品商装独'
fp = [c for c in mustnot if c in keep]
print(f'candidates {len(cand)} | japanese {len(lex)} | DENY {len(keep)}')
print(f'must-have (chinese-only)  : '
      f'{"ALL PRESENT" if not miss else "MISSING " + "".join(miss)}')
print(f'must-not-have (real ja)   : '
      f'{"OK" if not fp else "WRONGLY DENIED " + "".join(fp)}')
with open(HERE + 'ja_zhcheck_denylist.txt', 'w', encoding='utf-8') as fh:
    fh.write(''.join(keep))
print('-> ja_zhcheck_denylist.txt')
sys.exit(1 if (miss or fp) else 0)
