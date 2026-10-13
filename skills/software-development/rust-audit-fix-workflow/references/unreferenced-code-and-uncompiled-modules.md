# Finding code that exists but never runs

Two failure modes hide behind a green build. Neither shows up as a compiler
error, so neither is found by "compile it and see":

1. **unreferenced code** — a private item whose only occurrence in the whole
   workspace is its own definition
2. **uncompiled code** — a module, or a directory of tests, that is fully
   written but never wired into its parent's `mod` list

Both look like "the build passes" while a feature is entirely inert.

## Unreferenced code: use the compiler, not a scan

`cargo check` / `cargo clippy` are the ground truth for dead code. Run both
targets and grep for the diagnostic families:

```bash
cargo check --all-features --offline --workspace --exclude <cli-crate> \
  --target wasm32-unknown-unknown --message-format=short 2>&1 \
  | grep -E "never used|never constructed|never read|dead_code" | sort -u

cargo clippy --all-features --offline --all-targets --message-format=short 2>&1 \
  | grep -iE "never used|never constructed|never read|dead_code|unused" | sort -u
```

Zero output from both is a real, defensible answer. Report that instead of
manufacturing deletions.

### Do not hand-roll an identifier-frequency scan to find dead code

A regex scan that counts identifier occurrences across the workspace produces
two kinds of garbage, and both look authoritative:

- **False positives at scale.** Every `#[test]` function and every `pub` item in
  a library crate is legitimately "unreferenced" from inside the crate. A scan
  reported 745 dead functions in a repo that had zero.
- **False negatives that delete live code.** A scan that reported a
  `pub const` in one module as unreferenced missed its real use in a *sibling*
  module further down the file, because the scan's file list or name-resolution
  did not match how Rust actually resolves it. Deleting it broke the build with
  `E0425`.

If you must scan (e.g. to size a slice before the compiler run), the only safe
form is: tokenize once into a `Counter`, treat any identifier with count `<= 1`
as a *candidate*, and then **prove every candidate with `cargo check` before
touching it**. A candidate that is not confirmed by a compiler error is not
dead. When a candidate turns out to be live, restore it byte-for-byte from
`git show HEAD:<path>` and re-verify with `git diff --stat -- <path>` returning
empty — comparing the diff, not re-reading the file, is what proves the restore.

### A scan that needs a workspace-wide regex per candidate will time out

`len(re.findall(pattern, all_text))` inside a loop over every definition is
O(definitions × corpus). Tokenizing the corpus once into a frequency map and
looking each name up is the difference between minutes and under a second. If a
scan times out, that is a signal to invert the loop, not to widen the timeout.

### Exclude by path *component*, not substring

Skipping build output with `if "target" in str(path)` also skips any path that
merely contains those characters (`/Users/target/…`). Split on path components
and test membership against the skip set.

## Uncompiled modules and test directories

A module directory that exists but is absent from its parent's `mod` list is
inert: rustc never reads it, so it can hold any amount of code and no error is
raised. A test directory in the same state looks like a test suite but runs
zero of its tests.

Diff the directories on disk against the `mod` declarations in the parent:

```python
import pathlib, re
R = pathlib.Path("<crate>/tests")
registered = set()
for line in (R / "mod.rs").read_text().splitlines():
    m = re.match(r"\s*mod\s+(r#)?([A-Za-z_][A-Za-z0-9_]*)\s*;", line)
    if m:
        registered.add(m.group(2))          # group(2) strips the r# escape
orphans = {d.name for d in R.iterdir() if d.is_dir()} - registered
```

**Strip the `r#` escape before comparing.** A keyword-named module is declared
`mod r#input;` / `mod r#fn;`; a plain string comparison reports it as an orphan
and you will "fix" a live directory by deleting it. Capture the optional
`(r#)?` group and key on the bare name.

Do the same for `src/lib.rs`: every `<crate>/src/<dir>/mod.rs` on disk should
have a matching `mod <name>;` in `lib.rs`, **and** a `pub use` entry if the
module's items are meant to be reachable. A fully-implemented module that was
never declared in `lib.rs` is invisible; its types are unnameable from tests,
which surfaces as a wall of `cannot find type` errors that look like "the tests
are wrong" when they are actually a one-line registration gap.

## Distinguish an empty stub from a missing implementation

An empty test file is a different artifact from a test that references an
unbuilt API. Check the size and the test count before assuming which you have:

```python
fn = (R / name / "fn.rs").read_text()
print(len(fn), fn.count("#[test]"), fn.count("wasm_bindgen_test"))
```

- **0 bytes / 1 byte / no `#[test]`** and no corresponding subsystem in
  `src/` → an empty shell, safe to delete outright.
- **many `#[test]`** referencing symbols the crate does not define → a written
  specification for an unimplemented feature. **Do not delete.** The tests are
  the spec; implement what they assert.

This distinction is the whole decision. Deleting the second kind destroys the
only written record of intended behaviour, and a test file that "isn't wired up
anyway" still encodes what the feature was supposed to do.

## When you do implement the missing API, the tests are the spec — read the assertions

The errors name the missing symbols but not their contracts. Read the test
bodies for the invariants:

- `assert_eq!(pool.len(), high_water, "1000 cycles never grow the pool")` — the
  counter must not double-count
- `assert_eq!(recycled.get_tags().len(), 0, "a recycled entity carries no tags")`
  — released state must be scrubbed, not handed back as-is
- `assert_ne!(second.get_id(), first_id, "a recycled entity must not reuse the
  previous identifier")` — recycle resets identity

Expect to introduce a real bug and have the suite catch it. That is the tests
working. Do not then delete or `#[ignore]` the failing test.

## Two bugs this shape invites, both caught instantly by the suite

**Double-counting a counter the callee already bumps.** If `pool.acquire()`
increments `active` internally, a caller that also does
`set_active(get_active() + 1)` inflates it on every checkout — visible as a
counter that grows linearly with a loop that should be flat. Read the callee's
body before adding an increment at the call site; count the increment exactly
once, in one place.

**`mem::swap` moves the value into the *other* variable.** After
`swap(a, &mut b)`, `b` holds `a`'s old value. Writing `swap(entity, &mut clean)`
to "extract the dirty entity" puts the *dirty* one in `clean` and returns it to
the pool. Prefer `std::mem::replace(slot, fresh)` — it names the direction in
the signature and cannot be read backwards.

## Report an honest final count

After activating previously-uncompiled tests, the suite count goes **up**. Sum
the `test result:` lines across the per-package runs and report the new total
plus how many tests were newly activated; do not report only the delta, and do
not present the new number as if it were a regression fix.
