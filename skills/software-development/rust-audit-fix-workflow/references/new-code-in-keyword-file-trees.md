# Adding new code to a keyword-file tree

Governs work that *adds* a file or a helper to a tree that already follows the
§1.3 keyword-file layout — as opposed to auditing existing files, which the
other references cover. The trap is that every rule below binds the code you
add, not the code you moved, so a change that is correct in isolation still
fails the audit.

## An auto-fixer that repairs one rule can leave a sibling rule red

`fix_dep_order.py` sorts a dependency block, and in doing so leaves the last
entry flush against the following `[section]` header. The dep-order check goes
green and the *section-blank* check goes red in the same file. That reads as
"the fixer broke something" and is really "the fixer fixed one rule and exposed
the next" — the fix is inserting the missing blank line.

Rule: after any auto-fixer, re-run the full audit and read every new `FAIL:`
line **by name**. A run that lowers the summary while raising a different check
has not regressed anything.

## A test-only helper is not dead code, and a pin mechanism is not an API

Two shapes the compiler's `never used` / `never constructed` warning reports as
dead when they are not:

- **A setter exercised only from `#[cfg(test)]`.** `pub(crate) fn set(..)` called
  from a test module but never from production compiles clean in a release
  build, because `cfg(test)` is compiled out — the release build sees a function
  with no callers. Rule 14 forbids `#[allow(dead_code)]`, so the fix is to give
  it a *production* caller, not to suppress it. The natural caller is the code
  path that should have been using it: an installer that resolves a value,
  installs it, then reads it back through the getter.
- **A thread-local override used only by tests.** Held in `thread_local!`, it is
  invisible to the dead-code pass in a non-test build for the same reason.

**Do not design a test seam only tests can reach.** A `set`-then-`get` override
re-implements a one-time initializer the type already has. When a `OnceLock` is
what you want, `OnceLock::set` *is* the seam: it returns `bool` saying whether
this call won the initialisation, which is both the production path and exactly
what a test needs to assert. One API, two callers, no warning.

Corollary: check whether a project already has in-src unit-test modules before
inventing one.

```bash
grep -rn 'cfg(test)' --include=*.rs <crate>/src   # empty => tests belong in tests/
```

An empty result means a new `#[cfg(test)] mod` is a structural choice that needs
extra import and export wiring to compile — budget for it.

## The three keyword-file rules bind the new file

| Rule | What it forbids in the new file |
|---|---|
| purity | free `fn` in `impl.rs` (they belong in `fn.rs`); `type` alias in `impl.rs`/`fn.rs` (they belong in `type.rs`) |
| imports centralized §6.3/§6.4 | any `use` other than `use super::*;` — a `use std::time::…` hoisted into the file is a finding |
| first line | the file must open with `use super::*;` |

A `///` doc comment above a `thread_local! { … }` block is also a finding —
`unused doc comment`, because a macro invocation is not an item for a doc comment
to attach to. Use a `//` comment and say why.

**Write the file in its final shape from the start.** Moving a function from
`impl.rs` to `fn.rs` to satisfy purity also requires:

- changing its visibility to `pub(crate)` so the parent `mod.rs` glob re-export
  carries it — a private `fn` in a sibling file is `cannot find function`;
- hoisting any new import one level up, into the crate root;
- a `mod r#type;` line **and** a `pub(crate) use` entry, both in alphabetical
  position, when the new `type.rs` is in a directory that had none.

## A doc comment asserting a fact you never checked is a defect

A test that asserts a fact about the language or a crate is only as good as that
fact. Two failures seen in the same session, both caught only by running the
suite many times:

- A charset picked as "URL-safe Base64" contains `-`, which is **not** a legal
  character in a bare identifier. It works as a bracketed property key, so the
  code is correct in the narrow sense while the name is a trap for the next
  reader. The alphabet has to be derived from the constraint, not from habit:
  64 *distinct* characters, all identifier-legal.
- The identifier-legality assertion that caught this was itself wrong — it
  rejected `$`, which **is** legal. Two of the three failures in a 40-run sweep
  were the test being wrong, not the code.

**When a generated name crosses into another language's grammar, assert the
grammar, not your intent of it.** And run a stability sweep before believing a
suite is deterministic:

```python
for _ in range(50):
    run()          # assert exactly one distinct outcome
```

A single passing run cannot distinguish a real flake from a wrong assertion;
only the repetition rate can, and a mixed outcome set is the signal to read the
failing assertion's *premise* before its code.

## Verifying an encoder/transform by extraction, not by inspection

When output shape is the deliverable (a generated name, a formatted string, an
encoded payload), read the transform's source and then **run it** in a scratch
crate that calls the real function:

```bash
mkdir -p /tmp/harness/src            # own [workspace], so it does not join the build
# copy the real fn verbatim, add a main() that prints several samples
cargo run --offline -q
```

Reading the source is not enough, and here it was wrong twice: the crate
zero-pads every input byte into a 3-byte group before base-encoding, so six
input bytes produce a 24-character output, not twelve; and the `encode` entry
point takes `&str`, so a `to_le_bytes()` array does not compile. Both were
invisible in review and obvious in one run.

Extract the *function under test* into the harness. Extracting the whole `impl`
block drags in the struct, the getters and any `cfg(test)` sibling, and you end
up debugging the harness instead of the transform.
