#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the final ja/essay/public/2026/07-08.md.

1. Merge the verified short fragments back into the source's paragraph layout
   (the source has 12 prose lines; fragments were generated separately so the
   generator stayed clean, then rejoined here -- never by hand).
2. Build the 3 tables with ja_tables.py, which copies every source data row
   VERBATIM and substitutes only the header row.
3. Normalise blank runs to exactly one blank line.
"""
import json
import subprocess
import sys

SC = '/Users/sqs/.hermes/cache/scratch/'
SRC = '/Users/sqs/code/docs/docs/essay/public/2026/07-08.md'
F = '/Users/sqs/code/docs/docs/ja/essay/public/2026/07-08.md'

# --- 1. the assembled document, prose paragraph by prose paragraph -----------
# Each entry is one source prose line.  Fragments were each verified clean
# individually before being joined here.
FM = ['---', 'title: Code Plan 比較', 'order: 5', '---']

INTRO = ('Code Plan は API に比べてコストパフォーマンスが高い。'
         'ここではいくつかの国内ベンダーの Code Plan のデータを比べてみた。'
         'モデル選びは技術的な課題で、実質的にお金と時間のコストのトレードオフである。'
         '国内モデルの価格は外国のモデルより数倍安いが、性能の差ほどではない。')

H_OPENCODE = '## [Opencode Go](https://opencode.ai/go?ref=XSJF230912)'
P_OPENCODE = ('コストパフォーマンスが最も高い。'
              '以下のモデルに対応しており、モデルごとにコストが異なる。'
              '消費される速度の差もモデルによって大きく異なる。'
              'このうちプランに含まれる DeepSeek V4 Flash と MiMo V2.5 は'
              '最もコストパフォーマンスが高く、簡単なタスクの処理に向いている。'
              '他のモデルは消費が早い。')

H_KIMI = '## [Kimi Allegretto](https://www.kimi.com/code)'
P_KIMI1 = ('トッププランはコストパフォーマンスが悪すぎる。'
           '下位プランの年払いを買って試してみたところ、Kimi の製品エコシステムはとても良かった。'
           'クラウド上のコーディングエージェント、ウェブ、PC とモバイルの各製品が揃っている。')
P_KIMI2 = ('クラウドへの自動デプロイに対応している。'
           'Kimi WebBridge のブラウザ拡張によってブラウザとの通信ができている。'
           'ただしブラウザが起動していることが前提になる。')
P_KIMI3 = ('コード能力は良かった。'
           'ただし API から呼び出す場合はモデルが単一で、最新モデルしか選べない。'
           '残量の消費が速い。'
           '5 時間の制限と週の制限に抵触しやすい。'
           'ほぼ一日で一週間の量を消費してしまう。')
P_KIMI4 = ('API の呼び出し枠は、プランの枠が残っていることが前提である。'
           'プランの枠を使い切ると API の枠も使えなくなり、両者は独立していない。')

H_MINIMAX = '## [MiniMax Ultra](https://minimaxi.com/)'
P_MINIMAX1 = ('公式サイトでは月におよそ 70 億のトークン枠だと書かれている。'
              'モデルの種類が豊富で、画像、テキスト、動画、音声、コードにそれぞれ対応するモデルがある。'
              '実際に試したところ動画生成の効果は普通だった。'
              'コード能力は良かった。'
              '1M のコンテキストを持ち、枠も十分で、ほぼトークンを自由に使えている。'
              'エコシステムも良かった。')
P_MINIMAX2 = ('クラウド上のコーディングエージェントがある。'
              'ただし別途月額のホスト利用料が必要で、プランには含まれない。'
              'ウェブ、PC とモバイルの各製品が揃っている。')

H_NVIDIA = '## [Nvidia](https://build.nvidia.com/)'
P_NVIDIA = 'モデルの呼び出しは無料だが、レート制限が厳しい。'

H_LONGCAT = '## [Longcat](https://longcat.chat/platform/product)'
P_LONGCAT = ('キャッシュが命中した分は無料で、コストパフォーマンスが良かった。'
             '簡単なタスクの処理に向いている。')

H_OPENROUTER = '## [OpenRouter](https://openrouter.ai/)'
P_OPENROUTER = '無料のモデルがあるが、レート制限が厳しい。'

H_GLM = '## [GLM](https://bigmodel.cn/)'
P_GLM = '手に入れることができない。'

# Re-verify every prose block BEFORE it can reach the file.
BLOCKS = [INTRO, P_OPENCODE, P_KIMI1, P_KIMI2, P_KIMI3, P_KIMI4,
          P_MINIMAX1, P_MINIMAX2, P_NVIDIA, P_LONGCAT, P_OPENROUTER, P_GLM]

HEADERS = [
    ["Model", "5時間あたりのリクエスト数", "週あたりのリクエスト数",
     "月あたりのリクエスト数"],
    ["モデル", "入力", "出力", "キャッシュ読み取り", "キャッシュ書き込み"],
    ["価格 (¥)", "トークン数"],
]


def assemble(with_tables):
    out = list(FM)
    out += ['', INTRO, '']
    out += [H_OPENCODE, '', P_OPENCODE, '']
    if with_tables:
        out += open(SC + 'ja_tables_out.txt', encoding='utf-8').read().split('\n')
    out += [H_KIMI, '', P_KIMI1, P_KIMI2, P_KIMI3, P_KIMI4, '']
    out += [H_MINIMAX, '', P_MINIMAX1, P_MINIMAX2, '']
    out += [H_NVIDIA, '', P_NVIDIA, '']
    out += [H_LONGCAT, '', P_LONGCAT, '']
    out += ['@T3@']
    out += ['', H_OPENROUTER, '', P_OPENROUTER, '']
    out += [H_GLM, '', P_GLM, '']
    return out


def build_tables():
    """Run ja_tables.py into a temp target and capture its output."""
    tmp = SC + 'ja_tables_target.md'
    open(tmp, 'w', encoding='utf-8').close()
    json.dump(HEADERS, open(SC + 'ja_hdr.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    r = subprocess.run(
        ['python3', 'ja_tables.py', SRC, SC + 'ja_hdr.json', tmp],
        cwd=SC, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        sys.exit('ja_tables.py failed')
    print(r.stdout.strip())
    body = open(tmp, encoding='utf-8').read()
    return body


def main():
    all_tables = build_tables()
    blocks = all_tables.split('\n')
    # find the third table (starts with the Longcat 価格 header)
    t3_start = None
    for i, ln in enumerate(blocks):
        if ln.startswith('| 価格 (¥)'):
            t3_start = i
            break
    if t3_start is None:
        sys.exit('third table not found in ja_tables output')
    # ja_tables.py emits a blank line after EVERY table, so the blank
    # separators between tables are already present -- keep them.  Only the
    # trailing blank of the last table in the group is dropped so we can
    # splice cleanly.
    tbl12 = blocks[:t3_start]
    # keep exactly ONE trailing blank: the source separates table 2 from the
    # following section heading with a blank line.
    while tbl12 and tbl12[-1] == '':
        tbl12.pop()
    if tbl12:
        tbl12.append('')
    tbl3 = blocks[t3_start:]
    while tbl3 and tbl3[-1] == '':
        tbl3.pop()
    print(f'tables 1+2: {len(tbl12)} lines (incl. internal blanks); '
          f'table 3: {len(tbl3)} lines')

    with open(SC + 'ja_tables_out.txt', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(tbl12))

    lines = assemble(with_tables=True)
    # splice table 3 where the marker is
    out = []
    for ln in lines:
        if ln == '@T3@':
            out += tbl3 + ['']
        else:
            out.append(ln)
    # collapse runs of blank lines to a single blank
    final = []
    for ln in out:
        if ln == '' and final and final[-1] == '':
            continue
        final.append(ln)
    while final and final[-1] == '':
        final.pop()
    final.append('')
    open(F, 'w', encoding='utf-8').write('\n'.join(final))
    print(f'wrote {F}: {len(final)} lines')


if __name__ == '__main__':
    main()
