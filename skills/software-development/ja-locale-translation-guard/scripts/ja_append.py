#!/usr/bin/env python3
"""Append a block of text to a markdown file, then scan for corruption."""
import re, sys, unicodedata

# Corruption signature: hangul or replacement chars, or unexpected Latin words in JA prose.
HANGUL = re.compile(r'[\uac00-\ud7af\u3130-\u318f]')
BAD_LATIN = re.compile(r'[A-Za-z]{3,}')
ALLOW_LATIN = set(
    'NFC T-money App CU SM KTX UNESCO '
    # product / brand names that legitimately appear in Japanese prose
    'API Code Plan DeepSeek Flash MiMo Kimi WebBridge Web PC'.split()
)
# Simplified-Chinese-only forms that are wrong in Japanese
ZH_ONLY = re.compile(r'[网上这来对时说过还们个为后会见风书车东门马鸟长门开关闭间问题]')
REPL = re.compile(r'[\ufffd\u2028\u2029]')

def scan(path):
    txt = open(path, encoding='utf-8').read()
    probs = []
    in_fm = False
    for i, ln in enumerate(txt.split('\n'), 1):
        s = ln.strip()
        if i == 1 and s == '---':
            in_fm = True; continue
        if in_fm:
            if s == '---': in_fm = False
            continue
        if not s or s.startswith(('![', '|', '```', '#')):
            continue
        for m in BAD_LATIN.finditer(s):
            if m.group(0) not in ALLOW_LATIN:
                probs.append((i, 'latin:' + m.group(0), s[:70]))
        if HANGUL.search(s):
            probs.append((i, 'hangul', s[:70]))
        if REPL.search(s):
            probs.append((i, 'replacement-char', s[:70]))
        for ch in s:
            if unicodedata.category(ch).startswith('C') and ch not in '\n\t':
                probs.append((i, 'ctrl:' + repr(ch), s[:70]))
    return probs

def report(path, probs):
    print(f'SCAN {path}: {"CLEAN" if not probs else "PROBLEMS(" + str(len(probs)) + ")"}')
    for i, t, c in probs[:15]:
        print(f'  L{i} {t} | {c}')

if __name__ == '__main__':
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'append'
    if mode == 'scan':
        p = scan(path); report(path, p); sys.exit(1 if p else 0)
    block = sys.stdin.read()
    with open(path, 'a', encoding='utf-8') as f:
        if not block.startswith('\n'):
            f.write('\n')
        f.write(block)
        if not block.endswith('\n'):
            f.write('\n')
    p = scan(path)
    report(path, p)
    sys.exit(1 if p else 0)
