#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build char -> real-Japanese-word evidence from janome's raw IPADIC data.

janome/sysdic/entries_*.py hold  DATA={id:(surface, posA, posB, ...)}  where
posA/posB index the lexicon in janome/sysdic/pos.py (or entries' sibling
tables).  We only need the SURFACE forms: a CJK char is Japanese iff it occurs
in a multi-character surface, or in a one-character surface that is a real
Japanese word.

Usage: python3 build_index.py
"""
import glob
import os
import pickle
import re
import sys

HERE = '/Users/sqs/.hermes/cache/scratch/'
CJK = re.compile(r'[一-鿿]')
sys.path.insert(0, os.path.expanduser(
    '~/Library/Python/3.9/lib/python/site-packages'))

import janome  # noqa: E402

D = os.path.join(os.path.dirname(janome.__file__), 'sysdic')
files = [f for f in sorted(glob.glob(os.path.join(D, 'entries_*.py')))
         if 'idx' not in f]
print(f'{len(files)} entry files under {D}')

# file -> {id: (surface, posA, posB, ...)}
shards = {}
for f in files:
    ns = {}
    with open(f, encoding='utf-8') as fh:
        src = fh.read()
    body = src[src.index('=') + 1:].strip()
    try:
        obj = eval(body, {'__builtins__': {}}, ns)  # noqa: S307
    except Exception as e:
        print('  skip', os.path.basename(f), type(e).__name__, e)
        continue
    shards[os.path.basename(f)] = obj
    print(f'  {os.path.basename(f)}: {len(obj)} entries')
print('parsed shards:', {k: len(v) for k, v in shards.items()})

# Find the POS table so we can drop 固有名詞/組織 entries.
posfile = os.path.join(D, 'pos.py')
have_pos = os.path.exists(posfile)
print('pos.py present:', have_pos)
if have_pos:
    print(open(posfile, encoding='utf-8').read()[:400])

# Surface forms only: every char appearing in a >=2 char surface.
index = {}
single = {}
for name, obj in shards.items():
    for eid, e in obj.items():
        if not (isinstance(e, (list, tuple)) and e):
            continue
        surf = e[0]
        if not isinstance(surf, str):
            continue
        chars = set(CJK.findall(surf))
        if not chars:
            continue
        if len(surf) >= 2:
            for ch in chars:
                index.setdefault(ch, set()).add(surf)
        else:
            for ch in chars:
                single.setdefault(ch, set()).add(surf)

print(f'multi-char index: {len(index)} chars; single-char surfaces: {len(single)}')
for c in '国会体性能格品厂效够网马鸟龙这说门车长问吗师层务异装独动':
    print(f'  {c}: multi={sorted(index.get(c, []))[:4]} single={sorted(single.get(c, []))[:3]}')

pickle.dump({'multi': {k: sorted(v)[:10] for k, v in index.items()},
             'single': {k: sorted(v)[:10] for k, v in single.items()}},
            open(HERE + 'ja_ipadic_index.pkl', 'wb'))
print('-> ja_ipadic_index.pkl')
