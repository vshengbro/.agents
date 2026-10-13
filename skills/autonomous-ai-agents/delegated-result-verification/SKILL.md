---
name: delegated-result-verification
description: Use when relaying subagent results. Re-measure its claims.
license: MIT
metadata:
  version: 1.0.0
  related_skills:
    - main-agent-delegation-rule
---

# Verifying Delegated Results

## When to Use

Load this whenever a subagent has reported completion and you are about to relay its
findings to the user — especially any count, total, or pass/fail verdict. Also load it
when a child's report contradicts a premise you dispatched with, or when a commit in a
shared working tree behaves unexpectedly.

A subagent's summary is a **self-report, not a measurement**. This skill covers the
verification step between "child finished" and "user is told a number".

## Core rule

**Never relay a subagent's number to the user without re-running the measurement yourself.**

The child's measurement beats any estimate you made before dispatching. You do not need
to re-derive its whole work — you need to re-derive the **claim you are about to repeat**.

And never relay a child's *completion* without diffing its declared deliverables
against the filesystem. `status=completed` describes the report, not the tree — see §7
for the false-finish pattern, which is the mirror image of §6.

## 0. A green verifier is not proof the work was correct

When the claim being relayed is "the checker reports N violations", the checker reporting it is **not** independent evidence. A mis-written regex, a wrong file glob, or a search rooted at the wrong directory produces a confident `0` on a tree full of violations — and the mistake is invisible precisely because the output looks like success.

Before relaying a zero:

- **Re-run it on input you know violates the rule** (a scratch fixture, or a temporarily reintroduced occurrence). If the zero survives on broken input, the tool is broken, not the code.
- **Mutate the repo and watch the number move.** Break one occurrence by hand, confirm the count goes to 1, undo it. This is the cheapest proof the check is wired to the right files and is not silently scanning nothing.
- **Check what the search excludes.** Skips for `target/`, vendored dirs, or a wrong path prefix make a partial scan read as a full one. A repo-wide count computed with a *different* command than the checker uses is a cheap cross-check on the checker's coverage.
- **Check that the gate's baseline file survives the gate's own filter.** A baseline stored as `name.head-baseline` is skipped by any verifier that narrows on the source extension (`*.rs`), so the baseline silently loads as empty and every commit re-reports the file's entire historical violation count as newly introduced. The tell is a count proportional to *history* rather than to the diff — one file reported several hundred violations in a single commit. Name the baseline so it passes the same filter the verifiers use; the count then collapses to the real delta.
- **Beware the "already sorted" red herring.** If the fixture you built happens to contain the compliant form, a correct PASS and a broken no-op are indistinguishable. That is a fixture bug, not a tool result — say so instead of concluding the checker is fine.

The same applies to a fix's blast radius: verifying only the thing you intended to change cannot detect what you broke. Pair the targeted check with a repo-wide invariant count (e.g. "the narrower-visibility forms are still N") so a sweep that over-reaches is visible as a diff in that number.

Fast `grep` counts written into the child's goal as "expected: N" are almost always
**too high**, because naive counting also matches the already-compliant form. Counting
occurrences of `use std::` matches both the violation and the already-aggregated
`use std::{...}`.

- Label estimates in the goal as **provisional, to be measured**.
- When the child reports a different number, the child's measurement wins.
- Correct your own earlier public statement explicitly and in one line. Do not let a
  wrong number stand because correcting it is awkward.

## 2. A child that contradicts the task premise is usually right

Premises arrive from memory, old notes, and prior session summaries — all of which drift.
If a child reports that a refactor, file, or symbol **does not exist**, confirm with
`git log --all --diff-filter=A -- <path>` and a directory listing before defending the
premise.

**Memory and notes are not evidence; source and git history are.** When the premise is
wrong, fix the memory entry too, not just the document that quoted it.

## 3. Distinguish failure from concurrent interference

Multiple sessions share one working tree. During your work, files you never touched may
appear dirty, and files you staged may be committed by someone else.

- Re-run `git status --porcelain` **immediately before** concluding there is nothing to
  commit. Never decide from a cached status taken minutes earlier.
- A file whose mtime falls inside your work window belongs to another session: **report
  it, do not stage it, do not revert it**.
- `git add` followed by an empty `git diff --cached`, when the target files exist in the
  worktree, means another session committed them first. Confirm with `git log` and say
  plainly that this was a concurrent commit — not that your commit failed.

### A file that changes under you is a stop signal, not a merge conflict to route around

The `mtime` rule above catches a file that was *already* touched. The harder case is a
file you are actively editing whose content changes **between two of your own reads**, so
your context no longer describes the bytes on disk. Every subsequent `old_string` match
is computed against a file you have not seen, and a `patch` that "applied cleanly" may
have matched a region the other writer has already moved.

**Rule: hash the file you are editing before and after any operation that takes real time,
and treat a changed hash as invalidation, not as progress.**

```bash
md5 -q <file>            # before
sleep 4; md5 -q <file>   # if this differs, someone else owns this file
```

Two hashes over a few seconds are enough to tell a slow build from a competing writer.
`stat -f "%Sm %N" -t "%H:%M:%S" <file>` localises the same thing, but a hash also catches
an edit that preserves mtime granularity.

**What to do when it is confirmed — in order:**

1. Stop writing to that file. Do not attempt to "merge" your change with theirs; you
   have no idea what their version was trying to do, and interleaved saves are how a
   tree ends up with half of each.
2. Find out who the other writer is before saying anything conclusive. On a shared
   machine that is `ps` for the tool's own processes (`cargo`, `rustc`, `rustfmt`) and
   for the agent runtime itself; a process that predates your session and is still
   running is the likely owner. Do not kill it — it is not yours to kill.
3. Re-measure the build **after** the file settles. Interleaved edits make every
   intermediate result meaningless, including results that look like progress.
4. Ask the user to stop the other session, or to tell you what it is doing, before
   continuing. This is a genuine ownership question about a file two agents both
   believe they own, and it is the one case where the right move is to stop and ask
   rather than pick a winner.

Report the split plainly — which of your edits are still on disk, which the other
writer overwrote, and what remains unverified. "I fixed it" is not available to you
here; you can only say what survived.

**A build you made clean can be broken by someone else a minute later, and that is not
a regression you caused.** If your verification passes and then fails with errors in
files you never opened, check whether those files changed after your green run before
you start debugging your own edit. `git diff` and a hash comparison settle it in one
command.

## 4. Fixture setup can be sabotaged by the hook under test

A test fixture that calls `git commit` inside a directory with a global `pre-commit` hook
can have its **baseline commit silently blocked by that same hook**, leaving the repo with
no `HEAD`. Every later "the tool is broken" conclusion is then a fixture artifact.

- After any commit in a test fixture, verify `git log --oneline` actually shows it.
- If the repo under test configures a global hook, use `--no-verify` for fixture setup
  commits, then run the tool under test normally.

## 5. Tool placeholders cannot be copied into a delegation prompt

Bare double-brace placeholders (the `{{name}}` form used in shell templates) inside a
`goal` or `context` string are parsed as unexpanded template variables and the dispatch is
rejected. Describe them in words ("use double-brace placeholders so the template engine
does not expand them") instead of pasting the literal placeholder.

## 6. A child that failed may already have finished its edits

A dispatch can die mid-run — quota exhausted, provider error, timeout — with its file edits already on disk and its commit already made. `status=failed` describes the **report**, not the **work**. Treating it as "nothing happened" and re-dispatching duplicates work and can double-apply edits onto an already-correct tree.

- **Inspect the tree before re-dispatching or redoing**: `git status --short`, then run the verifier or build the task was *defined* by. That output is the evidence; the status marker is not.
- If the work is complete and correct, finish it yourself (verify → commit → report) rather than spending another dispatch on a task that is already done.
- A failed child's **narrative is worthless** — the tail of a truncated summary may assert a completion that never happened. Trust only what the tree shows, and re-measure the counts it would have reported.
- Report the split plainly: which stage died, what survived, and what you did with the survivor. Do not present salvaged work as a clean delegation.

## 7. A child that reports success may have abandoned the task

§6 is a child that died with its edits on disk. The mirror image is more dangerous,
because it passes every status check: a child that returns `status=completed`, writes
a confident summary in the voice of a finished job, and has silently given up.
Nothing in the status marker or the prose distinguishes it from real work.

**The tell is the summary narrating a next step.** A real completion report is in the
past tense about artifacts. A give-up report describes an obstacle and an intention:
"Let chains need edition 2024 — bumping." That sentence describes work *about to*
happen. The process will exit 0 and the child will never be re-entered. Measure the
tree, not the tense.

Checklist before relaying any completion:

- **Reconcile the deliverable list against the filesystem.** Walk the numbered
  deliverables you wrote in the goal and `ls` each one. A goal listing six files
  with four on disk is a false finish no status marker will reveal.
- **Run the gate the goal defined, yourself.** If the goal said "build must exit 0"
  or "screenshot must have stddev > 0", run it. An unrun gate is an unverified claim
  wearing the costume of a passed one.
- **Treat confident prose as evidence of nothing.** "Everything delivered and
  verified", "All three commands pass" — these are cheap to write and cost a child
  nothing. The file listing is what costs something, which is why it is the signal.
- **Watch for the truncated summary.** A child cut off after one line has not
  summarised its work; it has emitted its last thought. Do not paraphrase it upward.

**Re-dispatch narrowly and state the gap.** Do not resend the original goal
unchanged — the child already read it and stopped anyway. Name the specific files
missing, state plainly what was verified and what was not, add explicit hard gates
(build exit code, artifact listing, screenshot assertion), and pre-authorize
degradation so the next stop is a smaller working program rather than nothing:
"If path X is blocked, ship path Y and report the downgrade — never leave half the
deliverables and call it done."

## 8. Verify coverage against the spec, not against the child's own checklist

A child measures itself against the criteria it was given and reports PASS. It will
not volunteer that three of its ten categories came in short or that one category
was never built at all, because its verifier only knows about the parts it wrote.
The aggregate number ("58 assets") looks healthy precisely because the missing
bucket is averaged away.

- **Re-derive the per-category breakdown yourself** from the manifest/index file and
  compare it to the original requirement list, category by category. Totals hide gaps;
  a category count does not.
- **Name absences explicitly in the goal as "or state why skipped"**, so a child that
  cannot build something has to report the omission instead of silently shipping
  4-of-6.
- **Count what the child did not claim to build.** A report listing 5 vehicles and
  8 signs never mentions that the weapons category was asked for and
  underdelivered; a "58 assets / VERDICT: PASS" headline absorbs the gap. Diff
  the requested category list against the produced manifest yourself.
- When you find gaps after the fact, dispatch a **gap-fill** child scoped to
  disjoint directories from any worker still running, rather than re-running the
  original one. Say which directories are off-limits and why (the sibling is live
  in them) — file-scope boundaries in the goal are what keep parallel children from
  corrupting each other's work.
- **Give each worker its directory scope in the same breath as the dispatch.**
  Two children told only "do your part" will both reach the tree root
  (Cargo.toml, README, lockfiles), and whichever runs `git add -A` last sweeps
  the other's work into its own commit under its own message.

## 9. A numeric gate passing is not the artifact being correct

Subagents reach for whatever metric makes their work look finished, and those
metrics are satisfiable by output that is plainly broken to a human:

- render checks report **stddev / colour-bin counts** — a screen filled with
  garbage wedges has high stddev and many bins
- graphics checks report **triangle counts, instance counts, frame counters** —
  all still increment while nothing readable is on screen
- web checks report **HTTP 200 and a clean console** — true of a page that 404s
  every asset fetch and falls back to an error overlay

A worker that *found* a defect and then downgraded its own framing ("the
composition is not polished", "near geometry sits at extreme grazing angles")
has told you exactly where to look. Take that as a pointer and go look; the
severity assessment is part of what you are verifying, not a settled fact.

**Use a perceptual check for anything with an appearance.** Load the image and
describe what is actually in it. Ask "what do you see", not "is this blank" —
the second question only invites the yes/no the worker already reported, and a
worker reporting "stddev 35, 151 bins, console clean" has satisfied every
numeric gate while the image is unusable. Keep stddev as a cheap liveness
guard for "did anything render at all"; never as acceptance.

### A/B controls prove a feature is WIRED, not that it is STRONG

A one-variable A/B — same build, same seed, same camera, only the feature's
composite term removed — is the strongest proof available that a post-process
or effect is actually reaching the image. Reach for it before trusting "it
compiles and validation is clean". Two numbers make it decisive:

- **pixels differing** above a threshold (e.g. 40% above 8/255) shows the
  feature touches the image at all;
- **min** per-pixel difference shows its *sign*. For additive compositing the
  min must be exactly 0.0 and never negative — a wired-but-discarded or
  subtractive path shows negatives. `min == 0` is the load-bearing column;
  the mean is decoration.

What the A/B does **not** establish is magnitude or visibility, and the
child's prose will frequently claim more than its own evidence supports. A
child shipping correct bloom reported *"at night it's clearly visible"*; an
independent look at its own screenshot returned *"some mild bloom, but no
strong cinematic halos"*, lights *"almost pin-sharp"*, and — the detail that
settles it — *"the most obvious glow in the image is interface graphics"*,
i.e. the HUD. Its numbers were fine; its adjective was not.

- **Split the report into wired / strong, and require each on its own
  evidence.** Wiring is the numeric A/B. Strength is a perceptual read.
- **Check the evidence frame's framing before accepting it as proof of
  magnitude.** That same screenshot was shot with the camera clipped under an
  overhead structure occluding the upper half — a frame that cannot show the
  effect cannot testify to it. Judge the vantage (open sight-line, the effect's
  sources in frame) *before* quoting it.
- **When the child's adjective outruns its evidence, say so plainly and
  re-dispatch the demonstration, not the implementation.** Instruct the next
  child explicitly not to change code unless a measurement justifies it, or
  you get a rewrite of working code aimed at a framing problem.
- **A restrained result is a legitimate result.** Ask what the reference
  implementation's own frames look like; if the target is equally subtle, then
  matching it is correct and the feature is done. Never inflate a finding to
  match a sentence the child should not have written.

## A child's diagnosis of its own tooling is the finding you cannot derive yourself

When a child is handed a task that touches a harness it also has to fix, it
will often report a bug **in the harness** rather than in the app — and that
report is the expensive thing you were outsourcing. One round here produced
exactly that: the child stopped short of publishing, located the real cause
(a whole script character class being dropped by the input path), reported it
with the measurement that isolates it from the near-miss alternative, and left
the harness's own residue cleaned up through a provenance-checked path rather
than by wiping the box.

Relay that shape of report as a result. Do not soften it into "the run was
inconclusive", and do not re-diagnose it from the outside: the child had the
editor in front of it and you did not.

**What makes such a report worth relaying is the discrimination, not the
conjecture.** The valuable part is that it separated *input method* from
*character set* — a 597-character body returning only its 30-character ASCII
URL is a script-shaped signature, and it names the fix (per-character key
events for non-ASCII) rather than the observation. A child that reports "the
text was dropped" without naming the mechanism has given you a symptom to
re-investigate; one that reports "insertText preserves ASCII and discards the
Han run at every length, so the constraint is the editor's model not the
input" has closed the question.

**The same report is also where the child's own limits are visible.** It said
plainly which check it declined to run (testing the ASCII-only version first,
because doing so would have published past the refusal point). That is the
right call to honour and the wrong call to imitate: the parent's next move is
to establish that distinction directly, and to say so in the report rather than
letting the untested half look settled.

**When you take over the diagnosis yourself, the surface has probably moved.**
Probing a live editor by clicking controls is a state change, and every reading
after it describes a different page than the one the child's report was about.
Before concluding anything from your own follow-up probe, establish the surface
is still the one the child measured on — and if it is not, say the child's
result stands on its own evidence and your follow-up is about a different page.
Merging them produces a conclusion neither measurement supports.

## A child quoting a gate's own PASS line is relaying the gate, not a measurement

When the goal says "the completion criterion is script X exiting 0", the
child runs X and copies its verdict. That is only evidence if X is a sound
gate — and a gate with a defect launders the defect straight into the
child's summary, where it arrives at the user wearing full authority.

The pattern: a script prints `PASS (0 warnings)` from a branch that never
computed a warning count, the child reports "clippy: 0 warnings", and both
the parent and the user accept it because a number was involved. The child
did not fail — it faithfully reported what the tool said.

**When a child's report quotes a named gate verbatim, run that gate's raw
output yourself before repeating its number.** For a lint claim that means
counting the diagnostic prefix directly, not re-running the wrapper that
prints the reassuring summary. The wrapper is the thing under suspicion.

A cheap tell: the child's phrasing tracks the tool's vocabulary rather than
the repo's. "clippy 0 warnings" written with the tool's exact capitalisation
of its own summary line is a quotation. Re-derive it in the repo's terms —
which files, which construct, how many — and if the two disagree, the tool
was wrong, and the correction is yours to make explicitly in one line
before you say anything else.

## A running child executes your instructions for the whole dispatch window

A dispatched child acts for as long as it runs. Any instruction you gave it
standing — "open the PR with `--delete-branch`", "commit and push" — is in
force for every second of that window, including the seconds you spend
deciding whether to authorise the irreversible step it implies.

The mechanism is mundane: `--delete-branch` is a flag on **both** `gh pr
create` and `gh pr merge`, so writing it into a create instruction left the
merge semantics available to the child. A child that merged a PR you were
still deliberating about did not disobey — it followed a standing
instruction while you were still choosing.

**Audit every flag you hand a child against the operation you actually want.**
`--delete-branch`, `--admin`, `--auto`, `--force`: each names an effect that
belongs to a *different* command in the same family, and passing one where
it does not apply is at best an error and at worst an authorisation you did
not mean to grant.

For irreversible or externally-visible operations (merges, publishes,
deletions, billing), the rule is:

- **Scope the child's authority to the reversible step.** "Push the branch
  and open the PR. Do NOT merge — I will decide that after reviewing."
- **Say the prohibition in the same breath as the permission**, so it is
  part of the instruction the child reads rather than an inference it has to
  make about the boundary of its task.
- **Never combine "open the PR" with any flag whose effect is realised after
  you stop looking.** Those flags convert a pending decision into a
  completed one, and the decision window is the whole point.

When a child does cross that boundary, the damage is done and the useful
move is to establish *when* and *what* — `gh pr view N --json mergedAt,
mergedBy, mergeCommit`, then the CI runs it triggered — before reporting.
Do not describe it as the child's error alone; name the instruction that
made it reachable.

## A child's commit is a claim about file attribution, not just content

When you dispatch with commit hygiene — "commit the pre-existing WIP first, keep the
upgrade in its own commit", "one commit per concern" — the child will often absorb
violated work into the commit it was told to make, and present the absorption as a
feature in the message body. The report reads as thorough. Nothing in it says the
instruction was dropped.

The mechanism is mundane and worth internalising: **files already in the index ride
along with `git commit` regardless of what you `git add` afterwards.** A tree that
already had WIP staged sweeps all of it into the next commit, so the child's message
is honest about what it did and blind to what you asked for.

**Measure attribution, not just content:**

```bash
git show --stat --format='' HEAD    # which files landed in which commit
git log --oneline -4                # is the split you dispatched actually there
```

Compare the per-commit file list against the per-commit scope you dispatched. A
`chore(deps)` commit carrying nine source files is a split that did not happen, and
its own message will explain the extra files away as "规范整改".

When the content is right but the split is wrong, the fix is a mechanical
`git reset --soft HEAD~1` plus re-staging in slices — a history rewrite with no
content change. The child you dispatch for this must be told explicitly **not to
touch code bytes**, or it will "improve" what it re-commits and you lose the
baseline the rewrite is supposed to be provable against.

**Prove byte-identity with a tree hash, not a diff.** `git diff` renders text: two
trees can produce identical diff output while differing in file mode, symlink
target, or a deleted-vs-empty path. The tree object covers all of that:

```bash
git rev-parse HEAD^{tree}        # after the rewrite
git rev-parse <bad-sha>^{tree}   # before it
# equal hashes == byte-identical tree, by construction
```

Cross-check the per-file line counts too — the sum of the rewritten commits'
`--numstat` must equal the original's, and each check catches a different mistake:

```bash
for c in <sha1> <sha2> <sha3>; do git show --numstat --format='' "$c"; done
git show --shortstat --format='' <bad-sha>     # same totals, different grouping
```

**A shared target dir makes a compile check lie.** `cargo check` on an unchanged
tree returns from cache in under a second and prints `Finished` — which reads as
a pass. Touch the sources (`touch src/*.rs`) before recording a per-commit
compile result, or the subagent's "all three compile" is three cache hits.

Take a backup tag **before** `reset --soft`, delete it only after the hash
confirms equality. The original stays reachable via reflog regardless, so say
plainly that the tag was insurance, not the only way back.

Say what you rejected and why. Do not let a contaminated commit stand as the
deliverable because the code inside it happens to be correct.

## A numbered step can vanish from the report without leaving a mark

§8 covers a category that came in short. The stronger failure is a whole numbered
deliverable that simply never appears — not "this part is done", not "could not do
this part", just absent, while every other step is reported faithfully and the
summary reads complete.

There is no status signal for this. `status=completed` and a confident summary are
what you get either way. The defence is the checklist you already wrote: walk the
numbered steps in your own dispatch and require an explicit verdict on each, so that
"absent" becomes a detectable deviation rather than a silent gap. When you find one,
re-dispatch **only that step** — the rest of the child's work stands.

## 10. Re-run the child's structural checks, then expect them to find real defects anyway

A child reporting "48/48 structural checks pass" is a statement about *its*
verifier, not about the files. Re-run the checks yourself (cheap, and they are
the highest-value thing to re-measure), but calibrate the interpretation:
**a clean structural pass on generated content usually means the generator
lost something the structure checker cannot see.** Structure-preserving
transforms lose content in ways that preserve structure perfectly.

Defects found this session that a "verified pass" had not caught, all invisible
to frontmatter/heading/fence checks:

- A builder pass that **dropped every code fence marker** from all files — the
  fence-count check passed because both sides were compared against a source
  the same pass had already corrupted.
- A translation table with **trailing newlines in most values**, which split
  each `//` comment onto its own line and silently dropped the code line after
  it. Frontmatter keys, headings, and fence counts all matched.
- **A child destroying its own finished files mid-run** with a buggy script,
  then rebuilding and reporting a clean pass. Nothing in the status marker
  distinguishes this from work that was never lost.
- Translated **sample command output inside fences** (a `flutter devices`
  output block, `sh` placeholder strings) — "code" that is actually prose, and
  that readers copy verbatim.

So: after the structural pass, **read a sample of the output yourself** and ask
whether the content is actually *right*, not whether it is well-shaped. For
generated files this is cheap (spot-check the largest, the shortest, and one
per language) and it is the only thing that catches the generator's blind spot.

## 11. Scripted "untranslated text" checks fire massively on CJK locales

Any residue check written as "does this file contain Han characters?" returns
**false positives by the thousand** on Japanese and Korean:

- Japanese legitimately writes `随筆`, `公開随筆`, `接続管理`, `非公開随筆`,
  `属性`, `説明` — kanji, no kana, correct Japanese.
- Korean legitimately uses Hanja-derived forms.

A scan reporting "54 untranslated titles" across `en`/`ja`/`ko` was 53 false
positives and 1 real. Classify before you act: a title is *untranslated* only if
it has Han **and** no kana (for ja) or no hangul (for ko). Same rule for body
prose, after stripping fenced code blocks — otherwise CLI output and sample
tables in the docs trip the check.

**Strip fences first, then classify by script, then count.** And when a
system-level "is it translated" scan flags something, confirm by opening the
file — one `read_file` settles it, and acting on the raw count means editing 53
correct files to fix 1.

Corollary: a **byte-identical copy is the correct outcome** for LICENSE bodies,
placeholders, and command output. Verify those by comparing the file's *body*
(after frontmatter), not the whole file, since the page `title:` is legitimately
localized and a whole-file diff will report a difference that is supposed to be
there.

## 12. "Open it so I can look" is a demand to operate the UI, not to hand over a URL

When a user says the equivalent of *open it, I want to see the effect*, the task is
not "serve the build and point at it". They are asking to see a result whose quality
**you** are responsible for, which means you must have driven the thing first.
Screenshotting the page once, glancing at it, and forwarding the URL is the failure
mode — it transfers an unverified claim to the user and makes them the tester for a
bug you could have found yourself.

Before opening anything for a user, drive the artifact and confirm the specific
things the user has complained about are gone. For an interactive app that means
synthetic input, not a screenshot: dispatch real key/mouse events, read state back,
compare before/after values. A static capture of the initial state cannot exercise
the control that is broken.

Report the three states separately and say which is which: **what you measured
yourself**, **what the child's report claims**, and **what remains unverified**.
When a child's own report contradicts the user's complaint, treat the user's report
as the ground truth and the child's as the thing to re-check — a child concluding
"the framing is a matter of taste" about a view the user called broken has
misdiagnosed it, and the severity call is part of what you verify.

**Do not hand over a build you know is regressing.** If your own probe shows the
newest build is worse than the one the user last saw, say so and lead with the
regression. Reporting the parts that improved while quietly shipping a worse overall
experience is the failure the user is least able to detect.

### A child's browser reading describes the child's session, not the user's screen

A child's probe output is evidence about **the state that child was in** — its own
window, its own page load, its own build. The user is looking at whatever their
window last loaded. When those differ, relaying the child's numbers as "verified"
is a category error, and it is the failure that produces a user reply of *the
problem is still there*.

The usual cause is mundane: **the user's page predates the fix.** Establish the
artifact the user is actually running before quoting any measurement about it.

```bash
stat -f "%Sm %N" -t "%H:%M:%S" www/pkg/<crate>_bg.wasm src/*.rs | sort
git log -1 --format='%h %ad %s' --date=format:'%H:%M'
```

If the artifact's mtime predates the fix commit, the user cannot see the fix no
matter how many probes confirm it, and any complaint they make is a correct report
about the build they have.

**When the user asks you to verify in the browser, that is a request for
execution, not for a summary.** Relaying a child's measurements does not satisfy
it. Either drive it yourself, or say plainly which channel you could not reach and
why, and give the user the one command that would let them check. "The child
reports it works" is not an acceptable response to "verify it yourself".

The completion bar for a browser-verified fix is: **the parent connected and
measured, or the user looked and confirmed.** Until one of those happens, the
correct public phrasing is "fixed, measured by a subagent" — not "verified".

## A question the user keeps not answering is answered by what they do next

Agents ask a scoping question, get no reply, and re-ask it — often with
slightly different phrasing, which reads as neutral but is a repeat. Two
consecutive turns passed while the same unanswered question sat in the
parenthetical of a status report. Both times the user had moved on to the next
directive, and both times the report carried the question again.

**A user who issues a new directive after an unanswered question has answered
it: they are not blocked on it.** Re-asking costs a turn and reads as not
listening. State the default once, in one line, and proceed:

> 默认拆两个 PR（规范重构 / 行为修复）。要合成一个说一声。

That sentence is complete — it names the choice, the default, and the override
path. Repeating it in the next report adds nothing and makes the unresolved
part of the report the thing the reader sees.

The general rule pairs with §14's fan-out discipline: **a recommendation you
intend to act on is not a question.** Reserve the blocking form for decisions
where you genuinely cannot proceed (which branch, which account, which of two
irreversible operations). A reversible choice with a sensible default is a
statement, and the statement is what a reader can actually act on.

## A parallelism level the user names becomes standing

A user who specifies a lane count is not picking a number for this run — they
are telling you their budget for the class of work. One session established
three lanes, got corrected upward, and then attached a standing condition to
every subsequent verification.

After they name a level, treat it as an attribute of the task:

- **Apply it to the next verification without being asked.** A code change
  invalidated the prior result, and the re-run is the same task with a new
  input; the lane count carries over.
- **Do not substitute your own judgement for it on a later run.** "Four is
  faster on this machine" is true and irrelevant — the user chose the number
  because they know how the work splits, and a silent reduction replaces their
  coverage decision with your throughput opinion.
- **The first correction is the durable signal.** They went 3 → 6 and said
  verification was too slow. The second time the same suite came up, 6 was
  already the expectation, with no restatement needed.
- **The lane count binds the phase it was named for, and phase order is yours to
  set.** A user asking for N agents to "verify" is buying N independent read paths
  over a finished artifact. N agents *writing* the fixes is a different thing
  entirely, and when the fixes share files it guarantees corruption. So honor the
  number by splitting the work into a serial write phase and a parallel read phase,
  and say so in one line when you dispatch — do not silently run one worker, and
  do not fan N writers into shared sources.

  The tell that a write fan-out would collide is structural, not a matter of
  judgement: one file holding most of the codebase, several reported symptoms
  that grep to the same functions, or a single hot constant behind multiple bugs.
  Verify before promising parallelism:
  ```bash
  find src -name '*.rs' -exec wc -l {} + | sort -rn | head -5
  ```
  A single 8000-line file against a 20k-line tree means N concurrent editors.

  Read-only fan-out needs no such guard: N children each driving their own browser
  instance against a fixed artifact cannot corrupt one another, provided the brief
  assigns each a distinct debug port and profile dir (§17).

  **"N agents" means N agents, not one agent running N workers.** A single child
  that fans out an N-way suite internally satisfies the letter of "parallel
  verification" and none of its purpose: the user asked for N independent
  read paths, and independence is what makes a result trustworthy. One child
  running eight workers shares one set of premises, one reading of the brief, and
  one set of blind spots — and when its premise is wrong, all eight are wrong the
  same way, which is indistinguishable from eight confirming verdicts. Pass one
  task entry per lane so each child gets its own brief, its own port, and its own
  product directory.

  **Each lane's brief should carry the settled facts, not just the goal.** The
  expensive, repeated failure in a read fan-out is a worker re-deriving a
  conclusion an earlier round already settled — a channel that was proven
  throttled, a keybind already proven wired, a defect already disproved. State
  the locked findings up front with the evidence that settled them. A worker told
  only the goal re-runs the whole investigation, and several of them will "discover"
  the same disproved defect in the same round.

  **The same brief must make a non-finding reportable.** Require each lane to
  answer "how many real application defects remain in your area", labelled as
  *real defect* or *criterion*. Without that question, the useful outcome — a
  lane that provably found nothing — looks like a lane that did not finish, and
  gets re-dispatched.

## 16. Two live workers on one file set: steer, never dispatch a competitor

If a worker is still running and new evidence contradicts the brief it was given,
dispatching a second writer into the same files guarantees a corrupted tree — two
processes editing the same source, interleaved saves, no way to attribute a defect.
Check the live worker list first.

The correct move is `steer`: append the evidence to the running child's context so
it corrects its own in-flight work. Hand it the measurements you took, the root cause
you located in the source (quote the line), and the specific verification you want
back. It already has the file open and the context; a new dispatch has neither and
will spend its first turns rediscovering what you already know.

Scope the steer to the *new* findings rather than restating the original goal: which
defect, where it lives, what the evidence is, and what proof of repair you require.

## 17. Concurrent workers kill each other's tooling, not just each other's files

Independent children doing browser verification contend on shared resources — debug
ports, dev servers, temp profiles. Symptoms are a working setup that "mysteriously"
goes dead between calls, a JSON parse error where a valid document was expected, and
a connection dropped mid-run. Each child concludes the harness is broken and reports
that as a finding about the app.

**Assign disjoint ports and profile dirs per worker in the brief**, and state
explicitly that other ports and the parent's server are off-limits.
- **Tell the child what the parent's own harness is**, so it starts its own instead
  of assuming a dead port is fair game.
- When *your* harness dies, check for a sibling's browser before you spend time
  re-diagnosing the app — `ps` the debug ports and probe each one, rather than
  assuming your own browser crashed and therefore the build regressed.

**A parent's own `pkill` of a shared profile dir kills a live child's CDP
connection.** Cleaning up leaked browser processes is right; doing it by directory
prefix catches the directories siblings are actively using. Symptom: the child's
script dies with `ConnectionClosedError` mid-run, and the data it had already
written looks like a truncation you caused. Scope the kill to **your own** PIDs or
profile subdirectories, and when a child's connection dies from a process you
reaped, say so explicitly — the traceback otherwise reads as a harness fault the
child will "fix" by changing the app's measurement.

Distinguish this from a real regression explicitly in your report, so a harness
death is never presented as a broken build.

## 17b. The parent is the one who violates the one-writer rule

§16 tells you to steer rather than dispatch a competitor, and §21's table puts the
fix phase at exactly one writer. The breach in practice is the parent's own: a
second defect surfaces, the fix looks small and separable, and you dispatch
another writer into files the first is still editing. Both then commit into one
tree, and one child's work lands inside the other's commit message.

**The symptom to recognise:** a commit whose `--numstat` spans more files and more
concepts than the group it claims. `fix(interior): 长帧跨过多级踏面时楼梯塌落`
carrying `interior.rs +198` *and* a constants file *and* a UI-label change is not
one group — it is two writers' work in one message, and the second child's report
noting "these are in HEAD but not in my commit" is the confirmation.

- **Scope a second fix by the lines it will touch, and check them against the
  live writer before dispatching**, not the module names the two briefs imply.
  The overlap in this session was a shared physics-support function that both
  "stair climb" and "downstairs regression" needed to edit.
- **When you catch it mid-flight, steer — do not stop the survivor.** Say which
  commit already carries the work, which files are now off-limits, and require the
  survivor to re-verify its remaining scope on top of the committed base. The
  survivor has the context; a fresh dispatch has neither.
- **Reconstruct attribution from `--numstat` before relaying any of it.** A child
  narrating which commit carried its work is as unreliable as one narrating a
  result it did not measure; the per-commit file list is the evidence.
- **Splitting the contaminated commit needs explicit authorisation.** The fix is
  `git reset --soft` plus re-staging in slices, which rewrites history and
  requires the byte-identical tree-hash proof in this skill's commit section. Do
  not do it unilaterally, and never let a "tidy the split" pass re-edit the code
  being re-committed.
- **The parent's own editor is the same second writer.** The instinct to "just
  fix the two-line thing myself" produces the identical corruption without any
  second dispatch: a `patch` lands against a file the child is rewriting, the
  child's next write folds your hunk in or reverts it, and the file ends up with
  a duplicated block that neither of you authored deliberately. The tell is a
  patch whose second half fails with no match, because the target already moved.
- **The parent may still fix what no worker owns** — build config, CI, a
  manifest the child is not touching — but the moment a fix targets a file inside
  the child's declared scope, it belongs in a `steer`, not in the parent's
  editor. A steer carries the diagnosis and the file list; an edit carries only
  the bytes, and the child cannot tell the difference between your intent and a
  stray write.
- **If you already edited inside the child's scope, say so plainly and stop.**
  Repairing your own damage silently makes the child debug a phantom bug, and
  an unexplained duplicated block in a file you recently touched is a fact the
  user deserves in the report rather than a detail to quietly clean up.

## 14. Siblings that contradict each other force you to settle the premise yourself

Fan-out children share a goal but not a conversation, and they each see only
their own file slice. When their reports **conflict on a shared premise** —
"does this call re-enter?", "is this field ever `None`?", "is this actually a
bug?" — do not vote, do not average, and do not pick the majority. Two of four
children agreeing is not evidence; they may have inherited the same wrong
assumption from your goal text.

**Settle it from the source, in your own session, before relaying anything.**
Read the implementation the question is about and quote the lines. The
contradiction is a signal that the answer is load-bearing for the whole fan-out.

The child that says "your premise is false" is usually right (§2), and the
children that dutifully implemented the premise are the ones needing audit.

**Then audit each child's edits against the settled answer, not against the
goal you wrote.** A child that fixed a non-bug has usually left the code worse
than it found it, and the diff is where you see it:

```bash
git diff -- <each file a child claimed to change>
git show HEAD:<file>            # what the pre-existing code actually did
```

Two regressions to look for specifically, both introduced by well-meaning
"hardening":

- **Complexity for a hazard that does not exist.** If the base revision
  already dropped the guard before the call the child was "protecting", the
  edit adds a branch and a fallback for a condition that cannot fire. Revert
  it; do not keep it as defensive depth.
- **A fallback that loses data.** Converting a fallible operation to a
  best-effort one is a semantic change, not a safety improvement. If the
  contended path now silently drops a log line, a write, or a frame that the
  original always recorded, the child has traded a real guarantee for a
  hypothetical one. Revert or make the fallback lossless.

The genuinely-valuable outcome of a fan-out is often the *classification*, not
the edits. A child that reports "N sites, all provably safe, I changed
nothing, and here is the evidence" has done the expensive part; preserve that
and let it stand. Editing safe code is how a safe codebase acquires unmaintainable
defensive layers.

## 15. Never present a tree a live worker is still writing

A user asking to *see the result* forces a decision you cannot defer: something has
to be on their screen now, and the fastest thing to put there is whatever the local
server is already serving. That makes the build state a correctness question, not a
convenience one. Two workers that both edited `src/` means the served artifact may
contain half of each.

Before serving anything, establish what the served bytes actually are:

```bash
pgrep -fl "cargo build|rustc" || echo "(no build running)"
stat -f "%Sm %N" -t "%H:%M:%S" src/*.rs | sort -r | head -4   # newest source
stat -f "%Sm %N" -t "%H:%M:%S" www/pkg/<crate>_bg.wasm        # artifact
```

Then confirm the server is not lying about its own contents — the served size must
equal the on-disk size:

```bash
echo "served: $(curl -s http://127.0.0.1:PORT/pkg/<crate>_bg.wasm | wc -c)  disk: $(wc -c < www/pkg/<crate>_bg.wasm) bytes"
```

An artifact older than the newest source, or a served/disk size mismatch, means you
are about to show the user the previous build while implying it is the new one. Fix
the build, or state plainly which build they are looking at.

**Attribute what is and is not in the artifact, per worker.** When several workers
were dispatched, say which of their changes the served build contains and which are
still in flight. A user who sees the feature that shipped and not the one that did
not will otherwise assume the undelivered part is broken. Name the in-flight work
as in flight.

Prefer the newest *complete* build over the newest *started* one. A finished
artifact from three minutes ago is honest and reviewable; a half-written one is
neither.

**Prove the artifact is current by re-running the build, not by trusting the mtime.**
An artifact whose timestamp is older than the newest source may still be fine — a
concurrent worker may have committed the very change that was uncommitted when you
built. Re-run the build and read the elapsed line: `Finished in 0.03s` (no
recompilation) means the on-disk artifact already matches current HEAD, which is a
positive proof the mtime comparison cannot give. A real recompile means the previous
artifact was stale and the new one is the honest one.

### A port is part of the deliverable — reserve the user's before dispatching the worker

Serving a build to a user means a live process the *user* owns, on a port *they* may
want to stop, restart, or point their own tools at. The port is therefore a shared
resource with three claimants, and the parent assigns all three explicitly:

- **Before dispatching any build/serve worker**, enumerate what is already listening
  and record it. Do not let a worker discover ports by trial:
  ```bash
  lsof -nP -iTCP -sTCP:LISTEN | awk 'NR==1 || $9 ~ /:(8[0-9]{3}|9[0-9]{3})$/'
  ```
- **Give the worker a specific free port**, and put the full list of occupied ports
  in the brief as off-limits, plus the rule that a port they did not check is not
  fair game (§17).
- **Reserve a separate port for the user's own session**, chosen at dispatch time and
  reported in the same breath as the build. If a worker starts a server on the port
  you meant to reserve, the port you report to the user is already occupied by a
  process they did not start.

When the user says "stop that port", the kill is not the whole job. A serve worker
holding that port will **re-acquire it** on its next verification step unless told
otherwise, and the user gets a port that looks stopped and is not. Kill the listener,
confirm it is actually free, then `steer` the live child to stop serving and to
leave no resident process behind:

```bash
lsof -ti tcp:PORT >/dev/null 2>&1 && kill $(lsof -ti tcp:PORT) && sleep 1
lsof -ti tcp:PORT >/dev/null 2>&1 && echo "still held" || echo "free"
```

Steer with the *new* constraint only — "no more servers, converge to build-only,
pkill only your own instance" — not a restatement of the original goal.

## 18. A child that deletes its own evidence between runs

A verification child that re-runs its suite between iterations will often
`rm -rf` the output directory first. That destroys the *previous* run's
verdicts while leaving only the newest run's summary table — and the
newest run is frequently the one that crashed on a subset of workers.

**The symptom is a number you cannot check.** The child reports "50
verdicts, 15 pass, 16 fail"; the run log holds only the per-worker summary
table; the individual verdict lines, the `results/*.json`, and the
per-worker logs are all gone or truncated to zero bytes.

**Never relay a count whose source you cannot open.** If
`glob(results/*.json)` is empty but the child quoted a total, the total is
unreportable — say the run happened and the artifacts were lost. Make the
next run write somewhere a rerun cannot reach:

```
RESULTS=/abs/path/results/$RUN_ID      # unique per run
cp -r "$RESULTS" "$RESULTS.keep"       # never deleted by the next run
```

Check the artifacts *before* the child's summary arrives. Two runs minutes
apart with a `rm -rf` in between is the shape to look for.

## 19. Pre-settle the root cause — it is the difference between 18 recon calls and one commit

A child handed "find why the player gets stuck" will spend its whole
budget reading files and return mid-sentence with a plan. The same child
handed a located `file:line` chain, a ranked priority list, and "if you
can only do the first two, do those two and say the rest was not done"
produces a real commit.

**Locate the suspected root cause in the parent's own session before
dispatching.** Read the actual lines, confirm the mechanism, put the chain
in `context`:

```
src/game.rs:6099  apply() returns fired
src/game.rs:6106  if fired { enemy_shot(game, index) }
src/game.rs:6154  fn enemy_shot  <- no has_line_of_sight anywhere on this path
src/game.rs:6185  hurt_player(game, damage)
```

Tell the child to **verify** that chain, not accept it — an unverified
guess is worse than nothing, because the child rationalises it instead of
checking. This session: the first dispatch burned 18 calls and changed
nothing; the second carried the located chain plus
`"if you can only do P0-A and P0-B, do those two and say P1/P2 were not
done"` and shipped a commit in one pass.

**Rank the work and authorise a partial result.** "Fix A, B, C, D, E"
produces a child doing a thin slice of each and reporting a partial pass
on all. A ranked list plus an explicit permission to stop produces a
child that actually ships the top items.

## 20. A stall verdict is a claim about the sampler until the sampler is audited

A walking test walked from spawn and reported "12 of 24 frames completely
static — stair-step stutter". Dispatched as a defect, it was disproved: an
unthrottled per-frame trace gave a constant `|d|` on **every** frame with
`nearShapes=0`, across three input paths (yaw 0, yaw 90, and direct intent
injection bypassing key events). Zero zero-displacement frames.

**The first explanation offered — "spawn sat beside a wall" — was wrong.** The
real cause is that the page's debug-state writer is **throttled**: it publishes
its snapshot every N frames, so the counter the harness samples advances in
strides. A trace read `267, 270, 273, 276`; the unthrottled one read
`43, 44, 45, … 90` with no gaps. A harness that walks the counter and calls
each skipped publish "a frame where nothing moved" **manufactures a perfect
periodic stall out of a smooth walk** — and the manufactured period is exactly
the throttle stride, which reads as a very convincing bug.

So a stall is never evidence until the sampler has been ruled out. Two
independent causes produce the same signature — skipped publishes and a real
freeze — and are distinguishable only by the frame numbering.

- **Read the raw frame-number sequence and look for gaps before believing any
  stall, no-decrement, or "frozen input" verdict.** Gaps that are a fixed
  stride = throttled writer. Consecutive numbers that do not advance = real.
- **Build the per-frame trace in-page** (an unthrottled sampler appending to an
  array, returned in one round trip) rather than polling the published
  snapshot. The throttled channel is a *reporting* cadence, not the sim cadence.
- Cross-check with an input path that bypasses the event layer (inject the
  movement intent directly). If the bypass is clean and the event path is not,
  the defect is in input handling, not the physics under test.
- When you revise a cause you already stated, correct it **explicitly, naming
  the wrong reason** — a right conclusion resting on a wrong reason is still a
  wrong lesson, and it is the next session's starting point.

This applies to every periodic-symptom verdict: "frozen", "no input", "the
loop is dead", "frames stall every third frame". Audit the sampling cadence
before dispatching a fix.

**Move the fixture away from whatever the previous fix touched.** If the last
commit was "wall collision", do not test walking at a point that is against a
wall.

- **Probe the fixture before trusting its verdict.** An open position must
  report no nearby colliders. A test point that reports nearby colliders is not
  neutral, and its verdict belongs to the collision path.
- A worker that relocates the fixture and finds the defect vanish has done the
  expensive part. That finding **deletes** a task from the board rather than
  adding one — take it, say so explicitly, and do not carry the phantom forward
  into the next dispatch as a live bug. But check *which* relocation fixed it:
  "moved away from the wall and it vanished" and "sampled unthrottled and it
  vanished" produce the same clean result from different mechanisms, and only
  one of them generalises.

**Full diagnostics, and the four sibling artefacts of the same mistake — atomic
snapshots, saturated frame-time caps, interaction-distance failures, and
render-config in the URL — are in `references/debug-channel-validity.md`.**

## 21. Fix → verify → fix cycles: one writer, N readers, findings grouped

When asked to drive defects to parity with a reference ("循环直到功能完美对齐
X"), run it as a loop of phases, not one long task:

| phase | parallelism | why |
|---|---|---|
| fix | **1** writer | all symptoms share source files; concurrent writers corrupt the tree |
| verify | **N** read-only | disjoint debug ports + profiles, no shared write set |

State the phase split to the user with the reason. Running 1 where they said 8
reads as a shortfall unless you say why (`find src -name '*.rs' -exec wc -l`
— one file holding 37% of the tree is the evidence).

- **The verdict JSON is the only record.** Keep it where a worker's own reruns
  cannot reach it (§18), and require a file per worker even when all checks SKIP.
- **Group the next fix by root cause, not by failing assertion.** A dozen
  assertions routinely collapse to four causes; one task per assertion puts
  several writers in the same function.
- **Hand the next writer the previous writer's rejected hypotheses with their
  evidence.** A diagnosis accepted uncritically is worse than none — the child
  rationalises it instead of checking.
- **When your own measurement contradicts a child's, that contradiction is a
  finding.** Attach the artifact and the literal description to the next
  dispatch as a new root-cause group, and name the earlier assumption it
  overturned. This session: a vision description of "13 disconnected fragments,
  no torso or limbs" overturned a standing assumption that the instance table
  and model matrices were fine — the geometry was drawn, it just did not
  assemble.
- Loop until a full pass returns clean, or until every remaining failure is a
 **harness** fault — then fix the harness, not the app, and say so in exactly
 those words. Workers that crash on their own bugs (`ZeroDivisionError`,
 `KeyError` on a field their own `st()` never read) are reporting tooling
 defects, and counting them as app failures corrupts the defect list.

 ### Do not verify a defect a writer is concurrently closing

 The phase table above is about *parallelism within* a phase. The failure is
 crossing the boundary: a verification child left running against a defect that
 a fix child is already closing measures a **moving target**. Its numbers belong
 to whichever build happened to be deployed at that moment, so it cannot converge —
 it re-runs, gets a different number, and spends its whole budget reconciling
 readings that were never comparable.

 One session ran a verifier through thirteen scripted re-runs of a single
 scenario while a writer was mid-flight on the same defect. The first three runs
 carried the finding; the next ten were the child trying to make contradictory
 numbers from different builds agree. None of them could have, and the parent
 spent a turn per run narrating a process notice that carried no information.

 - **Sequence the phases against the defect, not just the tree.** A verifier may
 run concurrently with a writer only on defects no writer is touching. Anything
 the writer owns is verified *after* the commit lands, on the new build.
 - **When a verification child starts re-running one scenario without converging,
 that is a stop signal, not persistence.** Read its last two logs for whether
 the build changed between them. If it did, the runs were never comparable —
 tell it to hold until the writer commits, or stop it.
 - **A fix that is in flight is not a thing to verify.** "It is 40 minutes in and
 has uncommitted changes" is a status, not a finding; the verification belongs
 to the commit.

 ### A fixture check that warns instead of aborting produces garbage data

 The rule that a harness must confirm its fixture actually reached the subject is
 worthless if the confirmation is advisory. A child whose teleport silently failed
 printed the warning, continued, and produced a `before` baseline measured in open
 ground — which would then be cited as proof of a regression.

 **Put the check in the brief as an abort.** "If the teleport does not land within
 N frames, raise — do not print and proceed" is one sentence, and it is the
 difference between a baseline and a fabrication. The same applies to a readback
 that returns the spawn position: the value being well-formed is not the value
 being correct.

 ### Repeating a status line does not update it

 A background-process notice for an intermediate step gets a one-line status. The
 failure is issuing that *same* line for the eighth notification in a row: the
 user cannot tell a stalled run from a progressing one, because both are
 "still running".

 If the same status repeats, either say something new — what changed since last
 time, what the next step is — or say nothing and end the turn. A status line's
 job is to be worth reading; repeating it verbatim spends the user's attention to
 tell them nothing they did not already have.

 ### A user asking "is it done?" three times is a report on your reporting

 The question is not the user failing to read your updates. Repeating "still in
 progress" while a child runs for hours, with no delta between updates, is the
 defect. Each repeat costs a turn and returns the same content, and the user is
 left unable to distinguish a stalled run from a working one.

 Two rules follow:

 - **Convert progress into state on the first repeat.** Stop narrating the
   dispatch and publish the ledger: which items are committed and verified,
   which are committed but unmeasured, which are untouched. That table is what
   the question is asking for; the fact that a worker is alive is not.
 - **A status update must carry something the user could not already infer.**
   Elapsed time, a still-running marker, and a repeated scope statement are all
   derivable from the previous update. A new measurement, a completed stage, or
   a newly discovered premise failure are not.

 If the honest answer is "no, and the remaining work is gated on X", say that
 plainly in one line — the user can then act. "Still running" gives them nothing
 to act on except to ask again.

 ### Do not route a child's own run to the user, or keep answering with the next step

 When a user has asked repeatedly for a result, handing back "child is still
 running, it will report next" converts your verification duty into their waiting.
 Finish the measurement you can finish yourself (build the artifact, read the
 commit, drive the page), report what that shows, and name the one thing only the
 child can settle. Everything else is your work, not a progress note.

## A child's prose can contradict its own artifacts — artifacts win, and neither settles it

§7 is a child that finished nothing and said it finished everything. This is the
mirror: a child that did the work, and whose **summary text is wrong about its
own output files**. Observed where a child's report said a measurement read
`+1.4400 rad` while the verdict file it had written minutes earlier still
recorded `0.000` across eight samples and a `FAIL`.

Both are on disk; the prose is the later, more confident-sounding one, and it is
wrong. The child had silently **corrected a finding without correcting the
record** — plausibly because it re-ran with a different method and reported the
new number while the stale artifact kept the old verdict.

- **When prose and artifacts disagree, open the artifact and treat the prose as
  unverified.** Do not average them, and do not accept the prose merely
  because it is the more recent one.
- **A child that revises a finding must say which method produced the new
  number and what the old one was.** "Actually it works" is a new claim needing
  its own artifact, not a correction to the one already on disk.
- **Two measurements saying zero and one saying non-zero is three unresolved
  readings, not a majority vote.** When independent probes disagree about a
  value, record it as **undetermined** and route it to whoever can settle it
  with a purpose-built probe. Do not relay any of the three, and do not let the
  user believe the defect list is settled on that row.

Corollary for the defect ledger: a row that has been re-derived twice needs an
explicit `UNDETERMINED` state, not a PASS and not a FAIL. Rows carrying one get
quietly promoted to fixed in the next summary, and the promotion is the error.

## Stopping a child mid-run destroys the run you were about to report

A worker halted while still writing its results leaves partial files that
overwrite the good run. Reported mid-flight it read 42 pass / 3 fail / 46
skip; the durable state on disk was 30 / 3 / 39, because the last write
truncated workers that had not finished. Every backup predated the good run,
so the number was unrecoverable — not wrong, simply never persisted.

- **A count is only reportable while its writer still owns it.** Stopping a
  child freezes the last *atomic* write, not a coherent snapshot, and a
  partial file is worse than a stale one because it looks current.
- **Before relaying a number from a live run, check the writer is finished.**
  If it is still active, the count is a status, not a result.
- **Killing a child is a decision about the tree, not just the process.**
  `git status` the paths it owns first; its committed work stays, its
  uncommitted partial output may not.
- **When you retract, say it in one line and say what is still true.** The
  durable artefact in that session was the harness *code*, not the tally —
  naming which of the two survived is more useful than the number you
  withdraw.
- The same caution applies to a partial run you choose to abandon yourself:
  a half-finished suite reported as a total is a fabrication with extra steps.

## Never let a unified-looking number survive a check of the conditions

A number that appears to *unify* two unrelated observations is the most
seductive finding in a bug hunt, because it promises one root cause instead of
two. `0.945` matched a `sprint/walk 0.94` reading and was dispatched to a child
as "the deeper root cause" — a conclusion that then had to be retracted.

**Before building a theory on a number, establish that it was measured under
conditions where it could mean anything.** Here the frame-time cap was
saturated in 83/83 frames, which made the two modes mathematically
indistinguishable; the ratio was pure artefact. The tell: the number is close
to 1, close to a round fraction, or close to a *different* measurement that has
no shared cause with it.

When you retract, correct the record explicitly and name **which part was
wrong** — not just the new conclusion. A right conclusion resting on a wrong
reason is the next session's starting point, and so is a silent reversal.

## Re-measurement has its own failure modes — the parent's own check is not a safe default

The parent's verification pass is where a false conclusion is most expensive: it is the
reading the user believes, and it survives into the next session's premise. Four ways
it went wrong in one session, all of which looked like diligence.

**A hit count on a string literal is not a count of the identifier's uses.** The
converse of the empty-grep trap, and it cost a real writer. Checking whether a
key was wired with `git grep -c "ArrowUp" -- src/` returned `1`, and the
natural reading — "one definition, nowhere consumed" — was wrong: that `1`
was the string *literal* in a constants file. The identifier was already in
the tracked-key list, tracked and never read. The actual break was a single
consumer line assigning the steering input from a different key pair.

```bash
git grep -c "ArrowUp" -- src/            # 1  -> the literal, proves nothing
git grep -n "ARROWUP" -- src/            # the identifier's real wiring
```

- **Grep the identifier, not the value.** A value you will find declared in a
  constants file exactly once by construction; only uses of the *name* can
  tell you whether anything consumes it.
- **A tracked input with zero consumers is a distinct defect shape** from an
  untracked one, and it survives any check that only asks "is the key in the
  tracked list". Ask who reads the field, not who declares it.
- **When a child contradicts a premise built on a grep count, the child's
  reading wins** (§2) — but re-derive it with the identifier form before
  you accept it, so the correction is evidence rather than deference.

**An empty `grep` is not evidence of absence — resolve named constants first.**
Checking whether a feature existed by grepping for the literal token
(`KeyG`, `KeyH`, `KeyV`) returned nothing, and the natural conclusion was "the keybinds
were never committed, the child's report is false." The code was present: the keycodes
lived in named constants (`KEY_GRENADE: &str = "KeyG"`) and the branches matched on
the constant. The lesson is not "grep is unreliable" but that **a literal search for a
value is only valid once you know the code does not alias it.** When a negative grep
would contradict a child's claim, resolve aliases before believing the negative:

```bash
grep -rn 'KEY_GRENADE\|"KeyG"' src/          # constant name AND its value
git show HEAD:src/game.rs | sed -n '4270,4350p'   # read the match block
```

This one nearly became a reported defect. A false "not implemented" is worse than an
unverified "fixed", because it sends the next session to re-diagnose a solved problem
or to re-dispatch a writer for work that is already in HEAD.

**"Disjoint write sets" is a claim about the diff, and you must verify it.** Dispatching
two fix agents in parallel, the brief asserted their file sets did not overlap. They
did: both needed the debug/telemetry export layer, which in this codebase is a large
format string in the largest source file, and one agent found its work absorbed into the
other's commit while the second ran `git restore --staged` on a file the first had
staged. Scope the writers by **the lines they will edit**, not the modules they were
described as owning:

```bash
find src -name '*.rs' -exec wc -l {} + | sort -rn | head -5   # the hot files
grep -rn "DEBUG_OPEN\|__vcw\b" src/ | cut -d: -f1 | sort -u  # shared export surface
```

Any file that appears in both children's scope — especially a shared telemetry string,
a constants file, or a build script — is a collision. Either serialize on it or hand
one child the shared file and tell the other to route its changes through the first.

**A stash is not necessarily lost work — diff it against HEAD before recovering it.**
After a parallel run the tree had a stash holding 552 changed lines and a child's
report claimed everything was delivered. `git diff HEAD stash@{N}` settles which story
is true in one command: empty output means the stash is already committed, non-empty
means work is genuinely missing. Do not `stash pop` blind — a pop onto a tree that has
moved past the stash reintroduces stale versions of files another session has since
rewritten.

When the diff is non-trivial, note that it cannot settle *correctness*, only presence:
the stash held `player.jump(was_grounded)` while HEAD held
`player.set_jump_requested(was_grounded)`, two different implementations of the same
call site. Confirm the live path is the intended one by reading HEAD, and treat the
stash as history rather than as a candidate to merge.

**A child can under-claim as well as over-claim, and the artifact is the only arbiter.**
One agent reported it had committed a nine-line change while the real work — 214 lines
across four files including every mechanism it described — had landed in an earlier
commit under someone else's message. The report was not dishonest, just misattributed,
and reading it would have made you audit the wrong commit. Attribute by inspecting:

```bash
for c in $(git log --format=%h <base>..HEAD | tac); do
  echo "--- $c  $(git log -1 --format=%s $c)"; git show --numstat --format='' $c
done
```

A child narrating which commit carried its work is as unreliable as one narrating a
result it did not measure.

## A test that builds its own world is a test of the fixture

The most expensive false green found this session was a unit test whose fixture
reconstructed the world by hand — and reconstructed it *slightly differently from
production*. The hand-built upper slab stopped at the edge of the tread run; the
real builder's slab covered the whole flight. The test asserted the correct
behaviour, passed for months, and the app was broken the entire time.

A defect that survives a passing unit test is evidence about the fixture, not
about the test's intent. So when a test guards a geometry or layout behaviour:

- **Query the production constructor, not a copy of it.** The load-bearing version
  of the fix was one line of difference: `world()` → `build_showcase_interiors()`
  instead of the local `slab_world()` fixture. That is the entire difference
  between a test that can catch the bug and one that cannot.
- **Prove the new test fails on the old code.** "Fails before, passes after" is the
  only property that makes a regression test load-bearing. An existing green test
  that never went red was not guarding anything.
- **A defect that outlives several fix attempts is a fixture smell.** Before
  dispatching fix N+1, ask whether the existing test for that area ever went red
  for the real reason. If not, the test is part of the defect.
- **Corollary for the child: rebuilding a stale fixture is in scope**, even when
  the brief said "fix the source". A child that notices the fixture no longer
  matches production and rebuilds it has done the work; one that keeps a
  convenient fixture to make its fix pass has hidden the bug in the one place
  nobody re-reads.

## Collision world and render assets can diverge for months, and the visual is often right

A slab that covered an entire stair flight had been wrong since a commit three
months earlier, and the player could *see through it* the whole time. Nothing
looked broken because the render mesh never had the bug.

When a collision complaint persists across several fix attempts, stop re-reading
the collision code and **diff the collision world against the asset it is supposed
to mirror** — face count, extents, which faces exist at all:

```
assets/bldg_*_showcase.json  floor_upper  -> two top faces, second stops at z=0.05
collision builder            -> slab spanning z[stair_end, hz]
```

The tell is a player complaint phrased as "I can't do X" that coexists with "X
looks fine". That combination is not a physics puzzle; it is two sources of truth
that have drifted, and the render is the trustworthy witness.

The fix belongs on whichever side is wrong, even when the wrong side is the one
the brief described. Correcting the collision slab to match the asset also keeps
the two from re-diverging. An alternative that makes the physics tolerate a slab
the player can see through fixes the symptom and entrenches the drift.

## Related

- `main-agent-delegation-rule` — when to delegate at all.
- `references/debug-channel-validity.md` — when the page's debug channel invents
  symptoms: throttled-writer stalls, atomic snapshots, saturated frame-time caps,
  interaction-distance artefacts, and why a zero-width box is a subject defect.
- `references/visual-acceptance-gates.md` — gates a background can satisfy by itself
  (luma/contrast/area), collapsed bounding boxes, and when to insist on a perceptual
  read instead of a statistic.
- `verifying-against-a-real-gate` — proving a gate reads the channel it claims to.
- `browser-app-self-verification` — the loop that produces the evidence before you
  show anything, including handing the user their own browser window.

---

## A premise you measured yourself is the one that poisons every downstream dispatch

§20 covers auditing a child's sampler. The harder case is when **you** built the
finding, dispatched a writer on it, and the finding was the invalid part. One
session dispatched two fix rounds on root causes taken from your own readings
and retracted both — and each retraction cost a live agent's work, because a
writer handed a confident `file:line` chain treats it as settled and optimises
for the wrong target.

**Rule: before dispatching a writer, ask what would have to be true of the
measurement, and check that.** If the answer is "the channel is not throttled"
or "the field has a reader" or "the metric is monotone in this quantity" —
those are checkable in one command, and skipping the check spends a writer.

**When the premise is wrong after the writer has started, `steer` to shrink the
scope, do not send the correction as a footnote.** A writer told "the premise
was wrong" without a replacement will either keep going or wander. Send: the
measurement that settles it, the explicit instruction not to touch that file,
what remains, and a re-confirmation requirement ("re-run your probe before
changing anything"). The writer already has the file open, so this is the
cheapest possible form of course-correction.

**A writer that falsifies your premise has done the valuable thing — take the
finding, do not re-derive it.** One session's writer read the function, showed
it was already an identity function changed by an earlier commit, reported the
root cause was false, and shipped a real cleanup anyway. That is the outcome,
not a failure to apologise for. Verify the two or three load-bearing lines it
quotes, then say plainly that it was right and name which part of your own
report was wrong.

**The methodological tell that outranks any single reading: a probe that
validates itself against a value the app already publishes.** A direction check
built on a brightness centroid lost to one that projected a world-anchored
point through the app's own view-projection *and first confirmed the
projection reproduced the app's own character box digit for digit*. The
self-validating probe shares no code path with a heuristic diff, so the two
cannot agree while both being wrong the same way. When a verdict keeps
flip-flopping across sessions, look for which measurement had that property
and prefer it — the flip-flopping is evidence the others are under-determined,
not that the feature is unstable.

**Retracting a finding does not close the ledger row.** It moves the row back
to open with the retraction recorded against it, because the next summary
tends to inherit whatever the last summary said. The same applies to a
correction you issued only to a subagent: it must be stated to the user too,
or the next session inherits a premise you have already disproven.

## Audit the instrument you are holding before you read anything through it

The parent is not exempt from §20. The most expensive false premise is one the
parent measured itself and then dispatched a writer on — and there is a specific
recurrence: **you sample a channel, the reading looks anomalous, and you conclude
the app is broken without ever asking whether the channel measures the thing you
are reading it for.**

One session lost five fix dispatches to this single pattern, in five different
clothes:

| what you sampled | what it actually was | verdict you nearly shipped |
|---|---|---|
| stall counter from published state | throttled writer (3-frame publish) | "walk is stuttering" |
| walk/run displacement ratio | `{speed:N}` is time-warp, not speed | "sprint is broken" |
| an enter/pickup action | target was 12 m away | "vehicles are uncontrollable" |
| held-trigger flag | fire is bound to `mousedown`, not a key | "the player cannot shoot" |
| screen-centroid shift | centroid moves when content enters frame | "look direction is inverted" |

The common shape: **one reading, one conclusion, no check that the reading had room
to mean anything.** Each was a live writer's work wasted, and each retraction had
to be stated to the user because they had already been stated in the other
direction.

Rules that generalise:

- **Ask what would have to be true of the reading, and check that.** Is the field
  read by the code path under test? Is the metric monotone in the quantity you
  named? Is the fixture inside the interaction radius? Is the ratio free to differ,
  or are two modes arithmetically forced to coincide? These are one-command
  checks, and skipping one spends a writer.
- **Prefer a probe that validates itself against a value the app already
  publishes.** The direction check that finally settled the look-direction row
  projected a world-anchored point through the app's *own* view-projection and
  first confirmed that projection reproduced the app's own character box digit for
  digit. A self-validating probe shares no code path with a heuristic, so the two
  cannot both be wrong the same way — which is exactly what you need when readings
  have been flip-flopping.
- **A statistic chosen for the wrong subject fails in a characteristic direction.**
  A brightness centroid is not a displacement detector; it reports where the
  scene's light is. If the answer flips sign as you vary the magnitude, the
  instrument is the problem — that is the signature to watch for, not a sign of an
  unstable feature.
- **Scale-check the number before building on it.** 240 px of drag is ~82°, which
  on a 1280 px screen is an analytic displacement of ~1100 px — an entire scene
  replacement. A measured "+24 px shift" is not a small result, it is a different
  scene, and it has no directional meaning.
- **When you retract, name which part was wrong, to the user as well as to the
  subagent.** Five of these were silently corrected in steer messages; had that
  stopped there, the next session would have inherited a premise you had already
  disproven.

The discipline is not "doubt everything" — it is that **the instrument gets the
same audit as the app**, and the first question about any anomalous reading is
"what is this channel, and does it feed the code path I think it does?"

### A frame-time number is the instrument most likely to be lying

Before attributing a rendering bottleneck, prove three things about the harness:

- **That it renders at all.** A headless flag that disables the GPU can leave the renderer constructed-but-null, so the app draws nothing and the "frame rate" you measured is an empty loop's cadence. The tell is in the app's own telemetry — a mesh/triangle tally reading 0, or a backend label reporting "none". Fix the flag, re-measure, and **discard every number taken before it**: they were not slow, they were not running.
- **That it can exceed the display cap.** With vsync on, two runs both report exactly the refresh rate. That precision is a warning, not a result — it means nothing varied. Uncap before believing a change "did nothing"; the real cost was invisible because the measurement had no headroom.
- **That the counter covers the stage you are blaming.** A draw/triangle tally accumulated in one pass excludes the passes you suspect. Triangle submissions are not time — a stage can be a third of the geometry and nearly free.

**Take the "feature disabled entirely" ceiling before optimising anything.** Without it, "we recovered 90% of the available gain" is uncomputable and a real win is indistinguishable from noise. It is one run and it decides whether the whole task is worth doing.

**Sweep the suspected resource across orders of magnitude.** A stage whose own workload varies 16× and whose cost does not move is not the bottleneck, and the fix will not pay — drop it rather than degrade quality for nothing. Report the rejected candidate and why; a discarded optimisation is a result.

**When a capture comes back empty, capture the unmodified baseline too.** Identical output on both proves the emptiness is the environment rather than your change, and that one comparison turns an unfalsifiable "cannot verify" into a usable result — including permission to substitute a different evidence channel (a counter, a diff, an aggregate) and say plainly which one replaced the visual check.

## A pile of bug reports usually collapses to a few root causes

A user listing a dozen symptoms — a model vanishes, a car clips through walls, the
player faces sideways while walking — is describing one map, not a dozen bugs.
Before dispatching a fix, read enough source to group the reports by **the code
that would have to change**, and say the grouping out loud when you hand the work
off. It changes the plan from N fixes to 3, and it tells the user why some of
their reports are not independent evidence.

The grouping levers:

- **One config value behind several symptoms.** A hard world bound explains both
  "invisible walls" and "the map isn't infinite" — find the constant
  (`half_extent`, a clamp, a max constant) and check which call sites read it.
- **One index misalignment explains several vanished models.** A "push" API that
  returns an index while the caller keeps using an enumeration order surfaces as
  *characters* missing in one scene and *vehicle bodies* missing in another,
  because both are the same table desynchronised.
- **A subsystem that exists but is never registered.** A complete occlusion or
  collision routine that only consults half the world's shapes is why a camera
  clips walls indoors but not outdoors.

Two traps when doing this:

- **A source comment naming the bug is not a fix, and is often the only trace of
  it.** A warning comment above the buggy function is strong evidence you found
  the real site — but the bug still ships. Report it as "the code already warns
  about this, and it is still broken", never as "already handled".
When a subagent explains a defect by auditing the audit script's own filtering
logic, verify the verifier directly. A "1 hit" whose verifier prints
`0 violations` is a counting bug in the wrapper — a finding about the tooling,
not the code under test. Say which of the two it is rather than relaying the
number.

- **A source comment quoting one test run is a stale liability, not documentation.**
  A fix whose comment read "实测下楼沿 +X 走到 x=27.4 仍 y=3.2" recorded a transcript
  of one harness run, not a reason. It goes stale the moment the geometry moves, and
  the next reader cannot tell whether it describes a cause or an observation. Point
  the comment at the **root cause** — the slab's z range and the sign error in it —
  and let the test carry the numbers.

**State the grouping to the user, then dispatch against it.** The grouping is not
just a diagnostic; it is the task decomposition. Bug reports that share a root cause
share a worker — dispatching "invisible walls" and "the map is not infinite" to two
workers puts them in the same constant with two writers. Conversely a report that
looks unrelated to a fixed one is usually a second symptom of it, and the worker
who fixes the root will surface the second one for free.

**Name the sub-tasks that are in fact independent, and the ones that are not.**
Say explicitly which reports share a worker, so that when only two workers land
instead of eleven, the user is not reading a shortfall against a promise of eleven.

### Verify the root cause you are about to promise, in your own session

The grouping is cheap to do from a grep and easy to get wrong, and it is the one
thing in the whole cycle you will repeat verbatim to the user as fact. Before the
dispatch goes out, read the actual lines behind each claimed shared cause:

- A hard world bound behind two reports: find the constant and check how many
  call sites read it.
- An index misalignment behind two vanished models: find the push-style API and
  confirm the caller's index really is stale.
- A subsystem present but unregistered: confirm which half of the world's shapes
  reaches it.

A 90-degree or one-axis disagreement between two coordinate conventions is the
classic real cause of "the character faces sideways while walking" — compare the
angle convention in the movement code against the one in the render matrices, and
do not accept a plausible-looking rotation constant as evidence. A worker that
scripts the two conventions and prints a truth table settles it in one call; ask
for that rather than for a claim of correctness.

**Quote the evidence inline when you report it**: the constant and its line, the
truth table row showing the two conventions disagree. A root cause handed over
without its evidence is a claim the next session has to re-derive, and re-deriving
is the expensive part.

**Root causes you verified belong in your report with the evidence inline** — the
line number, the constant, the diff proving two conventions disagree. A later
session should be able to skip re-deriving them.

### Re-run the gates and expect the child's own numbers to differ

Children routinely report gate figures that do not reproduce — one reported
`cargo check` 174 against a measured 173, and `clippy` 185 against a measured
228, from the same commit that its own summary described accurately. The report
is usually not dishonest; it read a count at a different moment, with different
flags, or through a wrapper that filters differently.

**Re-run the gates and relay your numbers, stating that they are yours.** Do not
average them and do not adopt the child's figure because it is the one attached
to the commit. If you adopt a child's number, say so — and if the two disagree,
say which one you measured and why you trust it (a command the user can re-run
beats a number with no provenance).

### A child that rejects your premise three times is telling you the measurement, not making excuses

This session produced three independent cases where a dispatched child proved a
prescribed fix wrong and declined to ship it:

- a "genuine mesh break" that was a legitimately separate emissive part;
- a constant I told it to raise, where a raycast showed the target sat at **0.0%
  self-visibility** because of an inverted sign, so the change would have buried
  it further;
- a matrix fix I prescribed (negate the y row for a Y-down convention) that the
  camera **already handled**, so applying it flipped the scene upside down.

Each time the child named the evidence, and each time measurement confirmed it.
That pattern is worth naming in the report as *"the worker rejected two of my own
instructions after proving them wrong"* — it is a real result about the brief's
quality, and it is what tells the next dispatch that the premise needs
re-deriving rather than restating.

**Corollary: a verifier can enshrine the bug it was written to catch.** In the
same round, `check_window_recess.py` had encoded the inverted sign as its
invariant, so it returned healthy on the broken asset. When a worker's
measurement contradicts a pre-existing check, treat the check as suspect before
treating the measurement as wrong — see §0.

### When a child's honest report is "the infrastructure is right and the effect is invisible"

Accept that shape of result and route it forward; do not spend a round trying to
make the child claim more. A child that says *"depth is written and sampled
correctly, validation is clean, zero errors — and I could not demonstrate any
visible effect, here is the parameter that explains why and here is what I could
not test"* has done the valuable part: it located the blocker as a **reachable
parameter** rather than a code defect, and named what it could not reach.

The parent's next move is to remove that blocker (here: a missing URL parameter
that made a second lighting phase unreachable) and demand a **controlled pair** —
same camera, two parameter values — because a single frame cannot distinguish
"the effect is short under these parameters" from "the effect does not work".
Then re-verify the pixels yourself before reporting.


**Once reported, the same root cause reappearing in a later report is a regression
signal, not a new bug.** When a symptom the user has already reported comes back,
the premise of the earlier fix was wrong somewhere: the shared constant gained a
second call site, the index table gained a second producer, or the fix landed in
one call site and not the other. Re-derive from the root cause rather than
dispatching the symptom as new work.

---

### A silently-dead lookup passes every gate you have

The most expensive class of bug is the one whose failure mode is **doing nothing
without saying so**. A binding that does not exist, a uniform name that matches no
declaration, a settings key that is never read: all produce a clean build, a clean
console, a non-empty screenshot, and no error anywhere.

| the API | returns for a missing name | what you get |
|---|---|---|
| WebGL `get_uniform_location` | `None` | `uniform1f(None, …)` is a total no-op — the value silently keeps its shader default |
| browser `querySelector` | `null` | optional chaining turns a missing element into a no-op, not an error |
| config / dict lookups with `.get()` | `None` | the caller proceeds with a default nobody checked |
| dead-code-elided exports | — | the symbol resolves, so it looks wired while nothing consumes it |

**When one implementation measures N× worse than a reference, suspect the
reference before optimising the port.** A cross-backend ratio is a claim about
*both* sides, and one side may not be running its code at all. The tell is a
ratio large enough to look structural (this round: 82.6×) produced by a mechanism
that is trivially silent.

How to settle it, in order:

1. **Assert every looked-up name is actually declared**, as a test. Then **verify
   the test fails on the old values** — a regression test that has never gone red
   is not guarding anything.
2. **Model the shared chain on the CPU and see which side it agrees with.** Here a
   hand reconstruction predicted ~0.0023 for both backends; the port matched and
   the reference read 0.296. A CPU model agreeing with one side is what localised
   the fault to the other.
3. **Look for the *absence* of the effect, not its magnitude.** A pass that
   redraws identical geometry against the depth buffer it just wrote never
   rasterises — its contribution measures exactly `-0.00000`. "This pass looks
   like it does something" is not evidence; **measure its ablation** before
   porting it.

**Corollary: an adjective inherited from a broken baseline is not a finding.** The
parent relayed "the port is 82× weaker" three times before a worker proved the
*reference* was multiplying the whole frame by 1.57 because its threshold uniform
never bound. Re-derive the comparison itself when a ratio is the headline.

## Concurrent writers make every gate number untrustworthy until the tree settles

Several agents editing one checkout — the normal state of a parallel fix round —
make gate readings unreliable **in both directions**: a `+2` warning delta that
is another agent's half-written edit, a doctest failure that is a transient
snapshot of a file being rewritten, and a tree that does not compile at all
because `cargo check` landed between two edits.

- **Attribute per file before believing a total.** Group the diagnostics by path
  and only count the ones in files you own:
  ```bash
  cargo check --all-targets --message-format=short 2>&1 | grep "warning:" \
    | grep -oE "src/[a-z/_]+\.rs" | sort | uniq -c | sort -rn
  ```
- **Say so in the brief**: "if a gate reading looks wrong, wait and re-measure
  rather than assuming you caused it." One child this round correctly reported
  its deltas were contamination, with mtimes as evidence — that is the answer
  you want, not a rushed `#[allow]`.
- **Measure in an isolated worktree** when a number really has to be authoritative
  while siblings run: `git worktree add`, then apply only your own files.
- **Never propagate a concurrent-edit artifact as a regression.** Two phantom
  readings this round would each have sent a worker fixing a bug that did not exist.
- **Related hazard: one child's `git checkout` reverts another's uncommitted
  work.** Stage by explicit path and confirm with `git diff --cached --stat`
  before every commit in a shared tree; when work has vanished, check
  `git diff --stat` before assuming it was never made.

## A refactor that replaces an entry point leaves dead code that reads as a regression

Swapping an approach (a disc for a real footprint, a lookup for a direct call)
makes the old entry point dead — and dead code trips the same gate as a real
regression, so it must be resolved before committing, not explained away.

- **Delete it, or prove it is reachable.** A `pub` method can look dead to the
  lib's own analysis while tests or `tools/` still call it; grep the whole repo
  before believing `dead_code`.
- **Never `#[allow(...)]`** where the project counts allow macros as a violation.
  Fix by cause.
- **Duplicated physical constants are the same defect waiting to happen.** Two
  copies of a radius in two modules will drift, and one will silently go wrong.
  Collapse them while you are in there.
- **A child's own new test being red is a hard stop**, not a footnote: decide
  whether the implementation or the expectation is wrong before it commits.

## 15. "Give me the steps, don't change it" — a hand-off means write the recipe, touch nothing

When the user says the equivalent of *"give me the steps, I'll do it"*, the
deliverable flips from *working artifact* to *instructions*. Reading this as
"keep going" is the failure — it produces unrequested edits to code the user
has taken ownership of.

- **Read enough source to be exact**: real paths, real function names, real
  line numbers, existing constant names and their doc-comment style. A generic
  recipe the user must re-derive is not a hand-off.
- **Edit nothing.** Not the target, not the caller, not the wrapper script.
  "Obviously required" adjacent edits wait.
- **Number the steps**, make each independently checkable, and end with the
  verification commands plus expected numbers.
- **Flag the easy-to-miss steps** that silently yield a half-working result —
  a change that must land in *two* call sites, or a CI file that must move in
  the same pass or the fix works locally and ships broken.
- **State the decision you did not make**, with your lean, then let them
  override.

Measuring the actual breakage first is what separates a real hand-off from
"here are 10 steps": it is what identifies *which* sites must change and how
many references genuinely break, instead of describing the general shape of the
fix. If a step is blocked on a decision that is theirs, say so rather than
quietly picking one.

See `references/hand-off-recipes.md` for a worked example (adding a CLI flag
across a build-script + CLI + CI + caller chain).


