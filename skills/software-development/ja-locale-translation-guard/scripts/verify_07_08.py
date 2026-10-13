#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify docs/ja/essay/public/2026/07-08.md against the Chinese source.

Checks:
  (a) line 1 is exactly '---'
  (b) yaml.safe_load of the frontmatter succeeds; keys are exactly
      ['title','order'] in that order; order is identical to the source
  (c) the ATX heading-level sequence matches the source exactly
  (d) all 3 tables: same row count, same column count per row, and every data
      row plus every '| ---: |' alignment row byte-identical to the source
  (e) the ordered list of link targets is byte-identical to the source's URLs
"""
import re
import sys

import yaml

SRC = '/Users/sqs/code/docs/docs/essay/public/2026/07-08.md'
DST = '/Users/sqs/code/docs/docs/ja/essay/public/2026/07-08.md'

src = open(SRC, encoding='utf-8').read()
dst = open(DST, encoding='utf-8').read()
fails = []


def check(name, ok, detail=''):
    print(f'[{name}] {"PASS" if ok else "FAIL"}' + (f' -- {detail}' if detail else ''))
    if not ok:
        fails.append(name)


# (a) starts with ---
check('a: starts with ---', dst.split('\n')[0] == '---',
      repr(dst.split('\n')[0]))


def fm(text):
    lines = text.split('\n')
    assert lines[0] == '---'
    end = lines.index('---', 1)
    return lines[1:end]


# (b) frontmatter
try:
    s_fm = yaml.safe_load('\n'.join(fm(src)))
    d_fm = yaml.safe_load('\n'.join(fm(dst)))
    ok = (list(s_fm.keys()) == list(d_fm.keys()) == ['title', 'order']
          and s_fm['order'] == d_fm['order'])
    check('b: frontmatter', ok,
          f'src keys {list(s_fm.keys())} order {s_fm["order"]!r} | '
          f'dst keys {list(d_fm.keys())} order {d_fm["order"]!r}')
except Exception as e:
    check('b: frontmatter', False, f'{type(e).__name__}: {e}')

# (c) heading level sequence
HEAD = re.compile(r'^(#{1,6})\s+(.*)$', re.M)


def heads(t):
    body = '\n'.join(t.split('\n')[fm(t).__len__() + 2:])
    return [(len(m.group(1)), m.group(2)) for m in HEAD.finditer(body)]


sh, dh = heads(src), heads(dst)
check('c: heading levels', [l for l, _ in sh] == [l for l, _ in dh],
      f'src {len(sh)} headings {sorted(set(l for l, _ in sh))} | '
      f'dst {len(dh)} headings {sorted(set(l for l, _ in dh))}')


# (d) tables
def tables(t):
    out, cur = [], []
    for ln in t.split('\n'):
        if ln.startswith('|'):
            cur.append(ln)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


st, dt = tables(src), tables(dst)
ok = len(st) == len(dt) == 3
detail = f'src {len(st)} tables, dst {len(dt)} tables'
if ok:
    for i, (a, b) in enumerate(zip(st, dt), 1):
        ra = [r.split('|') for r in a]
        rb = [r.split('|') for r in b]
        rows_ok = len(a) == len(b)
        cols_ok = [len(x) for x in ra] == [len(x) for x in rb]
        # every non-header row must be byte-identical
        data_ok = all(a[k] == b[k] for k in range(1, len(a)))
        detail += (f' | t{i}: rows {len(a)}/{len(b)} cols_ok={cols_ok} '
                   f'data_identical={data_ok}')
        ok = ok and rows_ok and cols_ok and data_ok
check('d: tables', ok, detail)

# (e) link targets in order
LINK = re.compile(r'\[[^\]]*\]\(([^)]*)\)')
sl = LINK.findall(src)
dl = LINK.findall(dst)
check('e: link targets', sl == dl,
      f'src {len(sl)} links, dst {len(dl)} links'
      + ('' if sl == dl else f' | src={sl} dst={dl}'))

print()
if fails:
    print(f'RESULT: {len(fails)} CHECK(S) FAILED: {fails}')
    sys.exit(1)
print('RESULT: ALL CHECKS PASSED')
