---
name: capability-gap-audit
description: 'Audit a library for missing features and API reachability.'
license: MIT
metadata:
  version: 1.0.0
  tags: ["audit", "refactoring", "code-quality"]
  related_skills: ["main-agent-delegation-rule", "rust-standards"]
---

# Capability gap audit

## When to Use

- "This library/framework/crate is incomplete — fill in the missing functionality."
- "Some interfaces need to be made `pub`." / "External crates can't construct this."
- Any request to assess a codebase's completeness against a capability list, feature matrix, or its own documentation claims.

For "this crate is incomplete / fill in the missing features / some interfaces need to be `pub`" requests. The deliverable is a **shipped implementation**, but the work must not start until the gap list is real — most such requests hide a wrong premise that would waste the whole effort.

## 0. Never let the first list drive the edits

A request like "complete the missing functionality" is a *symptom*. The measurable facts live in the source. Auditing first is not ceremony; in practice the audit is what determines whether the requested work is even the right work.

The same applies to "some interfaces need to be `pub`". "Not `pub`" does not mean "unreachable from outside" — for attribute-macro-driven codebases it very often does. See §2.

## 1. Procedure

1. **Enumerate the surface**, not the vibes: module list, line counts, manifest, re-export lines. A feature is "present" only if a real `struct` + impl + non-trivial body exists.
2. **Split the audit into two independent tracks** and dispatch them as parallel subagents (§4):
   - *visibility / API reachability* — what can an external crate actually name, construct, read, write, call?
   - *functional completeness* — walk a capability checklist for the domain, judge each `present / partial / stub / missing` with `file:line` evidence.
3. **Diff the crate's own doc comment against the source.** A crate-level `//!` claim that is not implemented is the highest-value finding in the whole audit, and it is invisible to grep-for-missing-things.
4. **Verify the audit before implementing** (§2, §3). This is the step people skip, and it is the step that saves the work.
5. **Rank by value-per-unit-risk, not by feature size.** A one-line missing call in the main loop outranks a missing subsystem, because it silently corrupts every frame rather than being absent.
6. **Implement in waves** (`references/wave-planning.md`), one wave per branch, delegating each.
7. **Fix the doc comment in the same wave as the code.** A comment that lies about behaviour is worse than a missing feature, because it removes the reader's ability to notice the gap.

## 2. Verify the visibility premise before editing a single line

When the request is "make things `pub`", check what the language/toolchain actually does before trusting any list.

**Attribute-macro-generated accessors break the naive rule.** In crates using lombok-style derive helpers, a bare `#[get]` / `#[get(type = "Copy")]` generates a **`pub`** accessor *regardless of the field's own visibility*. So a `pub(crate)` field with a bare `#[get]` is fully readable from an external crate. An audit that flags it is wrong.

The real blockers in that situation are only:

| Form | Effect on an external crate |
|---|---|
| `#[get(pub(crate))]` / `#[set(pub(crate))]` / `#[get_mut(pub(crate))]` | the accessor itself is crate-private — **this is the blocker** |
| item is `pub(crate)` but its module is re-exported via `pub use module::*` | the item is not re-exported — hard error at the use site |
| field has no `#[get*]` at all | no generated accessor — genuinely unreadable |

Note the asymmetry: **reads are often already fine while writes are blocked.** `get_mut`/`set` are commonly pinned to `pub(crate)` by the macro's default. Count the write-path attributes separately from the read paths; conflating them inflates the number of edits and sends you to change things that were never broken.

**Check the macro's own source for its default visibility** before concluding anything — the derive's `Default` impl is the authority, not its documentation.

**Method-inheritance carve-out:** a non-`pub` fn inside a `trait` definition, or inside a `trait` impl, inherits the trait's visibility. Auditing those as "not public" is pure noise; a large codebase can easily produce hundreds of such rows.

## 3. Check each audit row's stated *rationale*, not just its line number

An audit table carries a claim per row ("external crate cannot construct this", "this is never read"). Spot-check two or three rows at their cited `file:line`.

Rationale failures are the common case, because the scanner reasons from syntax while the compiler reasons from the whole construct. A row saying "struct literal construction is rejected" is moot for a type that has a public constructor; a row saying "never called" needs a `search_files` sweep (or a repo-wide `grep` inside a terminal) across the whole crate, not its own module, before you delete or rewire anything.

**If the rationale collapses, the entire category is suspect** — do not edit from it. Re-derive that category yourself and record the corrected finding where the next session will read it (annotate the report in place; do not silently delete the wrong table, because the next reader needs to know it was wrong and why).

Corollary for the subagent that produced it: the agent had no access to what it did not measure, and will not flag its own error. Assume certainty outruns evidence.

## 4. Dispatch shape

- Two audit tracks in parallel, read-only, each writing a report file and returning a short summary. Do **not** let an auditor also implement.
- Give each implementer a **file-ownership list** and name the other agent's files as off-limits, with "stop and report, do not edit" as the escape hatch. Partition by module; when two tasks both need one directory, split at the file level and name the exact paths in both briefs.
- Put the current HEAD in both briefs so neither rebases under the other.
- Tell every agent in a repo the user owns: **do not `git stash` / `git stash pop` / `git stash list`.** The user's uncommitted work is not yours to move.

Verification of the returned claims is covered by `main-agent-delegation-rule` §6a.

## 5. Tests must be shown red

For any behaviour fix, the regression test must be demonstrated failing against the unfixed code, not merely passing against the fixed code.

Do it in place without stashing:

```bash
git checkout HEAD~1 -- path/to/impl.rs   # revert just the implementation
cargo test -p <crate> <testname>          # must FAIL
git checkout HEAD     -- path/to/impl.rs   # restore exactly
git diff HEAD -- path/to/impl.rs          # must be empty
```

A test that has never run red may be measuring nothing at all — wrong geometry, a re-seeded input that hides the bug, or an assertion on an outcome that holds regardless. This is the single most common way "fixed and tested" is untrue.

## 6. A multi-wave audit shares one working tree — the tree is the fragile part, not the code

Wave-based audits (§1.6, `references/wave-planning.md`) run subagents back-to-back against a single checkout. That checkout is process-global state, and anything else that touches it — another session, another agent, the user in their own terminal, an IDE — invalidates your model of it without warning. The failure is not a compile error; it is **silently fewer commits than you expect**.

What this looks like in practice: a wave's edits vanish from both the working tree and the branch, a commit you made is sitting on a *different* branch, or `git rebase <remote>` reports "up to date" while replaying nothing because the ref already moved out from under you.

**Cheap guards, in order:**
- **Pin a rescue tag before any ref-moving operation** — `git tag rescue/<topic> <sha>` on every commit you have finished. Dangling commits survive `git gc` only until the grace period expires, so a tag costs nothing and is the difference between a one-command recovery and re-implementing a wave.
- **Assert the branch before every stateful git op**, including immediately before `git commit`. A mismatch is an emergency, not a curiosity.
- **Confirm each wave's commit count**, not its exit status: `git log --oneline <base>..HEAD | wc -l` against the number you expect, and `git branch --contains <sha>` to confirm *where* a commit landed. A commit on a neighbouring branch still reports success — you find out at PR-diff time, when it is expensive.
- **Back up in-flight work outside the repo** before any `stash`/`checkout`/`reset`: `git diff > /tmp/x.patch` for tracked edits, plus a real `cp -r` for untracked new files, because a diff cannot contain them.
- **Use `git worktree add` for genuinely parallel waves** if the waves can be split by module. Separate checkouts on one object store remove the whole class of problem instead of mitigating it.
- **Never `git stash` on a shared repo** (§4 already says the user's work is not yours to move) — the stack is shared too, and `stash pop` takes the *top* entry, which may not be yours.

Recovery is a sequence, not a guess: `git reflog` to locate the commits, `git tag` to pin them, then `git reset --hard <sha>` and redo the rebase. Do not attempt a fresh rebase against a moving remote until the work is anchored to a SHA you control.

## 7. Stage explicit paths; `git add -A` sweeps in artifacts you were told to leave

A cleanup commit that targets several crate dirs invites `git add -A <dir> …`. That stages **everything untracked** under those paths — build output, vendored bundles, generated HTML/JS/WASM — not just the edits you made. Anything already excluded by a `.gitignore` is safe; anything merely *untracked* is not.

- **Add the exact files** the task changed. If a bulk add is genuinely easier, check `git status --short` first, note the untracked entries that predate your work, and confirm the staged set with `git diff --cached --stat` before committing.
- Correct an over-broad commit rather than leaving it: `git rm -r --cached <artifact-dir>` then `git commit --amend --no-edit`, and re-verify the amended stat is exactly the files you meant.
- Removing from the index does not touch the working tree — the files stay on disk, which is what you want when the instruction was "leave the build artifacts alone".

## 8. Report shape the user can act on

Lead with the counted state, not a narrative: how many items in each class, and the top gaps with difficulty + landing file. Then the confirmed bugs with `file:line`. Then what was fixed and what was deliberately skipped **with the reason**. If a fix is a pragmatic approximation rather than the textbook solution, say so and name the term a later solver should replace.

## 9. If the audit's own tooling claims green while the data is wrong, that is a finding

A checker that reports `0 violations` on input you can see is unsorted is a **false negative, and more dangerous than no checker** — it manufactures confidence. Confirm the ordering/verifier story by running it against an input you deliberately broke, and confirm the check has real coverage by running it against a second repo that has never been subject to it.

The discriminating fixture is the one that distinguishes the rule from a weaker rule that happens to agree on the easy cases. When a rule is "length first, then lexicographic", a fixture of *equal-length* elements is the only one that proves the tiebreak is implemented; sorted-vs-unsorted alone would pass under plain alphabetical order too. A verifier that only ever saw the happy path is unverified.

Register a new check in the project's audit/gate runner rather than invoking it ad hoc — a rule enforced only by a one-off script at the moment it was written has no enforcement value the next time the file is edited. Confirm the gate actually blocks: the real test is that a deliberately-violating staged change is *rejected*, and that a clean one is allowed.

**When a fix is a pure refactor of a macro-generated API, the compiler is the real test.** Removing a redundant annotation changes no runtime behaviour, so a passing verifier only proves the text is gone. Prove the *semantics* survived: an external-crate call to the renamed/regenerated item that used to compile must still compile, and the full test suite must still pass. Diff-shape assertions are what catch collateral damage — for a bulk attribute edit, assert that every removed line is the target attribute, that lines carrying a *narrower* qualifier than the default were left untouched, and that repo-wide counts of those qualifiers are unchanged. A count check (`pub(crate)` still 237 before and after) is what proves the sweep did not "helpfully" widen anything.

## References

- `references/wave-planning.md` — sizing waves, ordering by value-per-risk, and what belongs out of scope for a first pass.
- `main-agent-delegation-rule` — when to dispatch, and how to verify what comes back.
- `rust-standards` — the style/lint gates any Rust audit output has to satisfy.
