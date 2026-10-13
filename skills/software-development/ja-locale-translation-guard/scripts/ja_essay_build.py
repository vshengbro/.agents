#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build docs/ja/essay/public/2026/07-08.md incrementally.

Every write goes through ja_para.py (Latin/hangul scan) and is immediately
re-checked with ja_zhcheck.py (Chinese-leak denylist).  Any failure aborts, so
a corrupt paragraph can never survive into the file.
"""
import subprocess

SC = '/Users/sqs/.hermes/cache/scratch'
F = '/Users/sqs/code/docs/docs/ja/essay/public/2026/07-08.md'

FM = '---\ntitle: Code Plan 比較\norder: 5\n---\n'


def para(*sentences):
    r = subprocess.run(['python3', 'ja_para.py', F] + list(sentences),
                       cwd=SC, capture_output=True, text=True)
    line = r.stdout.strip().split('\n')[0]
    ok = 'CLEAN' in line
    print(('  ok  ' if ok else ' FAIL ') + line)
    if not ok:
        print(r.stdout)
        raise SystemExit('scan failed; aborting')
    zh()


def zh():
    z = subprocess.run(['python3', 'ja_zhcheck.py', F], cwd=SC,
                       capture_output=True, text=True)
    if z.returncode != 0:
        print(z.stdout)
        raise SystemExit('chinese leak; aborting')
    return z.stdout.strip().split('\n')[0]


def h2(text):
    para('--h2', text)


def blank():
    para('--blank')


def show(tag=''):
    print('---', tag, '---')
    for i, ln in enumerate(open(F, encoding='utf-8').read().split('\n'), 1):
        print(f'{i:3d}| {ln}')


def reset():
    open(F, 'w', encoding='utf-8').write(FM)
