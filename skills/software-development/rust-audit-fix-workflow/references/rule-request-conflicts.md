# When a fix fights the rule that asked for it

Some rust-standards checks have no source edit that satisfies them and the
user's request at the same time. Recognize the shape early: you are about to
write an exemption, a comment, or a `pub` marker purely to move a counter.
That is a decision for the user, not a workaround you get to pick.

## §6.2 `pub mod` vs. "use the concrete module path" — mutually exclusive

`verify_mod_visibility.py` (check 29) requires every `mod r#xxx;` in a
`mod.rs` to be **bare** — no `pub` / `pub(crate)` / `pub(super)` prefix.
But "import by concrete module path"
(`hyperlane_bootstrap::application::db::DbBootstrap`) **requires** `pub mod`.
Bare `mod` is not addressable from outside its parent, and the only
middle form — `pub use <child>::*` — flattens the child into the parent
namespace, which is the coarse granularity the request exists to remove.

**The two rules cannot both hold.** The reason §6.2 gives for banning `pub`
("`mod` in mod.rs is already crate-internal, `pub` is redundant") is wrong at
this boundary: inside `mod.rs`, `pub` is not redundancy, it is the only thing
that makes the module addressable.

| Choice | Result |
| --- | --- |
| bare `mod` + `pub use <child>::*` | §6.2 passes, coarse globs return |
| `pub mod` + concrete paths | concrete paths work, check 29 reports N hits |

### The one compliant exit, and where the marker must live

`verify_mod_visibility.py` ships an in-band exemption. Its constant is
`ALLOW = "# mod-visibility-allow: "` — **the marker literal includes the `# `
prefix**, and the reason after it must be non-empty. Audit check 5 separately
forbids bare `//` comments in `mod.rs` (regex `^\s*//[^/!]` exempts `//!`, not
`///`). Both constraints together leave exactly one legal spelling:

```rust
/// # mod-visibility-allow: consumed by concrete module path, which a bare `mod` cannot express.
pub mod request;
pub mod response;
```

- `// # mod-visibility-allow: ...` — does **not** match `ALLOW` (missing `# `), check 29 still fires.
- `# mod-visibility-allow: ...` at column 0 — not Rust; `cargo build` reports
  `unknown start of token` then `expected one of ! or [, found keyword mod`.
- inside `///` — matches the marker and stays clear of check 5.

## Two user rules can collide — surface the choice, don't pick it

The `mod-visibility-allow` marker restores the audit baseline. But §3 declares
"`mod.rs` gets no comments" and marks it **hard, no exceptions**. Those two
user rules contradict each other, so **only the user can resolve it**.

The right delivery is: implement the zero-comment form, run the full gate set,
then report **both measured numbers** — "adding the marker → 49/50, omitting →
48/50" — and let them choose. Do not add the comment to make a score look
better, and do not quietly ship 48/50 without saying so.

## Finding every non-globbed local import

A grep for `use .*hyperlane` over-reports badly: crate-root brace forms like
`hyperlane_plugin::{common::*, env::*, logger::*}` are **already** globbed, and
every leaf inside carries `::*`. The real violation is a **leaf that does not
end in `::*`**:

```python
for m in re.finditer(r'^(?:pub(?:\([^)]*\))?\s+)?use\s+(.*?);', txt, re.M | re.S):
    for leaf in re.findall(r'([A-Za-z_]\w*(?:::\w+)*(?:::\*)?)', m.group(2)):
        if leaf.split("::")[0] in WORKSPACE_CRATES and not leaf.endswith("::*"):
            ...  # real violation
```

`use` statements routinely span lines, so scan with `re.S` to the first `;` —
a line-by-line grep misses every multi-line brace block.

## Globbing one level too high silently changes meaning

`use hyperlane_bootstrap::application::*` resolves to the **modules**
(`db` / `env` / `logger`), not the structs inside them. `DbBootstrap` lives at
`application::db::DbBootstrap`, so the working form is
`application::{db::*, env::*, logger::*}`; the one-level glob fails with five
`E0433`s. **The glob must land on exactly the layer the symbol lives on** —
when unsure, build and let the E0433 list name the paths.

## Bin entry points are not `mod.rs`

`src/main.rs` and `bin/<name>/main.rs` are outside §6.2 / §6.1. The user rule
"mod.rs uses `*` for local deps" does not reach them, so a crate-root
`main.rs` that imports structs across crates keeps its concrete paths. Do not
glob it for tidiness — it will not compile.

## The auto-fixer will undo your concrete paths

`rust_pre_commit.py` Phase 1 has an import-centralization fixer that rewrites
specific local paths back to coarse globs:

```
use hyperlane_resources::{docker::path::SERVER_ENV_FILE_PATH, env::path::SERVER_ENV_FILE_PATH}
→ use hyperlane_resources::{docker::*, env::*}
```

Re-check every local-dependency import after running it. And when verifying,
look at `git diff` **and** `git diff --cached` separately: when the fixer works
through the index, plain `git diff` is empty and the change only appears under
`--cached`, which reads exactly like "my edits vanished".

## Related

- §6.3 / §6.4 sub-file rules and the `use super::*;` limitations: see the
  "`use super::*;` is not a free fix" section in SKILL.md.
- Verifier scope bugs that are genuinely unfixable: see
  [verifier-scope-bugs.md](verifier-scope-bugs.md). This file is the other
  class — the rule and the request are both legitimate, they just cannot hold
  at once.