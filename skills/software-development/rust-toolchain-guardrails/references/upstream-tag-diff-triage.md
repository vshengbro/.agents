# Upstream tag-diff triage for consumer-side upgrades

Use when upgrading a **consumer** of a framework/crate you have a **local clone
of** (so you can read the exact upstream diff by tag) rather than reading
release notes or guessing from error messages.

The win: you know the breaking surface *before* you edit the consumer, so you
can tell "this is a real migration" from "this is a no-op bump" without
speculating — and you can hand a subagent an already-sorted fact sheet instead
of a research assignment.

## 0. Confirm the local clone has both tags

```bash
git -C ~/code/<framework> for-each-ref --sort=-creatordate \
  --format '%(refname:short) %(creatordate:short)' refs/tags | head -8
git -C ~/code/<framework> diff --stat vA vB          # the whole story
git -C ~/code/<framework> log --oneline vA..vB
```

If the clone is a work-in-progress branch with a dirty tree, `git describe
--tags` tells you how far ahead/behind the tags are. **A published version is
not the same commit as the local HEAD** — check which one the consumer resolves
to (`cargo tree -i <crate>`, or the `version` lines in `Cargo.lock`) before
diffing against HEAD by reflex.

## 1. Published versions ≠ consecutive integers

Read the registry's actual publish list; a gap in the sequence is normal
(sketch releases, a squashed bump, a version prepared but never published).
Do not let a missing number make you "fix" the target version.

```bash
curl -sS "https://rsproxy.cn/index/3/e/euv" | python3 -c "
import sys,json
vs=[json.loads(l)['vers'] for l in sys.stdin if l.strip()]
print(vs[-8:])"
```

Sparse-index prefix rule: for a 3-letter name `abc` the path is
`/index/3/a/abc`; for 1-letter, 2-letter and 4+ letter names the segment
lengths are `1` / `2` / `3` respectively. Getting this wrong returns an empty
list, which reads as "this crate has no versions" — verify you got a
non-empty list before trusting it.

The crates.io REST API answers `403` to plain `curl` from some networks while
the sparse index and `static.crates.io` still return `200`. Probe all three
endpoints before concluding you have no route to the registry.

## 2. Sort the diff by which crates the consumer actually uses

A monorepo release diff is mostly noise for a consumer that touches one entry
point. Classify each changed area into exactly one row, and only the last two
rows can break the consumer:

| Diff shape | Meaning for the consumer |
|---|---|
| root `src/` **zero diff** | the re-export surface is unchanged — every `use fw::{…}` still resolves |
| `pub use` added / private glob removed | additive, not breaking |
| internal module *moves* (file renamed, new `mod.rs`, `pub(crate) use` added) | invisible unless the consumer reaches into private paths |
| `pub fn` signature changed / public type removed | genuinely breaking |
| one sub-crate churns heavily while the consumer has **zero references** to it | inert — do not migrate it |

Then prove the "zero references" claim with a grep before relying on it.

## 3. Predict, then verify — never substitute for the compiler

The tag diff tells you where to look. It does **not** replace
`cargo check --all-targets` on the consumer: the diff misses behaviour changes
that type-check fine, and the consumer may use a re-export path the diff shows
as unchanged. Report the prediction and the compiler result as two separate
facts.

## 4. Zero-diff is a finding, not a reason to skip verification

"Root re-export surface is identical and the only pub changes are additive" is a
strong reason to expect a clean bump — and it is still reported *after* the
consumer's own build is green, never instead of it. A version bump validated
only by reading a diff is the same false green as bumping an orphan declaration.

## 5. "Use the new API for breaking changes" has a bounded reading

The standing instruction means: **when something is actually breaking, migrate
to the new API instead of shimming the old one** — no `compat` module, no
`#[allow(deprecated)]` re-export, no wrapper preserving the old shape. It does
**not** license rewriting working code to adopt unrelated new conveniences.
The migration criterion is:

- the old API no longer compiles, or
- it compiles but its documented behaviour changed, or
- it is deprecated in the release notes.

Anything else is scope creep, and a version bump that also refactors untouched
code is unreviewable. State which criterion each individual change met, so the
user can tell migration from gratuitous rewrite.
