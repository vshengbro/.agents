# Mass-edit fallout: rustc-coordinate repair loop (tests/ especially)

When a mechanical batch edit (const de-pub inline, visibility narrowing, rename)
breaks dozens of files, do NOT keep regexing — switch to compiler-driven repair.

## The loop

1. `cargo check --workspace --all-targets --message-format=short 2>&1` (per-crate
   `-p` runs surface errors the workspace run can mask behind compile order).
2. Group errors by class and fix ONLY the coordinates rustc names:
   - **E0425** `cannot find value `X`` → the original was a string literal;
     quote exactly that occurrence (`X` → `"X"`).
   - **E0423** `expected value, found struct/macro `X`` → same: re-quote the
     bare identifier at that column.
   - **E0308/E0277** `expected &str/String, found {integer}` → quote the bare
     number; inverse (`expected bool/f64/usize, found &str`) → unquote the
     `"..."` literal at the site. Direction comes from the EXPECTED type.
3. Re-run; the next class surfaces. Converges with zero guessing.

## Hard rules (each cost real damage when violated)

- **Never run span-blind sed/regex over `tests/` after the tree is damaged.**
  Quoting an identifier inside a string literal corrupts the string;
  unquoting a string in pattern position corrupts the match. Span computation
  on ALREADY-broken text is unreliable (one missing quote re-pairs the rest of
  the file) — compiler coordinates beat reparsing.
- **Quoted bindings are the recurring damage shape**: `let "entries" = …`,
  `match "value" {`, `Some("value") =>`, and worst `"lit" =>` — a match-arm
  literal turned into a catch-all binding that COMPILES and silently matches
  everything. Find leftovers via `unused variable` warnings (a binding whose
  use sites all got quoted).
- **Run the full test suite after repair** — silent semantic flips compile
  fine; only tests expose them. Count failures with `grep -c FAILED` on saved
  output; awk field-splits on `test result:` lines misalign (`ignored` vs
  `failed` fields swap).
- `format!` message strings capturing `{CONST_NAME}` dangle after a const is
  de-pubbed: replace with plain text — `{"Some Text"}` is not placeholder
  syntax, and substituting a quoted literal into braces yields `""Text""`
  artifacts.
- Never substitute a value into pattern or const position. Match arms on
  consts must be restructured to if/else, or the test deleted (see below).

## Const de-pub campaign decision table (user-ruled, absolute)

`pub const`/`pub static` are never allowed in `src/` — no "tests read it" or
"another crate reads it" exception (`pub const fn` is a function, unaffected).
And: **unit tests must not verify constants** — value/spelling asserts and
const-table shape tests (uniqueness, "exactly N entries") are DELETED, not
preserved by inlining literals.

| Reader set | Action |
|---|---|
| zero readers | delete the decl |
| only same-crate `tests/` | behavior tests using it as input: inline the value at expression sites; tests asserting the const itself: delete |
| crate's own `src/main.rs` | inline |
| cross-crate src reader | std equivalent (`std::f64::consts::{PI, TAU, FRAC_PI_2}`), consumer-local `const.rs` copy for tiny values, or a `pub fn` getter for big shared assets (a fn is API; a const is not) |
| big multi-line value | verbatim-inline the decl RHS into the few reader sites |

Traps:

- Sibling crates routinely define their OWN same-named consts (`CHAR_*`,
  `STR_HYPHEN`, `EPSILON`). Token-name matching reports phantom cross-crate
  readers — confirm with an import path or Cargo.toml edge first.
- `f64::EPSILON` (2.2e-16) vs domain `EPSILON` (often 1e-6): read the decl
  value before swapping a use site to std.
- A parent `pub(crate) use {a::*, b::*}` aggregation makes same-named consts
  in sibling modules ambiguous (E0659) the moment a second module adds one —
  rename use sites to the std name instead of adding per-module alias consts
  under an aggregating glob.
- A deleted item's doc comment survives the sweep and resurfaces as
  `empty_line_after_doc_comments` above the next item — and clippy's
  suggestion ("remove the empty line") treats the symptom. Grep the tree for
  the symbol the comment describes; if it is gone, delete the orphan doc
  block, don't reflow the spacing.

## Deleting a const-verification test suite

Delete the whole `tests/<suite>/` dir + its `mod <suite>;` line in
`tests/mod.rs` when every test asserts const content. For a mixed file,
delete just the const-verification fns (from the `#[test]` attribute through
the closing `}` at column 0, plus the trailing blank line).

## Status note

The absolute rules above are pending formalization in the `rust-standards`
spec skill (§18 const clause upgrade + a `no-const-verification-in-tests`
verifier check); this file is the workflow-side authority until that lands.
