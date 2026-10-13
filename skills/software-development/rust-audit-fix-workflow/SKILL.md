---
name: rust-audit-fix-workflow
description: 'Use when fixing rust-standards audit violations.'
metadata:
  hermes:
    tags:
      - rust
      - audit
      - cleanup
    related_skills:
      - rust-standards
---

# Drive a repo to rust-standards audit-clean

`rust-standards` is the spec — what each rule means. This skill is the workflow — the order, the commands, and the discipline that gets a repo from "audit fails" to "audit passes" without breaking the build or burning context on verifier quirks.

## When to load

- User: "修复所有不符合要求的代码" / "pass rust-standards strictly" / "audit-clean this"
- After a fresh clone of any eastspire/.agents repo (`hyperlane`, `euv`, `ctares`) whose audit is not 35/35
- When a slice finishes and the next violation count is reported

Do NOT load to *read* the audit rules — load `rust-standards` for that. This skill is for *applying* it.

## Reference files

- `references/let-type-annotation-harvest.md` — the explicit-type-on-`let` rule at scale: harvest real types from `rustc` one site at a time, the four ways that harvest silently under-reports, and the closure / generic-parameter / call-then-move shapes the compiler cannot answer for.
- `references/audit-counts-masking-and-splitting.md` — reading the audit's counts when a fix unmasks hidden rules (hit count rises while the pass total rises), splitting follow-up work by file across parallel children (by crate in a Cargo workspace, including visibility-reduction sweeps), and the doc-comment verifier's return-type parsing limit.

## Work in the project root, not a worktree

The user has explicitly corrected this. Worktrees created in `.worktrees/audit-fix/` got pruned mid-session and the work was lost. The user's standing preference for this class of task:

- Commit directly on `master` (or the branch the user is on) — the user's review is the same regardless of branch
- Scope each commit to one violation class (`Vec<_>` → `Vec<&T>`, `closure type annotations`, `Cargo.toml dep order`, etc.)
- Commit before any refactor that touches more than ~5 files; never let uncommitted work accumulate across an audit slice

`git worktree add .worktrees/...` is wrong for this task. `git switch -c audit/fix-...` on a worktree is also wrong. Just commit on the branch you started on.

If the user *does* want a branch for review (e.g. PR-style review against `master`), they will say so — wait for that instruction, don't assume.

### The carve-out: a shared upstream repo is not your workspace

Direct-commit-on-`master` applies to a repo you own and work in. It is
**wrong** when the target is a shared upstream (`euv-dev/euv`,
`crates-dev/*`, `hyperlane-dev/*`) where `eastspire` is admin but not the
sole author. There the audit sweep is a **code change**, so it takes the
PR route: branch off clean `origin/<default>`, commit only your own paths,
push to upstream, open a PR, stop at green. See
`gh-pr-creation-workflow` for the mechanics.

**Tell:** `git remote -v` shows an org other than your personal namespace,
and `gh api repos/<o>/<r> --jq .permissions.admin` is true while other
authors exist. Committed straight to `master` there is a review bypass,
not a preference.

## A rule that lands with real violations is a two-phase job — fix them, per repo, in parallel

Adding a check to the skill is only half the deliverable. The user's standing
expectation for the moment a new rule reports non-zero on real repos is:
**sweep the real violations, one dispatched agent per repo, then open a PR
per repo.** Reporting the count and stopping is the incomplete half.

Before dispatching, the parent runs one measurement pass and folds the result
into each agent's brief:

```bash
# 1. per-repo violation inventory for the NEW check
python3 <skill>/scripts/verify_<rule>.py ~/code/<repo>          # exit 1 + the real list
# 2. which OTHER checks already fail there = legacy debt the agent must NOT chase
python3 <skill>/scripts/audit_rust_standards.py ~/code/<repo> | grep '^FAIL:'
# 3. how much uncommitted work is already in that tree
git -C ~/code/<repo> status --porcelain | wc -l
```

Each of those three answers a question the agent cannot answer for itself and
will otherwise get wrong:

| Measurement | Goes into the brief as |
|---|---|
| the new check's exact findings | the literal target list — "expected N dirs, run this command to see them" |
| the other failing checks | an explicit scope carve-out — "checks 31,32,35,37 are legacy debt on files you are not touching; report them, do not fix them" |
| the dirty-file count | a staging rule — "stage only `<paths>`; before committing, `git status --short` must show nothing unrelated staged" |

The third matters most. A repo whose working tree already carries someone
else's uncommitted edits — including, on a layout refactor, an edit to the
exact file being moved — will have them swept into the agent's commit by any
`git add -A` or `git add <dir>/`. Baseline the dirty set in the brief and
require the agent to re-read `git status --short` before committing.

### A shared worktree changes the plan, not just the staging rule

When another agent is live in the same checkout, an audit sweep has a second
party who can rewrite the numbers under you. The tells are cheap and one of
them is decisive:

| Tell | Reading |
|---|---|
| the new check's violation count **drops** while you have edited nothing | another agent is fixing the same rule — stop writing, back up, wait |
| `git status --short` grows files unrelated to your task | someone else's scope, must stay unstaged |
| `.rs` mtimes advance while you poll | still writing; a quiet window is not proof they stopped |
| `cargo check` errors appear in files you never opened | they are mid-edit; a stale failure, not your regression |

**Stop writing and take a backup the moment the count moves on its own.** A
`git diff > backup.patch` plus a copy of the tree costs seconds and is the only
thing standing between you and a lost afternoon. Then re-verify every gate after
their edits land — a `cargo check` that passed against your tree may have been
run against a file that has since changed underneath you, so touch the file
(`touch <file>`) to force a rebuild rather than trusting an incremental cache.

**Never reconcile a shared worktree with a worktree-wide git command.**
`git reset --hard origin/<default>` after a merge looks like routine cleanup and
destroys every uncommitted file the other agent has. Use
`git merge --ff-only origin/<default>`, which moves HEAD and leaves the tree
alone. If a `reset --hard` has already run, recover from the object database
(`git stash list`, `git reflog`, `git fsck --lost-found`, then
`git checkout <stash-sha> -- <paths>`) and tell the user what you reconstructed —
see `delegating-and-verifying-verifier-script-work` §4.4.

Dispatch one agent per repo (not one agent for all repos): the trees are
independent, the gates differ per repo, and a shared agent serialises two CI
waits behind each other. Put the per-repo numbers in the brief rather than
making each agent rediscover them, and require each to read back the PR URL
with `gh pr view` before reporting it.

### A dispatched child holds your standing instructions for its whole run

The child acts for as long as it runs, which includes the window you spend
deciding whether to authorise the irreversible step. It merged nothing
"against orders" — it followed an instruction that was still in force.

**Audit every flag in the brief against the command you actually mean.**
`--delete-branch` exists on both `gh pr create` and `gh pr merge`; writing it
into a create instruction leaves merge semantics sitting in a brief you were
reading as "just open the PR". Same family: `--admin`, `--auto`, `--force`.
If a flag's effect is realised *after* you stop looking, it converts a
pending decision into a completed one.

So: scope the child to the reversible step, and put the prohibition in the
same breath as the permission — "push the branch and open the PR; do **not**
merge" — where the child reads it as part of the task rather than inferring
where the task ends. Never write "open the PR" next to a flag that deletes
the branch.

**A merge is not undoable, and on a release pipeline it is not quiet.** The
merge commit triggers the default-branch workflow, and a publish job moves
dozens of artifacts to a public registry within minutes. When a child has
crossed that line, establish the facts before reporting them —
`gh pr view N --json mergedAt,mergedBy,mergeCommit`, then the runs it
triggered and which are still `in_progress` — because "which crates are
already out, and can it be stopped" is the user's first question and it is
answered by those two commands. Report the instruction that made the
boundary reachable alongside the outcome; that is the part that generalises.
And cancelling a half-finished publish is a decision the user makes, not a
cleanup you perform unasked.

**The brief carries your environment, because the agent cannot see it.** A
dispatched agent inherits a sandbox whose env and config you cannot inspect,
so every assumption you hold silently becomes theirs — and each one produces a
mid-task hard stop instead of a wrong-but-plausible result:

| Put in the brief | Otherwise |
|---|---|
| which CLI is authenticated, and that re-authenticating is not needed | agent runs `gh auth login`, or a hand-assembled token that 401s |
| the repo's real push route (`admin:true` + `fork:false` → push to upstream, unqualified `--head <branch>`) | agent forks a repo that must not be forked |
| the exact CI job names the PR must go green on | agent reports "CI pending" on an invented job list |
| read the PR URL back with `gh pr view` before reporting it | agent echoes the URL its own command printed |
| the repo's dirty-file count, and re-read `git status --short` before committing | `git add -A` sweeps a prior session's work into the commit |
| authority stops at the reversible step — "push and open the PR; do NOT merge, I decide that after reviewing" | the child merges while you are still deciding, and CI proceeds to publish |

Establish the working auth path yourself before dispatching, in this order:
`gh auth status` → `gh api repos/<o>/<r> --jq '.permissions, .fork'`. A 401
from a hand-assembled token says nothing about your access — `gh` reads its
credential from the keyring and works with no `GH_TOKEN` in the environment at
all, so a stale credential must never be what decides the route.

## Procedure (one violation class at a time)

For each failing check in `audit_rust_standards.py`:

1. **Inventory the violation set, not just the count.** The `N hits` number is unreliable: verifier scripts sometimes crash mid-run and the Python Traceback gets piped to stdout, inflating the count. Run the verifier directly (`python3 <skill>/scripts/verify_<rule>.py .`) to see the real violation list, then cross-check the audit's count.
2. **Read at least 5 sample violations before patching in bulk.** Many checks share root causes — `let statements = multi_X.X_values.iter().map(|x| { ... })` repeats across the macros crate with the same type signature. One patch handles 12 lines.
3. **Dry-run, write, audit, commit — in that order, every slice.** Never combine two violation classes in one commit. If the bulk fix breaks something, `git reset HEAD~1` and patch surgically.
4. **Run the completion command, not a hand-rolled gate list.** The spec's single completion condition is now one script — it runs the fixers, the full audit, `crate fmt` twice, clippy, and a test compile:

   ```bash
   python3 <skill>/scripts/rust_pre_commit.py <repo>
   ```

   Only `PASS — all phases clean` / exit 0 counts. The previous manual list (`audit_rust_standards.py` then `cargo check` then `clippy` then `crate fmt`) is now *insufficient on its own* — see the two-gate section below, because `rust_pre_commit.py` exiting 0 still does not mean the commit will be accepted.
5. **Commit with a message that names the rule + §X.X.** Future sessions read commit messages when fixing similar violations.

## Count and locate violations from the source, not from the audit's sample

The audit prints a few sample findings per check but reports the full hit count,
so a file distribution derived from the printed lines is wrong. Count with the
verifier's own patterns in the source instead:

```bash
grep -rc 'PATTERN' --include='*.rs' . | grep -v ':0$'
```

Re-run the audit before stating a count in a summary, commit message or report —
a number quoted in chat and then repeated often traces back to a truncated tool
result, and a stale count is the one error the reader cannot detect. When a fix
reveals previously masked rules, or the work is being split across children, read
`references/audit-counts-masking-and-splitting.md`.

## The audit is blind to uncommitted work, and its line numbers move

Four failure modes that all present as "my fix did nothing". Establish which one
you are looking at before changing any source.

**1. Most checks read `git diff origin/master HEAD` — committed state only.**
A fix sitting in the working tree does not lower the count, so a correct edit and
a no-op edit look identical. Compare the two diffs:

```bash
git diff origin/master HEAD -- <file> | grep -c '<pattern>'   # what the audit sees
git diff origin/master     -- <file> | grep -c '<pattern>'    # what you changed
```

Non-zero on the first and zero on the second means fixed-but-uncommitted. The two
check classes also have different remedies: a **walk-based** check sees the tree,
so re-running after an edit is enough; a **diff-based** check only ever sees
`HEAD`, so only a commit or that manual comparison tells you the truth. Read the
command in the audit script to tell them apart.

Report the stale finding as stale, with both counts. **Do not commit in order to
move the number** — a commit made so a counter drops puts unverified code on the
branch, and the gates that matter (fmt, clippy, test) are independent of the
counter. Run the gates, commit, re-audit; a finding that survives into a committed
state is a real one.

**2. Hunk coordinates expire the moment you move a file.** A check reporting
`file:line` locates violations *through the diff*, so a `git mv` anywhere in the
tree shifts the hunks and the same check starts pointing at unrelated code — the
five blank lines you just fixed in one file reappear as five blank lines in a file
you never opened. Treat every coordinate from a previous run as expired: re-read
the audit's detail lines after each structural edit, and re-verify each site by
content rather than by the number the audit gave it.

**3. A check naming a file wants the sibling convention, not an invention.** When
a check reports a non-keyword or mis-shaped filename, read what the peers already
use before choosing a replacement:

```bash
for d in <parent>/*/; do ls "$d"; done     # the majority spelling
```

Renaming to what the sibling directories already do is reviewable and leaves one
dialect; a freshly invented name is a second one, and the next audit will want to
rename it again. The same applies to a `r#` prefix — it is only legal on keyword
filenames, so a semantic directory carrying one is being reported for a reason.

**4. The other writer can commit underneath you and retire your baseline.** The
tells above cover a moving count and advancing mtimes. Add the one that ends the
session's work: `git status --porcelain | wc -l` falling to 0 while you are still
writing, and `git log` showing commits you did not make. Your edits are now inside
someone else's commit, their `git add -A` decided your staged scope, and every
gate you ran beforehand was measured against a different `HEAD`. Re-run all four
gates afterwards, and check whether their commits touched your files before
reporting a diffstat or a violation count that predates them.

## Every finding gets exactly one of two endings — decide which, per finding

The user's correction when an audit slice stalls: **if it is a script problem,
fix the script; if it is a real violation, fix the repo.** Offering a third
option — "here are the counts, where would you like me to start" — is the
failure, and it recurs because deferring a whole-repo finding looks like caution
while actually being an unanswered question presented as a conclusion.

Decide per finding, and the decision procedure is mechanical:

```
is the wrapper's detail line a file:line, or a banner/summary/traceback?
├── banner / summary / traceback   -> the WRAPPER is buggy  -> fix the script
└── file:line
    ├── is it diff-scoped, and is the line one you touched?
    │   └── yes -> real violation -> fix the repo
    └── is it whole-repo?
        ├── compiler proves no legal annotated form -> fix the script (exemption)
        └── otherwise                             -> real violation -> fix the repo
```

Two rules make this hold up. **Never let "the script is buggy" become the default
reading** — a wrapper filter, a mis-scoped regex and a genuinely unfixable grammar
slot all present as a finding, and the first two are rarer than the third. **And
never batch a whole check into one verdict without reading its findings** — one
check routinely contains both a stale wrapper line and real source violations,
and the honest report separates them rather than picking the cheaper label for the
whole check.

A fix to the script is itself a real deliverable: the skill repo gets the change
in its own commit, with the verifier, any gate that calls it, and the spec text
moved together. A fix to the repo touches only the user's checkout.

## A failing test you did not cause is a decision, not a footnote

The instinct to present a failure you cannot attribute to your change as a
pre-existing note is right about the attribution and wrong about the deliverable.
Attribute it properly first, then hand the choice back.

**Attribution — three commands, in this order.** A test that fails in CI but not
locally, or fails only in parallel, is usually neither yours nor flaky:

```bash
git log -S '<the global or symbol>' -- <file>          # who introduced it
git show HEAD:<file> | grep '<symbol>'                  # is it already there
git diff HEAD --stat -- <dir>                          # did you touch that dir
```

`git log -S` empty and `git show` already containing it, while your diff for that
directory is empty, is a complete proof that it predates you. Anything less is an
attribution you have not earned.

**Then measure the failure rate, because "passes on my machine" is not a
finding.** Run the compiled test binary in a loop rather than re-invoking `cargo
test` — a rate is the deliverable, and a single green run proves nothing:

```bash
BIN=$(ls -t target/debug/deps/<name>-* | grep -v '\.d$' | head -1)
for i in $(seq 200); do "$BIN" --test-threads=8 >/dev/null 2>&1 || echo "fail $i"; done
```

Sweep `--test-threads` 1 / 8 / 16 / 32. Two readings matter: a rate that is
non-zero only above one thread count is shared state, not a race in the code under
test; a rate that holds at 1 is a plain logic bug and the parallel reading is
irrelevant. Time the runs too — a loop that hangs is reporting a deadlock, and a
hang at `--test-threads=1` rules out concurrency as the cause.

**Isolate to one module before theorising.** `binary --test-threads=8 <module>::`
per module, then `--nocapture` to see the last test that started. The module that
fails alone names the culprit; the module that passes alone is exonerated, and
attributing a shared-global failure to whichever test you happened to read last is
the expensive mistake.

**The deliverable is a fix, in the layer that owns the bug.** A global shared by
parallel tests is a test-isolation defect: serialise the tests that touch it, and
keep the lock held across each test's whole body (a fixture that acquires and
returns a guard, bound to a live binding — a bare `_` drops immediately and the
lock protects nothing). A `static mut` reached from a worker thread is a real
concurrency bug in production code, and it moves to `thread_local` + `RefCell`.
`--test-threads=1` is not a fix for either; it converts a real defect into a slower
test run and hides the next one.

Report the measured before/after rates and say which layer you changed. If the
defect sits in production code and fixing it is out of scope, that is a scope call
for the user, not a silent carry-forward — state the rate you measured and the
fix you did not apply.

## Some checks are unfixable by construction — classify before you bulk-patch

A verifier that scans source text also scans `macro_rules!` matcher syntax and
proc-macro template bodies, and reports tokens that have no legal annotated form:

| Reported | Actually | Fixable? |
|---|---|---|
| `closure parameter without explicit type annotation` on `$( $arg:ident $(: $ty:ty)? )` | `macro_rules!` matcher | **no** — `*` and `$()` are not closure params |
| `hardcoded string` on a literal inside a macro body | the template text | only by editing the macro's own `const.rs` |
| `let` without type annotation on `let mut map = HashMap::new();` inside a macro arm | template text | **yes** — delete the `let`, build from `From<[(K, V); N]>` |

Tell: the reported "violation" is a fragment of matcher syntax (`$(`, `*`, `$arg:ident`),
or a line whose operators belong to a **different language** (a WGSL shader or
template carried inside an `r#"…"#` string literal), not a Rust expression.
Classify the whole check before patching — a check reported as
several hundred hits may be zero real violations, and the honest answer is a
verifier scope bug, not a source edit that fights the language. All four
classes, with the four-probe exemption discipline each one needs, are in
[references/verifier-scope-bugs.md](references/verifier-scope-bugs.md).

**Classify every hit by category before touching source, and read the source
line — not just the verifier message.** Print the offending line next to each
finding and bucket them (`DOC-COMMENT` / `MACRO-RULE` / `REAL-CODE`). When a
batch is dominated by doc-comment examples, the answer is a scoped exemption,
not a sweep: hoisting `///     name: "test".to_string(),` into a `const.rs`
turns working documentation into nonsense, and a bulk regex over it will do it
to all 56 occurrences without complaint.

**Prove each "cannot be fixed" claim with the compiler before reporting it.**
Write the minimal program and confirm rustc rejects the hoisted form — a
finding filed as a genuine, easily-fixable violation has twice turned out to be
a grammar slot. `cfg!(target_os = "windows")` looks exactly like a §1.3c
hardcoded string and is not one; `cargo build` on `cfg!(target_os = CONST)`
returns `error: expected a literal, found expression`. Asserting "this one is
fixable" would have shipped a build break.

**A batch where the real-code bucket is empty has no source fix at all.** In
one sweep, 76 of 84 findings were doc examples and macro matchers, 7 were
grammar-slot or macro-expansion cases, and 1 was an untracked local scratch
file (`git ls-files <dir>` empty = not shipped code). When the real-code bucket
comes back empty, the only honest deliverable is the exemption — say that, with
the counts, instead of starting a sweep that can only do damage.

### A string literal in a grammar position is not a hardcoded string

The second unfixable class is subtler than macro fragments: the literal sits in a
**syntax slot**, where the grammar admits a keyword-like string and no expression.
§1.3c hoists program data to `const.rs`; an ABI name is not program data, it is part
of the item's shape.

| Reported | Actually | Fixable? |
|---|---|---|
| `hardcoded string` on `extern "system"` / `extern "C"` / `extern "C-unwind"` | foreign-ABI grammar slot | **no** — there is no expression position to hoist to |
| `hardcoded string` on `cfg!(target_os = "windows")` | `cfg!` predicate slot | **no** — `cfg!(target_os = CONST)` is `error: expected a literal` |
| `hardcoded string` on a literal inside a `///` doc example | documentation, not code | **no** — hoisting it breaks the example |
| `hardcoded string` on an `assert!` / `format!` / `panic!` / `write!` message | **format-string slot** | **no** — the grammar requires a literal, see below |

The format-string slot is the one that recurs, because every assertion with a
message produces one, so a test-heavy slice reports a residue that grows with
the feature. Rust requires the format string to be a *literal*; `const MSG: &str
= "..."` in the first position is `error: format argument must be a string
literal`. So for a test asserting with interpolated values there is no
compliant spelling, and the honest deliverable is the message hoisted as far as
it can go — a `const` for the static prefix, with the interpolations left in
place:

```rust
// reported, and the best available form
assert!(cond, "{} must be {}", NAME, LIMIT);              // literal msg required
assert!(cond, "{}", consts::WALK_ROUTE_SUMMARY);          // no interpolation
```

Report the residue as a count with the reason in the commit message rather than
rewriting the assertions until the checker is quiet, and never convert a
dynamic message into a static one that stops naming the offending value — that
trades a verifier finding for a test that can no longer be diagnosed from its
failure output.

A macro arm's untyped `let` looks like the same grammar-slot case and is not —
see "A macro arm's collector is fixable, and `_` is not the answer" below.

The compiler is the proof, and it costs one file to check:

```rust
const ABI: &str = "system";
extern ABI { }   // error: expected `fn`, found `ABI`
```

`extern <expr>` is not valid Rust, so the extraction the rule demands cannot
compile. The check is wrong, not the source.

### A macro arm's collector is fixable, and `_` is not the answer

A macro arm that accumulates into a collection — `let mut map = HashMap::new();
$( map.insert($key, $val); )*` — reads like the grammar-slot case: the element
types are only known after expansion, so there is no type to write down. **It is
not the same case, and "the types are unknown" is not the reason it is unfixable.**

Annotating with a placeholder compiles and satisfies the verifier:

```rust
let mut map: HashMap<_, _> = HashMap::new();   // builds, verifier accepts — still wrong
```

It is wrong because the rule exists so the reader does not have to jump to the
RHS to learn a type, and `HashMap<_, _>` leaves the type exactly as unresolved
as before while adding a placeholder that hides it. **Reaching for `_` is
recognising the wrong signal: the `let` is what should go, not the type.**

Delete the binding and construct the collection in one step, via
`From<[(K, V); N]>`:

```rust
// WRONG — placeholder, same reader problem, more code
let mut map: std::collections::HashMap<_, _> = std::collections::HashMap::new();
$( map.insert($key, $val); )*
map

// RIGHT — no binding, no annotation, no placeholder, callers unchanged
std::collections::HashMap::from([$(($key, $val)),*])
```

The same shape covers `HashSet::from([$($elem),*])`,
`LinkedList::from([$($elem),*])`, `BTreeMap::from([...])`, and
`BTreeSet::from([...])`. Semantics match the old `insert` loop, including
last-write-wins on a duplicate key. **Test the empty-collection arm separately**:
`($($e:expr),*)` with zero arguments gives `from([])`, whose type is
unconstrained, so that arm usually still needs `::new()` — the macro's existing
`()` arm already provides it.

**Rule: `let mut x: C<_, _> = C::new()` is a signal to delete the `let`, not a
license to keep a placeholder.** When a finding looks unfixable because the type
"is only known at expansion", first ask whether the construct needs a binding at
all — most collectors exist only to be filled and returned, and the std `From`
impl removes the binding, the annotation, and the inference question together.

### A gitignored path is not source

A verifier that walks the filesystem picks up scratch trees a maintainer never
ships. A crate whose `.gitignore` has `/tmp/` accumulated 25 scratch crates
from local tool runs; scanning them produced findings in files that no commit
can contain, and every one of them is unfixable in the only sense that matters
— you cannot fix a file that will never exist in the repo.

**Rule: before classifying a finding, ask whether the path is tracked.**

```bash
git ls-files <path>            # empty  = not shipped, not a source finding
git check-ignore -v <path>     # names the rule that excludes it
```

Filter them in the walker, not by hand, so the count is right for every run and
every repo that shares the script. One batched query beats one call per file:

```python
r = subprocess.run(["git", "-C", str(root), "check-ignore", "--stdin"],
                   input="\n".join(rels) + "\n", capture_output=True, text=True)
ignored = {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}
```

`check-ignore` exits 0 when it matched something and 1 when nothing matched, so
both are success for this caller; any other exit, a non-work-tree root, or a
`git` that is not on PATH should return the full list unchanged rather than
silently reporting zero violations. **Scripts that each carry their own copy of
the file walker must each get the filter** — fixing one leaves the others
reporting the phantom directory.

**Anchor the exemption on the keyword, and scope it to the span — never the
line.** Two failure modes, and the first one is easy to walk into:

- *Anchoring on the literal* (`"system"`) misses `"C"` and `"C-unwind"` and
  teaches the rule as a string allowlist. Match the construct instead
  (`EXTERN_ABI_LINE`, allowing `pub` / `pub(crate)` / `pub(in path)` /
  `unsafe`), so `let t: &str = "extern-mod-table";` and `("extern", 1)` still
  report.
- *Anchoring on the line* (`if matches_extern_line(line): continue`) is worse:
  it drops **every other literal on that line**. A one-line
  `extern "C" fn f() -> &'static str { "/home/u/.ssh/id_ed25519" }` then passes
  clean, and one line of `#![rustfmt::skip]` keeps it on one line while still
  satisfying `cargo fmt --check` — so neither the format gate nor the
  staged-file gate sees it. Capture the ABI literal as a **named group** and
  exclude only that span in the literal loop.

The span fix has its own trap: a quote-pairing regex re-entered at the exempt
literal's **closing** quote pairs with the next quote in the line, swallowing
the code between them into one bogus match and potentially missing a real
literal inside that run. Restart the scan *past* the span
(`STRING_LITERAL.finditer(line, abi_end)`) rather than skipping the span and
rescanning from zero.

**Prove an exemption with an attack, not a fixture.** A fixture shows the happy
path; only a deliberately malicious input shows the hole is closed. For each
exempt category build the widest single-line form that still parses and assert
the payload is reported. A related trap: a loose comment match `^\s*//` also
exempts plain `//` comments, so `// TODO: hoist "/home/u/.ssh/id_ed25519"` passes
clean — restrict to `^\s*//[/!]`, the forms that cannot be code.

**Measure the blast radius before shipping an exemption.** It is global across
every repo running that verifier, so diff the counts on all of them and report
them (`euv 3819 → 3398`, `hyperlane 466 → 246`). A large silent drop changes
every baseline and any gate keyed to a violation count.

**A block-scoped exemption is proved by a triad, not a fixture — and the
after-close probe is the one that finds the bug.** A whole-block exemption
(inside `class! { .. }`, `vars! { .. }`, or any other declarative macro whose
literals *are* the payload rather than incidental program data) is implemented
by tracking brace depth and re-arming on every opener. Two failure modes, one
of them silent:

```python
# WRONG — exempts to end of file; the block's real tail becomes a blind spot
if path.name == "const.rs" or path.parts[:2] == ("ui", "style"):
    return []
```

| Probe | Expected | Catches |
|---|---|---|
| literal **inside** the block | 0 | the exemption does nothing |
| literal **outside** the block | +1 | a filename/path exemption that is too wide |
| literal **after the block closes** | +1 | depth tracking that never terminates |

The third is the one a single-block fixture misses, because the test file ends
before the bug can express itself. Anchor the exemption on the *macro keyword
plus brace depth*, and write the docstring so the next session can tell the
`vars!` case from the `extern "C"` case (span-level, above) — a payload-whole
block exempts on lines, an in-code token exempts on a span.

**A whole-repo check is binary, so a large reduction does not move the score.**
`SUMMARY: 40/45` stays `40/45` when a check's findings go 3160 → 1437, because
the check records FAIL for any N > 0. Reporting only the unchanged score reads
as "the exemption did nothing"; report the violation count and the score
together, and say explicitly that the score cannot move until the residue
reaches zero. A count that falls but never reaches zero has also not converted
a FAIL into a PASS — the slice is not complete, and the remaining count is the
next slice's real scope.

### Two responses to a verifier bug — pick by what the user asked for

A false positive has two valid endings and they are not interchangeable:

- **Report and move on** — right when the finding is a macro fragment you cannot
  classify with certainty, and the fix is out of scope. Note it in the commit.
- **Fix the verifier, the gate, and the doc** — right when the user asks for the
  exemption, or when the false positive blocks the task's completion condition.

The second is a real deliverable, not a footnote: the exempting script, any
staged-file gate that runs it, and the skill's own script table all ship
together in the skill repo, in their own commit, with the user's repo untouched.
A verifier the hook never calls is a hole in the hook's coverage — when you add
an exemption, check whether the commit gate's verifier list includes that script
and register it if not.

**Proof obligations before you call it fixed.** Both fixtures, in the skill repo,
with the baseline captured first:

- *compliant* — the exempt construct in every legal shape → 0 violations, exit 0.
  Capture what it reported **before** the patch: a compliant fixture that never
  failed proves nothing about the fix.
- *violating* — decoys that must still be caught → N real violations, exit 1.
  Audit your own fixture for over-broad exemption: a magic byte literal sitting
  in a function body is a genuine §1.3c hit and belongs in the *violating*
  fixture. An exemption that swallows real violations is worse than the bug.

Then run the aggregate wrapper and reconcile: the audit's hit count must equal the
verifier's violation count, not exceed it by one.

## A `git checkout -- <dir>` revert is too coarse to undo one bad bulk edit

A repo-wide regex that should have touched four files also rewrote a macro crate's
debug sandbox. Reverting with `git checkout -- <macro-crate>/` restored the sandbox but
**also silently discarded three legitimate fixes made earlier in the same directory.**

Revert the file, not the tree, and re-apply what the coarse revert destroyed:

```bash
git diff --stat                     # what the bulk edit actually touched
git checkout -- <path/to/one-file>  # narrowest revert that fixes it
```

Before scoping a repo-wide edit, enumerate what the pattern will match and check each
hit is a file you meant to change — a macro crate's `debug/` sandbox, a vendored tree, or
a fixtures directory is a common unintended target.

### A bulk replace that also rewrites the definition it was meant to skip

Pattern-rewriting N call sites of a helper is where the subtle version of that lives.
A replace scoped to the helper's **name** also matches the helper's own **body**, so
after the sweep the helper calls itself:

```python
# 7 call sites rewritten — and so were the 3 fixture definitions
s = s.replace("I18n::new()", "fresh_i18n()")   # fresh_i18n() { fresh_i18n() }
```

It presents as a **hang**, not a compile error: the first N runs pass, then a run
deadlocks on a lock the recursive re-entry double-acquires, or the stack grows until
the process dies. Nothing in the compiler output points at the edit.

**Rule: rewrite call sites with a construct the definition cannot match.** A call site
has `name(`; the definition has `fn name(`. Match `(?:[^f]|^)name\(` or anchor on the
assignment (`= fresh_i18n(` / `: I18n = fresh_i18n(`), and assert the replacement count
equals the number of call sites you enumerated *before* writing. Re-read the
definition's full text after any bulk edit to a helper — not its first line.

`str.replace` counts are a weak guard on their own, because a wrong-but-plausible count
(7 instead of 4) still "succeeds"; printing the count alongside the expected one is what
makes the drift visible.

### A mutation test that times out leaves its payload in the tree

A verifier is proven by mutating the input. If each case re-runs the **full** audit
(~2 minutes), the loop exceeds the tool timeout — and the injected violation is still in
the file when the kernel dies.

**Rule: mutate, then restore in a `finally`, and keep each case cheap.** Run the
verifier script directly instead of the aggregate audit, which takes well under a
second; the aggregate is for the final confirmation, not for the case loop. On any
timeout or interrupt, assume the payload is still on disk and re-read the file's first
lines before doing anything else:

```bash
head -3 <mutated-file>          # is the injected comment still there?
git diff --stat <mutated-file>  # an unexpected diff means the restore never ran
```

The tell that the loop is too slow is the timeout itself: a verification step that
cannot fit in one tool call is a design problem, not a patience problem.

## Verify before patching the verifier, then audit, then the source

Three places a "FAIL" can come from, in order of frequency:

- **Verifier regex / scope bug** — e.g. check 23 reports "first non-comment line must be `use super::*;`" for every `mod.rs`, but §6.2's three-stage template requires `mod.rs` to start with `mod r#xxx;`. The skill's own verifier disagrees with its own spec on this point. **You cannot fix this from the repo** — flag it in the slice commit message ("verifier bug, see the spec sentence in <skill>/references/02-documentation.md") and move on. The skill's curator fixes it in the skill repo, not in the user's repo.
- **Spec conflict between two § rules** — e.g. §6.2 says `mod.rs` must end with `use super::*;`; clippy says it's `unused_imports` if no parent symbol is used. The fix is *remove* the trailing line for leaf mod.rs, contradicting the spec literally. Apply the spec where it doesn't break the compiler; document the carve-out in the commit message.
- **Real source violation** — fix in source.

### Sibling `struct.rs` + `impl.rs` forces `pub(super)` fields — `use super::*;` cannot fix it

When purity requires the `struct` in `struct.rs` and the inherent `impl` in a **sibling** `impl.rs` (both directions of §1.3a forbid the other), every private field the impl touches is **E0616 field is private**. Rust decides field visibility per *module*, and a sibling module is not a child of the defining module.

**`use super::*;` does not fix this** and chasing it is the expensive mistake: a glob only imports symbols the parent already `pub use`d, and it never lifts a sibling's private fields. Three-line reproduction:

```rust
// src/m/struct.rs        use super::*;   pub struct T { x: i64 }
// src/m/impl.rs          use super::*;   impl T { pub fn get(&self) -> i64 { self.x } }  // E0616
```

Fix is `pub(super) x` on the field: visible to every module in that directory, still invisible to the crate root and external crates, so the public API surface is unchanged. Use `pub(super)`, never `pub` — `pub` silently converts an internal field into semver-owed API.

Apply only to fields the impl actually reads. Struct-internal access (constructors, field declarations) keeps the bare name. Note this is orthogonal to the `self.field` ban: widening to `pub(super)` gets it to compile; the accessor-body-only rule still governs where `self.field` may appear.

## A gate that passes is not proof the code survived

A verifier that only detects **forbidden** declarations can never notice **missing** ones. `verify_keyword_file_purity.py` checks that `struct.rs` contains no `impl`; if a bulk edit, regex pass, or hand-rolled split script drops whole `impl` blocks from disk, that check reports clean, `cargo test` stays green (the tests call methods defined elsewhere), and `audit` prints 39/39 — while five types have silently lost their entire implementation.

**Tell:** a wide swath of `cannot find function` / `no method named get_*` errors, with **no file deleted**. That points at code that vanished from inside a file, not at a broken glob chain. Diagnose by structure count, not by compiler output:

```bash
for m in <module>; do printf "%-16s %s\n" "$m" "$(grep -c '^impl' $m/impl.rs)"; done
```

A count of 0 in a directory that has a `struct.rs` / `enum.rs` means the declaration is gone — restore it from git or rewrite it. Do **not** try to fix it by adding imports.

**The rule: after any mass-edit, regex rewrite, or hand-written fixer, `audit PASS` and `cargo build` / `cargo test` are two independent required pieces of evidence.** When restoring lost code, trust the structural count; a green build only proves what survived is self-consistent.

When audit reports a `use super::*;` "unused_imports" warning after you added the line to satisfy a check, **revert the addition immediately** — adding the import to silence a verifier while breaking `cargo check` is worse than no check at all. The user has corrected this directly.

## `use super::*;` is not a free fix

Two specific traps:

- **const.rs files** rarely use parent symbols — adding `use super::*;` triggers `unused_imports` warning. The right move is usually to NOT add it; the verifier flag is a false positive on a const-only file. If the build then fails on unresolved types (e.g. `Ipv4Addr`), the constants file *does* need the import — fix that by adding only the specific symbols via `pub use` in the parent mod.rs.
- **mod.rs files** — never add a leading `use super::*;` because §6.2 three-stage template requires `mod r#xxx;` first. If the verifier flags it, that's a verifier bug.

**Rule:** before adding `use super::*;` to make a verifier happy, run `cargo check -p <crate>` and verify the import isn't flagged as unused. If it is, the verifier flag is wrong on this file. Skip it, note the carve-out in the commit, move on.

When a verifier is genuinely buggy, record it where the next session will look for it — the commit message of the slice, and the skill repo's own pitfalls reference — with the reproducing input and the observed-vs-expected output. A bare "verifier is wrong" claim gets re-litigated every time.

## Verifier crash inflate hit counts

When a verifier Python script crashes (e.g. `verify_dep_order.py` has `return violations` indented inside a `for` loop, falls through to `None`, then `for v in None: ...` raises `TypeError`), the traceback goes to stdout. `audit_rust_standards.py`'s `run_check` does `len(out.splitlines())`, so the count includes traceback lines.

**Tell:** the audit report shows `check N: 135 hits` but only 5 distinct file:line violations are visible in the report.

**Mitigation:** run the verifier directly (`python3 <script> .`) and read its output. If the last 130 lines look like a traceback, subtract them from the count and you have the real violation total.

### A hit count exactly one too high is a wrapper filter, not a verifier bug

Crashes inflate counts by a *lot*; this inflates by exactly **one**, every single time, and only on the failing path. A check reporting one more hit than the verifier prints as violations is not miscounting the violations — it is counting a line that is not a violation. The audit splits subprocess **stdout** into lines and counts them, and verifiers print a summary line on every run (`N files checked, M violations`), not just on success.

A wrapper that strips the summary with a filter written as the literal zero-count form passes the clean case and leaks the failure case:

```bash
| grep -v -E '^[0-9]+ files checked, 0 violations$'   # leaks every real FAIL
| grep -v -E '^[0-9]+ files checked, [0-9]+ violations?$'
```

Anchor the filter on the summary's *shape* (`'^=== <rule-name>:'`) rather than on its current value, so a reworded summary can't reintroduce it. Filter a summary line on every count — and note the same rule covers the FAIL trailer, which must go to `>&2`.

**Rule: reconcile the numbers instead of reading them.** Compare the audit's hit count against the verifier's own violation count on a fixture, and treat any delta as a wrapper defect to fix. A check only ever observed passing looks correct forever, so a delta of 1 hides until the first real failure.

The same defect inverted — a filter that no longer matches its verifier's *banner*, so a check with zero real violations reports `1 hits` and FAIL — plus the whole wrapper-artifact family, is in [references/verifier-scope-bugs.md](references/verifier-scope-bugs.md) §1.

## Never run an auto-fixer unscoped

`rust_pre_commit.py` Phase 1 runs three fixers, and **all three are whole-repo rewriters, not per-file checkers**:

| fixer | default scope |
|---|---|
| `fix_dep_order.py` | every `Cargo.toml` under the root |
| `strictify_tests_layout.py` | every `tests/` tree under the root |
| `doc_comment_audit.py` | every tracked `.rs` (`git ls-files`) |

On a repo with legacy debt this rewrites files you never touched. The doc fixer alone can add thousands of lines across dozens of files in one invocation.

**Before running it:** `git status --porcelain | wc -l` to record the baseline dirty count. **After:** if the count jumped, `git checkout -- .` and re-apply only your own edits — do not try to selectively keep the fixer's output, because you cannot tell its intended changes from the damage.

The fixers accept `--files <paths...>` and the orchestrator passes the git change scope by default. If the run prints a whole-repo scope line, something about scope detection failed — treat that as a stop, not a warning.

## Classify every failing check's SCOPE before calling it debt

"Pre-existing / legacy debt" is a conclusion you earn by reading how the check
reads its input, not a label you attach to keep the number from moving. The
audit splits into two families and the difference decides whether a finding is
yours to fix:

| Family | Reads | Consequence |
|---|---|---|
| **diff-scoped** | `git diff origin/master HEAD` | carry-over lines are not blamed on you — a fix sitting uncommitted is invisible to it, and a hunk-coordinate edit can redirect it at unrelated files |
| **whole-repo** | a `verify_*.py` invoked with `{{target}}`, scanning the tree | **every hit is a real violation of the current tree**; "it was already there" is not a defence, and the deliverable is a fix or an explicit scope decision from the user |

Classify mechanically, from the audit source:

```python
import re, pathlib
src = pathlib.Path("<skills>/scripts/audit_rust_standards.py").read_text()
for name in re.findall(r"\('([^']+)',\s*'''", src):
    seg = src[src.find(f"('{name}', '''"):][:1200]
    kind = "DIFF-SCOPED" if "git diff" in seg and "origin/master" in seg else "whole-repo"
    print(f"{kind:12s} {name}")
```

**Probe the verifier the check actually registers, not a sibling whose name
matches the check's title.** The §5.1 checks are registered against
`verify_let_type_annotations.py`, and a separate
`verify_closure_type_annotations.py` exists one word away; running the closure
one returns a confident `0 violations` and reads as "this check is clean". Take
the script path from the wrapper text, not from the check's human-readable
name:

```python
m = re.search(r'verify_\w+\.py" "(\{\{\w+\}\})"', seg)   # the registered target
```

A `0` from a hand-picked verifier is a claim about the verifier you ran, not
about the check.

Roughly half of each. **Classify the scope before you report a single number**,
because the two families need opposite answers and the difference decides
whether the slice is even close to done:

| Family | Reads | Is a finding yours to fix? |
|---|---|---|
| diff-scoped | `git diff origin/master HEAD` | only the lines this change touched — carry-over is not blamed on you |
| whole-repo | a `verify_*.py` invoked with `{{target}}`, walking the tree | **every hit**, and "it was already there" is not a defence |

**The classification must precede the triage sentence.** Reaching for "master
既有欠债 / pre-existing legacy debt" before running the classifier is the single
most common wrong turn in this workflow, and it is wrong in the same direction
every time: it defers a whole-repo check's findings indefinitely, under a label
the user never granted. The deliverable for a whole-repo check is a fix or an
explicit scope decision handed back to the user — never a provenance note.

The same table tells you which findings can disappear on their own: a
whole-repo check counts down as you edit, while a diff-scoped one only
acknowledges committed work.

**When a finding is ambiguous between the two, the honest answer is to fix it
and say why, not to resolve the ambiguity in favour of deferring.** A change
you authored that leaves a failing check failing is a review finding regardless
of when the offending line was written.

## A bulk `let` annotation slice: harvest the types, do not infer them

§5.1 requires every `let` binding to carry an explicit type annotation, no fixer
ships for it, and a whole-repo verifier can report several hundred. The RHS is
usually a multi-line chain, so reading it and naming a type is a guess — and a
wrong guess costs a compile cycle per site across hundreds of sites.

Ask the compiler instead. Rewrite the binding to inject a deliberately wrong
type, and read back the type rustc wanted:

```rust
let on_clear_click: std::convert::Infallible = move |_: Event| { /* ... */ };
// error[E0308]: expected `Infallible`, found `Result<bool, JsValue>`
//                                  ^^^^^^^^^^^^^^^^^^  <- annotate with this
```

```bash
python3 <this skill>/scripts/harvest_let_types.py <repo>
# probes every site the verifier reports, writes .let_types.json
```

Four details decide whether this works or silently returns nothing, and all four
are baked into the script:

| Detail | Consequence if missed |
|---|---|
| the probe type must **exist in scope** (`std::convert::Infallible`, not an invented name) | an unknown name fails name resolution and rustc never reaches type checking — zero answers, and no error pointing at the cause |
| use `--message-format=json`, not `short` | `short` renders the type as the bare word `None` |
| read the **`found`** side, not `expected` | `expected` is the probe you just injected |
| batch ~6 sites per invocation | rustc stops emitting after ~8 errors, so the rest of the batch is silently unprobed — a short round is normal, the next round picks up the remainder |

**The probe mutates real source, so run it as a background command.** The script
restores every touched file in a `finally` and re-writes its results after each
round, but a *foreground* call that hits the tool timeout is killed mid-batch and
leaves the tree holding probe types. If that happens, treat the first line of each
touched file as suspect and restore from a backup before doing anything else:

```bash
grep -rn 'convert::Infallible' --include=*.rs <repo> | grep -v /target/
```

A killed run is also the signal that the loop belongs in a script, not in an
`execute_code` cell — the same timeout the loop hit is what killed it.

**Three groups are un-harvestable, not two — count all of them before starting.**

The third is **rustc's type elision**, and it is a silent data-corruption
source, not just a gap. When the inferred type is a long generic, the E0308
label arrives truncated:

```
expected `Infallible`, found `Result<RwLockWriteGuard<'_, ...>, ...>
```

`...` is rustc giving up on printing the generic arguments. It is not an
expandable placeholder, and writing it into source is a syntax error, not a
type error:

```
error[E0586]: inclusive range with no end
error[E0425]: cannot find type `RwLockWriteGuard` in this scope
```

The cascade is what makes it expensive: one `...` line reports eight-plus
errors, the crate stops compiling, and the failure surfaces against a
different crate in the next command. The shipped script now drops any
harvested type containing `...` so the site falls through to its
hand-annotate list, which is the honest outcome — the elided arguments are
exactly the part a human has to supply.

**The elision also means the harvested type is not necessarily the right
one to write.** rustc reports the type as normalized at the use site, and a
probe compiles the value inside an `if`/match arm where the same nominal type
prints under a different path than the one a later reader expects. The repo's
own alias is the better annotation:

```rust
// probe said: std::iter::Peekable<std::vec::IntoIter<Event<'_>>>
// the real value came from a VecDeque, and the repo already has:
//   type EventIter<'a> = Peekable<VecDeque::IntoIter<Event<'a>>>
let mut iter: EventIter<'_> = events.into_iter().peekable();
```

Grep for a `type ... =` alias before writing a long generic by hand; when
one exists, use it. Qualifying a name the probe spelled out in full can also
*break* the build, because rustc then compares the qualified path against an
inferred one carrying the unqualified name.

**A standalone-crate file resolves nothing from the parent crate's globs.**
A `build.rs` is its own crate root, so a harvested `Error` / `Iter` /
`Peekable` / `IntoIter` is in scope inside the library and **not found** in
the build script. Every harvested annotation must be compiled in the crate it
will live in — a `docs/build.rs` slice needs `cargo check -p <pkg>` on that
package, not the workspace wasm target that skips it.

**Closures cannot be harvested at all — count them before starting.** A binding
whose value is a closure reports `found closure`, not a type:

```
let on_clear_click: Infallible = move |_: Event| { .. };
// error[E0308]: expected `Infallible`, found `closure`
```

There is no type text to read back, so these sites must be annotated by hand
from context, and a binding like `let mut iter = nodes.into_iter();` is in the
same position — the element type is inferred at the use site. **Run the
harvester first and treat its two output lists as the work estimate**: the
typed sites are mechanical, and `by-hand` is the part that needs a human read.
Do not promise the slice is fully automatable on the strength of the count
before the harvest has run.

**Do not report a per-crate "resolved" number you did not compute from the
results file.** A loop that drops a site from its work queue when a batch
returns nothing has *abandoned* that site, not resolved it, and a counter
computed as "total minus queue length" reports it as a success. The
signature is a per-crate line claiming full coverage while the results file
holds far fewer entries than that line implies. Read the output file and
count it, not the queue.

**Verify the slice the way any other slice is verified** — the four gates, then
the verifier itself. A `let` annotation changes no behaviour, so `cargo check`
is the load-bearing gate and the others are confirmation.

## Whole-repo checks with no fixer: bring a size estimate, not a refusal

The whole-repo family has verifiers that report hundreds of findings and ship
**no `--fix` mode**. Before starting, and before proposing it, establish scale
and composition — the aggregate decides whether the slice is one commit or a
negotiation:

```bash
python3 <skills>/scripts/verify_<rule>.py <repo>            # header = N violations in M files
python3 <skills>/scripts/verify_<rule>.py <repo> | grep -oE '\S+\.rs:' | sort | uniq -c | sort -rn | head
```

Then bucket the literal shapes before touching source. A §1.3c sweep over
thousands of findings is not one task, and the buckets decide it: identifiers
and CSS keyword strings hoisted to `const.rs` are a multi-thousand-line
readability regression, prose and doc examples are unfixable by design, and a
modest remainder of real call sites is a normal slice. Present the buckets and
let the user choose the boundary — do not start a sweep whose result you already
suspect is wrong, and do not quietly shrink the rule instead.

## A gate that counts absolute violations is a broken gate

Any check whose only question is "how many violations exist" will fail forever on a repo with legacy debt, and will keep failing after you fix your own change. The commit hook and the audit both hit this.

**The rule: compare against a baseline, not against zero.** For a commit gate, that baseline is `HEAD` — block only the delta. For a whole-repo audit run, the baseline is the same check on a clean checkout; if the numbers match, the change introduced nothing.

To confirm a change introduced no new violations: `git stash push -- <your files>`, re-run the check, compare numbers, `git stash pop`. Identical numbers mean the failures are pre-existing debt, not your regression. Say so explicitly in the report rather than presenting historical debt as a failure of the current work.

**Never run `git stash` while a background command may be holding the same repo.** The stash is repo-global, not session-scoped: a backgrounded `cargo test` / CI-watch that runs `git stash && ... && git stash pop` and your foreground work on the same working tree will pop each other's entries, and the loser reports `No stash entries found` — which looks like a lost commit. Either finish every backgrounded command before baselining, or baseline with a method that touches no shared state: `git worktree add` a scratch checkout of `HEAD` and run the check there, or `git show HEAD:<file> > /tmp/baseline` and diff against it. After any stash-based baseline, confirm the tree is intact before continuing:

```bash
git stash list          # empty == no dangling stash
git log --oneline -1    # your commit still at HEAD
git status --short      # your edits still present
```

The same hazard applies to a stash left behind by an interrupted run: check `git stash list` first thing after any backgrounded command, and pop it before making new edits.

## Verify a rewriter is idempotent before you trust it

A fixer that is not idempotent cannot be run safely even when correctly scoped — it compounds on every invocation. Test it before relying on it:

- Run it on an **already-compliant** input. Zero changes expected.
- Run it twice. Output must be byte-identical (`diff` the two results), not merely "visually the same".

The doc fixer appended a second complete `# Arguments` / `# Returns` block to functions that already had one, tripling each doc block per run. Scoping alone did not contain this; only an explicit "is this section already present" guard stopped it. When adding a fixer or unforking one, check that every insert is guarded by the same predicate the auditor uses to report the violation.

## CLI argv contracts are not interchangeable

A script that requires a directory must never be handed a file path. When a hook or wrapper loops over files and shells out per file, check what the callee actually accepts:

```bash
grep -n "is_dir()\|is not a directory\|return 2" <script>   # does it reject files?
```

If the callee exits non-zero on a usage mismatch, the caller is wrong — and the failure looks like a content violation, so it blocks every commit with no useful signal. Import the callee's per-item function instead of shelling out, when one exists; that sidesteps the argument contract entirely.

**When a gate blocks 100% of the time, suspect the gate, not the code.** Verify the block is real by testing the same input on a clean baseline before concluding anything about the change.

## Before you push the skill repo

If a commit changes a script that other scripts or hooks reference, confirm the referenced files are actually tracked:

```bash
git ls-files <referenced-script.py>   # empty output = never committed
```

A pipeline pointing at an untracked file works on the developer's machine and crashes on every fresh clone. When you find this, fix it in the same push — the reference and the file must land together.

Also re-read `git log --oneline -3` before pushing. If HEAD moved while you were working, another process or agent is committing to the same tree; diff your worktree against the new HEAD to see whether your changes were absorbed, overwritten, or duplicated before you add anything.

`rust-standards` explicitly says the audit script is the single source of truth, *for the user's repo*. But the skill lives in a separate git repo and its scripts are not always consistent with its spec text. Hierarchy when there's a conflict:

1. User's instruction in chat — wins everything
2. Spec text in `references/` (the user maintains it)
3. Verifier script — usually right, occasionally buggy
4. Your prior assumptions — never a source of truth

If verifier and spec text disagree, fix the source to match the spec text and put the verifier-bug note in the commit message.

**Editing a verifier is legitimate only when the verifier itself is the bug.** Two different acts, do not confuse them:

- **Wrong repo, wrong reason** — editing a verifier in the *user's* repo, or editing one so a failing check reports clean. That is gaming the gate. The check's job is to report the truth; a verifier you adjusted to agree with your code reports nothing.
- **Right repo, right reason** — the verifier genuinely mis-implements the spec (wrong regex, wrong scope, non-idempotent fixer, argv contract that makes it unusable). That fix belongs in the **skill repo**, committed and pushed there, in its own commit, with the spec sentence it now actually enforces. The user's repo stays untouched.

When the second kind of fix is needed, it is a first-class deliverable, not a side effect to skip because the user asked for a code fix. Say you are making it, and keep it in a separate commit from any change to the user's repo.

## Two gates, and the pre-commit one is stricter

`rust_pre_commit.py` (Phase 2) and `~/.git-hooks/pre-commit` run **overlapping but non-identical check sets**. A green `rust_pre_commit.py` is necessary, not sufficient — a repo whose full audit read `40/40 PASS` still had its commit refused for a file that audit had exempted.

**Rule: a `rust_pre_commit.py` PASS is not commit approval, and `--no-verify` is never the answer.** When the hook blocks, that report is the real spec for the next slice.

Three collisions recur; their signatures and fixes are in [references/commit-gate-collisions.md](references/commit-gate-collisions.md). The one worth remembering cold:

> An auxiliary `fn` in a test file has no legal shape — documenting it satisfies the staged gate's doc-comment check and breaks §14.5 (no comments in `tests/`) at the same time. **Delete the helper and inline its body at each call site.** A test file should contain only `#[test]` functions.

## Hand-written accessors must not be `const`

§17.12 exempts hand-written accessor bodies from the `self.field` ban, but the verifier recognises the exemption by matching the fn name on a **plain `fn`**. `pub const fn get_x(&self) -> T` does not match, so its body is treated as a business method and every `self.field` inside it is reported.

**Accessors are plain `pub fn` project-wide.** Do not "improve" one to `const` later — it silently reintroduces the violation.

## Test layout: loose files beside `mod.rs` run the suite twice

**A falling test count is a measurement question before it is a regression.**
A slice that only runs `cargo test` on the host target will report fewer tests
than a previous run simply because the wasm-gated ones never executed — the
count moved without a single test being deleted. Establish which it is before
reporting:

```bash
# 1. did the target-gated suite even run?  exit 126 = no wasm runner on host
cargo test --target wasm32-unknown-unknown 2>&1 | tail -3
# 2. are the test files themselves still there?
grep -rc '#\[test\]' --include=*.rs <dir>/tests | grep -v ':0$'
# 3. did THIS session touch them?
git status --porcelain -- <dir>/tests
```

Command 3 is the one that decides it: an empty result proves the files are
byte-identical to `HEAD`, so the lower count is a harness difference and not
lost work. **Report it as "N passed on the host target; M more are wasm-gated
and did not run"** — reporting the bare smaller number invites a review that
you deleted tests, and reporting `cargo test --workspace` as if it passed is
worse, because the workspace invocation on a wasm-only crate fails outright
with `can't find crate for euv_core` and a test run that reports `0 passed`
from a single package is not a suite at all.

Run the suites per package and **sum the `test result:` lines yourself**; never
trust a wrapper's summary or assume a workspace-wide `cargo test` covers
everything.

## Test layout: loose files beside `mod.rs` run the suite twice

`tests/mod.rs` declaring `mod a; mod b;` **plus** loose `tests/a.rs` and `tests/b.rs` compiles each file twice — once inside the `mod.rs` target, once as its own test binary. The output shows the same tests in three separate `test result:` blocks with counts split across them, which reads like a flaky or duplicated run.

One directory per group is the correct shape:

```
tests/mod.rs            mod a;  mod b;
tests/a/mod.rs          mod r#fn;   + pub use the crate
tests/a/fn.rs           use super::*;
```

A loose `tests/<file>.rs` is correct only when it is the *sole* test target — then it is the crate root, and `use super::*;` fails there with `E0433: too many leading super keywords within crate`. Use `use <crate_name>::*;` directly.

## Redundancy rules delete the default spelling, never the narrowing one

Many rust-standards rules forbid an **explicit spelling of a default** — a visibility argument on a macro that already defaults to `pub`, an explicit type equal to the inferred one, a default trait method that needs no `impl`.

The removal and the narrowing case are the same token in a different position, so a rewriter that matches on the keyword will strip the prefix of `pub(crate)` and silently widen a field that the rule's own spec requires you to keep narrow.

**Tell:** the diff's deleted lines include a narrowing form, or the narrowing form's count drops after a "redundancy cleanup".

**Rule: match the whole token — bare `pub` only, never the `pub(...)` prefix — and prove the narrowing counts are unchanged.** Snapshot `grep -c 'pub(crate)'` (and the other narrowed forms) before and after; zero delta is the evidence the rewriter distinguished them. Include those narrowing forms plus comment-embedded and substring cases in the *compliant* fixture, because a rule written as "delete the keyword" passes every violating fixture and still corrupts them.

The build is the load-bearing check here. When a macro default is what makes the argument redundant, deleting a *wrong* argument shows up as `E0599` / `E0624` at the first external call site, not as a warning.

### The fix for redundancy rule A can be the violation of redundancy rule B

Two rules can forbid successive spellings of the same thing, so the "correct"
rewrite of A is itself a hit for B. Removing the visible marker of A lands on
the default spelling — which B says is also redundant, because the macro already
emits that behaviour with no argument at all. Example: forbidding an explicit
`pub` visibility argument whose default is already `pub`, then separately
forbidding a bare attribute with no arguments on a derived field.

```rust
#[get(pub)]   // violates A
#[get]        // the table says "the fix" — violates B
              // legal: the whole line is gone
```

**Rule: a redundancy rule's destination is the minimal legal form, not the next spelling down.** Before writing "the fix is X" in a spec table, check X against every other rule that touches the same construct; if X trips one, the table entry is wrong and must say so. Fix the sentence that misled — don't append a correction under it, because the table is what a future session copies from.

Corollary for the audit: when a new check fires on lines a previous check's guidance told someone to produce, grep the older doc for the now-wrong mapping and reconcile it in the same commit. The verifier is not the thing that disagrees; the prose is.

## Vet a new rule's prescribed fix against the toolchain, in one directory, before the rule ships

A rule whose fix is a *structural* change ("move this file to `X/X.rs`")
has, by construction, a remedy the toolchain gets a vote on. The rule can
be perfectly written and still mandate a layout that clippy flags by
default, in which case every agent that faithfully applies it introduces a
new warning per file. The rule and the fix are one deliverable; shipping the
rule before the fix is measured ships a trap.

```bash
# 1. baseline on the untouched tree
cargo clippy --all-targets 2>&1 | grep -cE '^warning:'

# 2. apply the remedy to exactly one directory, then re-count
cargo clippy --all-targets 2>&1 | grep -cE '^warning:'
```

Match `^warning:` at column 0. The indented continuation lines (`--> file`,
`= note:`, `= help:`) make one warning count as three or four if you
substring-match anywhere in the line, which inflates the total and makes a
correct fix look insufficient.

**A zero baseline is what makes this measurable.** In a repo already at
zero, "two new warnings" is a net regression rather than noise. Also confirm
the shape is genuinely *new* rather than assumed: grep the tree for the
post-fix layout **before** the sweep. A remedy that was already the
convention in one crate and absent from another is a consistency fix; a
remedy absent from every crate is one you are introducing, and it needs the
lint to have opinions about it.

The conflict is often structural rather than accidental. "Name the directory
after the keyword" forces `mod r#impl;` inside `impl/`, naming the module
`impl` inside directory `impl` — `clippy::module_inception`, on by default.
And the rule may be *self-conflicting* as well: the honest reading of "no
`.rs` beside a directory" flags every keyword file, plus every `macro.rs`
that legitimately sits alongside sub-modules. A repo carrying two dozen of
those is telling you the rule is wrong at the scope level, not the file
level — the strict version is not merely expensive, it is reporting valid
code.

**When the remedy conflicts with the toolchain or with a sibling rule, the
usual right exit is to narrow the rule to what it was actually for**, and
say which files the narrowing covers. "No orphan file with no module name"
keeps the intent, drops the cost, and produces a fix the toolchain accepts.
Record the measurement that forced the narrowing — the delta in warning
count and the count of files the strict version flagged — because the next
session's first instinct will be to widen it back.

## The completion script's lint phase must be read for the channel it checks

`rust_pre_commit.py` is this skill's documented single completion command,
so a defect in one of its phases is inherited by every agent that follows
this skill — it does not stay a local bug. A lint phase written as

```python
rc = run(["cargo", "clippy", "--all-targets", "--quiet"])
if rc == 0:
    print("PASS (0 warnings)")    # the count is a literal, not a measurement
    return True
```

passes for **every repository, permanently**: `cargo clippy` exits 0 with
any number of `warning:` diagnostics unless `-D warnings` is passed. The
telltale is a number in the success line that is never computed on the way
to it.

```bash
cargo clippy --all-targets 2>&1 | grep -cE '^warning:'   # the real number
cargo clippy --all-targets --quiet; echo $?             # always 0 — proves nothing
```

Two traps make this survive longer than it should. The repo's **CI runs the
same command without `-D warnings`**, so the pipeline and the local gate are
not two independent confirmations — they are one bug counted twice. And a
**subagent relaying the gate's own PASS line** will quote the unreality
verbatim, which is how a fabricated "0 warnings" reaches the user while
every visible signal says clean.

When a lint gate is what stands between you and a claim, count the
diagnostics yourself rather than re-running the wrapper that prints the
reassuring summary. The wrapper is the thing under suspicion.

## Commit scope: never `git add -A <dir>/` on a directory that holds build output

Generated artifacts (`dist/`, bundles, `.wasm`) are often untracked and unignored. Adding a parent directory pulls them in alongside the real edits, and the commit carries hundreds of KB of machine-specific output.

**Tell:** `git show --stat HEAD` lists paths in a directory you never opened.

**Fix:** `git rm -r --cached <artifact-dir>` then `git commit --amend --no-edit`, then confirm the artifact is back on disk and untracked — `--cached` unindexes it, it does not delete it. Verify against the post-amend diffstat, not the pre-amend one.

## Pitfalls

- **Don't sweep a worktree another agent is using, and don't reconcile it with `reset --hard`.** A violation count that drops with no edit from you is another writer, not a fix — stop, `git diff > backup.patch`, and wait for a quiet window. After a merge, sync with `git merge --ff-only origin/<default>`; `reset --hard` destroys their uncommitted work. Re-run every gate after their edits land, forcing rebuilds with `touch` rather than trusting the incremental cache.
- **Don't accept a source-side fix that only survives until the next `crate fmt`.** When a "do not modify the checker" task must reach zero, the rewrite has to be formatter-stable: an or-pattern that a span scanner reads as a closure param list must be *rewritten* (`const` + `.contains()`, or a `match` guard) because rustfmt re-joins a line-split or-pattern, while a `|` construct inside a raw string only needs a line break, since raw-string contents are never re-wrapped. Re-run the checker **after** `crate fmt`, not just before.
- **Don't report a new rule's real violations and stop.** A check that ships
  with N findings in M repos is half-delivered. Sweep them — one dispatched
  agent per repo, one PR per repo — and put the measured per-repo numbers in
  each brief (findings list, which other checks are legacy debt, dirty-file
  count) so no agent rediscoveres them or sweeps someone else's staged work
  into its commit.
- **Don't commit an audit sweep straight to a shared upstream's `master`.**
  That rule applies to a repo you own; an org repo where you are admin but
  not the sole author is a review bypass, and the sweep is a code change, so
  it takes the branch → PR route.
- **Don't expect `rust_pre_commit.py` exit 0 as commit approval.** The pre-commit hook runs a stricter, narrower check set (delta vs `HEAD`, tests not exempt) and will still block. The hook's report is the spec.
- **Don't resolve a `tests/` doc-comment block by adding the doc comment.** §14.5 forbids it. Delete the helper and inline it.
- **Don't mark an accessor `const`.** The `self.field` verifier's exemption matches plain `fn` only, so `const` turns every accessor body into a reported violation.
- **Don't leave a free `fn` in `impl.rs`.** Only inherent methods belong there; move it to `fn.rs`.
- **Don't put loose test files next to `mod.rs`.** Each one becomes a second test binary and the suite runs twice.
- **Don't run the Phase 1 auto-fixers unscoped.** They rewrite the whole repo. Record the dirty-file count before, and `git checkout -- .` if it jumps.
- **Don't treat historical debt as your failure.** Stash your changes, re-run the check, compare. Same numbers means the failures predate you.
- **Don't call a failing check "pre-existing debt" without reading how it reads its input.** Half the audit is diff-scoped and half scans the whole tree; a whole-repo check reporting N findings is reporting on the tree as it stands, so the deliverable is a fix or an explicit scope decision from the user, not a label. Classify with the grep over the audit's own check registrations **before writing a word about provenance** — and take the verifier path from the wrapper text, not from a sibling script whose name resembles the check's title, or a confident `0` from the wrong script will read as "this check is clean".
- **Don't start a no-fixer whole-repo sweep without a size and composition estimate.** Bucket the findings (`grep -oE '\S+\.rs:' | sort | uniq -c`) and classify the literal shapes; thousands of §1.3c hits are a readability regression, not a task. Bring the buckets and the remaining count to the user and let them set the batch boundary.
- **Don't let a fixer override the verifier.** If `fix_<rule>.py --write` leaves the verifier still failing, the fixer is wrong, not the file. Read the verifier's real sort key, order by hand, and report the fixer bug.
- **Don't `git stash` next to a running background command.** The stash is repo-global, so concurrent stash/pop pairs clobber each other and report a misleading `No stash entries found`. Verify `git stash list` is empty and your commit is at HEAD after any backgrounded command, or baseline via a scratch worktree instead.
- **Don't attribute a build failure to your own edit without isolating it.** `git diff HEAD` includes whatever was already staged in the index, so a pre-existing staged change reads as part of your diff. Apply your change alone, then the pre-existing one alone, and compare before concluding.
- **Don't trust a fixer you haven't seen be idempotent.** Run it on compliant input (expect 0 changes) and run it twice (expect identical bytes).
- **Don't report damaged source as lost before counting its structure.** A scripted
  literal-substitution pass over a test module deleted the `assert!(` opener lines
  and mangled the format arguments. The first read of the result looked like the
  module had been wiped, and reporting it as unrecoverable was wrong: every `#[test]`
  function was still present, only the macro openers were gone. `grep -c '#\[test\]'`
  and `grep -c '<macro_name>('` settle it in one call, and they distinguish "the
  declarations vanished" from "the syntax around them was eaten" — which have
  completely different fixes (restore from git vs re-add the openers). State the
  count you measured, never a guess from a partial read of a large diff.
- **Don't use a regex tokenizer to bulk-edit Rust source.** Rust raw strings (`r"..."`, `r#"..."#`) and `b'<'` byte literals defeat naive regex. Use `syn` (the actual Rust parser) or `cargo fmt --emit=files` for validation, and `cargo check --workspace` to confirm no parse damage. A bad bulk edit silently deletes every blank line between fns.
- **Don't blindly add `use super::*;` to satisfy a check.** Run `cargo check` after — if the import is unused, revert. The user has corrected this directly.
- **Don't combine two violation classes in one commit.** If the dep-order slice accidentally breaks a closure slice, `git reset` becomes hard. One class per commit, audit-gated.
- **Don't trust the `N hits` number blindly.** Tracebacks inflate it and re-quoted results go stale; run the verifier directly, and re-run it before the number goes into a commit message, PR body, or summary. And a report that caps findings per rule is a prompt to switch tools: re-running shows the next slice, which reads as steady progress rather than as an unbounded backlog. Get the real count per affected path.
- **Don't compare violations as a whole-repo total.** Additions and removals cancel: +21 in one file against -22 elsewhere nets to -1, and a diff of failing *rule names* is unchanged too. Both framings pass while one file regressed. Compare per file, each against its own `HEAD` content — which is exactly what the commit gate does, and why it caught what the aggregate could not.
- **Don't write the fixture after changing the rule.** Run it against the *old* implementation too: that is what shows the rule was previously backwards rather than merely newly strict. A tightening that only looks green afterwards leaves open whether the old code enforced anything.
- **Don't accept a fixture that has never failed.** Prove the test has teeth by mutating the rule — re-widen the exemption, disable the check, invert the comparison — and require a FAIL each time. Guard each mutation with `assert mutated != original`, or a stale replace target reports `CAUGHT` for a mutation that never applied.
- **Don't split a module on the obvious axis before measuring who shares what.** An item referenced by two of the would-be new modules belongs in a shared tier, not either of them. Two backends that both use `FilterMode` / `AddressMode` / `CompareFunction` / `DrawArgs` force `state/` + `descriptor/` + one directory per backend; splitting by backend instead leaves one implementation importing its sibling. Measure the cross-references, put the table in front of the user, then let them pick the axis.
- **Don't let a rule's justification keep a count the measurement contradicts.** If a spec says "this repo carries 24 of these" and the files are actually in leaf directories the rule never flags, the sentence described a hypothetical shape. Fix it in place; a correction appended underneath is the part nobody reads.
- **Don't derive a violation's file distribution from the audit's printed sample.** The audit caps displayed findings per check; count in the source instead, or you will attribute 464 hits to the 1 file it happened to print 5 lines from.
- **Don't bulk-patch a check before classifying its hits.** A check whose findings are `macro_rules!` matcher fragments has no legal fix — report the verifier scope bug upstream instead of editing source to satisfy it.
- **Don't revert a bulk edit with `git checkout -- <dir>/`.** It discards unrelated legitimate work in the same tree. Revert the single file.
- **Don't trust a hit count that is exactly one too high either.** A delta of exactly 1 is a summary line the wrapper failed to filter on the failure path, not a miscounted violation. Match the filter on the summary's shape, and reconcile the audit count against the verifier's count.
- **Don't chase a FAIL whose detail line is a banner, a summary, or a traceback.** There is no `file:line`, so there is nothing to fix in the repo: the wrapper's `grep -v` is written against a success banner the verifier no longer prints, and the leaked line is counted as a hit. A check with zero real violations then reports `1 hits` and FAIL. Audit every wrapper's filter against the banner its verifier really prints, and prove the repair both ways — mutate in a real violation and confirm the filter still lets it through, or you have swapped a noisy gate for a silent one.
- **Don't let one rule's documented fix be another rule's violation.** When two rules forbid successive spellings of the same construct, the "fix" for the first is a hit for the second. Check the destination form against every other rule before writing it into a spec table, and correct the table in place.
- **Don't ship a structural rule before running its own prescribed fix past the toolchain.** "Move the file to `X/X.rs`" can mandate a layout clippy flags by default (`module_inception` when the directory is named after the keyword), and the strict reading can flag every keyword file plus every `macro.rs` that legally sits beside sub-modules. Apply it to one directory, diff `grep -cE '^warning:'` against the untouched baseline, and check the post-fix shape didn't already exist. Narrow the rule to what it was for when the remedy costs a lint or a sibling rule — and record the measurement that forced it.
- **Don't trust a lint phase that reads the process's exit code.** `cargo clippy` exits 0 with any number of warnings unless `-D warnings` is passed, so a `if rc == 0: print("PASS (0 warnings)")` gate passes for every repo forever — the count in the success line is a literal, not a measurement. Count `^warning:` at column 0 yourself; the wrapper that prints the reassuring summary is the thing under suspicion. CI running the same command without `-D warnings` is the same bug counted twice, not a second confirmation.
- **Don't hand a child a flag whose effect lands after you stop looking.** `--delete-branch` is on both `gh pr create` and `gh pr merge`, so a create brief carrying it leaves merge semantics available for the whole dispatch window. Scope the child to the reversible step and say "do not merge" next to the permission. On a release pipeline the merge triggers a publish job that moves artifacts to a public registry within minutes — establish `mergedAt`/`mergeCommit` and the in-progress runs before reporting, and leave cancelling to the user.
- **Don't offer "which finding should I fix first?" when the findings are not interchangeable.** The user has corrected this: if it is a script problem, fix the script; if it is a real violation, fix the repo. Classify each finding with the decision procedure, then execute. Handing back a count and a menu is deferring work you can already classify, and it reads the same whether the items are genuinely undecidable or you skipped the classification.
- **Don't file a failure you did not cause as a footnote.** Attribute it with
  `git log -S` + `git show HEAD:<file>` + `git diff HEAD --stat -- <dir>`, measure
  the rate by looping the compiled binary, sweep `--test-threads` 1/8/16/32, and
  isolate per module before theorising. Then fix it in the layer that owns it —
  serialise the tests, or move the global to `thread_local` — because
  `--test-threads=1` hides the defect rather than removing it. If the fix is out of
  scope, hand the user the measured rate, not a reassurance.
- **Don't conclude a fix didn't work from an audit that only reads `HEAD`.** Most
  checks run `git diff origin/master HEAD`, so an uncommitted fix is invisible to
  them; verify with `git diff origin/master -- <file> | grep <pattern>`, report the
  stale finding as stale, and do not commit just to move the number. And re-read the
  detail lines after every `git mv` — a structural edit shifts the diff hunks, so
  the same check reports different files and the coordinates you were working from
  are expired. When a check names a file to rename, read the sibling directories'
  spelling first; renaming to the existing convention beats inventing a new one.
- **Don't report a verification that a concurrent writer has since invalidated.**
  A shared tree can go from N modified files to 0 with commits you did not make, at
  which point your edits are inside someone else's commit and every gate you ran
  was measured against a different `HEAD`. Re-run the gates after their commit lands
  and check whether it touched your files before quoting a diffstat.
- **Don't fix the verifier script from the user's repo.** It's a different git repo; your edits there are ignored. Two valid endings: note the bug in the commit and move on, or — when the user asked for the exemption — fix script + commit gate + skill doc together in the skill repo, in its own commit.
- **Don't accept a false positive as a residual.** When a check flags something the compiler proves cannot be fixed, the deliverable is the exemption, not a footnote about the one finding left over. Ask which ending the user wants before settling for the first.
- **Don't allowlist the literal.** Exempt `extern "C"` by matching the `extern` construct; an exemption for the string `"system"` misses every other ABI and turns a structural rule into a string list.
- **Don't exempt a whole line because one construct on it is exempt.** Line-level `continue` drops every other literal on the line, and `#![rustfmt::skip]` (one line, still `cargo fmt --check` clean) keeps a payload like a key path on it. Capture the exempt span by name, exclude only that span, and restart the scan *past* it — a quote-pairing regex rescanned from zero pairs off the exempt literal's closing quote.
- **Don't prove an exemption with a fixture.** Fixtures show the happy path; build the widest single-line form that still parses and assert the payload is still reported. And don't exempt `^\s*//` for doc comments — that also hides secrets in plain comments; use `^\s*//[/!]`.
- **Don't reach for `_` when a macro arm's type is "only known at expansion".** `HashMap<_, _>` compiles and satisfies the verifier while leaving the reader with the same inference the rule exists to prevent. Delete the `let` and build with `From<[(K, V); N]>`; it works for `HashSet` / `LinkedList` / `BTreeMap` / `BTreeSet` too, and the callers need no change. Check the zero-argument arm — `from([])` has no type to infer.
- **Don't classify a finding before checking the path is tracked.** A gitignored scratch tree can hold files that violate any rule and that no commit can ever contain. `git ls-files <path>` empty = not source; filter gitignored paths inside the file walker (one batched `check-ignore --stdin`) and apply the fix to every script carrying its own copy of that walker.
- **Don't sweep thousands of findings into one PR.** A cross-repo remediation splits by scale: measure per check and per crate before starting, and take the mechanical low-risk class first. A single PR over ~100 crates makes review ceremonial, and the diffstat is the only thing anyone reads. State the batch boundaries and the remaining count up front so the user can redirect the granularity before the work starts.
- **Don't report a violation count you haven't re-run.** The same number gets restated through a long session from a truncated tool result; re-run the verifier before it goes into a commit message, a PR body, or a summary.
- **Don't skip `cargo check --release`.** CI runs release mode — debug-only warnings can hide there. Always run both profiles.
- **Don't treat a pre-rebase gate run as evidence for a rebased release PR.** A version bump merged on top of earlier work inherits all of it; rebase onto the merged default branch and re-run the full gate (build, tests, clippy `-D warnings`, fmt, and the check scripts) on the rebased branch. A green run on the pre-rebase tree is a stale claim, and a release PR is the last place to discover it.
- **Don't use `#[allow(...)]` to silence clippy.** Rule 14 of rust-standards forbids it; fix from root or the slice gets review-rejected. **Deleting the attribute is not the fix** — confirm the lint actually fires first (`cargo clippy -p <crate> 2>&1 | grep -c too_many_arguments`); a load-bearing `#[allow]` fails the moment it is removed, and the honest repair is to reduce the parameter count. When every parameter describes one value, bundle them into a struct in `struct.rs` and pass one argument — it reads better than positional soup and needs no lint suppression. **Search for every call site before you finish**: a long-lived helper usually has more than one, and the compiler finds the one you missed only after the struct is already in place.
- **Don't rewrite helper call sites with a name-only replace.** A replace on the helper's name also rewrites the helper's own body, so it calls itself — which presents as an intermittent hang or a lock deadlock, not a compile error. Match a call-site-only construct (`name(` preceded by a non-`f`, or the assignment), assert the replacement count against the call sites you enumerated, and re-read the definition's full text after the sweep.
- **Don't add test-file `///` doc comments.** §14.5 forbids any comment in `tests/`. If `doc_comment_audit.py` (the bulk fixer) added them, `git checkout -- <crate>/tests/` to revert.
- **Don't expect `verify_dep_order.py` to finish.** It has a `return violations` indented inside a `for` loop (line ~249) that crashes on fixtures. Run a custom parser or skip and document the carve-out.
- **Don't treat `audit 39/39 PASS` as evidence that a bulk edit preserved your code.** Purity checks detect forbidden declarations, never missing ones — deleted `impl` blocks pass every check and keep tests green. After any mass edit, pair the audit with `cargo build` / `cargo test` and confirm impl blocks by count (`grep -c '^impl'`), not by absence of errors.
- **Don't add `use super::*;` to a sibling `impl.rs` hoping to reach a sibling `struct.rs`'s private fields.** The glob cannot do that; the field needs `pub(super)`. Chasing the import wastes a cycle and leaves the E0616 in place.
- **Don't leave a signature edit's doc comment behind.** Bundling 12 parameters into a struct, or swapping `impl IntoIterator<Item = Node>` for `<I: IntoIterator<…>>`, invalidates that fn's `# Arguments` list — and the doc-comment check reports it against the file you just edited, where it reads as pre-existing debt. Mirror the change into the doc in the same edit, then confirm the fn is absent from the doc verifier's output rather than trusting that you updated it.
- **Don't report a whole-repo check's score without its count.** A finding that drops 3160 → 1437 leaves `SUMMARY` at the same value, because the check is FAIL for any N > 0 — the score is not evidence the exemption did nothing, and a count that never reaches zero has still not converted a FAIL into a PASS. Report both.
- **Don't infer the type behind a bulk `let`-annotation finding from the RHS.** A multi-line chain is a guess, and at several hundred sites each wrong guess is a compile cycle. Inject a wrong type and read back E0308's `found` side (`scripts/harvest_let_types.py`). Two details silently return zero answers: an invented probe name fails name resolution before type checking ever runs, and `--message-format=short` truncates the type to the word `None`.
- **Don't promise a `let` slice is automatable before the harvest runs.** Closure bindings report `found closure`, long generics are elided to `...`, and generic iterators report nothing — three un-harvestable groups. Run the script and read its by-hand list, which is the real size of the manual part.
- **Don't apply a harvested type without reading it for `...`.** rustc elides long generics to a literal `...` in the E0308 label, and writing that into source is a syntax error whose cascade reports against a different crate than the one you edited. The shipped script drops them; if you harvested by hand, grep the results for `...` before applying.
- **Don't write a harvested long generic verbatim when the repo has an alias for it.** rustc normalizes the type at the use site, so the probe's fully-qualified path can be both wrong (a `VecDeque` iterator reported as `vec::IntoIter`) and insufficient (`build.rs` has none of the parent crate's globs). Grep for `type ... =` and use the repo's own alias; compile in the crate the annotation will live in.
- **Don't take a per-crate "N/N resolved" line as measured.** A loop that removes a site from its work queue when a batch yields nothing has abandoned it, and a total computed as "sites minus queue length" counts that as a success. Count the entries in the results file.
- **Don't run a probe loop that rewrites source in a foreground tool call.** A timeout kills it mid-batch and leaves the tree holding probe types. Background it, and `grep -rn 'convert::Infallible'` first thing if a run is interrupted.
- **Don't prove a block exemption with a single fixture.** `inside the class!` passing tells you nothing about a depth tracker that runs to end-of-file. The probe that finds it is a literal appended *after* the block closes.
- **Don't scan a string literal's payload as if it were Rust.** A shader or template carried in an `r#"…"#` looks exactly like host code to a line-oriented verifier — `let ball = u_balls.balls[vi / 6u];` in WGSL is not a §5.1 violation. Mask the literal's lines and prove the mask with a real `let` placed *after* the closing delimiter, since a fixture ending inside the string cannot express the leak.
- **Don't annotate a closure from its own syntax; annotate it from the consumer's bound.** `impl Fn(..)` is `E0562` in a binding, a bare trait object is `E0308: found closure`, and `fn(..)` rejects any capturing `move` closure — the working form is whatever the call site's `From` / `F: FnMut(..) + 'static` bound accepts, usually a `Box<dyn FnMut(Event)>`. Grep the bound before choosing.
- **Don't put a type alias in `impl.rs` or `fn.rs` while fixing an annotation.** §1.3 puts aliases in the module's `type.rs`, and a new `type.rs` needs both `mod r#type;` and a `pub(crate) use r#type::*;` — the missing re-export surfaces as `cannot find type X in this scope`, which reads like a missing import rather than an unfinished registration.
- **Don't report a lower test count without checking whether the target-gated suite ran.** `cargo test` on the host skips wasm-only tests (the runner exits 126) and a workspace-wide invocation can fail outright with `can't find crate for euv_core`. Prove it with `git status --porcelain -- <dir>/tests`: empty means the files are identical to `HEAD` and the count moved because of the harness, not because tests were lost. Report the gated remainder explicitly.

## References

- `references/lombok-accessor-semantics.md` — the `lombok-macros` derive behaviours the README understates: the derive emits an accessor for **every** field (only `skip` withholds one), the two redundancy rules that forbid `#[get(pub, …)]` and `#[get]` in turn, which `type(clone|copy|deref)` mode breaks what, the `get_mut_` naming, and **why an `Option` field's `get_*` panics while `try_get_*` does not** — including how to settle it by expanding the macro, why field-name matching is not a verifier, and when to delete the unwrap by storing a non-`Option` field instead.
- `scripts/harvest_let_types.py` — compiler-driven harvest of the real type behind every §5.1 `let` annotation finding; probes with an injected wrong type and reads back E0308's `found` side. Run it in the background; it rewrites source while probing.
- `references/verifier-scope-bugs.md` — the four classes of finding that are not Rust (wrapper artifact, macro fragment, grammar slot, second-language-in-a-string), how to tell them apart by reading the reported line, and the four-probe exemption discipline each one needs.
- `references/annotating-let-bindings.md` — the by-hand half of a bulk §5.1 slice: annotating a closure from the *consumer's* bound (`Box<dyn FnMut(Event)>` vs `Rc` vs `fn` vs `Arc`), the two traps in rewriting a `-> T` closure, and where a repeated type alias belongs.
- `references/pipeline-safety.md` — recipe for scoping, baselining and idempotence-testing a rewriter before trusting it in a commit gate.
- `references/commit-gate-collisions.md` — the two commit gates, their differing scopes, and the three rule collisions that leave a test helper or accessor with no legal shape.
- `references/authoring-a-new-rule.md` — the five places a new rule must land, differential fixtures (including the tiebreak that catches a wrong-but-plausible verifier), and the three measurements that prove a removal preserved meaning.- The rust-standards skill holds the spec text and the `audit-pitfalls.md` false-positive list. Load it via `skill_view(name='rust-standards')` when you need to read the rule for a failing check.