---
name: md-locale-skeleton-parity
description: Use when making locale copies of a docs markdown page.
---

# Locale markdown skeleton parity

Creating `docs/<locale>/<path>.md` copies of a source page where a site build
breaks on any structural drift.

## Workflow

1. **Read the source first.** Never generate from a description.
2. **Translate prose; leave structure byte-exact.** Frontmatter keys stay in the
   same order with the same `order:` value. Only `title:` is translated.
3. **Verify with a script, not by eye.** Compare each target against the source:
   starts with `---`; `yaml.safe_load` of the frontmatter succeeds; ATX heading
   level sequence identical; per-table row count and per-row column count equal;
   every image URL byte-identical in order; every link target byte-identical;
   paragraph-line count equal; and a full line-kind skeleton
   (`BLANK`/`H2`/`H3`/`P`/`IMG`/`TBL<n>`) equal.
4. **Also assert the target is NOT a copy of the source.** A byte-equal
   "translation" passes every structural check and is the worst possible output.

## Build tables mechanically, never by hand

Copy every data row and every `| ---: |` alignment row verbatim from the
source, substituting only the header row. Hand-typed delimiter rows drift in
dash count and break the byte-identical check.

## Traps

- **Never write the source into the target while normalising whitespace.** A
  "fix trailing newlines" script that does `open(dst,'w').write(source)` destroys
  the whole translation. Compute the tail from the *source*, apply it to the
  *target's* body: `target.rstrip('\n') + tail_from_source`. If a file was
  untracked in git, it is unrecoverable — check `git status` before bulk edits.
- **Long single-shot generation corrupts.** This model degenerates on long CJK
  paragraphs, emitting stray Latin words, Hangul in Japanese text, or repeated
  filler. Generate one short paragraph per tool call and machine-check it before
  moving on. Delete and regenerate on any hit; never continue past a failure.
- **Subagent self-reports are not verification.** Re-measure every claim
  yourself, including files the subagent says it wrote.
- **Delegation transcripts truncate `read_file` output** (~400 chars), so they
  cannot restore a lost file. Prefer build scripts that can be re-run.
- **Count the parenthesised forms, not raw substrings.** Korean/Japanese prose
  uses 돌탑/해녀 natively, so a substring count is meaningless. Match
  `[（(]term[）)]`.
- **"No Han characters" is the wrong check for Japanese.** Japanese is written
  in Han (済州島, 釜山, 大晦日). Detect leaks with 2+ consecutive Han characters
  that form a Chinese word and appear verbatim in the source, minus an allowlist
  of legitimate place names — not per-character.
- **Korean terms in the source may appear more often than expected.** Count them
  in the source and match that, rather than assuming.
- **Source paragraphs can span multiple adjacent lines** with no blank line
  between. Mirror the source's blank-line structure exactly or the paragraph
  count drifts.
