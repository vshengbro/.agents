---
name: proc-macro-reexport-trap
description: Use when a macro expands a bare crate path.
version: 1.0.0
author: curator
license: MIT
metadata:
  hermes:
    tags:
      - rust
      - proc-macro
      - cargo
      - dependencies
    related_skills:
      - rust-crate-use
      - rust-standards
---

# proc-macro re-export trap

## When to Use

- A macro-using line fails with `E0433: could not find <crate> in the list of imported crates` while the rest of the file compiles.
- Deciding a dependency set for a crate that uses procedural macros, especially when a facade/shim crate re-exports them.
- Anyone proposes dropping a dependency on the grounds that "the shim already re-exports it".

## The rule

**A `pub use` re-export never satisfies an absolute `::crate::` path in a macro expansion — only a real dependency does.**

Rust resolves `::foo::Bar` (leading `::`) against the **extern prelude**: the set of crate names from the current package's actual `[dependencies]`. A facade/shim crate doing `pub use {inner_crate::*}` re-exports *items* (`Bar`), so `use shim::*;` brings `Bar` into scope — but it does **not** add the name `inner_crate` to the downstream crate's extern prelude. The macro body is expanded *in the downstream crate*, so the path must resolve *there*.

Symptom, one error per attribute that uses the macro:

```
error[E0433]: cannot find `inner_crate` in the crate root
  --> src/main.rs:11:1
   |
11 | #[route("/")]
   | ^^^^^^^^^^^^^ could not find `inner_crate` in the list of imported crates
```

## Procedure

Before guessing a dependency set, read what the macro actually emits:

```sh
grep -rhoE '::[a-z_0-9]+::' <registry-src>/<macro-crate>-<ver>/src | sort | uniq -c
```

- Output is all `::inner_crate::` → downstream must depend on `inner_crate` explicitly, even if a shim re-exports the macro names.
- Output is all `::shim::` → the shim alone suffices.

Then confirm in a throwaway crate before touching the real project:

```sh
mkdir -p /tmp/probe/src && cd /tmp/probe
# minimal Cargo.toml + src/main.rs with exactly the candidate dep set
cargo build 2>&1 | head -30
```

## Pitfalls

- **Non-macro code compiling is not evidence the dep set is right.** Items pulled in by `use shim::*;` resolve fine without the inner crate, so ordinary types type-check and only the *macro-using* lines fail. A partially-compiling file is not a partial success.
- **Do not paper over it with `#[allow]`** or by hand-writing the expansion — that hides the breakage and drops macro updates.
- **Check every published version before declaring the dependency unavoidable.** Older macro crates sometimes target the shim path and newer ones target the inner path (or vice versa); the answer is per-version, not per-library. State the version you tested.
- **Version-align the pair.** When both the shim and the inner crate are needed, pin them to the same exact version.

## Fixing it at the source (when you own the macro crate)

If the emitted `::inner_crate::` paths are your own macro's, the real fix is to make the expansion point at the **facade** name users already depend on — never at an internal implementation crate. That pushes an internal dependency onto every downstream user.

The obstacle is a cycle: `macros` needs `facade`, and `facade` re-exports `macros`. **Break it with a dev-dependency** (verified — both branches behave differently):

```toml
[dependencies]
# facade = { path = ".." }        # <-- HARD FAIL: error: cyclic package dependency
syn = { ... }   # proc-macro crate needs nothing from the facade at runtime

[dev-dependencies]
facade = { path = ".." }          # <-- LEGAL: cargo check --workspace passes
```

A proc-macro crate only needs the facade **at expansion time**, and dev-deps are compiled for the package's own tests/doctests — which is exactly where expansions get compiled. The runtime dependency is genuinely unnecessary, so the cycle is an artifact of Cargo's graph, not a real requirement.

Two benefits, both verifiable:
- No cycle for crates.io consumers (the cycle only ever existed in the local workspace).
- A path-only dev-dep is **stripped from the packaged manifest** by `cargo package`, so the published crate carries no facade dependency and imposes no publish-order constraint. Check with `cargo package -p <macros> --no-verify` and read the normalized manifest.

**Blast radius of a path flip** — the `::` sites are not the whole surface:

```sh
grep -rc '<inner_crate>' <macros>/src        # the emitted paths
grep -rn 'use <inner_crate>::\*' <macros>/src/lib.rs   # doctest imports
```

Doctests are compiled by `cargo test` and resolve through the same paths. Flipping `::` sites while leaving doctest `use` lines stale fails in the doctest build, not the lib build. **A clean `cargo check` is not sufficient verification here — `cargo test` is.**

## Verifying a path flip actually did something

A passing build proves nothing on its own (it also passed before the change). Use a negative control: revert *only* the edited source, keep the new manifest, and confirm the consumer reproduces the original error.

```sh
git stash push -- <macros>/src      # keep Cargo.toml
(cd /tmp/probe && cargo build 2>&1 | grep -E 'E0433|error')
git stash pop                       # verify the restore actually landed
```

If the reverted build still succeeds, the change was a no-op and the "fix" was already true.

## Before you debug the script, check the fixture is real

A verification script that diffs against a baseline needs that baseline to **actually exist**. A global `core.hooksPath` hook applies to *every* repo including throwaway probe fixtures, so the setup commit gets blocked and the fixture ends up with no HEAD. The script then fails to read the baseline, silently treats it as "absent", and reports violations that are really just the file's pre-existing content. You end up debugging a script that never had a bug.

```sh
git commit -qm "baseline" --no-verify   # setup commits bypass the hook
git log --oneline | wc -l              # must increase — assert, don't assume
```

Symptom combination that identifies it: fresh repo + a `git commit -qm` that prints nothing and creates nothing + the tool later claiming the file is not in HEAD. Assert the log grew after every setup commit; otherwise fix the fixture before trusting any verdict from the script.

## Distinguishing "the tool is broken" from "my baseline is missing"

When a comparison tool reports a uniform, implausible delta (every check firing the same +1 on a file you only touched cosmetically), suspect the harness before the tool. Re-derive the baseline fetch by hand — `git show HEAD:<path>` — and confirm it returns content rather than an error. Only after that returns real bytes is a reported delta meaningful. Rewriting the verifier in response to a bad fixture buries a working tool under a fix for a problem that does not exist.

## When the tool is right and you are wrong

The same discipline applies to claims about the source tree itself. If a check reports a refactor, module, or path you believe exists does not, verify before defending it:

```sh
git log --all --diff-filter=A -- '<claimed/path>'   # ever created, on any branch?
test -d <path> && echo EXISTS || echo MISSING      # present now?
find <parent> -type f | sort                       # what the layout really is
```

Empty output from the first command means the thing was never created, so any memory or note describing it as done is wrong — correct both the document and the note, or the next session repeats the mistake. When the directory exists but the files are named differently than remembered, the source is authoritative and the note needs updating to match.

## When the user disputes it

Prove it in a throwaway crate rather than re-asserting. Show the grep output, show the E0433, and if a different published version emits the other path form, say which versions you checked. If no version works, offer the real alternative (drop the macro, or the extra dependency) and let the user choose — do not silently change their dependency set.
