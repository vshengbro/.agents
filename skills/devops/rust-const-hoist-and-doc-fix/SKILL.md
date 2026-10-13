---
name: rust-const-hoist-and-doc-fix
description: 'Use when bulk-fixing §1.3c or §2.2 Rust violations.'
---

# Bulk-fixing §1.3c + §2.2 in Rust view files

Clearing these two rust-standards rules across many files is mechanical,
but the verifiers compare **literally**, so hand-editing drifts. Build a
script that reuses the verifier's own parser.

## The two verifiers are the spec

- `~/.agents/skills/rust-standards/scripts/verify_hardcoded_strings.py` — §1.3c
- `~/.agents/skills/rust-standards/scripts/verify_doc_comment_format.py` — §2.1/§2.2

Import them as modules and call `audit_one(path)` directly. That gives
violations without re-running the whole-repo `find` walk, and — far more
importantly — it gives you the *exact* helper functions the checker uses,
so your rewrite spans and accepted forms cannot diverge from what gets
measured:

```python
import importlib.util
from pathlib import Path
def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
S = Path.home() / ".agents/skills/rust-standards/scripts"
vhs = load("vhs", S / "verify_hardcoded_strings.py")
vdc = load("vdc", S / "verify_doc_comment_format.py")
```

## §1.3c: span-exact literal hoist

Reproduce the checker's own span computation, or you will rewrite spans
it never reported and miss ones it did:

```python
def literal_spans(line):
    cs = vhs._comment_start(line)          # same comment truncation
    scan = line if cs is None else line[:cs]
    return [(m.start(), m.end(), m.group(0)) for m in vhs.STRING_LITERAL.finditer(scan)]
```

Rules that matter:

- **Copy the literal token verbatim** into the const. Recover it from the
  ORIGINAL text (before rewriting), not by re-quoting a decoded value —
  `rustfmt` wraps long literals onto a continuation line, so a naive
  one-line regex reports them as "missing" when they are present.
- **Deduplicate by value.** The same `"Pause"` in three tabs becomes one
  const and three references. That is the rule's intent ("reuse, don't
  invent duplicates"), but it means the literal *multiset* will not match
  the original; compare **sets** of distinct values when verifying.
- **Never rewrite a literal that is itself a `const ... : &str =`**
  initializer in the same file — that yields a self-referential alias
  (`const X: &str = X;`). Instead *move* the declaration to `const.rs`
  and delete the original line plus its `///` block.
- Skip const.rs, `class! {}` blocks, `vars! {}` blocks, attribute lines,
  whole-line comments, and format-macro format strings — the checker
  exempts all of these, so hoisting there creates a false positive.
- Name constants by **role** (`EVENT_VIDEO_EVENT_CAN_PLAY`,
  `GAME_3D_EXIT_BUTTON_LABEL`), never by truncating a prose paragraph
  into `..._THIS_DEMO_USES_EUV_ENGINE_S_3D_MA`. Add a `///` line stating
  the role; the value itself is now one line below the doc.

### New `const.rs` needs mod.rs wiring

Three-part layout, alphabetical, matching the repo convention:

```rust
mod r#const;
mod r#enum;
mod r#fn;
mod r#struct;

pub(crate) use {r#const::*, r#enum::*, r#fn::*, r#struct::*};

use super::*;
```

Parse the existing use line by stripping the `};` **and** the `;` —
`line[len(PREFIX):].rstrip("}").strip()` leaves the semicolon and emits
`r#struct::*};};`, a syntax error `audit_one` will never catch. Only
`cargo check` finds it.

## §2.2: derive doc bullets from the signature

Take the types from the checker so the doc cannot drift:

```python
name, raw_types, ret = vdc._fn_signature_types(lines, fn_idx)
```

- `raw_types` are the **bare** signature types: `&str`, `K`,
  `VirtualNode<PageAboutProps>` — not `&str: AsRef<str>`. Layer 4
  compares these literally.
- Insert sections at `doc_end + 1` (after the whole `///` block), never
  at `doc_start + 1` — inserting mid-prose splits a sentence across the
  section header and reads as corruption.
- Format is `- \`Type\` - description` per param, with `# Arguments` and
  `# Returns` separated by a bare `///`. At least one prose line must
  precede the first `#` header.

## Verify in a throwaway copy first

Overlay onto a full copy of the repo and `cargo check` there. Two
reasons:

1. `audit_one` returning 0 is necessary, not sufficient — a broken
   `mod.rs` is invisible to both verifiers.
2. Concurrent agents share the worktree. Copy first, then check, so you
   are not reading your own edits as someone else's.

```bash
cp -R /path/to/repo /tmp/trial && cp -R transformed_example /tmp/trial/example
cd /tmp/trial && CARGO_TARGET_DIR=/tmp/trial-target cargo check -p <crate> --all-features --offline
```

`fmt` is workspace-wide: `crate fmt` reformats other agents' files too.
Run it, then re-run your audit to confirm your files are still 0.

## Rehearse on a copy, always

A copy costs one `cp -R`. It is the only way to catch the self-alias,
the `};};`, and the mid-prose insertion before they land in a shared
tree where two agents are editing at once.
