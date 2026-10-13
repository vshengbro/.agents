#!/usr/bin/env python3
"""Build the tables for ja/07-08.md by copying the SOURCE table rows verbatim
and substituting ONLY the header cells. Data cells stay byte-identical by
construction. Usage: ja_tables.py <source> <headers-json> <target>
headers-json: list of lists, one per table, of translated header cells.
"""
import json, sys, re

src, hdr_json, dst = sys.argv[1], sys.argv[2], sys.argv[3]
headers = json.loads(open(hdr_json, encoding='utf-8').read())

src_lines = open(src, encoding='utf-8').read().split('\n')
# collect table blocks: consecutive lines starting with '|'
blocks, cur = [], []
for ln in src_lines:
    if ln.startswith('|'):
        cur.append(ln)
    else:
        if cur:
            blocks.append(cur); cur = []
if cur:
    blocks.append(cur)

assert len(blocks) == len(headers), f'{len(blocks)} tables in source vs {len(headers)} headers given'

out = []
for block, hdr in zip(blocks, headers):
    assert len(hdr) == len(block[0].split('|')) - 2, (
        f'header width {len(hdr)} != source width {len(block[0].split("|")) - 2}')
    # rebuild only the header row, preserving nothing else from it
    new_hdr = '| ' + ' | '.join(hdr) + ' |'
    out.append(new_hdr)
    # alignment row and all data rows: verbatim
    out.extend(block[1:])
    out.append('')

with open(dst, 'w', encoding='utf-8').write('') if False else open(dst, 'a', encoding='utf-8') as f:
    for ln in out:
        f.write(ln + '\n')

# verify widths preserved
chk = open(dst, encoding='utf-8').read().split('\n')
newblocks, cur = [], []
for ln in chk:
    if ln.startswith('|'):
        cur.append(ln)
    else:
        if cur:
            newblocks.append(cur); cur = []
if cur:
    newblocks.append(cur)
for i, (a, b) in enumerate(zip(blocks, newblocks)):
    assert len(a) == len(b), f'table {i}: rows {len(b)} vs {len(a)}'
    for ra, rb in zip(a, b):
        assert len(ra.split('|')) == len(rb.split('|')), f'table {i}: col width mismatch'
        if ra != b[1] and ra != rb.split('|')[0] + '|':
            pass
    # data rows must be byte-identical
    for k in range(1, len(a)):
        assert a[k] == b[k], f'table {i} row {k} changed:\n{a[k]}\n{b[k]}'
print(f'OK wrote {len(newblocks)} tables to {dst}; rows+cols match, data rows byte-identical')
