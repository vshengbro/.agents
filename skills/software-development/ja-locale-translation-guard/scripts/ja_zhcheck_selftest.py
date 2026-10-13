#!/usr/bin/env python3
"""Self-test for ja_zhcheck.py: (1) no false positives across every Japanese
file in the repo, (2) known-leak fixtures are caught, (3) a clean fixture
passes."""
import glob
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHK = os.path.join(HERE, 'ja_zhcheck.py')
FILES = sorted(glob.glob('/Users/sqs/code/docs/docs/ja/**/*.md', recursive=True))

bad = []
for f in FILES:
    r = subprocess.run([sys.executable, CHK, f], capture_output=True, text=True)
    if r.returncode != 0:
        bad.append((f, r.stdout.strip().split('\n')[1:4]))
print(f'[1] false-positive scan over {len(FILES)} Japanese files: '
      f'{"CLEAN" if not bad else str(len(bad)) + " FILES FLAGGED"}')
for f, out in bad[:10]:
    print('   ', f)
    for l in out:
        print('      ', l)

LEAKS = [
    ('国内厂商の Code Plan', '厂'),
    ('效果却没那么大', '效'),
    ('这个价格', '这'),
    ('网络请求数', '网'),
    ('简化车型', '车'),
    ('开门见山', '门'),
]
fail = 0
with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False,
                                 encoding='utf-8') as fh:
    for text, ch in LEAKS:
        fh.write(text + '\n')
    leak_path = fh.name
r = subprocess.run([sys.executable, CHK, leak_path], capture_output=True, text=True)
caught = r.stdout
print(f'[2] leak fixture ({"".join(c for _, c in LEAKS)}): '
      f'{"CAUGHT" if r.returncode != 0 else "MISSED"}')
if r.returncode == 0:
    fail = 1
    print(caught)

GOOD = ('Code Plan は API に比べてコストパフォーマンスが高い。'
        '国内モデルの価格は外国より数倍安い。\n'
        'この実装は性能が高い。気_radius と Ajax の構成に需要注意。\n')
with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False,
                                 encoding='utf-8') as fh:
    fh.write(GOOD)
    good_path = fh.name
r = subprocess.run([sys.executable, CHK, good_path], capture_output=True, text=True)
print(f'[3] clean fixture: {"CLEAN" if r.returncode == 0 else "FALSE POSITIVE"}')
if r.returncode != 0:
    fail = 1
    print(r.stdout)

os.unlink(leak_path)
os.unlink(good_path)
sys.exit(1 if (bad or fail) else 0)
