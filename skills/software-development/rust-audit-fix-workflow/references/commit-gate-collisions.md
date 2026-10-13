# The two commit gates, and the collisions between them

`rust_pre_commit.py` and `~/.git-hooks/pre-commit` are **different gates**, not one gate run twice. Getting this wrong costs a commit cycle: `rust_pre_commit.py` reports `PASS — all phases clean`, and the commit is then refused.

## What each one actually checks

| | `rust_pre_commit.py` (Phase 2) | pre-commit `staged_file_gate.py` |
|---|---|---|
| Scope | whole repo, absolute violation count | staged `.rs` only, **delta vs `HEAD`** |
| Checks | the full 40-check suite | a subset of file-level verifiers |
| Baseline | zero | `HEAD` — only new violations block |
| `tests/` exemption | doc-comment + layout checks exempt | doc-comment check **still applies** |
| Authority | "is the repo clean" | "will this commit land" |

The absolute-count vs delta difference is what makes the hook survivable on a repo with legacy debt: it never blocks on debt you did not introduce. The subset-vs-full difference is what lets a green Phase 2 hide a real block.

**The hook is the only authority on whether a commit lands.** Never reach for `--no-verify` to get past it — when it blocks, that report is the spec for the next slice.

## Collision 1 — the `tests/` helper with no valid shape

An auxiliary `fn` in a test file has no legal form:

```
fn helper() -> T { … }        // no doc comment  -> staged gate FAIL
/// doc                        // with doc        -> §14.5 FAIL (no comments in tests/)
```

The staged gate runs the doc-comment verifier on files the full audit exempts, and §14.5 bans every comment in `tests/`. Documenting the helper satisfies one rule and breaks the other.

**Resolution: delete the helper, inline its body at each call site.** A test file should contain only `#[test]` functions; both rules ignore those. Do this the moment a second helper appears — the alternative is a file that no single shape can make legal.

A shared `const` is the other legal escape: it needs no doc comment and is not a function.

## Collision 2 — `const` accessors vs the `self.field` ban

§17.12 exempts hand-written accessor bodies from the `self.field` ban. The verifier detects that exemption by matching the fn **name** on a plain `fn`:

```rust
pub const fn get_kind(&self) -> ElementKind { self.kind }  // NOT exempt -> reported
pub fn get_kind(&self) -> ElementKind { self.kind }        // exempt
```

So marking an accessor `const` silently converts every accessor body into a reported violation. **Accessors are plain `pub fn` throughout — never add `const` to one.**

## Collision 3 — a free helper is not allowed in `impl.rs`

Check 15 pushes a pure `&Foo` helper out of `fn.rs` into an `impl` method. The reverse also holds: an inherent `impl Foo { … }` block holds **only** inherent methods, so a free `fn helper(…)` at file scope in `impl.rs` trips the keyword-purity check. Move it to the crate-level `fn.rs` and call it from the impl.

This bites hardest on comparison and encoding helpers that read like implementation detail of the impl.

## Triage order when a commit is blocked

1. Read the hook's per-file, per-check output — it names the verifier, so you know which § to load.
2. Run that verifier directly on the repo to see the full list, not just the delta.
3. Decide which of the three collisions above it is; each has a different fix.
4. Re-run `rust_pre_commit.py` (Phase 2 may now *also* report it, since the subset is only a subset) and then re-commit.

Never treat the hook's block as a false positive without first confirming the same input is clean on a `HEAD` baseline — see the baseline section of `SKILL.md`.
