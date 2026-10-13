# Building a string/comment masker for a Rust verifier

Rules for the scanner that blanks literals and comments before matching, when
writing or repairing a `verify_*.py` / `fix_*.py`. Each construction below
silently deleted real hits in production; all three live in
`rust-standards/scripts/verify_no_qualified_std_path.py` and
`fix_no_qualified_std_path.py`, with fixture coverage in
`self_test_no_qualified_std_path.py`.

## Char literal: exactly one character or escape

```
'(?:\\.|[^'\\])'
```

With a `*` quantifier the pattern treats a **lifetime apostrophe** (`'a`, `'_`)
as an unterminated char start and pairs it with the next quote far away,
masking everything between as a literal. Measured: 27 of 203 real hits gone on
one sweep. Established scripts (depub_consts, verify_no_impl_trait_params,
verify_no_pub_in_tests, verify_no_redundant_accessor_attr) all use the
exactly-one form — copy it, never hand-roll.

## Raw string: backreference the closing hashes

```
b?r(#*)".*?"\1
```

The naive `r?#*"..."#*` closes `r#"{"a":1}"#` at the first inner quote and
mis-pairs every quote after it, swallowing real code across lines. Order the
alternation raw-string first, then normal string, then char.

## Mask newline-preserving

```python
STRING_LITERAL.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
```

`" " * len(span)` flattens `\n` inside multi-line literals: length survives but
per-line filters (`zip(text.splitlines(), blanked.splitlines())`) misalign
after the first multi-line literal. For a verifier that only mis-reports line
numbers; for a fixer that rewrites by offset it shifts every later edit —
silent corruption that still parses (a tail landing mid-token glued `Error`
onto `tent`).

## Mask strings BEFORE splitting on `//`

If the line is first truncated at `//`, a `//` inside a string
(`"https://..."`) cuts the line early and hides real code after it. Blank
literals first, then split the comment on the blanked line — the `"` opener is
gone so only a real comment matches.

## Macro-token bodies are an exemption class, like string literals

A rule about paths a crate *consumes* (e.g. "no `std::`-rooted path in a
sub-file") must skip `macro_rules!` / `quote!` / `quote_spanned!` bodies: those
tokens are *emitted* into the downstream crate at expansion, so a root import
in the defining crate never reaches them — rewriting them breaks the macro
API. Same reason string literals are exempt. Scan after string-blanking with a
balanced-delimiter walk; note `macro_rules!` carries a name between `!` and
the delimiter (`macro_rules!\s*\w+\s*[({\[]`).

## Whole-file, not per-line

Apply the masker to the whole file, not per line: per-line masking flags the
interior lines of a multi-line string (a violation the rule exempts) and
mis-pairs quotes at line ends. Keep offsets 1:1 with the original so a fixer
can rewrite by span.
