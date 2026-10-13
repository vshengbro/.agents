---
name: rust-standards-verifier-repair-loop
description: Use when fixing doc/string verifier failures at scale.
---

# Driving the rust-standards verifiers to zero

Repairing §2.1/§2.2 doc-comment and §1.3c hardcoded-string violations at scale,
usually across many files and often across parallel agents.

## Get the authoritative violation list

Both scripts print **absolute** paths, so a `grep '^src/'` filter silently
returns nothing and looks like a pass. Filter on the absolute path:

```bash
cd <repo>
{ python3 ~/.agents/skills/rust-standards/scripts/verify_doc_comment_format.py . 2>/dev/null
  python3 ~/.agents/skills/rust-standards/scripts/verify_hardcoded_strings.py . 2>/dev/null
} | grep "/abs/path/to/repo/" | cut -d: -f1 | sort -u > /tmp/whitelist.txt
```

Pass `.` from the repo root, never the absolute path — one subagent reported the
absolute-path form producing a false "0 violations".

## What the checkers actually compare (read the source first)

`verify_doc_comment_format.py` compares backticked type literals against the
**raw signature**, character for character:

- `# Arguments` item: `^/// - ` + `Type` + ` - ` + desc. **Colon separator is
  rejected for Arguments** (allowed only for Returns).
- The doc type must equal the signature's bare type **including the leading
  `&`** and excluding the where-clause: `fn f<K>(k: K) where K: AsRef<str>` →
  `` `K` ``, never `` `K: AsRef<str>` ``.
- `self` / `&self` / `&mut self` receivers are **dropped** from the param list.
  Documenting them is a violation; an `# Arguments` section on a zero-param
  fn must be deleted.
- Return `Self` / `()` / absent ⇒ no `# Returns`. `-> Self::Output` is a
  non-empty return type and does need one.
- Arg matching is **set-based, duplicates collapse** — one `- `u32` - ...` line
  satisfies `fn f(a: u32, b: u32, c: u32)`. The checker therefore cannot enforce
  one-line-per-parameter; verify that yourself.
- A doc block must have ≥1 prose line before the first `/// #` header.

`verify_hardcoded_strings.py` flags any `"..."` of 4+ chars outside
`const.rs`/`tests/`, **except**: format-macro format strings, attribute lines,
`cfg!(...)` predicates, `extern "C"` ABI slots, whole-line comments,
`class! {}` / `vars! {}` blocks.

## Parallel-agent hazards (both bit me)

1. **Duplicated consts.** Two agents writing the same directory's `const.rs`
   produced a verbatim duplicated block ⇒ `error[E0428]: name defined multiple
   times`. `grep | uniq -d` over a single file misses it if the block landed in
   two files. **Always run a workspace-wide duplicate-const scan AND a real
   compile before declaring done** — this is the one failure a per-file
   verifier run cannot see.
2. **Mid-task `git reset` by an external process** silently reverts everyone's
   edits. Subagent self-reports are then stale. Re-run the verifiers yourself at
   the end; never relay a child's "0 violations" without re-measuring.

## Isolation rules to give subagents

Editable set = the violating file **plus its directory's `const.rs`** (needed for
§1.3c), nothing else. Check whether `mod.rs` already has
`pub(crate) use r#const::*;` before editing it. Forbid: `#[allow]`,
`cargo test`, `cargo fmt --all` (the workspace is usually unformatted in
*other* crates, and a workspace-wide format stomps other agents), and any
`git commit/add/stash/checkout`.

## Verify edits are non-destructive

```bash
git diff -U0 -- <dir> | grep -E '^[+-].*\bfn [a-z_]+' | sed 's/^[+-]//' | sort | uniq -c | awk '$1!=2'
```
Empty output ⇒ no `fn` signature line was added, removed, or altered. Then list
added lines excluding `///` and `const NAME` — what remains should be only
literal→const swaps. Finally diff each new const's value against the literal it
replaced to prove it is byte-identical.

## Gates

```bash
python3 ~/.agents/skills/rust-standards/scripts/verify_doc_comment_format.py . | grep -c '/abs/repo/'
python3 ~/.agents/skills/rust-standards/scripts/verify_hardcoded_strings.py . | grep -c '/abs/repo/'
rustfmt --edition 2024 --check <changed files>          # per-file, never --all
cargo clippy -p <crate> --all-features --offline --all-targets | grep -cE '^(warning|error)'
cargo clippy -p <crate> --all-features --offline --target wasm32-unknown-unknown | grep -cE '^(warning|error)'
cargo test -p <crate> --all-features --offline | grep '^test result'
```

Take a clippy baseline **before** editing so pre-existing warnings are not
misattributed. `cargo` may not be on PATH — it can live at `~/.cargo/bin/cargo`
while `which cargo` returns nothing, so `export PATH="$HOME/.cargo/bin:$PATH"`.

A stale session cwd pointing at a deleted directory makes every `cd`-prefixed
command fail confusingly; pass `workdir` instead.

## The verifier is structural, so two blind spots must be audited separately

The checker is a *structural* checker. Two classes of wrong doc pass it
silently, so audit them yourself after the gates go green:

1. **Set-based arg matching hides under-documented parameters.** Because arg
   matching collapses duplicates, `fn f(a: u32, b: u32, c: u32)` passes with a
   *single* `` - `u32` - ... `` line that describes none of them individually.
   The fix that satisfies the checker is often *worse* than what it replaced:
   three meaningful lines become one vague one. Write one line per parameter
   anyway — the checker accepts it (each type just needs to appear at least
   once), and it is strictly more informative. To audit, compare
   `Counter(signature param types)` against `Counter(doc types)` per fn and
   flag any type where the signature count exceeds the doc count.
2. **`impl`-level `# Arguments` / `# Returns` are NEVER read.** The checker only
   scans the `///` block immediately above each `fn`, so a section attached to
   an `impl` block is dead text that can contradict reality forever. This is
   where stale `&self` arguments and outdated return types survive a clean
   §2.2 run. Audit with a regex for `impl` lines, walk up the contiguous `///`
   run. Audit with a regex for `impl` lines, walk up the contiguous `///`
   run, and report any block carrying a `#` section. Fix by deleting the
   section from the `impl` doc and keeping the per-fn doc, which is where the
   section belongs.

## §1.3d: a crate-root `const.rs` is a trap, and moving it needs a `mod.rs`

Hoisting literals for a **crate root** (`docs/src/lib.rs`, `example/src/lib.rs`)
or a **build script** (`docs/build.rs`, `example/build.rs`) puts `const.rs`
next to sub-directories, which §1.3d forbids: a directory with children may
hold only `lib.rs` / `main.rs` / `build.rs` / `mod.rs`. rust-standards
SKILL.md:368 names `docs/const.rs` as the worked example of this trap, and
the pre-commit staged-file gate catches it (check `verify_no_sibling_dirs`).

The fix has three parts, and missing any one breaks the build:

1. Move to a **semantic** sub-dir, keeping the keyword file name:
   `docs/src/const.rs -> docs/src/app/const.rs`, not `const/const.rs`
   (the latter trips clippy `module_inception`).
2. The new sub-dir needs **its own `mod.rs`**. `mod codegen;` in the parent
   resolves to `codegen.rs` or `codegen/mod.rs` — it does *not* find
   `codegen/const.rs`. Symptom: `error[E0583]: file not found for module`.
3. Re-export through the **sub-dir's own name**, never through the keyword
   file: `pub(crate) use {component::*, app::*, ...}` in the crate root, NOT
   `app::r#const::*`. The inner `mod r#const;` is private to its own module,
   so naming that path segment from outside is a *visibility* error
   (`E0425 cannot find value ... in this scope` on every use site, ~47 of
   them) even though the constant is perfectly in scope. It looks like a
   missing export; it is not.

`use super::*;` in the new `mod.rs` is usually *not* needed and clippy flags
it as an unused import — the crate root's `pub(crate) use` already carries the
constants down the existing `use super::*;` chain in every other module.

## The `html!` child grammar, verified from the macro source

Read `macros/src/html/{fn,impl}.rs` rather than guessing. `parse_html_children`
dispatches a child on its leading token, and the *second* token decides the
shape:

- `LitStr` + `Brace` ⇒ element (`HtmlNode::Element`).
- `LitStr` alone ⇒ **text** (`HtmlNode::Text`), emitted as
  `VirtualNode::Text(TextNode::new(Cow::Borrowed(..)))` — no allocation.
- `Ident` + `Brace` ⇒ element. **`Ident` alone** ⇒ `HtmlNode::Expr`, emitted as
  `(#expr).into()` → hits `impl From<&str> for VirtualNode`, which goes through
  `Cow::Owned` (`core/src/vdom/cast/impl.rs`) — one heap allocation per render
  that the `Cow::Borrowed` fast path avoids.

So a hoisted `&str` const used as a **text-node child** is correct and
compiles (bare ident, no braces), but it is not free: it trades a compile-time
literal for a per-render `to_owned()`. Hoisting is still right — the verifier
demands it — but prefer a `&'static str` in a `Cow::Borrowed` path if a
literal must stay allocation-free, and do not "optimize" by adding braces
around an attribute-value const.

Brace rules, from the same dispatch:
- `title:` / `label:` / `placeholder:` / `subtitle:` — replace the literal
  **in place**, no braces.
- A const on an element whose **next child** is a `{ ... }` block needs
  braces; the parser reads the bare ident and the following brace group as one
  continuing expression and the error surfaces *inside the child's text* as
  `error: expected ,`. That is why a clippy "unnecessary braces" fix here
  compiles in some files and breaks in others.
- A **non-`if`/`for`/`match` element's** `Ident` child is checked against
  `is_user_fn(&tag_name)` + the component's props field names; a const that
  happens to share a name with a prop field would be captured as a boolean
  attribute. Const names with a `PAGE_`/page prefix avoid that by construction.

## A clippy warning can be a real false positive against a macro DSL

`unnecessary braces around function argument` fires on
`class: { CLASS_FEATURE_CARD }` inside the `html!` macro, and
`cargo clippy --fix` will happily strip the braces and break the build —
`html!` parses a brace group and a bare ident differently, so removal yields
`error: expected ,` at the *next* field, not at the one you edited.

**Test the fix before applying it** (make a backup, apply, `cargo check`,
restore) and prefer reporting the false positive over silencing it with
`#[allow]`. Silencing hides a lint that is correct for normal Rust.