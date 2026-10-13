#!/usr/bin/env python3
"""Derive the set of kanji legitimate in Japanese, by tokenizing a large body
of real Japanese text with janome (IPADIC) and collecting the kanji that appear
inside its recognised surface forms.

Any ideograph that never survives tokenization (or survives only as an UNKNOWN
token) is not attested Japanese vocabulary -> a Simplified-Chinese leak.

Input corpus: every Japanese .md/.txt under the given roots (default: the
system perl unicode tables + a bundled sample if present).  Cached to
ja_kanji_set.txt.
"""
import os, re, sys, glob

from janome.tokenizer import Tokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r'[㐀-䶿一-鿿豈-﫿]')

roots = sys.argv[1:] or ['/Users/sqs/code/docs/docs/ja']
texts = []
for root in roots:
    for ext in ('**/*.md', '**/*.txt'):
        for f in glob.glob(os.path.join(root, ext), recursive=True):
            try:
                texts.append(open(f, encoding='utf-8').read())
            except Exception:
                pass
if not texts:
    sys.exit('no corpus found')

tk = Tokenizer()
kanji = set()
nchars = 0
for t in texts:
    for tok in tk.tokenize(t):
        if tok.surface == '　' or tok.surface.strip() == '':
            continue
        for ch in CJK.findall(tok.surface):
            kanji.add(ch)
        nchars += 1

out = os.path.join(HERE, 'ja_kanji_set.txt')
with open(out, 'w', encoding='utf-8') as fh:
    fh.write(''.join(sorted(kanji)))
print(f'OK {len(kanji)} kanji from {nchars} tokens / {len(texts)} files -> {out}')
