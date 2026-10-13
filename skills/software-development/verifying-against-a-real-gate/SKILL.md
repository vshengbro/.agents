---
name: verifying-against-a-real-gate
description: 'Use when a check reported pass on code you just wrote.'
---

## A green gate is only as strong as its scope

The failure this prevents: shipping code that passed a check which was
never looking at that code, and reporting the pass as evidence of quality.

## Elapsed time is a symptom, not a measurement

A process that has been running much longer than it should, on a check you
believe it should have finished, is *evidence about the run* — never evidence
about the code. A three-hour job is equally consistent with a deliberate
metered wait and with a parser sleeping for thirty days; only the log line
distinguishes them, and until you have that line the honest report is "still
running, cause unconfirmed."

This is the same failure as a hardcoded `0 warnings` (below), wearing a
different mask: there the gate never measured; here the agent is measuring
the wrong thing because it is the only number available.

**Rule: when the only signal you have is "it is taking longer than expected,"
do not narrate the duration as progress or as a fix working.** Say what is
unconfirmed, name the check that would confirm it, and go get that check.
Re-deriving a cause from a stopwatch is a guess wearing a proof's clothes.

The corollary is a reporting rule: if you told the user a fix was working
based on an indirect signal, and it turns out not to be, correct it in the
open — do not quietly restate the new state. A user who has already read the
optimistic claim is owed the retraction, not the update.

## Incremental gates cannot certify new files

A delta-style gate — one that compares each file against `HEAD` and reports
only the *increase* in violations — is the right design for blocking new
mistakes on existing code. It has one structural blind spot:

**For a file that has never been committed, the baseline is 0, so the delta
is 0 no matter how many violations the working copy contains.**

The gate passes, prints a reassuring count, and the code lands unchecked.
"0 violations" here means "you did not make an existing file worse", which is
not the same claim as "this code is correct".

**Rule: when a change adds any new file in a class the gate covers, the
incremental gate is not sufficient evidence.** Run the full-scope check for
that class. Reserve the incremental gate for changes confined to files that
already exist in `HEAD`.

### An empty diff window fails closed and reports success

A whole-suite variant with no baseline at all: the audit computes its scope by
running `git diff <ref>`, and on a freshly seeded repo `<ref>` does not exist.
`git diff` exits non-zero with nothing to compare, the window is empty, and
every diff-scoped check short-circuits to pass. The tell is in the output — a
literal line saying the diff window is empty and that checks below would pass
without reading a file. That sentence is the finding; the `N/N PASS` summary
underneath it is the part that is lying.

**Rule: when a gate announces an empty or failed diff window, treat every count
it prints as void, and restore the comparison before trusting a single number.**
Push the initial baseline (or otherwise materialise the ref) and re-run, then
expect the score to *drop* — surfacing real inherited debt is the gate starting
to work, not a regression.

The tell-tale symptom is a perfect score on a template-derived tree. A cloned
scaffold carries whatever upstream shipped, so `51/51` before any edit is a
reason to suspect the scope, not to celebrate.

### Two disagreeing verdicts from one verifier means two different artifacts

When a verifier reports `0 violations` repo-wide and the commit hook still
blocks the same file, they are not contradicting each other — they ran on
different trees. Hooks commonly audit each staged manifest *alone* in a scratch
directory rather than in place, which drops sibling context (workspace members,
package-local crates) and can flip a cross-file classification such as
local-vs-third-party ordering.

**Rule: reproduce the hook's invocation exactly before calling its finding a
false positive.** Copy the file the way the hook does, run the same command,
diff the verdicts. Only a reproduced mismatch licenses the words "false
positive"; when the mismatch is real, fix the layout so both agree rather than
suppressing the hook. A mismatch confined to the repo's first commit and gone
once a baseline exists is itself proof it was a scope artefact, not a content
defect.

This applies to any staged-file linter, any pre-commit hook that diffs
against the last commit, any "did this change introduce a problem" check.

The same blindness has a sibling form: **a file exempt from the gate's scope is not a file
the gate checked.** A check that reports zero findings for your own files may simply not
scan them, while an identical construct one directory over is reported. Read the exclusion
list before treating a zero as a pass, and apply the rule regardless — prove compliance by
counting the pattern out of band, not by the gate's silence.

## Report truncation hides the real count

Audits commonly cap displayed findings per rule. One run then shows a
prefix of the work, and re-running shows the next slice, which reads as
steady progress rather than as an unbounded backlog.

**Get the real count by invoking the per-rule verifier directly against each
affected path**, not by re-running the aggregate report and reading the next
batch off it. A truncated report is a prompt to switch tools, not to run the
same tool again.

## A net-zero aggregate diff is not a per-file diff

The cousin of truncation, and harder to see because the numbers look clean.
An aggregate audit reports one hit count per rule, so a change that adds 21
violations to one file while a rewrite elsewhere removes 22 nets to **-1** —
and a comparison phrased as "no new failing checks appeared" is satisfied by
the *set of rule names*, which did not change either. Both formulations pass
while one file regressed badly.

**Rule: compare violations per file, never the aggregate total, when deciding
whether a change introduced problems.** Gross additions and gross removals
cancel; only a per-file delta can see a regression inside a net improvement.
A per-file delta needs a per-file baseline, and the baseline must be the same
file at `HEAD` — comparing a file's count against a directory total, or
against a whole-repo count taken at a different moment, is the same error in
a different shape.

```bash
# the shape of the comparison that hides it — set of failing RULE names
diff <(audit HEAD | grep '^FAIL:' | cut -d: -f1) <(audit WORKTREE | grep '^FAIL:' | cut -d: -f1)

# the shape that sees it — count per file, same file, two states
for f in $(git diff --name-only HEAD -- '*.rs'); do
  printf '%s: HEAD=%s now=%s\n' "$f" \
    "$(git show HEAD:"$f" 2>/dev/null | <verifier> - | wc -l)" \
    "$(<verifier> - <"$f" | wc -l)"
done
```

### Verify the baseline mechanism actually ran before trusting a 0-vs-0 comparison

The per-file delta above is only as honest as the baseline it subtracts. The
usual way to produce one is to stash the tree, measure, and pop — and the
failure is silent: if the stash did not happen (a path filter matched nothing,
a hook or filter intercepted it, the command was chained with `&&` after a
step that failed), the "HEAD baseline" is just the working tree measured
twice. Every count then reads `0` against `0`, the comparison reports **no
change**, and the conclusion is exactly backwards.

**Rule: assert the baseline differs from the working tree before believing a
zero.** A baseline that returns identical numbers for a file you know you
edited is not a clean baseline — it is a baseline that never moved.

```bash
# cheap sanity: after stashing, the file you edited must revert to HEAD
git stash push -u -m "baseline" || echo "STASH FAILED"
git diff --quiet HEAD -- <file> && echo "BASELINE INVALID: tree still equals HEAD"
```

A safer baseline needs no working-tree mutation at all, and is the default
when the work is uncommitted: materialise the `HEAD` copies into a scratch
tree and run the verifier there, so both sides are measured by the same
command with no stash to lose.

```bash
tmp=$(mktemp -d); mkdir -p "$tmp/src"
for f in src/*.rs; do git show "HEAD:$f" > "$tmp/$f"; done
verifier "$tmp"   # baseline, measured out-of-band
verifier src      # working tree
```

This also fixes the file-set trap that makes the delta silently wrong: if you
copy only the files you touched but the verifier scans a directory, the
baseline tree is *missing* files the working tree has, and the "new"
violations are an artefact of the comparison rather than of your change. Copy
the **same** file set you measure on the other side, or the two runs are not
comparable.

Corollary for the reporting rule: a violation at a line far from anything you
edited is **not** evidence that it predates you — code moves, and a verifier
reports positions in the current file, not in the diff. Establishing that
requires the baseline above, not an eyeball comparison of line numbers.

The commit-time gate is the per-file measurement, which is why it is the one
that catches this: it diffs each staged file against its own `HEAD` content,
so nothing cancels. **When a whole-repo audit says "no new violations" and you
also have a per-file gate available, run the per-file gate — the aggregate
cannot answer the question being asked.**

### A tolerance that was a placeholder becomes vacuous when the environment gets faster

A wait helper ends up with a threshold that was never a real assertion. The
shape: the slow environment meant a request needed seconds to become
observable, so instead of a predicate that could only be true after the work
completed, someone wrote a loose bound standing in for "has it had a chance
yet":

```python
if gap < 200.0:          # metres — a stand-in for "the teleport landed"
    return st
```

Under a 1 fps loop that is a harmless optimistic early-out. Restore real 60 Hz
and the same line is **always true on the first poll** — the start point is 15 m
from the target, which is under 200 — so the helper returns before the request
has been read, and every caller proceeds from the pre-request state. Nine
sequential steps each reported a failure at a different coordinate, because
each started from the wrong place, and the per-step data was individually
plausible enough to send the search after geometry.

The same helper became a genuine test as soon as the threshold was a fraction of
the thing being measured (a body width), which is the tell that the old number
was standing in for something.

**Rule: a tolerance in a wait helper must be a fraction of the quantity being
waited on, never a round number chosen to exceed anything seen so far.** When
you fix an environment-speed problem, re-read every threshold that was sized
for the slow environment — a timeout, a poll cap, a distance bound, and a
"success" predicate are all the same defect, and the predicate is the one that
reads as correct because it returns rather than hangs.

The diagnostic: a helper that returns "successfully" on its first poll, every
time, in an environment where the operation it is waiting on is known to take
more than one frame.

## A test that cannot fail is not a test — mutate the rule to prove the fixture bites

A bidirectional fixture proves the verifier passes on good input and fails on
bad input **at one moment in time**. It does not prove the test would ever
notice the rule being changed. A structural rule is especially exposed: the
verifier is a membership test over a name set, and the single most likely
future edit — widening the exemption so real code stops being reported — is
invisible to a fixture that only ever ran once.

**The proof is mutation testing: break the rule on purpose, confirm the test
catches it, restore.** Two or three mutations, each a one-line edit:

```python
import subprocess, shutil
p = SCRIPT; orig = p.read_text()
mutations = {
    "re-widen the exemption": orig.replace("EXEMPT = ENTRY", "EXEMPT = ENTRY | KEYWORD"),
    "disable the check":      orig.replace('.endswith(".rs")', "False"),
    "invert the comparison":  orig.replace("if not code_files:", "if code_files:"),
}
for name, text in mutations.items():
    assert text != orig, f"{name} did not apply — mutation is stale"
    p.write_text(text)
    rc = subprocess.run(["python3", SELF_TEST], capture_output=True).returncode
    print(f"{name:28} -> exit {rc}", "CAUGHT" if rc else "MISSED")
p.write_text(orig)          # restore unconditionally, even on failure
assert p.read_text() == orig
```

Report the table. "The test passes" is uninformative; "the test fails when the
rule is re-widened, when the check is disabled, and when the comparison is
inverted" is the claim that makes a future session trust it.

Two things this catches that a normal fixture run cannot:

- **A stale mutation.** `assert text != orig` is the guard. A rename that made
  the replace target vanish would otherwise report `CAUGHT` for a mutation
  that never applied — the worst possible failure, because it manufactures
  evidence for a test that was not exercised.
- **A test whose scope leaked.** A self-test that walks `fixtures/**/*.rs`
  instead of `fixtures/compliant/**/*.rs` sweeps the violating tree into the
  compliant assertion and reports failures that look like verifier bugs. Scope
  the walk to the case under test, and treat "the compliant case reports
  findings" as a bug in the test, never as a finding about the rule.

Restore the file in a `finally`/`assert` rather than at the end of a loop, so
an exception mid-run cannot leave the rule mutated in the skill repo.

## Prove a hook ran is a separate question from proving it passed

"Fixed the code, the hook let it through" does not establish that a hook exists, and the
cheapest apparent proof is not one. Two dead ends:

- **A clean commit message is not evidence.** Many `pre-commit` hooks print a banner and
  `exit 0` without touching the message. Read the hook script before reading anything it
  did or didn't write.
- **`.git/hooks/` may not be where hooks live.** When `core.hooksPath` is set (commonly
  globally, e.g. `~/.git-hooks`), every repo-local hook is silently ignored — it installs,
  looks correct, and never runs.

```bash
git config --get core.hooksPath     # empty => .git/hooks; set => that path, and .git/hooks is dead
ls -l "$(git config --get core.hooksPath || echo .git/hooks)/pre-commit"
```

**The one proof: a deliberate failure.** Stage a file that must trip the gate, attempt the
commit with no bypass flag, and confirm the commit did not happen:

```bash
printf 'pub fn probe() -> i32 { 42 }\n' > probe.rs   # no doc comment => trips a doc gate
git add probe.rs && git commit -m "probe"
git log --oneline -1        # must NOT show "probe"
rm probe.rs && git reset -q
```

This distinguishes three states that look identical from the outside — hook present and
passing, hook absent, and hook present but reporting a stale result — and it is cheap. The
user asking "did you bypass the hook?" is asking precisely this, and the answer must be
an experiment, not an assurance. When a hook previously *was* bypassed, that history is
the reason the question is asked; it does not substitute for re-proving the present state.

Always confirm the probe left nothing behind: the staged file is gone, `git status` is
clean, and no probe commit exists in history.

## Verify the number you are about to claim

Before writing "0 violations" into a summary, a PR body, or a commit
message, re-run the check that produced it **on the tree as it is now**.

Tool output that arrived before the last edit describes a state that no
longer exists. Re-running is cheap; a false claim in a PR body is the thing
the reader cannot detect.

The same applies to test counts. A suite that "passed" under a parallel
runner may have a race, and a suite count that changed between runs is
a signal to compare the underlying assertion totals, not the suite count.

### A green run that predates someone else's edit is not a green run

Concurrent work breaks the assumption that the tree is still what you last
measured. The check passed at 00:38; a source file was modified at 00:39.
Nothing about the result changed retroactively, so the pass you are about
to report describes a build that no longer exists — and the *source* mtime
is not even the right thing to check, because a build step may not have run
since.

**Rule: before reporting a pass on a shared tree, prove the artifact you
verified is the artifact still being served.** An mtime chain settles it
without re-running anything: if the build output predates your run and
nothing rebuilt after it, your result still stands, and you can say so with
the timestamps to back it.

```bash
stat -f '%Sm  %N' src/game.rs <build-output> <your-run-log>
# order matters: run-log < build-output < source  =>  source changed AFTER
# the binary you tested, and the binary is still the one served
git diff --stat <source>   # does the edit even touch what you measured?
```

The second command is the one that actually settles scope: a large
uncommitted diff elsewhere in the file says nothing about whether *your*
code path moved. Read the diff for the specific function the run exercised
and confirm it is untouched. Re-run when the chain says the binary moved,
when the edit does touch the measured path, or when you cannot establish the
chain.

### Another harness disagreeing with yours is usually a different artifact

The mirror image: a second tool reports the same operation failing while
yours passes. The tempting read is that your change broke it. Before
defending the result, check whether the two runs were even executing the
same thing — different build, different route geometry, different port, a
cached artifact.

**Rule: settle a cross-harness conflict by reading the live value out of the
running system, not by comparing the two logs.** Dump the value both
harnesses are asserting about and compare it to what each one recorded. If
the live value matches yours, the other harness is measuring a stale or
different artifact, and the disagreement is its staleness — say so plainly
and name what makes it stale (an output file older than your run, a
hardcoded endpoint carrying leftover state) rather than leaving the user to
assume your change regressed something.

This is a special case of the verification-by-proxy rule: the other
harness may be a faithful reimplementation whose *inputs* are out of date,
and a correct implementation plus wrong inputs produces a wrong number
that looks like a code defect. Check the inputs before the logic.

Do not "fix" the other harness to match yours without asking — it may be
another agent's, mid-edit, and its purpose (probing a different build) is
not yours to decide. Report the discrepancy, the evidence, and the one-line
change that would make it trustworthy.

### A dropped test count is a missing registration, not a flaky test

When the passing count falls, the tests did not get weaker — something stopped
compiling them. Rust in particular hides this completely: a test file on disk
that no `mod` declaration reaches is not an error, it is simply absent from
the binary. A directory split that added `tests/gesture/{mod.rs,fn.rs}` and
forgot the `mod gesture;` line in `tests/mod.rs` cost 15 tests with a green
suite and a clean build the whole time.

```bash
# attributes on disk vs. registered in the tree's mod declarations
grep -rc '#\[test\]' tests/ | awk -F: '{s+=$NF} END {print "on disk:", s}'
cargo test -p <crate> 2>&1 | grep -oE 'ok\. [0-9]+ passed'

# find test directories whose mod is never declared
# (raw identifiers: `mod r#input;` declares the directory `input`)
for d in $(find . -type d -name tests -not -path '*/target/*'); do
  for sub in "$d"/*/; do
    n=$(basename "$sub")
    grep -qE "^[[:space:]]*mod (r#)?$n[[:space:]]*;" "$d/mod.rs" \
      || echo "UNREGISTERED: $sub"
  done
done
```

**Rule: treat a lower passing count as a structural defect until proven
otherwise, and check the registration before re-running the suite.** A flake
varies run to run; a missing `mod` is constant and is fixed by one line. The
same applies to any framework where adding a file does not require a manifest
entry — the file existing proves nothing about it running.

## A flake is a defect until you have measured the rate, and a fix that passed once is not a fix

A test that fails under `--test-threads=8` and passes under `--test-threads=1`
has told you exactly one thing: state is shared across tests. It has not told
you what is shared, and it is not fixed. Serialising the whole suite in CI
converts a defect into a runtime cost nobody asked for and hides the next one;
fix the sharing instead.

**Count the shared state before adding a lock.** A failing test names one
test; the one racing it names another. Neither names the object. Read the
`static`/`OnceLock` and its `reset_for_tests` helper, then grep every access
site. What a lock has to cover is usually **not the test body** — it is
`reset + seed + assert`, because that is the window another thread can
interleave into, and the assertions are the only part that looks like
"the test".

**A guard bound to `_` is dropped immediately.** `let _ = lock.lock()` in a
test that ignores the name releases at the end of that statement, so the test
runs unserialised while reading as locked. Bind a named `_guard` and let it
live to the end of the block — RAII is what makes release correct on the
panic path too.

**Validate the fix in both directions, because the two failure modes produce
opposite evidence.**

| Run | Catches |
|---|---|
| affected module alone, repeated | self-recursion, double acquisition, per-module hang |
| full suite at high `--test-threads`, N ≥ 100 | residual races between modules |

A sweep that only ever runs the full suite cannot tell those apart, and
neither can a single clean run. A **hang must be counted as its own
anomaly, not retried** — a hung process never reports a failure, so a sweep
that treats a timeout as "flaky" looks green forever.

**Size the sweep from the rate you actually observed.** Twenty consecutive
passes have not excluded a 5% failure rate to any useful confidence; several
hundred across several thread counts have. Report `700/700 across
1/8/16/32 threads, 0 fail, 0 timeout` — a shape a reader can check — rather
than "tests pass", which after a serialisation change is the one claim that
matters.

Procedure, the isolation ladder, and the replacement-sweep recipe:
`references/flaky-test-triage.md`.

### Your own ad-hoc verification command is a gate, and a pipe disarms it

The clippy-exit-0 trap below is a *committed* gate wired to the wrong channel. The
same defect appears ad-hoc, every time you verify with a pipeline, and it is
invisible because you are looking at the count instead of the status.

The shape: `build 2>&1 | grep -cE '^error'`. When the build fails, this prints
a real number; when the build **succeeds**, it prints `0` — and `grep -c` exits
1 on zero matches, but the pipeline's status is the *last* stage's, so nothing
downstream can tell `0 because clean` from `0 because grep matched nothing`.
Reporting "0 errors" off that output is a claim you never measured. Worse, the
"did it even run" question is real: a wrong path, a missing tool, or a target
that does not exist produces the same `0`.

**Rule: capture the build's own exit status before summarizing its output.**
Never let a filter's output count stand in for the command's status.

```bash
cargo check -p <crate> > /tmp/c.log 2>&1; echo "EXIT=$?"   # status first
grep -E '^(error|warning)' /tmp/c.log | sort | uniq -c       # then the detail
```

`EXIT=0` with an empty grep is a real pass. `EXIT=101` with an empty grep means
the compile never got that far — a different failure, and reporting it as clean
is the exact error. The same applies to `| head` (SIGPIPE truncates the run),
`| tail`, and `| tee`: all of them replace the status of the thing you meant to
measure.

The tell that you have made this mistake: you are about to write a summary whose
headline is a count, and the count came from a pipeline. Go get the exit code.

## A diff that applied cleanly is not a diff that did what you meant

A patch tool reports the hunk applied; it cannot report that a line you never
intended to change changed anyway. The failure mode is invisible in the tool's
own output and only shows up in `git diff`.

**Redaction is the usual cause.** Credential-shaped literals (`$GH_TOKEN`,
`{GH_TOKEN}`, `ghp_…`, `sk-…`) are replaced with `***` in what read and diff
tools return. Text copied from one tool result into an `old_string` carries the
mask, and it lands on disk as the replacement — a working
`Authorization: token $GH_TOKEN` becomes `token ***`, the request 401s at run
time, and nothing flags it, because every hunk matched and applied. A build or
API call is where you find out, possibly much later.

**Read the whole diff, not the hunks you aimed at.** The uninvited line change
is the only evidence, and it is one `git diff` away. Concretely, before
committing an edited file:

```bash
git diff -- <file>                                  # every changed line, not just the target
grep -nE '\*\*\*' <file>                            # a mask that arrived uninvited
grep -nEi 'token|secret|password|api[_-]?key' <file>   # confirm the live references survived
```

The tell is an untouched `-$TOKEN` / `+token ***` pair sitting in a hunk you
did not target. Roll that hunk back immediately rather than continuing — each
later patch is computed against the now-corrupted file.

**The same sweep applies to a skill or template that ships a canned snippet.**
A documented example whose token reference is masked teaches the next agent to
copy the mask. Check the example, not just the prose around it.

## A passing compiler does not mean the batch edit kept the file intact

The cousin of the above, and the more expensive one. A scripted bulk rewrite
(`execute_code` over a file, `sed -i`, a "collect spans, then rebuild the
block" pass) can delete code outright, and a compile error is a *syntax* error
that names one line — nothing in it says how much is gone.

**The failure shape:** a script that rebuilds a call site from its argument
list slices from the format-argument slot onward, dropping the call opener
that precedes it. Twenty `assert!` invocations become one, and the file
compiles-fails on an unbalanced delimiter. Each fix then produces a *new* error
on a line you just edited, so the loop looks like progress for several rounds.

Three rules, in the order they bite:

- **Establish a recovery point before writing.** `git stash` or `git commit -WIP`
  first. On a dirty tree a destructive rewrite is unrecoverable — there is no
  second copy, and deleted tests can only be rewritten, not restored. This is
  the precondition, not a nicety.
- **Count semantic tokens, not just delimiters.** Paren balance catches gross
  damage but is a weak signal; a count of the things the file is *for* is a
  strong one, and it is the only check that names the loss.

  ```python
  import re
  s = open(path).read()
  mod = s[s.index("#[cfg(test)]"):]          # or the region you rewrote
  clean = re.sub(r'//.*', '', re.sub(r'"(?:\\.|[^"\\])*"', '""', mod))  # mask, then strip
  print(clean.count("("), clean.count(")"))   # balanced?
  print(len(re.findall(r'\bassert!', clean))) # the token you were protecting
  ```

  Mask strings before stripping comments, or brackets inside string literals
  make balance lie in both directions.
- **Bound a find-and-replace by the match count before running it.** A fix
  scoped to "the three call sites I introduced" is expressed as a bare
  string replace, which happily matches the seven pre-existing identical
  sites too. Count first (`s.count(old)`), replace only what you meant, or
  scope by surrounding context — an unannounced edit to unrelated code is
  indistinguishable from drift when the diff is read later, and it is
  reviewed as noise.
- **Never use a destructive git command to undo one bad edit inside a file
  you have been working in.** Recovering a single bad declaration by
  reverting the whole file to `HEAD` also reverts every good change you made
  to that file since — the completed test, the corrected geometry, hours of
  work — and those cost more to rewrite than the mistake did to make. Fix the
  bad lines in place, or snapshot the file first
  (`cp src/f.rs /tmp/f.rs.bak`) and revert from the copy. See
  `systematic-debugging` § "Never use a destructive git command to isolate a
  regression" for the full table.
- **Treat rising error complexity as a stop signal, not a work item.** If the
  error *type* changes each round (`must be a string literal` → `argument never
  used` → `multiple unused arguments`) and the new locations sit on lines you
  just edited, you are not converging — you are generating. Stop, read the
  bytes, revert.

The safe counterpart is worth stating too: `patch` with an exact
`old_string`, and scripts that **replace in place and print before/after**
rather than reconstruct a buffer. In-place edits fail loudly and leave the file
untouched; structural rebuilds fail quietly and take neighbours with them.

And the recovery lesson generalizes past edits: when a batch rewrite has
already damaged a file, the first useful move is to commit whatever *is*
intact before attempting more repairs. A known-good subset is recoverable; a
half-repaired file is not.

## A gate can read the wrong channel and still print a green verdict

Some tools separate "did the command succeed" from "did it find anything",
and the gate wires itself to the first one. `cargo clippy` exits **0** with
any number of `warning:` diagnostics — warnings are not errors unless
`-D warnings` is passed. A gate written as:

```python
rc = run(["cargo", "clippy", "--all-targets", "--quiet"])
if rc == 0:
    print("PASS (0 warnings)")     # ← the "0 warnings" is a literal
    return True
```

reports PASS for every repository, forever, and the count in the message is
a hardcoded string rather than a measurement. It is indistinguishable from a
working gate by reading its output — the failure only appears when you count
the diagnostics yourself.

The tell is a **number in the output that is not computed anywhere in the
code**. Any gate whose success line quotes a quantity ("0 warnings", "0
violations", "clean") must derive that quantity from the run. If the string
is only ever reached through the success branch, it proves nothing.

**Count the channel the rule is about, not the process's exit status.**
Grep the raw output for the diagnostic prefix itself:

```bash
cargo clippy --all-targets 2>&1 | grep -cE '^warning:'   # the real number
cargo clippy --all-targets --quiet; echo $?             # always 0 — useless
```

Match only the **column-0** prefix (`^warning:`, `^error:`). The indented
continuation lines — `--> file:line`, `= note:`, `= help:` — make one
warning count as three or four if you substring-match `warning:` anywhere in
the line, which inflates the total and makes a correct fix look insufficient.

**This class of bug survives a green CI run.** CI's own clippy step runs
without `-D warnings` too, so the repo's pipeline and the local gate both
report success. Two independent gates reading the same wrong channel are not
two confirmations.

## A host runtime that swallows the exit code is the same bug with no escape hatch

The clippy case above is a *tool* that exits 0 over findings. This is worse: a
**host interpreter that exits 0 over every failure, including the ones that
should never have been ambiguous.** Blender's `--python` runs a script and
returns 0 regardless of what happened inside it:

| what the script does | process exit |
|---|---|
| `raise AttributeError(...)` | **0** (traceback on stdout) |
| `sys.exit(1)` | 1 |
| `sys.exit(0)` | 0 |

A gate that prints its verdict and falls off the end therefore reports success
to every shell, every `&&` chain and every CI step. The traceback is right
there in the log next to `EXIT=0`, and both numbers are true at once — which is
what makes it survive: a reader scanning for the status sees a pass, and a
reader scanning for errors sees a crash, and neither resolves it.

**Rule: a script-in-host gate is only a gate if it calls the host's explicit
exit itself.** Put the conversion in one place — the module-level wrapper, not
each `main()`:

```python
def main() -> int:
    ...
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())          # the only line that can make the shell see it
```

Two details that matter. A gate returning its **failure count** instead of
0/1 is a valid non-zero status but says nothing anywhere except its own
print — return 0/1 and put the count in the message. And the wrapper must not
assume `main()` returns: `sys.exit(main() if isinstance(main(), int) else 0)`
keeps a `None`-returning path from becoming an unconditional pass.

**Sweep for the shape before fixing one file.** Six gates in one repo had it,
and none of them was discoverable from the outside — no caller imported them,
so no test failed and no CI job ran. Find them structurally: list the scripts
that print a verdict-shaped string, and check each for an explicit exit.

```bash
# every script whose output contains a verdict word
grep -rlE '_OK|_FAIL|_CLEAN' --include='*.py' . | while read -r f; do
  grep -qE 'sys\.exit|raise SystemExit' "$f" || echo "NO EXIT PATH: $f"
done
```

**The fix's payoff is that it makes real findings visible, and that is a
regression in the numbers.** After wiring the exit codes, a gate that had been
reporting failure into exit 0 since it was written suddenly started reporting
`FAIL` — for a geometry defect that had been there all along. Expect the pass
rate to drop when a read-wrong-channel gate is repaired, and report the
before/after per gate rather than the lower number alone.

### A gate that cannot identify the artifact it opened is measuring a lottery

The companion defect, and it hides a green result just as effectively. When the
thing a gate inspects is a **build artifact rather than a tracked source** —
a compiled binary, a generated bundle, a `.blend`/`.gltf`/model file, a
database — a gate that opens it cannot tell a fresh build from one three edits
stale, because nothing ties the file to the code that produced it. The gate
reports on whatever is on disk, and "the gates pass" never implies "the gates
ran against the current source."

It is usually reached by accident: a long build launched before an edit
finished after it, overwriting the artifact from a tree that no longer existed,
with nothing in the output saying so. No harm done that time, because the
refactor happened to be value-identical — which is exactly the point. It was
luck, and the next race would not be.

**Rule: when a gate reads a build artifact, make the artifact carry its
provenance and the gate check it.** Write a stamp into the file at save time
and compare it on open:

```python
# builder, before save_as_mainfile / before write
txt = bpy.data.texts.get("BUILD_STAMP") or bpy.data.texts.new("BUILD_STAMP")
txt.clear()
txt.write("spec_mtime: %d\nbuilder_mtime: %d\n"
          % (int(os.path.getmtime(SPEC_PATH)), int(os.path.getmtime(__file__))))
```

```python
# gate, right after opening
stamp = bpy.data.texts.get("BUILD_STAMP")
if stamp is None:
    print("STALE  no stamp - cannot show this matches the current builder")
else:
    print("stamp  spec %s" % ("current" if _field(stamp.as_string(), "spec_mtime")
                              == int(os.path.getmtime(SPEC_PATH)) else "STALE"))
```

mtimes rather than a content hash: the only question that matters is "is the
code next to this file newer than the file", and a hash is a second thing that
can go stale on its own.

Mutation-test it in both directions — a fresh artifact must read `current`,
and touching a source without rebuilding must read `STALE`. A freshness check
never exercised against a stale case is a check that has never fired.

Know the honest limit and state it rather than working around it: **restoring
a file's contents does not restore its mtime**, so after a `git checkout` the
stamp stays `STALE` until the next build. That is the correct answer — the
stamp genuinely cannot show the sources match — but it means a gate driven to
report `STALE` needs a rebuild to clear, not a checkout. Say so, or the next
session debugs a phantom staleness bug.

## A check whose script is missing passes vacuously

An audit runner that shells out to one script per rule and treats empty
output as a pass will report success for any rule whose script was never
written, was renamed, or was deleted. Nothing errors, the rule is absent
from every report, and its check number keeps appearing in the summary as
though it were contributing.

**A check that has never fired is indistinguishable from a check that always
passes.** Sweep the runner for every script it names and prove each one
exists, instead of trusting the numbering:

```bash
grep -oE 'verify_[a-z_0-9]+\.py' <audit-runner>.py | sort -u | while read -r s; do
  [ -f "scripts/$s" ] || echo "MISSING: $s"
done
```

Every `MISSING` line is a rule you have been citing as protection and do not
have — and because its enforcement was also being applied by hand, the manual
compliance reads as automated coverage.

**Treat the discovery as a scope question before you start writing.** The
sweep tells you the scripts are absent, not how many rules they were meant to
cover. Split the misses by whether the rule is *specified*: a rule whose
section exists in the references directory is a pure enforcement gap (write the
script from the spec), while a shell template that names a script no document
describes is a spec gap too, and a script written for it would be inventing a
rule. Read the rule section and the existing sibling verifiers before writing
anything — the sibling covering an adjacent section tells you the output
contract, the summary-line prefix the audit greps away, and the exit-code
convention all at once.

**Fixing the wrapper exposes the gap rather than closing it, and the pass rate
you get is not the one you will report.** Going from "silently passing" to
"explicitly failing" converts every un-written rule into a red row on your
first run. That drop is the size of the coverage you were citing, so report
before/after per repo rather than the lower number alone as a regression.

**Sweep the other caller before claiming the rule is protected.** An audit
runner and a per-file commit gate are separate tables, and registering only in
the runner leaves the rule absent from the gate the user actually runs on every
commit. Settle it by *loading* every entry rather than reading the dict — an
entry naming a script that does not import is a permanent silent zero, and a
dict read proves nothing about it:

```python
for name in VERIFIERS:                      # import, do not just read
    if load_verifier(scripts_dir, name) is None:
        print('unloadable:', name)
```

Then prove the gate *blocks*: stage a file that trips the new rule, run the
gate, confirm the FAIL and that `HEAD` did not move. A registered verifier that
has never blocked a commit in your session has not been shown to work.

**Write the missing scripts AND fix the wrapper's pass condition.** A runner
that maps "empty stdout" to PASS cannot distinguish "scanned everything, found
nothing" from "the verifier never ran", and while that condition stands every
future missing or crashing script is masked identically. Empty output is
ambiguous; the pass condition has to treat it as a verdict only when the
companion exited clean with no interpreter-level error:

```python
if not out:                                # empty is not yet a pass
    crashed = [l for l in r.stderr.split('\n')
               if 'No such file or directory' in l and '.py' in l]
    if crashed:
        return name, ['FAIL: companion verifier is missing — ' + crashed[0].strip()]
return name, out
```

Two interactions to respect. A FAIL trailer printed to **stdout** is counted as
a finding and inflates every total by one, so decide deliberately which stream
carries it. And expect the pass rate to **drop** when the repair lands — that
drop is the size of the coverage you were citing and did not have, so report
before/after totals per repo rather than presenting the new number alone.

**A repaired gate proves itself the first time it blocks you.** The strongest
available evidence that a read-wrong-channel gate is now honest is that it
refuses a commit you were about to make — the change you just authored, on a
repo you believe is clean. A gate that has never blocked anything in this
session has not been shown to work, and quoting its green output as validation
is quoting the bug back at yourself.

## A check that is present, registered, and inert is the same bug in a better mask

The missing-script case above is easy to spot because the runner names a file
that does not exist. The harder sibling is a check whose script exists, is
registered in every layer, exits 0, and **examines nothing** — because the
check's own body is inert. In every report, forever, it is indistinguishable
from a passing check.

The mechanism is embedding. A check authored as a shell heredoc inside a
Python triple-quoted string inside a bash template has three escaping layers,
and a layer that is one too deep does not raise — it produces a construct that
runs cleanly and computes the wrong thing:

| Written as | Evaluates to | Effect |
|---|---|---|
| `text.split("\\n")` | split on a literal backslash-`n` | `lines` is one element; the loop body never runs once |
| `r'^@@\\s+…'` | matches a literal backslash | no hunk header ever matches; every file `continue`s |
| `line.count("{")` over `format!("…{{…}}")` | counts literal braces | depth explodes and never returns to zero |

**Rule: when a check reports a suspiciously small number on a repo you have
reason to believe is dirty, suspect the check before the repo — and settle it
with a true-positive fixture.**

The diagnostic has one direction that carries all the information. When the
job is removing false positives, every compliant fixture proves nothing: a
check reporting 0 everywhere passes them all. The only evidence your fix kept
the rule alive is a fixture that must still report a **true positive**, and
`expected 1, got 0` means you did not fix the check, you deleted it.

This is why "it went down" is not evidence. On a check that was already
phantom, the *correct* end state for the real repo is also 0 — so the repo's
own number cannot distinguish a working fix from a dead check, and only the
fixture count can.

**Print the first intermediate that should have been non-empty, before
reasoning about the escaping.** Extract the check's body, run it on the
violating fixture, and read two values:

```python
lines = text.split("\n")
print("line count:", len(lines))   # 1  -> the split is wrong
print("hunks:", hunk_ranges)       # [] -> the regex is wrong
```

Both were wrong in one run — cheaper than deriving the escaping from source by
eye, and it names which layer to fix instead of "the check is broken".

**Anchor file reads to the repo root; a relative path in a template with no
`cd` reads the caller's cwd.** `open(f)` where `f` comes from
`git diff --name-only` silently depends on where the runner happened to be
invoked from, so the same check reports findings in one directory and nothing
in another. `os.path.join(root, f)` — and note the failure is a clean exit 0,
not an error.

**Scope a replacement to the template you are editing, and keep a restore
point.** A check file routinely holds several templates whose bodies are
byte-identical (a brace-counting loop is a natural thing to write twice), so
`text.replace(old, new, 1)` edits whichever comes first — possibly a
different rule. Slice the specific template out, patch inside the slice, and
assert the match count *within the slice* before writing.

When the check file is under version control, recover rather than reconstruct:

```bash
git -C <skill-repo> show HEAD:scripts/audit.py > /tmp/audit.orig.py
```

A mistaken global edit dropped 33KB of checks and still parsed as plausible
text until the next syntax check. The committed copy is the only cheap ground
truth, and `git status --porcelain <path>` tells you in one command whether
you are editing something that has a committed ancestor.

## A rule can be registered in every layer and enforced by none

A new check is usually reachable from several places, and each is a separate
opportunity to be silently dead. Enumerate the layers and settle each with one
grep before describing a rule as protected:

| Layer | Question that settles it |
|---|---|
| Per-file commit gate | Is it in the gate's verifier list at all? If its entry point takes a *file*, it cannot express a *directory* rule. |
| CI | Does any job invoke the audit? A test or lint job that does not import it is not enforcing it. |
| Local pre-flight | Is the phase that runs it gated behind unrelated legacy failures? If so the new check's signal dies with the legacy ones. |

```bash
grep -n 'verify_<rule>' <gate-script>
grep -rln 'verify_<rule>\|audit_' .github/workflows/
```

A rule whose only caller is a phase already failing on other findings is
documented, tested, fixture-verified — and enforcing nothing. Write the scope
limitation next to the rule in the spec ("whole-repo audit only; no single
file exhibits this violation"), and get a real enforcement point into CI
before calling the rule protected.

## A rule's prescribed fix is part of the rule — vet it against the toolchain

A rule that says "the file must move to `X/X.rs`" has, by construction,
prescribed a layout that some linter may flag. Shipping the rule before
running the prescribed fix past clippy means discovering the conflict after
the refactor has already landed in one or more repos.

**Before writing a rule that mandates a structural change, apply that change
to one directory and run the toolchain.** The question is not "is the rule
well-formed" but "is its own remedy clean under the project's other gates".

Two failure shapes, both silent:

- **The remedy trips a default-on lint.** A module named identically to its
  containing directory is `clippy::module_inception` (warn by default). It
  is the unavoidable consequence of "name the file after the directory" —
  `mod.rs` must declare `mod r#impl;`, and that names the module `impl`
  inside directory `impl`.
- **The strict reading mislabels valid files.** "No `.rs` beside a
  directory" flags every keyword file and every `macro.rs` that legitimately
  sits alongside sub-modules. Measure how many files the strict version
  flags before adopting it; if a real repo carries dozens of them, the rule
  is wrong at the scope level, not the file level.

**Measure the baseline before the change, not after.** A repo already at
zero warnings turns "two new warnings" from invisible noise into a measured
regression; a repo carrying hundreds buries it. Get `grep -cE '^warning:'` on
the untouched tree first, then again after applying the remedy — the delta
is the argument for narrowing the rule or dropping it.

Narrowing to what the rule was actually for is usually the right exit. If the
rule's purpose was "no orphan file with no module name", then exempting the
files that *do* have one keeps the intent while dropping the cost.

**Narrowing a rule re-opens work you already shipped.** The files the strict
reading flagged were fixed under the wide rule; once they are exempt, those
commits are the only remaining source of the warnings you just measured. Expect
a revert of your own earlier remediation and treat it as routine, not as a
regression — the work was correct under the rule as written at the time.

**When a gate blocks the change you just made, that is the deliverable, not an
obstacle.** A structural fix whose cost is a lint warning has exactly one
honest exit when the project forbids suppression: report the number, name the
files, and let the user choose scope. Do not re-derive the decision for them —
a rule's exemption list and a repo's warning budget are both standing
constraints the user owns, and the two conflict by construction. Deliver the
finding with both options and their measured costs.

**A rule's prescribed fix can be clean under every linter and still destroy
something the user cares about — vet the remedy for coverage loss, not only for
warnings.** A layout rule whose remedy is "a `pub(crate)` item has no test, so
delete the whole `#[cfg(test)] mod tests`" passes its own terms and compiles
clean. It also removes the only thing asserting the invariants that item
existed to hold — here, that four generated names share a suffix, that each is
a legal JS identifier, and that retired names do not survive. One of those
tests had caught a real bug (an illegal `-` in the identifier charset) at a
1-in-8 flake rate, and after the deletion nothing would catch its return.

The trap is that the coverage loss is invisible to every gate you have. Test
counts falling is the only signal, and a rule-driven removal *reads* as an
improvement. So when a rule's remedy deletes code rather than moving it, the
removal is the finding, and the report has to carry it:

- what the deleted tests asserted, in invariants rather than test names;
- which of those invariants nothing else checks now;
- what the coverage-restoring alternative costs — here, widening
  `pub(crate)` to `pub` so an integration test can reach it, which a *second*
  rule forbids, so it is a public-API decision and not one to make silently in
  a cleanup commit.

**Report a coverage loss as a cost in the first paragraph, not as a footnote
under a test-count change.** "618 → 612 tests" reads as noise or a flake; the
same delta with "these six were the only coverage of X" reads as a decision the
user needs to make. When a rule and another rule make the coverage-restoring fix
illegal, that is a genuine conflict between two constraints the user owns — put
both in front of them with their costs rather than picking the one that makes
your diff smallest.

**Do not commit on top of a run you are waiting on.** A release or publish
workflow in flight makes the default branch's content a moving target: pushing
a follow-up commit mid-run either lands inside the run being measured (the
green result then describes a tree nobody shipped) or forces a second run that
re-publishes what the first already published. Stage and commit locally, hold
the push until the run reports, and say which run you are waiting on.

## A constant you did not read at runtime is a constant you cannot compare against

The third cousin, and the one that hides best. A guard written against a
binding-layer constant can be permanently false while everything it guards is
fine, because the constant and the function disagree about their own numbering.

In `web-sys`, `WebGl2RenderingContext::FRAMEBUFFER_COMPLETE` is **36053** (the
WebGL 1 value) but `checkFramebufferStatus` returns **36054** for a WebGL 2
complete framebuffer. The comparison is never true, so every render target is
declared broken, the app falls back to software rendering, and the canvas is
black — while "all targets allocated" logs read healthy.

**Rule: when a status/error comparison looks permanently false, read both
sides out of the live runtime before concluding anything about the system
being compared.**

```js
// one Runtime.evaluate settles it
const gl = document.createElement('canvas').getContext('webgl2');
({ complete: gl.FRAMEBUFFER_COMPLETE, status: gl.checkFramebufferStatus(gl.FRAMEBUFFER) });
```

The mirror image is the trap that wastes the time: a probe whose decoder table
is written from the spec rather than from the runtime reports every real
`INCOMPLETE_*` code as "COMPLETE", and you conclude the application is fine
while its own log disagrees. **Both sides of a comparison must come from the
runtime, never from memory** — the probe that validates the probe is part of
the method.

Two corroborating habits from the same session:

- **A non-zero "objects submitted / triangles drawn" counter is not evidence
  that anything reached the screen.** It proves geometry reached the pipeline.
  To distinguish "dim but real" from "HUD over an empty canvas", measure the
  screenshot: fraction of pure-black pixels and mean channel value. The HUD
  draws over the canvas, so a small non-black fraction is expected — the
  question is whether the world region has anything.
- **Filter the console for content, not for severity.** Compiler and driver
  diagnostics arrive as plain `[log]`-level lines. A capture that keeps only
  `error`/`warning` types drops exactly the message that explains the symptom.

And do not let a software-GL (SwiftShader) headless context stand in for
"WebGL is unavailable here" — it reports its own limitations as driver-level
incompleteness, which sends you chasing a headless artifact instead of the
application's bug. Confirm the backend's health first, then read the app's own
reported error.

## Prove the channel is live before naming an application defect

A harness reading that contradicts the source is evidence about **the channel**,
not about the application. Four separate "defects" in one investigation were
each a measurement pointed at a field nothing writes: a speed multiplier that
is really a time-warp scale (assigned at one site, never read — so 1× and 8×
were bit-identical); a "stalled" walk that was a counter published every third
frame; a vehicle that would not start because the actor stood 12 m from it,
outside the interaction radius; a weapon that never fired because the test sent
key events while the trigger is a canvas `mousedown`. Each read as a clean,
specific, actionable defect with plausible numbers attached.

**Rule: before writing "the application is broken", prove the field you read is
written by the code path you think writes it.** Three cheap checks settle it:

```bash
# 1. is the field ever READ? (write-only fields read as permanently constant)
grep -rn '<field>' src/ | awk -F: '{print $3}' | sort -u   # declared / assigned / init only?
# 2. is the event the test injects the one the code binds?
grep -rn 'mousedown\|keydown\|dispatchMouseEvent\|dispatchKeyEvent' src/
# 3. is the precondition of the test scenario actually established?
#    (interactable range, target in reach, element in the viewport)
```

The signature of a dead channel: **an implausible measurement that is also
bit-identical across inputs that must differ.** Two settings producing the same
number to every digit is not a coincidence — it means nothing is scaling it.

**And the harness reading can be right while the verdict is wrong.** A check
whose `note` says "no such keybind exists in the source" while its own numeric
field shows the keybind firing is a broken gate, not a missing feature. When a
check's prose and its measurement disagree, the measurement is the evidence and
the gate needs fixing.

**Three runs of one scenario producing three different pictures means the
metric is not measuring a stable fact.** When a diagnostic is derived from a
value the probe computes (a chosen collider, a guessed bounding box), it is
only as good as that choice, and the choice varies per run. Stop re-running it
and go read the authoritative geometry out of the source; until you have, the
honest report is "not qualified", and re-running the same derived metric three
times is not evidence gathering.

### A fix validated at one speed is not a fix until it is validated at the boundary

The most expensive survivor: a root cause found correctly, a fix written that
addresses it, and every report saying PASS — with the defect still fully
present. The mechanism was right at the value it was tuned to and wrong at the
largest value the system accepts.

A stair-climb fix subdivided each frame's movement into substeps, so a long
frame could not skip a tread. It was verified twice by two agents, both
reporting `peak_y == 3.20, dy<0 == 0`, and the fix was believed. The substep
count had been derived from the *walk* speed (0.613 m/frame). Sprint is
`RUN_SPEED/WALK_SPEED` = 1.8–2.2x that (1.0–1.08 m/frame measured), and at
that stride a single substep still cleared more than one tread: `y` never rose
above the first step and the player ran off the far end of the staircase. Two
agents' PASS reports were both accurate — for the regime each one sampled.

**Rule: a fix tuned to a magnitude is verified across the range the system
accepts, not at the value that motivated it.** Sweep the input dimension the
fix consumes, and record the *sweep* in the report, not just the value that
passed:

- Fix consumes per-frame displacement → test the fastest speed the game
  accepts, not the default one.
- Fix consumes elapsed time / distance → test min and max, and the boundary
  between them.
- Fix consumes a count of items → test 1 and N, where N is the cap.
- Fix is a tolerance / substep / iteration budget → the question is not
  "is it enough for the case I saw" but "what is the largest input that
  breaks it", and that number belongs in a test.

A regression test that pins only the tuning value will keep passing after the
boundary regresses. Pin the boundary case too, or the fix is a constant that
happens to be currently sufficient.

**And when a fix's mechanism is a subdivision, verify the subdivision is
derived from the input rather than fixed.** A hardcoded substep count
calibrated at one speed is the same defect wearing the fix's clothes: a
`SUPPORT_SUBSTEP_DISTANCE` derived from `ceil(span / distance)` is adaptive and
holds at any speed; a `SUBDIVISIONS: usize = 4` chosen to make one case pass
does not, and the two are indistinguishable from their callers.

**Never launder a harness failure into an application verdict.** A crashed
worker, a `SIGTERM`/`exit 143`, a closed CDP socket, a wrong interpreter, a
missing dependency, a syntax error in the probe — each is the harness failing
to measure, and each is a third state that is neither PASS nor FAIL. Discard
the run and re-run it; do not report its partial readings as findings. Equally,
when you cause one yourself (killing a browser profile another agent is
driving), label the readings lost to your own action rather than quietly
dropping them.

Soak and stress harnesses fail in a further three ways that all present as a
clean report: a trigger that fires but never completes, a measuring helper that
crashes on the degenerate state it exists to probe, and a log that caps its own
diagnostics so silence starts reading as success. See
`references/trigger-integrity.md`.

## When every technique reports the same failure, the shared wrapper is the suspect

The case above is a probe aimed at the wrong DOM node. The sharper sibling is a
probe whose **own accessor lies about the shape of what it returns**, so every
question asked through it reads as a negative no matter what the system did.

One investigation concluded a third-party UI "refuses synthetic input", on the
strength of six activation techniques that all failed identically. Every one of
them was a caller reading a helper that wrapped the real answer into a
diagnostic string, so `.get("opened")` on a `{"opened": true}` reply was always
`None`. Four more defects in the same family followed, each reported as the
external system refusing to act while it had acted: an exact length compare
that no multi-line text can ever satisfy, a verification query looking for a
link in a place the app never puts one, a lookup that never returned to the
scroll position it had changed, and a collapsed view whose visible text is a
prefix rather than the whole. Nothing about the external system was ever the
problem, and it worked the whole time.

**Rule: N techniques agreeing on the same failure is evidence about the code
they share, not about the target.** Agreement this uniform cannot come from the
outside — a real target that blocks one activation path rarely blocks five
equally. So before concluding anything about the external system, print the raw
value crossing your own wrapper's boundary, with its type:

```python
print(type(raw), repr(raw)[:200])     # what actually came back
print(type(derived))                   # what the caller turned it into
```

A helper that can hand back a bare string, an object, or an error marker is the
whole bug: the caller has one shape to read and three shapes to handle, so two
of the three are misread as a legitimate answer. **Normalise at the boundary —
parse, or wrap, so exactly one shape leaves the helper** — and never let a
caller read a field out of a value whose type it has not checked.

Two rules that follow from the same measurement, and generalise past this
system:

- **A compare that must succeed on a correct input is not evidence about the
  input.** Before treating a length mismatch as a defect, ask whether the format
  can even represent the value: text nodes do not contain newlines, so an exact
  compare against multi-line source can never pass. Normalise to the invariant
  (non-space characters) and compare that.
- **A verification step run after the action changed the view may be reading the
  wrong place.** Scrolling to reach a target and not returning leaves the new
  result off-screen; scroll back to where new content appears before concluding
  nothing was created.

**Never promote a negative into a persistent claim about the outside world.**
Write "the app rejected the input" to a scratch note; write "the input path does
not work, X refuses synthetic input" to a doc only after the wrapper boundary
has been printed and the target identified by capability rather than by name.
The negative that becomes a document becomes the premise every later session
starts from, and it will not be re-tested — it will be cited, and the working
path will never be attempted.

## A probe that measures the wrong subject reports truthfully and is still worthless

The most dangerous failure in this document is not a probe that lies. It is a
probe that works perfectly, returns a real number, and measures something other
than the thing the question was about. There is no error to notice: the
`fetch` succeeds, the `disabled` flag is read from a real element, the
comparison is correct arithmetic. The answer is simply about the wrong object,
and it is indistinguishable from a correct negative unless you check what the
probe was pointed at.

**The shape, across three probes in one investigation.** Six input techniques
were tried against a rich-text editor and all six "proved" it undrivable. They
were not six failures — they were six truthful measurements of a
**non-editable display node** that sits above the real editor and carries a
similar testid. The real editor was found afterwards by probing candidates for
`contenteditable` and `role` rather than by trusting the testid name, and the
very first technique then worked. Every "impossible" was an artifact of
targeting, discovered only because a later probe re-derived the claim from a
corrected target.

**Rule: before reporting a negative result, name the subject the probe
measured and prove it is the subject you meant.** Two questions, and the
second is the one that gets skipped:

- Is this the object the question is about? (identity)
- Is the probe's failure mode specific to that object, or would any input fail
  the same way? (discrimination)

A probe that returns "unchanged" for a DOM write, a keystroke, a framework
state injection, and a paste is not four independent results — four consistent
failures are what a probe aimed at the wrong node looks like. Independence is
evidence; agreement this uniform is a warning.

**Verify the target by capability, not by name.** Identifiers are conventions;
capabilities are facts. A node that can be edited announces itself:

```javascript
[...document.querySelectorAll('[data-testid*="ext"],[data-testid*="extarea"]')]
  .map(e => ({ id: e.getAttribute('data-testid'),
               editable: e.isContentEditable, role: e.getAttribute('role'),
               len: (e.innerText || '').length }))
```

Read this **before** attempting a write, not after several have failed. Two
elements in one component differing only by a suffix in their testid, one
`contenteditable: true` and one `null`, is the whole bug.

**The same trap in a measurement loop: read every candidate, never the first
match.** A label regex plus `.find()` over a filtered list picks *a* button
when the component has two, and the readings then contradict each other
spuriously — an empty field and a full 188-character one both reporting enabled,
the full one reporting disabled. Contradiction means the probe is
underspecified, not that the app is non-deterministic. Select all candidates
and report the list; the contradiction resolves into "I was reporting on
different elements".

**A conclusion reached on a mis-targeted probe must be retracted in the terms
it was made, not quietly superseded.** The user acts on a confident "impossible"
— handing the task to a human, or abandoning an approach that works. Fix the
record as explicitly as you made it, and re-derive the earlier claim from the
corrected probe rather than leaving a stale "cannot" sitting in a doc where the
next session will read it as a settled fact.

## A green test can validate a reimplementation instead of the code that ships

The subtler cousin of the read-wrong-channel gate: the tests pass, and they
never touched the shipped code path. The shape is verification by proxy —
you re-derive the logic somewhere it is convenient to test (a throwaway
script, a scratch language, a standalone snippet), confirm the *algorithm*
is right, then port it to the real implementation. Nothing in the suite
exercises the copy that actually runs.

**Why it survives review:** the scratch copy and the shipped copy agree with
each other, so every check on the scratch side is green. The only difference
between "verified" and "broken" is the transcription itself, and one
differing character is enough. Date/calendar arithmetic is the classic
host — a month-stride off-by-one shifts every parsed value by a whole
month, which no single hand-typed test case reveals.

**Rule: when the logic is non-trivial enough that you reimplemented it to
test it, add a test that calls the shipped function.** Concretely:

- Exercise the real entry point, not a twin of it. `use super::*` reaching
  an internal helper is still the shipped function; a local re-derivation
  in the test file is not.
- Sweep the shipped function across the whole input class (every month of
  several years, both parities, the boundary cases) rather than one
  hand-typed example. A per-category error cannot hide behind a single
  case that happens to be correct.
- **Work backwards from the number a failed run actually produced.** Given
  a wrong output logged in production, recover the input the buggy code
  must have consumed, then assert the corrected code lands somewhere
  plausible — and that the old formula reproduces the logged value
  exactly. A fix that cannot reproduce the observed failure is not
  confirmed.
- Assert the **bounds**, not just the direction. A test asserting
  `wait >= FLOOR` passes for a value 30 days off. Assert an upper bound
  too, or the assertion is a floor test wearing a correctness test's name.

When a test asserts a property you have just deliberately changed, the
test is the bug: rename it to state the rule it now covers, or delete it. A
named test encoding a removed rule will keep it alive against the next
change.

## A verifier that reports a grammar-constrained literal is a verifier bug, not a finding

Some rules exist because the language will not let you do otherwise. A macro
whose format string must be a *literal* (`assert!`, `assert_eq!`, `panic!` —
the format string is the second or third argument, after the condition or the
compared values) cannot be routed through a `const.rs` at all: passing a
constant compiles to `multiple unused formatting arguments`, and hoisting the
message into a `const` is not an option the language offers.

When a lint reports those, the finding is an artefact of the linter's
argument-counting assumption, and the honest response is to **fix the
verifier**, not to contort the code to satisfy a rule it cannot be in
compliance with. Concretely: a scanner that assumes "the format string is
argument 0" for every format macro mis-credits the line holding the condition
as the format string and then reports the real format string as a violation.
The fix is a per-macro index table (`assert` → 1, `assert_eq`/`assert_ne` → 2,
`write`/`writeln` → 1, `format`/`println`/`panic!` → 0).

**The tell that a reported violation is a verifier bug, not a finding: the
finding is a bare `{}` placeholder pattern, or extracting it is impossible or
would break the build.** Fix the tool.

Because widening an exemption is exactly the edit that silently disables
detection, prove the fix both ways before believing it — a compliant fixture
that must now report 0, and a violating fixture that must still report every
real string it contained before, ideally including a decoy placed in a
non-exempt position. A fix that makes the compliant side pass while the
violating side's count drops is a disabled check wearing a passing one.

### A lint calling an import redundant is not a lint saying the import is unused

`hidden_glob_reexports` ("private item shadows public glob re-export") on an
explicit `pub(crate) use std::iter::Iterator;` reads as noise, and deleting it
is the obvious response. It is load-bearing whenever a glob in that module
exports the **same name as a different kind of item** — `web_sys::*` exports
a *struct* `Iterator` that shadows the *trait*, so every `impl Iterator<…>` in
the crate then fails with `expected trait, found struct`.

**Rule: before deleting an import a lint calls redundant, check whether a glob
in the same module exports that name as a non-trait item.** One grep settles
it, and it is cheap next to a build that breaks in every file that uses the
name. The glob and the import were each load-bearing — at the same
resolution point, in opposite directions — so removing the import is the one
warning-cleanup action that can break the build rather than clean it.

**A parser fix that makes findings explode is the same regression wearing the
opposite mask, and the repo-wide delta is the instrument.** The narrow fix for a
macro-argument parser is usually a per-macro index table plus a single-line
special case. The tempting "improvement" is a general rewrite — tracking
nesting depth so multi-line conditions parse correctly — and it is where this
class of fix usually goes wrong: a depth heuristic mis-classifies the
common shapes and reports nearly every call site in a previously-clean codebase.
That is not a stricter gate, it is a broken one, and the count going from a
handful to thousands is the signal.

Measure the full-repo finding count before and after, not just the fixture:

```bash
<verifier> /tmp/baseline-tree   # HEAD copies, same verifier, whole tree
<verifier> "$PWD"               # working tree
```

An increase on a tree that was previously near zero is the regression, and the
right move is to **revert the broad rewrite, keep the narrow verified fix, and
write down the shape the parser does not support.** Documenting a known
limitation is strictly better than shipping a rewrite whose output nobody trusts
— a verifier that reports a thousand false positives gets disabled wholesale,
taking the real detections with it. Ship the smallest change that made the
targeted finding disappear and the fixture pass; a parser that is honest about
its boundary beats one that is comprehensive and wrong.

## A rule's prose can contradict the repo's own template, and a swallowed read can make that thousands of findings

Two compounding defects, both invisible to a hand-written fixture, both found
only by running a new verifier against real repositories.

**The prose and the template are not the same authority.** A rule written as
"the three stages carry no blank lines between them" can be implemented
literally while the repo's own canonical template for that file — and every
compliant instance in every real crate — separates the stages with a blank line.
What the prose meant was *no blank line inside one stage*; the canonical file
settles which reading is correct, and it is the one that is right, because it is
what the codebase actually does and what passed review.

**Read the template and two real instances before writing the check.** They are
the ground truth; the prose is the description of them. When they disagree, the
template wins and the prose is the bug — fix the sentence, not the verifier.

```bash
# the template the rule points at, and the files it is supposed to describe
cat <skill>/templates/<shape>.md
find <real-repo> -name '<shape>.rs' -not -path '*/target/*' | head -3 | xargs -I{} sh -c 'echo "== {}"; cat {}'
```

**A broad `except OSError` around a file the rule classifies on turns one bug
into a wrong verdict for the whole corpus.** Assigning a *directory* to a
variable that is later `.read_text()` raises `IsADirectoryError`, which is an
`OSError`, which the blanket handler catches — so the read returns empty, the
manifest looks like it declares no dependencies, and every import in every crate
in the repository classifies as "local". The verifier does not crash, does not
report zero, and produces a confident wrong answer at scale.

Two habits close it:

- **Never swallow an error on the input a classification depends on.** Print it
  to stderr and return the neutral value, so the next run shows *why* the input
  was unusable instead of quietly reinterpreting it.
- **Assert the classification input parsed before trusting the output.** One call
  that prints the parsed set is worth more than any number of findings:

  ```python
  print('parsed deps:', sorted(dep_roots))     # empty on a real repo = the bug
  ```

**A finding count in the hundreds is a bug report, not a result.** A rule with
real teeth on a codebase you believe is clean produces a double-digit number. Six
hundred and eighty-eight findings against five repos is not "the codebase is
unclean" — it is one wrong assumption multiplied across every file. Bisect by
reading three findings in their source context before touching the threshold:
the cause is nearly always an input the check reads and the fixtures never
supplied (a manifest, a directory listing, a name that resolves elsewhere), not
the rule's core comparison.

**The same sweep finds the crashes the fixtures were too polite to trigger.** A
brace-matching helper that assumes balanced input returns a sentinel equal to
`len(lines)` on an unclosed block, and the caller's `range(idx, end + 1)` then
indexes past the end. Every hand-written fixture has balanced braces; real code
has a macro fragment or a truncated file. Clamp the sentinel and re-run — a
verifier that crashes on the first non-fixture input is a verifier nobody has
run.

## A per-file entry point that does not check its own path scope is the same read-wrong-channel bug

A CLI verifier is often correct because its *driver* narrows the file set
(`find … -path '*/tests/*'`) while its `audit_one(path)` is path-blind. A
commit gate that imports the module and calls `audit_one` directly on any
staged file bypasses that narrowing — so the rule that was scoped to test
files starts reporting every `///` in production source. The symptom is
indistinguishable from real debt: a four-digit finding count, spread across
dozens of files that have never been touched by this rule.

**Rule: the path/scope test belongs inside the per-file entry point, not only
in the driver that selects files.** Two callers with two different notions of
"which files are mine" will drift, and the one with the weaker filter is the
one wired into the gate that blocks commits.

```python
def is_owned(path: Path) -> bool:      # scope, in one place
    parts = {p.lower() for p in path.parts}
    if "target" in parts or ".cargo" in parts:
        return False
    return "tests" in parts

def audit_one(path: Path) -> list[str]:
    if not is_owned(path):
        return []                       # same answer from every caller
    ...
```

Prove it three ways before believing the fix — the scope case must stay silent
and the rule must still bite: a production file with many comments → 0; a test
file with one comment → 1; a test file with none → 0. Then check the aggregate:
a rule that was scoped to one directory should report roughly the pre-existing
count for the corpus, not a multiple of it.

**The diagnostic that finds this fast:** the CLI reports 0 but the gate reports
thousands, on a rule whose own docstring says which files it covers. That
disagreement is the bug report — the two callers disagree about scope, so find
which one lost the filter. Do not respond by widening the rule's exemption
list, which turns a loud bug into a silent one.

A related false reading: a finding count that *explodes* when a rule starts
scanning files it previously skipped is a scope bug, not a newly-unclean
codebase. Same evidence, opposite cause from "the repo got dirtier".

## When you have been reasoning about geometry, stop and read it

Nine consecutive rounds on one navigation bug were spent deriving a building's
wall positions from waypoint coordinates — trigonometry, yaw swaps, local-to-world
frames, re-derived constants. Every round produced a confident answer and every
round was wrong.

One debug channel that dumps the actual colliders (centre, half-extent, axis
ranges, penetration depth) around the stuck agent ended it in a single run,
because the very first output invalidated the premise the previous nine rounds
shared: the walls were not in the collision world being scanned. A solid-AABB
per building had been deliberately replaced by a per-piece interior model
precisely because a solid box would seal the doorway — and the reason was
written in a comment right above the code. The scan returned twelve cylinders
and zero boxes, which was the answer.

Rule: if you have written the same class of inference more than once and it has
not held, the inference is the bug. Build the read-only dump before the third
attempt. Also grep for the comment that explains *why* the obvious structure is
absent — deliberate omissions are documented, and the absence is a decision, not
an oversight to be reasoned around.

Corollary for the dump itself: scope it to the store that actually holds the
data. A first version scanned the nearest world, found nothing, and nearly got
written off as "the agent is not blocked by geometry" when it was reading the
wrong collection.

### An absent standard mechanism is a decision, not an oversight

Once the dump clears the world data, the next question is what the code *does*
do, and a surprising answer deserves a second look before it becomes a
root cause. The mechanism was missing, the surrounding comment said it was
removed on purpose, and a sibling comment named the bug it was fixing.

```rust
// 速度取「实际走出来的位移」/ dt,而不是把分离修正量加回去。
// 后者会被 1/dt 放大几十倍,一次 1 cm 的分离就会注入 0.6 m/s 的
// 侧向速度,角色会被「弹」着走。现在撞墙时朝墙的速度分量自然归零,
// 不会一直顶着墙搓,也不会被弹飞。
```

Read as a description of the code, the third line claims a *component* of
velocity goes to zero. The implementation zeroes the whole displacement, which
also removes the tangential component — the difference between "the wall stops
me" and "the wall stops everything". **A comment that reads as a narrower claim
than the code implements is a specification bug**, and it is why the behaviour
looked accidental for as long as it did: nothing in the file says the
distinction was ever considered.

The general rule for the fix: **when restoring a missing mechanism, write the
regression test for the case the original removal was protecting against.** The
first implementation of the restore passed the walk test and tunnelled a metre
through a wall; a test named for the guarantee that motivated the removal
(`head-on into a wall must still stop`) caught it immediately. A fix that
restores behaviour without pinning the constraint the removal encoded is
guaranteed to re-break it, and the next person to read the code will conclude
the original comment was right.

**Audit the code's own comments for claims narrower than its behaviour before
treating an anomaly as a bug.** The comment is the best available statement of
intent, and a mismatch names the defect precisely — usually the fix is to
implement the comment, not to write a new one.

## When every probe confirms the model, the model is the bug

The section above ends a ten-round search by building a read-only dump. The
dump worked, and the round *after* it wasted another ten on the same class of
error — because the dump answered the question that was asked and the question
was wrong. Both lessons are one rule.

**A probe answers the question you ask.** A run of dumps that all read *normal*
is not a dead end; it is the finding, and it invalidates the question. The tell
is that every probe asks a **where** question ("what is at this coordinate?",
"which shape is nearest?") and returns a correctly-placed, correctly-sized
piece of the world, every time. Correct data, repeatedly ruled out, means the
defect is not in the data.

**Then grep for the mechanism you assumed, by its standard name** — not the
symptom, not the coordinate, not the constant:

```bash
grep -rn 'move_and_slide\|resolve_with_radius\|sweep_and_prune' src/
```

The entity had velocity (`vel=[-3.18, 0]`) and zero displacement, and had it at
a different coordinate on every run (28.3, 28.4, 33.1, 35.0) — a signature that
points at the *integration step*, not at the world. A body that integrates
velocity into a position and then clamps the result has no sliding, and the
missing sweep was one `grep` away in a file nobody had opened. Chasing the
varying coordinate is what made it look like a geometry hunt: the number moved,
so the number looked like data.

**Class signatures beat coordinates for locating a defect:**

| Signature | Points at |
|---|---|
| velocity non-zero, displacement zero | the integration/move step |
| state flag set, action never runs | the dispatcher, not the handler |
| correct value, wrong default applied | the reader, not the producer |
| count plausible, output wrong | the encoder, not the consumer |

**A dump shows what IS there, so its silence has two causes** — nothing is
there, or the code that would read it is not there. Rounds were lost assuming
the first, because the probes were built to only ever return objects. After the
second clean dump, the higher-value query is not a wider one; it is a different
*kind*, from "what is at X" to "what reads X".

Rule: **instrumentation that keeps confirming your model is evidence the model
is wrong, and the next tool must be a different category, not a bigger version
of the same one.**

## A test in one coordinate space is blind to the invariant in another

A test that never leaves one coordinate system cannot see a property that
only exists in another. Writing more of the same test does not close this
gap — the whole test is structurally blind to it.

Concrete instance: an end-to-end stair-climb test walked its waypoint route
using **asset-local** coordinates throughout, so it never touched the
local-to-world transform. Three separate route bugs passed it:

- two waypoints that rotated to the *same* world position (same local z,
  different local x) — the route spun in place forever
- an axis-aligned leg whose "step further into the room" edit landed *past*
  a partition wall sitting at the very local z it was trying to stay clear of
- a constant that read like "further in" but after the ±90° yaw swap moved
  the point *back toward* the door

The fix was two new assertions evaluating the route in **world** coordinates:
adjacent waypoints further apart than one body width, and each leg moving on
exactly one axis (a diagonal inside a walled interior always jams on
something). Those two caught all three bugs on the next three edits —
including two that had already been hand-"fixed" in an earlier round and
re-broken by the round after.

Rule: if a property is only meaningful after a transform, the assertion has
to be written after the transform too. Prefer a helper that inverts the
transform (`to_local` for a `to_world` world point) over re-deriving the yaw
trigonometry inside the assertion — the re-derivation is itself a place to
get the sign backwards.

## A gate that checks a string the code may satisfy for the wrong reason

A checker that asserts a *name* is present in a file proves the name is in the
file, not that the code behind it is correct. The common case is a value that
another mechanism can legitimately supply: an import specifier in an import map
is satisfied equally by a bare package key and by a fully-qualified CDN URL, so
a check written as "the map contains `three/addons/`" passes while the page
loads nothing at all offline.

**Rule: assert the resolved value, and the condition that makes it meaningful.**
Resolve the specifier the way the runtime will, then assert a property of the
*result* — a local relative path, an existing file — rather than a substring of
the declaration. The same applies to a framing constant: a check that finds the
literal `1.00` passes whether or not any call site uses it.

**Then mutate it, because a name-shaped assertion is exactly the kind that goes
dead when someone edits the rule it was written to police.** A front/rear
direction gate covering three separate rigs is only trustworthy if a
deliberately-swapped value makes it fail:

```bash
cp rig.js /tmp/rig.bak
python3 - <<'PY'
import re, pathlib
p = pathlib.Path('rig.js'); s = p.read_text()
p.write_text(s.replace("front: 90", "front: 270").replace("rear: 270", "rear: 90"))
PY
run_gate            # must exit non-zero
cp /tmp/rig.bak rig.js
run_gate            # must exit zero again
```

Report the table both ways. "The gate passes" is uninformative for a structural
rule; "the gate fails when the direction is swapped, restored, and passes again"
is the claim that survives the next refactor.

**A checker that cannot parse one of its inputs must fail, not skip.** The
parser here had to handle a Python `VIEWS` list, a JavaScript `const VIEWS`, and
a set of Chinese-language viewer labels. Silently ignoring an unrecognised file
would have dropped the viewer from the gate's scope on the next rename, and a
scoped-out input is indistinguishable from a passing one. Anything the gate
cannot read is a hard error, and the restore is unconditional.

## A classifier that keys on the file extension mis-routes embedded languages

A gate that answers "is this change code or not?" by testing `path.suffix` is
correct only while every language keeps its content in a file that announces
it. The moment a framework declares one language **inside** another, the
extension test answers a question nobody asked, and the error is silent because
the file genuinely is a `.rs`.

The real instance: a "presentation direct-pushes, code needs a PR" classifier
allowlisted `.css`/`.scss`/`.less`, so a one-line CSS deletion inside a Rust
`class! { pub c_x { … } }` block was routed to a pull request. The declaration
was `border-left: format!("2px solid {}", var!(border));` — the `format!` is the
declaration's *value*, and the lexer read it as a changed statement.

**Rule: key the decision on the changed line's semantics, not the container's
extension, and treat "embedded in a host language" as a first-class case.** The
discriminator that generalises is *does a parser read this, or does something
execute it* — a property of the line, available in every language.

| Changed line | Verdict | Why |
|---|---|---|
| `border-left: format!(…);` inside a style block | presentation | a declaration; the macro builds its value |
| `let x = 1;` / a changed `fn` | code | the compiler runs it |
| `display: none` / `:hover {}` / `@media` / `transition` | **code** | the engine acts on it, though it is syntactically a declaration |

That third row is what a naive port gets wrong: syntactically-CSS lines that
change behaviour must keep their stricter route, or the new layer becomes a
blanket exemption for the whole file.

**Scope the decision to the diff's lines, not the file's overall character.** A
file containing one behavioural declaration is still a stylesheet; demanding
that every block in it be paint rejects the rule on exactly the real files it
exists for, and the resulting "0 files classified" is indistinguishable from a
detector that never fires. Compare the `+`/`-` lines of the unified diff
against the set of style-block contents.

**Fixtures must carry the negative direction, and the negatives are the
valuable half.** The positive case (a paint declaration direct-pushes) is the
one that motivated the fix; the cases that must stay rejected — behavioural
keys, a real statement in the same file, a plain code file — are what prove the
new layer is not a blanket pass. A fixture set containing only the motivating
case passes just as happily when the layer has been reduced to "any `.rs`".

**Corollary: a routing rule needs an enforcement point, or it is prose.** In the
same investigation the classifier's verdict was documented in four skills and
computed by a script that **no hook consumed**, so the routing error recurred
with nothing to catch it. A verdict nobody reads is not a rule. Wire the
decision into a commit-time gate, and place the gate **above** any early-return
in the hook: a repo-type or file-type check that returns early means a gate
below it never sees the commits the rule is about — which for a docs/config
rule is every commit of interest.

## A local fix that moves an already-passing step is not a fix

Correcting one waypoint frequently disturbs the previous one. Squaring the
walker up on the doorway axis is what let it through a 1.6 m opening; applying
that alignment on *every* leg pushed it further back down the street than the
unaligned version did. Before adding a correction to a multi-step walk, re-run
the steps that already passed and check they still do.

The same applies to a gate: a "fix" that silences the finding for the input
you were looking at while pushing a *different* input out of range has moved
the problem, not removed it. Re-run the neighbouring cases, not just the one
in the log.

## Before concluding "navigation is broken", find out which layer broke

A behaviour that fails identically under several parameter settings is not
tuned, it is located: vary one parameter (here the simulation's time scale)
and see whether the outcome moves at all. If a run ends on the same
coordinate at 1x, 2x and 4x, then no threshold, poll interval or speed is
the variable — the question is which surface that coordinate is, and that is
answered by dumping the *path between* the endpoints, not by tuning towards
the target. Endpoints alone cannot separate "cannot get there" from "arrives
and is thrown back", and the second reading names the obstacle.

## A click-offset measurement must freeze the world, or it measures physics

Measuring "the pointer lands N px from where the object drew" is the only way to
prove a coordinate-mapping fix, and it has three ways to return a precise,
confident, wrong number. Each produced a retraction in one session:

| trap | reading it produced | what to do |
|---|---|---|
| the click spawns something with a random initial velocity | the "offset" is drift between click and readback | pause the simulation first, **and assert the pause took** (check the control flipped label) — a pause that did not apply looks identical to a mapping bug |
| more than one object is on screen | the bounding box of *all* ink is the centre of nothing in particular | connected-component labelling, take the largest blob |
| the raw comparison is against an absolute expected value | two probes disagree and neither is obviously wrong | measure **two** points and subtract; drift and physics cancel, the mapping error does not |

**Prefer a derived invariant over an absolute pixel count.** "The drawn object
centroid equals the click point" needs a threshold and a frozen world. A
statement like *the error ratio equals the drawing-buffer / viewport ratio* is
both exact and self-identifying: a measured `0.73` on a 600/820 surface says
the render is being scaled by a known factor, which names the bug instead of
just flagging one. When a suspicious constant appears, divide it by the
nearest candidate surface ratio before searching further.

**Then assert a mechanical invariant per variant, not one aggregate verdict.**
"viewport == drawing buffer", for every canvas arm and every DPR, holds
exactly when the fix is present and breaks the instant it is not — better than
any single end-to-end coordinate number, and it localises the failure to an arm
rather than to the page.

**Never let an unverified arm share a verdict with a verified one.** A GPU path
that cannot initialise in the harness (no adapter, software rasteriser) must be
reported as untested, not as passing because the arm beside it passed.

## A render check measures pixels, and pixels have a lifecycle

A gate that reads a rendered frame has three ways to be wrong that no amount of
arithmetic catches, because each returns a real number about the wrong image.

**The drawing buffer is cleared after compositing.** `gl.readPixels` on a
context created without `preserveDrawingBuffer` returns nothing when the read
is not in the same task as the draw. The tell is a *self-contradicting* run:
the geometry raycast says the socket is 1.2 mm behind the skin while the pixel
read says the opening is 91-198% of the bare panel's luma, i.e. there is
nothing there. Both numbers are real. When two probes on the same frame
disagree about whether a thing exists, suspect the read before the model.

```js
await new Promise(r => requestAnimationFrame(r));
const flat = document.createElement('canvas');
flat.width = glCanvas.width; flat.height = glCanvas.height;
flat.getContext('2d').drawImage(glCanvas, 0, 0);   // snapshots current contents
```

**One pixel is not a measurement of a feature.** A USB-C socket's inner wall
is lit aluminium, so the pixel dead centre in the opening reads 107 where the
bare panel 15 px away reads 108 — a correctly-modelled socket that looks
exactly like a defect. A real recess has a **dark core**: a *population* of
shadowed pixels. Test the fraction of a box below a threshold, and let a
known-bare patch on the same surface be the control.

Prefer that fraction over an absolute luma. An absolute number quietly becomes
wrong when the page's exposure, background or tone mapping changes, and then
it fails on a model that did not change.

**A screenshot taken after the render loop stops is a blank page.** Capturing
on a second CDP connection *after* cancelling the reader task gives you the
page's CSS gradient: 61% pure white, ~1365 unique colours, no model on it. It
gets filed as the elevation, and someone then "inspects" a crop of it for
features that were never drawn. Take the picture from the page's own canvas in
the same task as the measurement, so it is provably the same frame, and make
the run fail when it is more than ~40% white. **A blank PNG is worse than no
PNG — it is evidence, and evidence gets trusted.**

## A boolean that fragments a surface makes area statistics lie

A CSG difference over a thin panel leaves the skin as thousands of small
faces. Total area over the region then reads *below* the region's area, so a
census of the form "strip area < skin area in strip ⇒ CUT" reports success
while the skin still covers 88-97% of every opening and stops a ray at 0.00 mm.

Fragmented is not open. For a hole, a **ray** is the measurement: cast through
the feature's own footprint and ask where it stops.

The same arithmetic bites in reverse — a cutter whose cap lands exactly on a
face is read as a pocket and the face survives. When placing a cutter, overshoot
the surface on *both* sides so neither cap can coincide with a face. Check the
arithmetic rather than the comment: the one that claimed "neither cap lands on a
face" was three lines above the line that put the cap on the face.

**Distinguish the feature from the fixture that fills it.** A connector's
socket walls are built *inside* the connector's own footprint; a gate that
cannot tell a socket from a lid calls 38-43% of every correctly-built port
capped. A gate that misreads its own subject is measuring itself, and its
output reads exactly like a finding.

## A gate that stays red is where live bugs hide

A static gate asserting facts a previous commit deliberately removed (eight
named camera views after the buttons were deleted) is red from that commit
onward. Nobody reads a permanently-red gate, so it stops being a gate — and
the checks it *should* be running are the ones that would have caught the next
bug. Here two live defects sat one commit apart, both of them in code the red
gate nominally covered.

**Assert what should be true, not what a deleted table contained.** Then
mutation-test it in both directions (above).

Scan **code, not comments**. The comment recording a bug frequently quotes the
very call the check greps for, so a naive regex keeps the check red forever
*after* the bug is fixed — the worst possible state, because it trains the
reader to ignore red. Strip comments before matching.

## A convention asserted three times backwards is a convention to measure

The same axis convention was written wrong, with a confident comment
explaining why, in three separate files. Memory does not hold this. Read the
convention out of the artefact itself — for glTF, the JSON chunk is
uncompressed even when the primitives are Draco-compressed, so node and
accessor bounds give you the answer in about a second with no browser and no
decoder. A measured convention can be gated; a remembered one can only be
re-asserted.

## Fix the gate, not just the finding

## An auto-fixer that clears a check can expose the next one

Visibility and ordering fixers rewrite one axis at a time: narrowing `pub const`
to `pub(crate)` satisfies the visibility check and may then leave a `pub(crate)`
item sitting ahead of a `pub` one, tripping the group-order check. The score
barely moves — one check green, the next red — and it reads like the fixer
failed, when it actually succeeded at its own job and uncovered a second rule the
file was already breaking.

**Rule: after any auto-fixer, re-run the audit and treat a newly appearing check
as newly exposed debt, not as a regression to revert.** Do not roll the fixer
back; feed the next violation to its own fixer and iterate until the run is
clean, then confirm a second run changes nothing. Fixers that deliberately skip
zero-reader items are behaving as designed — that residue is a keep-or-delete
decision for a human, so hand-fix it instead of reporting the fixer as broken.

Run auto-fixers yourself only when no worker owns those files. A repo-wide
rewrite while a subagent is editing the same `const.rs` overwrites live work,
and a fixer whose contract is "skip what I cannot judge" is explicitly asking a
human to finish the job.

When a gate let something through, ask which assumption was wrong. A
passing-zero-on-new-files gate is a bug in the gate's own contract, and
every future session will read the same false reassurance. If the gate's
scope is documented in a comment, make the limitation explicit there rather
than leaving the next reader to infer it.

The same applies when the gate was **correct but its scope never covered the
thing being asked**. A verifier that enumerates files by name cannot see a
directory-level violation, so it returns zero on a repo that violates the
rule everywhere. Before adding a rule to a per-file gate, ask whether its
`audit_one(path)` would return a non-empty list for *any* file in a
violating repo. If the honest answer is "no file alone shows it", it
belongs to the full-scope run, and wiring it into the fast path buys a
reassuring zero for nothing.
