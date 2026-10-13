---
name: ja-locale-translation-guard
description: Use when translating docs/ja/** from the Chinese source.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [japanese, i18n, translation, docs, markdown, validation]
---

# Japanese locale translation guard (docs repo)

## When to Use

- Translating any `docs/ja/**` file from the Chinese original in
  `docs/essay/**` or `docs/zh/**`.
- Regenerating or auditing a Japanese locale page where a docs build would
  break if the markdown skeleton drifts from the source.
- Before adding a new `docs/ja/` translation of a doc that contains tables.

All scripts live in `scripts/` beside this file. Copy them to a scratch dir and
run from there; they resolve their own data files by `__file__`/relative path.

Translating a Chinese doc into `docs/ja/` fails in one specific way: a **long
Japanese paragraph generated in a single tool call degenerates** into stray
Latin tokens, Hangul, or repeated filler. Tables, headings and link targets are
not the risk and must stay byte-identical to the source.

## Rule 1 — never emit a long Japanese paragraph in one call

Build every paragraph from 2-3 **short** sentences, each its own quoted
argument, and machine-check after every single write:

```
python3 ja_para.py <file> "短い文。" "別の短い文。"
python3 ja_para.py <file> --h2 "[Name](https://url)"
python3 ja_para.py <file> --blank
python3 ja_para.py <file> scan
```

On `PROBLEMS`, the helper prints the offending line — delete that line and
re-add it. **Never continue past a PROBLEMS.** Longer sentences corrupt more
often; if a 4-sentence paragraph keeps failing, generate the sentences as
separate verified fragments and join them in a script afterwards.

## Rule 2 — the shipped Latin allowlist is too small

`ja_append.py`'s `ALLOW_LATIN` starts as just `NFC T-money App CU SM KTX
UNESCO`. Legit prose in these files also needs `API Code Plan DeepSeek Flash
MiMo Kimi WebBridge Web PC`. Table and heading lines are skipped by the
scanner, so model names inside tables/headings never trip it.

## Rule 3 — CP932/JIS cannot detect Chinese leaks; use a lexicon denylist

`厂 效 网 车 门 这` are all valid **JIS X 0208 / CP932** codepoints, so a
"is this kanji in the Japanese repertoire" test silently passes them. Confirmed
by direct test: euc_jp, shift_jis and cp932 all accept 厂 效 网 价格 性能 商.

The working test is the reverse: a char is a Chinese leak iff it is **not a
word in the Japanese lexicon**. Build it once:

```
python3 build_index.py      # parse janome sysdic entries_*.py -> char index
python3 build_denylist2.py  # emit ja_zhcheck_denylist.txt (637 chars)
python3 ja_zhcheck.py <file>
python3 ja_zhcheck_selftest.py
```

Two IPADIC traps, both hit in practice:
- The `固有名詞` / `組織` bucket is junk — it admits 厂商, 效果, 层 as bogus
  proper nouns. Exclude `parts[0]=='名詞' and parts[1] in ('固有名詞','組織')`.
  Note the sub-classification is index **1**, not index 2.
- Jukujikun lists bare 厂/效/动/师 as 一般 nouns, so a 1-char probe is
  unreliable in **both** directions. Require multi-char or standalone
  *general-POS* surface evidence.

**Never add a corpus fallback** (chars seen in other `docs/ja` files). A
Simplified char has a *different codepoint* than its shinjitai (网/網, 动/動,
师/師), so corpus hits come only from untranslated Chinese or from typos —
crediting them re-admits exactly the chars you must catch. It also mis-fires
on Chinese comments left inside otherwise-Japanese files (e.g.
`hyperlane/quick-start/directory.md` `# 接口控制层`).

`docs/ja/essay/private/2025/11-23.md`, `2025/11-24.md` and
`hyperlane/quick-start/directory.md` still contain **pre-existing** Chinese
leaks. The self-test flags them; that is correct behaviour, not a regression.

## Rule 3b — two `ja_append.py` false positives on a CORRECT file

`ja_append.py` rejects a fully valid translation in two specific ways. Do **not**
edit `ja_append.py` while a parallel worker may be using it — copy the scanner to
scratch and fix the regexes locally instead.

- **`latin:money` (and `latin:<tail>` generally)** — `BAD_LATIN = r'[A-Za-z]{3,}'`
  splits on the hyphen, so the *allowlisted* brand `T-money` is matched as `money`,
  which is not in `ALLOW_LATIN`. Every hyphenated allowlisted brand fails this way.
  Fix: `r'[A-Za-z][A-Za-z0-9-]{2,}'`.
- **`hangul` on required Korean terms** — the scanner rejects ALL Hangul, but several
  zh sources require the original term kept in parentheses (e.g. `돌탑`, `돌하르방`,
  `해녀`, `갈치조림` in `essay/public/2026/06-09.md`). Mask exactly those four terms
  before scanning; the remaining hits are the real failures.

To confirm a hit is a false positive and not a file defect, re-scan a masked copy and
check that what remains points only at allowlisted text.

## Rule 3c — "no Han in prose" is unsatisfiable; allowlist instead

Japanese kanji are Unicode Han (U+4E00–U+9FFF), so a task brief saying "no Han
characters in prose" cannot hold literally: the mandated place names 済州島 釜山 仁川
弘大 景福宮 漢拏山 東海龍宮寺 鰆 and ordinary words like 大晦日 are all Han, and accepted
siblings such as `essay/public/2026/06-08.md` contain >1300 Han chars. Treat the
requirement as "no Chinese-only characters" and check with the denylist in Rule 3, not
with a raw codepoint range.

When writing a supplementary per-file check, allowlist = Jōyō list
(`https://kanjiapi.dev/v1/kanji/joyo`, 2140 chars) ∪ the file's mandated glossary.
Do **not** add the `docs/ja` corpus fallback for the *pass/fail* decision (see Rule 3);
it is only useful for spot-checking a suspect char. Confirm any surprise offender with
`unicodedata.name()` before editing — most are just glossary kanji missing from the
allowlist.

## Rule 4 — build tables mechanically, never by hand

`ja_tables.py <source> <headers-json> <target>` copies every source data row
**verbatim** and substitutes only the header row, so row/column counts and the
`| ---: |` alignment rows are identical by construction. Feed it one header
list per source table or it asserts. Data rows are asserted byte-identical.

It **appends**, so plan the write order: emit all text up to the last table's
paragraph, run the helper once for all 3 tables, then split the output and
splice table 3 at its marker.

## Rule 5 — match the source's blank-line pattern exactly

This is the check that most often fails last, after every content check
passes. In the source, consecutive prose lines with **no** blank between them
are one rendered paragraph (Kimi has 4 in a row; MiniMax has 2). Adding a
blank where the source has none does not change the visible text but shifts
every subsequent line and can drop a table from a table block. Compare a
skeleton of the two files (BLANK / P / H<n> / TBL<cols> / ---) line by line;
it must be identical.

## Verification suite

`verify_07_08.py` checks: (a) line 1 is `---`; (b) `yaml.safe_load` succeeds,
keys are exactly `['title','order']` in order and `order` matches the source;
(c) ATX heading-level sequence matches (7 level-2, no others); (d) all 3 tables
have the same row count, same per-row column count, and every data plus
alignment row byte-identical; (e) the ordered list of link targets is
byte-identical (7 URLs).

## Deliverable

Never paste the finished file back — report the path, per-check verification
output, table row/col counts, and any deviations.
