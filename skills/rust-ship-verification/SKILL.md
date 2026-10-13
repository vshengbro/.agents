---
name: rust-ship-verification
description: 'Use when shipping a Rust change to a PR.'
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Rust, Verification, Git, Pull-Requests, Release]
    related_skills: [rust-standards, git-standards, github-pr-workflow]
---

# Rust Ship Verification

The phase **after** the code compiles: proving it complies, shipping a diff that contains
only your change, and recovering when the git state moves under you mid-task.

Load `rust-standards` first — this skill does not restate its rules, only the shipping
workflow around them.

## 0. Decide the route before you create anything

**Route by what the diff changes, not by which repo it lands in** — full rule in
`git-standards` §3.3a. Run its classifier *first*, because the answer determines the
shape of everything downstream:

```bash
python3 ~/.agents/skills/git-standards/scripts/classify_change.py --staged
# exit 0 = DIRECT_PUSH   exit 1 = NEEDS_PR   exit 2 = error (never a free pass)
```

| Verdict | Route | Version bump |
|---|---|---|
| `DIRECT_PUSH` — docs / config / **comment-only** / frontend stylesheet | commit straight to the default branch | **no** |
| `NEEDS_PR` — any changed line of executable code | branch → push → PR → merge → delete branch | yes |

Do not infer this from the file extension. A `padding:` line inside a `class!` block in
a `.rs` file is a Rust string literal that gets compiled into the wasm and executed, so
it is code and needs a PR — while editing the comment above that same `padding:` is a
documentation change and direct-pushes. A comment-only commit shipped through a PR
ceremony (and a version bump) is a defect the user has to unpick, not a harmless extra
step.

**A version bump belongs to executable-code changes only.** Bumping for a comment-only
commit publishes a release whose contents are identical to the previous one. Re-run the
classifier after any edit that changes the diff's character — it lexes the code, so a
change that started as a comment fix and grew a statement flips the verdict mid-task.

## When to Use

- Writing or refactoring Rust that will be **committed or pushed** — especially new files
  or bulk file-level restructurings.
- A build/generate CLI in the workspace is known to touch tracked config.
- The user asks to bump a version, open a PR, or reports a PR whose state looks wrong.
- A push succeeded but the PR, the remote ref, or the live site does not reflect it.

Not for: authoring the code itself (that is `rust-standards`), or non-Rust repos.

## 1. Prove compliance with the FULL gate, not the commit hook

**The commit hook is not a compliance check.** It is a *delta* check: it compares each
staged file against `HEAD` and reports only the increase in violations.

**The trap: for a brand-new file the delta is structurally zero.** There is no `HEAD`
version to subtract, so the baseline is treated as 0 and the file is reported clean
*no matter what it contains*. The same applies to bulk refactors that rewrite files
wholesale. A green hook on new or heavily-rewritten `.rs` files means **nothing was
verified**.

| Gate | Scope | Use |
|---|---|---|
| commit hook (`staged_file_gate.py`) | staged files, **delta only** | fires automatically; catches newly-added violations in *existing* files |
| full gate (`rust_pre_commit.py`) | whole repo: fixers + all audit checks + fmt + clippy + test | **the only done criterion** — run it yourself, before commit |

**Rule: if this task added `.rs` files or bulk-refactored them, a hook-only "0 violations"
is a skipped gate, not a pass.** Sequence is: change → run `rust_pre_commit.py` → fix to
exit 0 → commit.

**Audit output truncates per rule (commonly the first 5 hits).** Violations therefore
surface in waves — fixing the visible batch reveals the next one, which reads as "new
problems appeared" and tempts you to declare victory early. For paths you authored, run
each verifier directly and read its own total instead of trusting the audit summary:

```bash
for s in verify_keyword_file_purity verify_hardcoded_strings verify_doc_comment_format \
         verify_module_imports_centralized verify_use_aggregation verify_no_allow_lints \
         verify_lib_rs_doc_comment verify_let_type_annotations verify_section_blanks; do
  printf '%-38s ' "$s"
  python3 ~/.agents/skills/rust-standards/scripts/$s.py <repo> 2>&1 | tail -1
done
```

Pre-existing violations are **not permanently out of scope** — but never widen a PR to
make a repo-wide counter read zero either. Report the debt with counts and locations
(`verify_<rule>.py <repo>` prints a per-rule total and file count; the audit summary
truncates), and let the user choose the sweep. When they choose it, it is its own scoped
piece of work with its own gates, not a side effect of a bugfix PR.

### 1b. Scaffolding added to satisfy a scanner and never wired up is dead code

A `macro_rules!`, re-export, or helper introduced to pass a static check, with no call
site anywhere in the tree, is a liability rather than a fix: the check that motivated it
may be satisfied by a different spelling, the next reader cannot tell it is load-bearing,
and removing it later becomes an unrelated change under someone else's commit. Confirm
the call site exists before you treat the scaffolding as finished:

```bash
git grep -n '<name>' -- '*.rs' | grep -v 'macro_rules!\|pub(crate) use'
# no hits outside the definition => nothing calls it, delete it
```

A `use` line added purely to satisfy a gate is the same shape, and it announces itself
one commit later: the staged-file gate reports `unused macro definition` /
`unused import` on the *following* commit — the cheapest possible warning shot, but only
if you read it instead of working around it. When a gate rejects a construct you added
to appease an earlier gate, delete the construct; do not build a second layer on top.

Also check whether the construct belongs in a `const.rs` at all. Placing a `macro_rules!`
in a keyword file and re-exporting it with `pub(crate) use` violates the import-centrality
rule even when the macro is called, because a keyword file's only legal `use` is
`use super::*;`. A bare `include!` at the original call site is often the correct answer
the macro was invented to avoid.

### 1a. Classify a blocking finding BEFORE you edit source

A gate rejection is not automatically a source defect, and editing source until
the gate goes quiet is how a real verifier bug gets papered over with a change
that makes the codebase worse. Three probes, in order:

1. Is the construct in **your** diff, or legacy in `HEAD`? (`git show HEAD:<file> | grep …`)
2. Is it a position the grammar requires a literal in — `extern "C"`, `cfg!`,
   an `assert!` message?
3. Do **siblings of the identical shape in the same file go unflagged**?

Probe 3 identifies a verifier bug: a shape tolerated three times and flagged
once is being discriminated on something other than its shape, and the fix
belongs in the verifier, not your edit.

Two hard rules:

- **Some findings have no compliant source spelling.** `extern ABI {}` and
  `assert!(cond, "{}", CONST)` are compile errors — the literal is part of the
  construct's shape, not program data, so §1.3c's "hoist to `const.rs`" does
  not apply. Hoist as far as it goes (static prefix as a `const`,
  interpolation left in the literal) and report the residue as a count.
- **Never trade a finding for an undiagnosable test.** Collapsing
  `"{} at={:?}, want {:?}", CONST, at, want` into `"{}", CONST` silences the
  check *and* deletes the values from the failure output. A test that fails
  without naming what failed is worse than the finding.

**Converge limit: two attempts, then revert to zero net change and report.**
If a fix does not pass the gate *and* `cargo test`/`clippy` on the second try,
it is not a source-shape problem. Restore the file exactly
(`git diff HEAD --stat -- <file>` must match the pre-session count) and report
with the three probes attached — the choice between rewriting the assertion's
information, narrowing the commit, or fixing the verifier belongs to the user,
since each costs something different.

Full classification table, proof obligations, and where the real fix lands:
`references/gate-block-classification.md`.

## 2. Audit tracked files after every build-tool invocation

Some build/CLI tools in Rust workspaces rewrite tracked config as a side effect — injecting
into `Cargo.toml` (workspace `exclude`/`members`), rewriting `.gitignore`, regenerating a
lockfile. The mutation is silent and lands in whatever commit you make next.

**After every such invocation, before staging:**

```bash
git diff --stat
git diff -- Cargo.toml .gitignore     # the usual targets
```

Anything outside your task's scope: `git checkout HEAD -- <path>`. Then re-check that a
scoped `git add <dir>` is what you actually meant — a `git add -A` in a dirty worktree
sweeps in unrelated edits and you will not notice until review.

**If it happens twice, stop and report it as a defect in the tool** rather than reverting a
third time. A build command that corrupts tracked config is a bug worth an issue.

## 3. Never stage a bare directory when the worktree is dirty

`git add -A <dir>` (or `-A` with no path) commits *everything* under that path, including
edits from an unrelated earlier task that were sitting uncommitted. Prefer explicit paths,
or `git add <file>` per file. Before committing, always read `git status --short` and
confirm every entry is yours:

```bash
git status --short | grep -v '^??'      # tracked modifications only
git diff --cached --stat                 # what will actually be committed
```

### 3a. The push gate — run all three before ANY push

A push publishes every commit between the remote ref and the local tip. That
is the last moment you can see what you are about to ship, and unlike a commit
there is no review step afterwards.

```bash
git log origin/master..master --format='%h %an <%ae> %s'   # whose commit?
git status --porcelain                                      # whose dirty files?
git diff --stat origin/master..master                       # does it overlap mine?
```

| Observation | Action |
|---|---|
| nothing unpushed, every dirty path is mine | push |
| dirty paths include ones I did not touch | stage explicit paths (above); **never** `git add -A` |
| `origin/master..master` has a commit I did not author | **STOP and ask** |

**Why the third row is a stop, not a judgement call.** A direct push ships that
commit under the repo's shared identity and takes away the author's last chance
to see it. Report the sha and author, the file count, and which paths overlap
your edits — overlap decides whether the options are cheap, since a
non-overlapping commit is a harmless extra push while an overlapping one may be
untestable mid-rebase.

This matters most in a repo where several agents work the same checkout, which
is the normal setup for a monorepo audit run. There the tree routinely holds
dozens of paths you never opened, and "my change is ready" is not the same
claim as "the tree contains only my change".

**Never `git stash` to establish a baseline.** It is the tempting move when a
build failure looks pre-existing, and it removes a colleague's in-flight edits
from the tree; if the session ends first, that work exists only in the stash
entry. Both read-only alternatives answer the same question:

```bash
git show HEAD:<path> > /tmp/baseline && diff -u /tmp/baseline <path>
git worktree add /tmp/baseline-wt HEAD      # whole tree at HEAD, yours untouched
```

**Confirm the push landed by reading the remote ref, not the exit code:**

```bash
git fetch origin
git rev-parse HEAD; git rev-parse origin/master     # equal == published
gh api repos/<owner>/<repo>/branches/master --jq '.commit.sha[:7]'
```

### 3b. A PR cannot follow a direct-push

Once a commit is on the default branch it *is* the default branch, and
`gh pr create` has nothing to propose — GitHub answers `No commits between
master and <branch>`. This is the direct-push route working as specified, not
a defect. Confirm against the remote ref (an unpushed commit is the opposite
symptom) and present the three real options: leave it published; rewrite
published history, which needs explicit approval every time because other
clones may hold the ref; or route the *next* change through a PR.

**Never manufacture an empty PR to satisfy the request.** A diff that does not
correspond to the work under discussion is worse than no PR — the reviewer
approves a placeholder believing they reviewed the real change.

### 3c. A version bump is a publish decision, not a housekeeping step

Ask whether the workspace is actually releasable before bumping. In a
sync-only workspace (CI runs `crate sync` and never `crate bump`) the version
is written by a human, and the publish job releases **every** workspace member.
So a bump taken while other crates have in-flight edits ships code you have
not reviewed and that may not even compile.

**A DIRECT_PUSH does not carry a version bump.** A comment-only or docs commit
publishes a release byte-identical to the previous one, so the number is
unchanged and the bump is noise. Conversely a NEEDS_PR that touches executable
code without a bump ships the fix and never releases it. The classifier verdict
and the bump decision are the same decision — see §0.

**"Upgrade and push" names a route, not a merge.** The phrasing covers the
version bump and the transport; it is not authorization to merge a PR that
already exists. A direct push is complete once `git push` returns and the
remote ref is read back. A PR cycle stops at green CI with the PR open —
`git-standards` §4 pitfall 9 forbids self-merging without the user saying so
in that turn. When the ask is ambiguous, ship the branch and report the PR URL
rather than merging; a merge is cheap to add afterwards and expensive to undo.

Count the members under modification first, and say plainly that the bump
would carry them. When several crates are mid-edit, the correct action is to
defer the bump until CI is green — and note that pushing the version change to
a release-triggering branch *is* the release, so "change the number but don't
publish" is not available on such a branch.

### 3a-1. Ask what the remote ref already contains before assuming a pile-up

`origin/master..master` counts commits you have **not pushed**. In a shared
worktree it is common to read a long list, panic, and ask the user — then find
the branch was already published and your push advances it by exactly one
commit. Check the actual remote ref first:

```bash
git ls-remote --heads origin <branch>          # where the branch really is
gh pr list --head <branch> --state all --json number,title,state,url
git log origin/<branch>..HEAD --format='%h %an <%ae> %s'   # what YOUR push adds
```

The second command is the one people skip: a branch can already carry an open
PR whose title has nothing to do with your change. "Reuse the PR" is a
legitimate user answer to that — see §3a-2.

### 3a-2. Before reusing a PR, prove the checkout will still compile

A PR checks out **base + committed branch**. It never sees the dirty
worktree. So any constant, type, or module your staged file references must
already exist **in `HEAD`**, or CI breaks on a diff that compiles perfectly
locally. Check the identifiers your diff *adds*, not the ones it removes:

```bash
git diff --cached -- <file> | grep '^+' | grep -oE '\b[A-Z][A-Z_0-9]{3,}\b' | sort -u \
  | while read c; do
      git grep -q "const $c" HEAD -- 2>/dev/null \
        || echo "UNCOMMITTED-CONST: $c"   # would break the PR
    done
```

A constant that only exists in an untracked `const.rs` is the usual shape.
Either commit the whole dependency set or leave that file out of the commit —
never commit the referencing half.

### 3a-3. Mixed diffs: prefer leaving the shared file out over picking hunks

When your change and a colleague's share a file, do not reach for
`git add -p` by reflex. Splitting one coherent file into two commits, where the
first half does not build and the second half belongs to someone else, is worse
than one commit. State plainly which files are yours and which you left, and
say in the PR body that the excluded ones are in-flight elsewhere. If the
user says "reuse the PR", they have accepted that scope — ship the clean
files, and record the exclusions in Notes so a reviewer is not surprised by a
`class:` that still has braces.

### 3a-4. When your change contradicts an earlier commit on the branch

Check what the branch's recent commits decided before adding to it:

```bash
git log --oneline -6
git show --stat --format='%h %an%n%s%n%n%B' HEAD
```

If HEAD already implemented your idea under a different limitation, your commit
**overturns its conclusion**. Do not land that silently — put it in the PR
Notes ("this invalidates the earlier decision because the limitation is now
fixed; the change is additive, the old form still compiles and is still
tested"). A reviewer who diffs the two commits needs to know they are not
looking at a regression.

### 3a-5. A CI bot can commit your uncommitted work out from under you

On a repo with a bot workflow that commits to the default branch (version sync,
`cargo fmt`, dependency bots), this happens mid-task:

```bash
git add Cargo.toml && git commit -F msg.txt   # hook BLOCKS it
git log -1 --format='%an <%ae>'
# github-actions[bot] <github-actions[bot]@users.noreply.github.com>
```

The commit is the **bot's**, not yours — and it now *contains your staged
edits*, because a bot ran between your verify and your commit and swept the
worktree. Your `git log --author` check (`git-standards` §7.4) is what catches
this; `git log -1 --format=%s` looks superficially fine and is not enough.

**Diagnose before doing anything else** — the state is genuinely ambiguous:

```bash
git log --oneline -3 --format='%h %an %s'
git log --format='%h %s' | grep -i "<my subject>" || echo "MY COMMIT DID NOT LAND"
git show HEAD --format='' | grep -E '^[-+]' | grep -v '^[-+][-+]'   # what the bot took
grep -nE "^(dep_a|dep_b) " Cargo.toml                                  # is my edit still present?
```

Then **stop and report**. Your work is now on the remote under a bot identity,
which breaks the user's "commits must be authored by me" rule. The fixes
differ sharply in blast radius, so none of them is yours to pick:

| Option | Cost |
|---|---|
| leave it — the change is on the remote and verified working | author is a bot, not the user |
| `git revert` the bot commit, re-commit as the user | also discards whatever else that bot commit did (a version sync, say) — **needs explicit approval** |
| ask the user | correct default when the bot commit bundled anything you did not author |

The real lesson is earlier: **a hook rejection is a signal the worktree is
still in flux.** Re-read `git status` and `git log` immediately after a blocked
commit rather than retrying the commit — a retry can land on top of whatever
changed in between.

### 3a-6. Do not report "repo is clean" from a partial gate run

Claiming zero violations repo-wide after running three of the verifiers is a
false report, and it is the kind that survives into the PR body. Enumerate what
is actually in `scripts/`, run all of them, and if only some were run, scope the
claim to those:

```bash
for s in ~/.agents/skills/rust-standards/scripts/verify_*.py; do
  printf '%-40s ' "$(basename "$s" .py)"
  python3 "$s" . 2>&1 | tail -1
done
```

Two real non-zero results were hiding behind three green ones. The report then
became the useful one: "my 7 files are clean across all 28; 8 pre-existing
violations elsewhere, in files I never touched" — which is both true and
actionable. **Attribute each remaining hit**: `git show --stat` on your own
commit plus `git status --porcelain` on each file separates your regression from
a colleague's in-flight work from historical debt.

**Matching the verifier's output by filename alone is a trap** — a per-file
grep on `basename` matches every other `fn.rs` in the tree and invents
violations. Match the full path the verifier prints.

## 4. Verify test results by assertion count, not suite count

**A green acceptance run proves nothing until you assert the thing under test
actually executed.** The common shape: a harness boundary is silently dead, a
caller falls back to a slower path, and every downstream verdict still comes
out correct — so the result table looks perfect while the code you meant to
exercise never ran.

Cheapest guard: assert one representative call returns a value of the expected
type, and that value is a *result*, not a sentinel. Then diff the library you
are editing against any near-duplicate copy — a previous session's fix often
landed in a scratch/untracked file that nothing imports, and the tracked
original is still broken. Before reporting a full pass, confirm the file the
runner imports is the file you edited:

```bash
grep -rn "sys.path.insert\|^from .*lib import\|^import .*lib" <runner>   # which lib loads
```

Suite count drops for benign reasons (a file restructure merges test binaries) and stays
flat for a real one. **Assertion totals are the stable signal:**

```bash
cargo test --all-features --workspace -- --test-threads=1 2>&1 \
  | grep -oE '^test result: ok\. [0-9]+' | grep -oE '[0-9]+' | paste -sd+ | bc
```

If the total is unchanged from the base, no coverage was lost.

**A crash under parallel test execution that does not reproduce with
`-- --test-threads=1` is an execution race in the suite, not a regression you introduced.**
Confirm by (a) re-running serially, and (b) running the failing suite in isolation. Report
it as a flake; do not "fix" the source to chase it.

## 5. Recover when the PR is merged or the base moves mid-task

**Signature symptom: pushes succeed, but the PR's reported state never changes.** After
pushing a fix, the PR still shows the old head / old file counts, and the API's
`headRefOid` disagrees with your local `HEAD`.

**Do not assume API caching.** Check the PR's `state` first — a **merged or closed PR stops
updating**, and every subsequent push lands on a branch nothing reads:

```bash
gh pr view <N> --json state,mergedAt,headRefOid,changedFiles
git fetch origin
git rev-parse HEAD; git rev-parse origin/<branch>   # push did land; the PR is just done
```

Recovery — build a fresh branch from the moved base and re-land only your work:

```bash
git fetch origin
git checkout -b <new-branch> origin/master
git cherry-pick <sha1> <sha2> ...        # only the commits that are still wanted
# conflicts where the base already contains a later version of your edit:
git checkout --theirs <file> && git add <file> && git cherry-pick --continue
git log --oneline origin/master..HEAD
git diff --name-only origin/master..HEAD | grep -v '^<your-scope>/'   # must be empty
```

Then **re-run the full gate from step 1** — the cherry-picked commits were verified against
a base that no longer exists — and open a **new** PR. Say plainly in your report that the
original PR was already merged and this is a follow-up, with what landed in each.

### 5a. Isolate a CI failure from a shared worktree before touching anything

CI checks out **base + committed branch**. Your worktree also holds every other agent's
uncommitted edits. So a local `cargo fmt -- --check` that fails does NOT mean the
committed tree is unformatted — the diffs may belong to files no commit of yours contains.
Running the check in place conflates the two and tempts you to "fix" a colleague's work.

Reproduce CI's exact command in a throwaway worktree at `HEAD`, which is the tree CI sees:

```bash
sed -n '/Format check/,+3p' <(gh run view <id> --log-failed)   # the literal command
git worktree add "$SCRATCH/ci-repro" HEAD
(cd "$SCRATCH/ci-repro" && cargo fmt -- --check)                # 0 diffs = your commit is clean
git worktree remove --force "$SCRATCH/ci-repro"
```

Run the **verbatim** command from the workflow, not a paraphrase. A gate that is
`cargo fmt -- --check && (cd docs && cargo fmt -- --check)` has a second leg that a
single-invocation substitute never exercises, and the second leg is a common failure site
precisely because the first one is the one you remember.

Two failure shapes this separates:

| Symptom | Reading |
|---|---|
| diffs in **files you committed** | real regression in your change — fix and re-push |
| diffs only in **untracked / other-agent files** | your commit is fine; the failure came from a different commit on the branch — find which with `git worktree add` + the same command |

Note the second row is still your problem to route: the offending commit is on the PR
branch even though the file was never yours, so locate it with
`git log --format='%h %s' origin/master..HEAD` and fix at that commit.

**Scope the same way when a rust-standards script reports a whole-repo total.**
`audit_rust_standards.py` walks the entire tree, so in a shared worktree its
summary line mixes your files with a colleague's uncommitted work. The split that
separates them is the per-check detail, not the summary:

```bash
python3 ~/.agents/skills/rust-standards/scripts/audit_rust_standards.py . 2>&1 \
  | grep -A 4 '^FAIL'          # the detail lines carry full paths
```

Capture the baseline BEFORE your first edit — a FAIL that is already there is
debt, and a FAIL that appears afterwards is a regression. Then confirm your own
scope directly, since the detail list truncates at 5 hits per check:

```bash
for s in verify_keyword_file_purity verify_doc_comment_format \
         verify_let_type_annotations verify_closure_type_annotations \
         verify_no_self_field_access verify_hardcoded_strings; do
  python3 ~/.agents/skills/rust-standards/scripts/$s.py "$PWD" 2>&1 \
    | grep -E "<your-crate>/src|<your-crate>/tests"    # any hit here is yours
done
```

**Two script outputs read as failure when the run is actually clean.**
`fix_dep_order.py` prints `Nothing to do (no Cargo.toml found)` both when it
found manifests needing no rewrite and when it found none — check the count
before believing it:

```bash
python3 ~/.agents/skills/rust-standards/scripts/verify_dep_order.py "$PWD"   # authoritative
```

Likewise `cargo fmt --all --check` reports every file in the tree. A
`rustfmt --check --edition 2024 <your files>` run over just your paths is the
scoped answer, and it is the one to report when the repo-wide number is
inflated by another agent.

**A hook that blocks on a new-file test fixture is the same shape.** When
`rust_pre_commit.py` fails on structural rules (`use super::*` in every member file,
features arrays unsorted) that no version bump could cause, count how many iterations the
auto-fixer ran before you conclude anything. Three iterations without convergence means
the debt is structural and out of scope for your commit — record it as follow-up per §1 and
bypass only that audit phase, never with a blanket skip of fmt/clippy/test.

## 6. Release bumps: confirm the version is unpublished first

Bumping "the next patch" is wrong when the previous patch already shipped. **Check the
registry, not just the manifest** — CI's publish job runs on the base merge, so a merged
PR's version is often already live:

```bash
for c in <crate> <crate>-ui <crate>-core <crate>-cli; do
  printf "%-12s crates.io: " "$c"
  curl -s -H 'User-Agent: check' https://crates.io/api/v1/crates/$c \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['crate']['max_stable_version'])"
done
```

Also check whether a `v<version>` tag already exists on the remote. If the manifest says
`0.28.1` and crates.io says `0.28.1`, the next bump is `0.28.2`, not `0.28.1` again.
See `euv-standards` §2 for the root-manifest-only bump rule.

**This is the hook working.** It reports only violations *this commit*
introduces; legacy debt never blocks. Fix the code, never bypass — §3.6 of
`git-standards` forbids `--no-verify` in your own repos.

Two failures recur, and both are real rule violations, not obstacles to route
around:

- **A new test file trips §14.5 (no comments in test files) and §1.4
  (keyword filenames).** A descriptively-named `some_topic.rs` is both. Look
  at the sibling test directories first — when each holds a single `fn.rs`,
  the convention is one test file per directory and yours is a second
  `mod.rs` entry that will be rejected. Merge the cases into the existing
  `fn.rs`; that clears both rules at once and loses nothing.
- **A commit body over 72 columns** is caught by
  `verify_english_only.py`. Re-wrap it; do not shorten the substance.

Run `staged_file_gate.py` directly before committing so a rejection is a
30-second fix rather than a failed commit — and when one does come back,
classify it with §1a before touching source.

## 7. Report state honestly

- Verify external effects by reading them back (remote ref, PR state, deployed bytes) — a
  successful command is not a successful task.
- When a check is scoped to your files but the repo has legacy debt, say so explicitly
  ("new code: 0 violations; N pre-existing elsewhere") rather than implying a clean
  repo-wide result.
- When a requested item cannot be done because its referent does not exist, **search
  thoroughly, then ask with the specific paths you searched** — and complete every other
  part of the request while waiting. Do not guess at a format and build the wrong thing,
  and do not silently drop the item.
- Before pushing, run all three of §3a and stop if the pending commit is not yours. State
  plainly when the tree holds edits you did not make, and how many.
- When the user asks for a step already completed in this session, say so with the sha and
  the verification, rather than re-running it or implying there is work outstanding.

### Standing preference: decide, then report

This user asks for autonomous execution: state the requirement, then carry it out under
the written standards without checking in at each decision point. Concretely —

- **When a rule in these skills already resolves the question, apply it and report the
  decision.** Pre-existing violations in a file you did not touch, a stash-free baseline
  check, reusing an open PR, picking the higher side of a version conflict: each has a
  documented answer, so use it and state what you chose in the report.
- **Do not ask permission to fix a defect your own change introduced.** A format violation
  in a line you wrote is yours to fix and re-push, not a question.
- **Reserve escalation for what is genuinely irreversible or undecidable from the rules** —
  rewriting published history, discarding another author's work, a publish that cannot be
  undone, a requirement whose referent does not exist. Even then, complete every other
  part of the task first, and say plainly what you did not do.
- **A blocking question is itself a failure mode when the standard answers it.** Presenting
  "which of these?" where the skill names the right choice stalls work the user already
  delegated, and costs more than picking and disclosing.
