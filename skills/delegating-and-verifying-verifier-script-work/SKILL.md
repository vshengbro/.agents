---
name: delegating-and-verifying-verifier-script-work
description: Use when writing or repairing a verifier, lint gate, or browser-automation suite, or delegating edits and trusting the result.
version: 1.1.0
author: hermes-curator
metadata:
  hermes:
    tags:
      - verification
      - code-review
      - git
      - delegation
    related_skills:
      - requesting-code-review
      - test-driven-development
    references:
      - browser-automation-harness-integrity
---

# Writing verifiers, delegating edits, and surviving a branch that moved

## When to Use

- Writing or fixing a `verify_*.py` / lint script for a repo, especially one
  that must tell real violations apart from legal-but-similar code.
- Building a guard that decides *whether a rule applies* — ownership, scope,
  exemption — before letting work through, whether it runs in a git hook, in
  CI, or in a pre-flight script.
- Accepting a script or a fix produced by a subagent, before wiring it into a
  hook or an audit suite.
- Establishing whether a derive macro / codegen library really exposes some
  API, especially when your probe disagrees with the user.
- Pushing follow-up commits to a branch whose PR may have merged meanwhile.

The failures below recur across this class of work. Each cost a full rewrite,
a silently false green, or a no-op commit.

## 1. Probe the library before believing a claim — including the user's

Before you state what a macro/derive/framework does, **compile a probe** and
call the generated code. Reading the source is not enough; source reading
answers "what is it supposed to do", the probe answers "what does it do".

The trap: a probe with a **wrong assumption about the API name** produces a
false negative that looks exactly like "the library does not have this
feature". A plausible wrong name ⇒ E0599 ⇒ you conclude the feature is
absent ⇒ you may "correct" a user who was right.

- Enumerate candidate names and test them all before concluding absence.
  `get_b_mut` / `get_mut_b` / `b_mut` — one of these exists, and the failing
  two produce identical E0599 text, so a single guess tells you nothing.
- When a probe contradicts the user, **assume the probe is wrong first**.
  The user has read the source; you wrote a guess.
- Corollary: a *negative* result from a probe is only as good as the names you
  tried. State what you tried.

## 2. Delegated verifier scripts: a subagent's version is a draft, not a result

A subagent handed "write a verifier for rule X" will happily return a script
that looks right and **silently over-flags**. A verifier that flags more than
the rule is worse than no verifier: it reads as "a check is running" while
producing false confidence.

Merge protocol before any delegated script is accepted:

1. **Fixture A/B diff, not eyeballing.** Build fixtures where the *correct*
   answer is known per-case. Run **both** implementations on the same
   fixture set; compare hit counts per case, not totals.
2. **The must-NOT-flag fixtures are the test.** Every exemption the rule
   grants needs a fixture that proves it is honoured. A `#[derive(Getter)]`
   struct's `#[set]` is load-bearing; a verifier that flags it proposes
   deleting a working setter.
3. **Prefer the conservative direction.** When uncertain whether an item is
   in scope, skip it. A missed violation is found later; a false positive
   burns the user's trust in the whole rule.
4. One script per rule. If two exist, diff them, keep the correct one, delete
   the other — never leave both registered in the audit, or every violation
   is reported twice.

### 2.0 Dispatch is part of the verification job — subagents cannot resolve placeholders

Writing the delegation prompt is drafting, not delegating: a `delegate_task` goal
is read literally by a child that has none of your context. Two failure modes
fire at dispatch time rather than at return time, so they cost a retry, not a
wrong answer:

- **Template markers are refused outright.** A goal containing `<run-id>`,
  `<PR_NUMBER>`, `<repo>` or any other unfilled placeholder is rejected with
  "contains an unexpanded template marker" — the child has no way to know what
  you meant. Substitute real shell syntax the child can execute
  (`gh run view RUN_ID --log`) rather than prose that names a value you do not
  have yet. Numbers the child will discover at runtime (`gh pr checks NUMBER`,
  where `NUMBER` is the child's own variable) are fine.
- **Shared environment facts travel in `context`, not `goal`.** Which auth path
  works, which binary is renamed, which CI jobs gate the merge, which trees
  already carry another session's uncommitted work — none of that survives if
  the child re-derives it, and each rediscovery is a turn. State it, and state
  the trap form ("the PAT in that path is stale — use `gh`") rather than the
  symptom, so a child that finds a different stale credential still knows what
  to reach for.

- **Flags do not travel between sibling subcommands.** Carrying an option from
  one verb to a sibling of the same CLI — `gh pr merge --delete-branch` into
  `gh pr create`, `gh run watch --exit-status` into `gh run view` — fails the
  child with `unknown flag`, usually *after* the work is done, so it costs a
  round trip. Check each flag against the verb it is actually attached to, and
  prefer a command the child could have confirmed with `--help` first.

  **When a CLI's preferred endpoint is the one that keeps failing, switch
  endpoints rather than retrying it.** `gh` prefers GraphQL for mutations and
  REST for everything else, so a `gh pr merge` that times out at the transport
  layer is not fixed by its fifth attempt — the same host path is the problem.
  `gh api -X PUT repos/<o>/<r>/pulls/<n>/merge -f merge_method=squash` takes
  the identical action over REST. And because a connection-level failure is
  indistinguishable from a request that never arrived, **always read the state
  back after a write**: `gh pr view <n> --json state,mergedAt` proves the merge
  landed, whereas a timed-out mutation proves nothing either way.

Put the verifiable acceptance criteria in `goal` (the command that must exit 0,
the exact fixtures and their counts, the PR URL to read back) and the environment
in `context`. A child that reports success against a file **it re-measured** is
the only report worth relaying — see §6 on claims that look verified.

**Check your own acceptance commands before dispatching, and prove an
environmental failure is pre-existing before the child spends a retry on it.**
A criteria line you wrote from memory is as likely to be wrong as a child's
conclusion, and the child will report the failure verbatim without judging it —
so an invalid command costs a round trip and looks like the child floundering.
Two habits prevent it:

- **Run the exact command once, yourself, on the current tree.** A
  workspace-wide flag combination that CI has never used is the usual culprit:
  a build that excludes a member is not a mistake, and asking for the full set
  fails on a dependency that cannot target that platform. Take the exclusion
  from the repo's own CI workflow rather than reconstructing it, and put the
  corrected form in the child's brief.
- **Reproduce at pristine HEAD before calling anything refactor damage.** The
  cheap proof is to park the work and run the failing command on the clean tree:

  ```bash
  git stash push -u -q -m probe && <failing command> 2>&1 | head -5
  git stash pop -q && git status --short | wc -l      # confirm it all came back
  ```

  Identical failure with zero modifications means the command was invalid, not
  the work. Check `git status` counts on both sides of the stash — a `pop` that
  partially conflicts leaves a tree that looks restored and is not.

Tell the child which is which explicitly, and **tell it not to attempt a fix**:
"pre-existing, do not chase it, use this command instead" saves a child from
"helpfully" enabling a feature flag or editing a manifest to make an invalid
gate go green.

**A child blocked on a sibling's scope is not a failure of that child.** When
two children share a worktree, one will routinely report the other's half-built
state as an unbuildable repo. Read the error's file paths before accepting the
explanation: a missing type in your crate is the other child's, and a
concurrent `git add` by one child can stage paths the other has not finished.
Attribute by **path ownership**, not by who reported it.

**One writer at a time is a design constraint, not a scheduling preference.**
The user often states it outright ("only one agent may write the code"). The
reason is not politeness: it is one shared checkout, so the second writer's
commit absorbs the first's staged work, and both children then report against
a tree neither of them fully produced. Cheapest discipline:

- Sequence writers, and make a read-only diagnosis the explicit precursor to
  each one, so the next writer's brief is settled before it starts.
- Two children touching the same module is the case to serialise, not to
  parallelise. Parallelise the *read-only* work — that is nearly free and it
  is what actually shortens the loop.
- A diagnosis child that goes on to edit anyway is a scope failure even when
  its edit is good; it makes the next child's brief stale.
- After any delegation returns, confirm the tree before repeating its claim
  as fact: `git log --oneline -3` plus `git diff --stat -- <the paths you
  scoped>`. Empty there is the proof that the scope held.
- When you discover two writers *did* collide, stop the redundant one
  immediately and re-verify against the commit that actually landed, rather
  than letting both push at the same file.

### 2.1 An exemption's fixture set is where it fails — audit it in both directions

When the change is **adding an exemption** rather than adding a check, the
fixture that matters is the one that must stay *loud*. An exemption is a hole
cut in a rule, and an over-wide hole is invisible in the compliant direction:
the positive fixtures pass either way.

Two obligations, both of which cost nothing and both of which catch a different
failure:

- **Record what the compliant fixture reported *before* the patch.** A
  compliant fixture that reports 0 both before and after proves the exemption is
  a no-op; 0 only *after* proves it did the work. Capture the baseline first or
  the evidence does not exist later.
- **Run the suite against the OLD implementation first and check the directions
  are actually opposite.** A rule rewritten to be stricter will have inverted
  which fixture tree reports findings, and a suite that only asserts the new
  behaviour cannot show the old code was wrong. Seeing the pre-patch verifier
  flag the compliant tree and pass the violating tree is the evidence that the
  patch changed the rule's discrimination rather than its thresholds.
- **Re-read every compliant fixture asking "is this genuinely exempt?"** Fixtures
  accumulate; a case added for an earlier reason may be a real violation that a
  new exemption will now swallow. A byte literal sitting in a function body,
  parked in the compliant tree as "just fixture setup", is a genuine rule hit —
  move it to the violating fixture rather than let the exemption absorb it.

**Exhaustiveness has a third direction beyond compliant/violating: a tree with
no children must not report.** A layout rule keyed on "a code file sits beside
a sub-directory" is vacuously satisfied in a leaf directory, and a fixture set
that omits the leaf case cannot distinguish that from a working rule. Cover the
three shapes — exempt-beside-children, violating-beside-children, and
keyword-file-with-no-children — or the rule has an untested silent pass.

**Persist the suite as a runnable script and mutate the rule to prove the
suite bites.** A fixture set that only ever passes is indistinguishable from
one that no longer tests anything. Two mutations settle it in seconds, and
both should FAIL:

```bash
# 1. re-widen the exemption the change just narrowed  -> violating tree goes quiet
# 2. disable the detection condition outright          -> violating tree goes quiet
# restore, re-run, confirm PASS
```

Ship it beside the verifier as `scripts/<verifier>_selftest.py` so the next
edit re-runs it (§5.7). When writing the assertion itself, scope the walk to
the compliant subdirectory — a `rglob` over the fixture *root* silently folds
the violating tree into the compliant pass set, and the suite then reports FAIL
for the correct implementation.

Anchor an exemption on the construct, never on the value. Exempting the
literal `"system"` because that is the value you were asked about misses every
sibling value (`"C"`, `"C-unwind"`) and quietly converts a structural rule into
a string allowlist that future code will grow entries into. Match the syntax —
`extern\s+"(?:[A-Za-z\-]+)"\s*(?:\{|fn\b)`, allowing the visibility and
`unsafe` prefixes — so a decoy that merely mentions the value keeps reporting.

**To let one file do something the rule bans, exempt by filename, and make the
self-test prove the exemption is that file and not its neighbours.** The
alternative — widening the rule, or adding `--allow <flag>` to every caller —
destroys the rule for everyone to accommodate one script. A named allowlist of
stems (`PAGE_LOAD_EXEMPT = {"ensure_browser"}`) alongside the existing
exemptions is the whole change; every other script stays subject to the rule,
and "the publisher opened its own tab" remains a defect rather than a shortcut.

Three ways the exemption silently does nothing, all caught by the fixture that
asserts the *positive* case is honoured — an exemption that never fires is
indistinguishable from a correct one on the compliant side:

- Matching on `path.name` fails whenever the caller passes a path whose name
  differs from the stem you allow-listed; match on `path.stem` and check what
  the caller actually supplies.
- A constant defined as `FOO` and referenced as `FO` raises `NameError` at call
  time, which reads as a flake rather than a typo. Grep the definition and
  every use together after renaming.
- **The fixture's own file name has to be the real one.** Self-tests that
  write `/tmp/_xguard_case.py` can never exercise a filename-scoped exemption,
  because the name it needs is the name the rule keys on. Give each fixture a
  scratch *directory* and write it as `ensure_browser.py` inside it; add a
  sibling `ensure_browser_helper.py` carrying the same offending code and
  assert it is still reported. That second case is the point of the exercise —
  it is the only thing that distinguishes an exemption from a deletion of the
  rule.

**The message a rule prints is part of the rule, and it must name a fix that
is clean under the repo's own lints.** A finding that says "move it into
`<name>/<name>.rs`" teaches the shape that trips `module_inception` and produces
warnings the flat layout did not have (§4.6) — the guidance manufactures the
debt it claims to remove, and the next session either follows it and regresses
the lint count or ignores the rule. When narrowing a rule, rewrite the advice in
the same patch: name the *semantic* sub-directory to use, say that the keyword
file name stays, and state the lint trap explicitly so the fix and the warning
cannot be reintroduced together.

Derive the suggested shape from something already in the repo, not from the
rule's own vocabulary: a rule about where declarations live should not invent a
directory name that collides with the filename it is told to preserve.

**Every rule that names one canonical home has a sibling home in the same
domain — find it before the first compliant change trips the gate.** A rule
saying "literals belong in `const.rs`" is only half a truth in a codebase that
also has a declarative token table: a CSS/DSL/config macro (`vars!`, `tokens!`,
`theme { … }`) is the *same kind* of home for the same kind of value, and it
gets no exemption. The tell is a token file carrying a large
**pre-existing** violation count in a repo you believe is clean — that count is
the sibling home, and every future token addition is a fresh gate block.

Proof before you exempt: the file's own contents are the evidence. A design-token
table whose every line is `name: "value";` is doing the same job the rule asks
`const.rs` to do, and hoisting those literals elsewhere would defeat the single
table the file exists to be. The legacy count alone is a *symptom*; read three
lines of the file and confirm they are the same shape the rule targets.

**Exempt by construct, brace-depth-tracked, and nested blocks are the case that
bites.** A macro block's inner groups close with an indented `}`, so a scanner
that ends the block on `stripped.startswith("}")` exits at the first inner
group and silently covers only part of the file — the remaining literals still
report, the count merely drops, and that reads as "the fix partially worked".
Count braces:

```python
if re.match(r"^vars!\s*\{", stripped):
    inside, depth = True, stripped.count("{") - stripped.count("}")
    marked.add(i); continue
if inside:
    marked.add(i)
    depth += stripped.count("{") - stripped.count("}")
    if depth <= 0:
        inside = False
```

Then assert the scope you intended, not merely a smaller number: the token file
should reach **0**, and a real string literal in a plain `fn` in the same file
must still be caught. "It went down" is the shape of both a correct fix and an
exemption that stopped halfway.

**Prove the construct is genuinely unfixable before exempting it.** Write the
one-line the rule demands and let the compiler rule on it: `extern ABI { }`
against `const ABI: &str` is a syntax error, which settles that there is no
expression position to hoist to. An exemption justified by "the author should
have written it differently" is a suppression, not an exemption.

#### 2.1.1 Exempt the narrowest span, never the whole line

Anchoring on the *construct* is necessary but not sufficient. The remaining
half of the bug is **granularity**: a scanner that recognises the construct and
then skips the entire line exempts every other literal on it, so one keyword
launders an unbounded amount of unrelated data.

```rust
// the rule is right; the granularity is wrong — 0 reported, 6 real violations hidden
extern "C" fn f() -> &'static str { "/Users/sqs/.ssh/id_ed25519" }
```

Capture the exempt token as a **named group** and suppress that span only, so
every other literal on the line is still reported. A line that *merely* contains
the keyword is now a test case rather than an assumption — build it, and confirm
the unwanted literal still reports.

**Resuming the scan is not the same as skipping the span.** Regexes that pair
quotes (`"[^"]*"` over a whole line) will, on a rescan from offset 0, begin at
the exempt token's **closing** quote, swallow all the code between the two
literals into one bogus span, report garbage like `'" fn f() -> … { "'`, and can
miss a genuine literal sitting inside that swallowed run. Start the scan *after*
the exempt span instead:

```python
# WRONG — rescan from 0 pairs the ABI's closing quote with the next literal
for m in STRING_LITERAL.finditer(line): …

# RIGHT — resume past the exempt span
for m in STRING_LITERAL.finditer(line, abi_match.end("abi")): …
```

**When a fixture fails, ask whether the code or the expectation is wrong.**
`#[link_name = "…"]` sitting mid-line after `extern "C" {` looked like a
regression the span fix had introduced; running the *pre-patch* script on the
same line showed it reported that input too. The expectation was wrong, not the
fix. Check the counterfactual before editing working code (§6).

**Deliberately try to defeat your own exemption.** Write the adversarial file —
one keyword, one line, everything else a real violation — and assert the count
both with and without the exemption active. A non-zero difference is the number
of violations you were hiding. `#[rustfmt::skip]` (file- or item-level) is the
one-line way to keep a whole construct on one line, and it survives
`cargo fmt --check`, so a per-line scanner plus a CI format gate will not catch
it for you.

When you build the rules yourself, the parsing bugs to expect (each cost a
debug cycle):

- **Attribute scanning backwards** must be depth-aware. Scanning back for `[`
  stops on the *inner* `]` of `#[derive(A, B)]`.
- **Slices taken at `[` drop the `#`** → `startswith("#[")` is then always
  false, and the script silently reports zero violations on a repo full of
  them. A verifier that reports 0 on a repo you *know* has violations is
  itself the bug report.
- **A backward walk must skip the visibility keyword** (`pub`, `pub(crate)`)
  between the attribute run and the item, or it stops one token early.
- **Forward blank-line tracking must treat attribute lines as transparent.**
  An outer attribute (`#[cfg(...)]`, `#[derive(...)]`) belongs to the *next*
  declaration, so a scanner that resets its `blank_before` state on seeing
  one glues a cfg-gated item permanently to whatever precedes it — and the
  only layout that would satisfy the scanner (a blank line between the
  attribute and its item) is one `rustfmt --check` always rejects, making
  the file unfixable. Preserve the blank state across attribute lines;
  reset it only on real code lines. When a whitespace rule and the
  formatter demand incompatible layouts, the verifier is wrong — the
  formatter is the ground truth the repo must stay clean under.
- **Strip comments and string literals before matching, or prose and doc
  examples become violations.** A string in a comment is documentation, not
  program data — hoisting `/// (e.g. ":hover")` into a const table corrupts
  the doc. But the same granularity trap as §2.1.1 applies: a line-level
  comment regex (`^\s*//`) exempts the whole line, so `// TODO: move to
  const: "/Users/sqs/.ssh/id_ed25519"` launders a real secret. Exempt by
  **position**, not by line shape — locate where the comment starts and skip
  only from there:

  ```python
  pos = _comment_start(line)          # string-aware
  if pos == 0:
      continue                        # whole line is a comment
  scan_line = line[:pos] if pos else line   # trailing comment: keep the code
  ```

  `_comment_start` must track string and char literals, or a `//` *inside* a
  literal reads as an opener and `"https://host/path"` is never reported. A
  trailing comment exempts only the text after it, so a real string on that
  line still reports. Then attack it: a comment-shaped line with a live
  credential in it must still be caught for whatever comment forms you
  exempted.
- **Build the string/comment masker to Rust's literal grammar, not a first
  approximation — char literals are exactly one char (else lifetimes mis-pair),
  raw strings need a backreference, and masking must preserve newlines (else
  line filters and offset rewrites shift). Construction rules and measured
  failures: [references/scanner-construction.md](references/scanner-construction.md).
- **Judge a match's shape from the source AROUND the capture, not the capture
  alone.** Delimiters sit outside the group, so a scanner reading only the
  captured text sees a fragment and misclassifies it. `((a as usize) << 16) |
  ((b as usize) << 8)` read as `params` yields `((b as usize) << 8)` with no
  `|` in it; the same applies to `macro_rules!` patterns such as
  `move |$( $arg:ident $(: $ty:ty)? ),*|`, where `$(` marks a repetition that
  cannot carry a type annotation. Pass the line and the span alongside the
  group text.
- **A `|` is ambiguous in Rust.** Inside a closure parameter list it delimits
  parameters; in an expression it is bit-or. Disambiguate from the group's
  content (a real param list is comma-separated bindings and never contains
  `<<`, `>>`, or `as`) plus the surrounding source — never from the delimiter
  alone.
- Instrument the parse function with a traced copy when it returns an
  unexpected empty set; the returned-empty symptom has four different causes
  and guessing which one costs more than printing the offsets.
- An exemption that is a no-op and one that is over-broad look identical from
  the compliant side. Record the pre-patch baseline, and re-audit the
  compliant fixtures for real violations the new hole would swallow.

#### 2.1.2 Prove the fix removed only false positives: differential replay against the old script

"Reports fewer now" is not evidence — a verifier that reports nothing always
reports fewer. The proof is a **differential replay**: restore the pre-patch
script from version control, run both over the same real repos, and diff the
*findings sets*. The assertion that matters is what the fix **added**:

```bash
git -C <skill-repo> show HEAD:scripts/verify_x.py > "$S/old_verify.py"   # exact pre-patch bytes
# parse findings as (file, line, param) sets for old and new, then:
removed = old - new     # want: every one manually re-read in its source context
added   = new - old     # want: ZERO — any hit here is a regression you introduced
```

Report `added == 0` explicitly. Then hand-read the `removed` set in its real
source lines and confirm each was genuinely exempt — 43 lines inspected by eye
is cheap next to shipping a silent false negative.

**Real repos beat hand-written fixtures here, and you need both.** The fixtures
pin behaviour you anticipated; the replay finds the shapes you did not. A
replay over three repos is what surfaced `a == b || c == d` chains and `|_|`,
neither of which any fixture I wrote covered.

**A fixture suite for this must assert BOTH directions, per case:**

```
compliant → exit 0, n=0      (exempt shapes stay quiet)
violating → exit 1, n=N      (real violations still caught)
tricky    → exit 1, n=small  (every known false-positive shape: 0 hits)
trap      → exit 1, n=small  (a real violation sharing a line with an exempt)
```

Only the compliant side is ever written first, and that is precisely why a
"fix" that just suppresses more output passes while quietly letting violations
through. Assert exact counts on the violating fixtures — a count that drops
from 5 to 4 is the regression announcing itself.

**Expect to break your own fix, and let the suite catch it.** Two defects
shipped in the first two attempts here: a tuple-pattern guard ordered *after*
the paren heuristic (so `|(k, v)|` was wrongly exempted — a false negative),
and a helper that `return False` where the caller needed `continue` (so one
exemption never took effect). Neither was visible from the happy path; both
were caught by the violating-fixture count and the `added` set.

**In span-based chain detection, skip whitespace when reading the neighbouring
character.** The captured group sits *between* the delimiters, so for
`a | b | c` the "character after" is `' '`, not an operand — a naive
`line[end+1:end+2]` reads whitespace, concludes the chain ended, and reports a
bit-or expression as closure parameters. Step over whitespace **and** the
group's own closing delimiter. Also order the guards: binding-list shapes
(`(a, b)`, `_`, `..`) must be tested *before* the "looks like an expression"
heuristics, or their parentheses and commas read as a call.

**Generated code is scanned as text but compiled as someone else's code.**
Inside a `quote!`/`macro_rules!` body, a `let` binding is source text to the
scanner and real code to every downstream crate. Pinning a type the macro
cannot know is how `let _: Status = hook(...).await` broke a documented hook
that returns `()`. When the type is genuinely unknowable, drop the binding to
a bare statement — but say so in the report, because that is a semantic edit
wearing an annotation's clothes, and it is the line a reviewer will question.
The doctests exercising the macro are what caught it; run them, do not assume
`cargo check` on the macro crate alone is enough.

**When several agents can touch one worktree, verify diff provenance before
building on their output.** Check file mtimes against your own edit times and
`git diff --stat` for line counts you did not produce. A 272-line change in a
file you never opened means someone else is writing; confirm the delta is what
you expect (here: annotations plus rustfmt re-wrapping) before continuing, and
report the overlap rather than presenting the merged result as solely yours.

**Compiling is not the same as correct.** When the fix under a rule is
"add a type annotation", the placeholder form will build and the verifier
will accept it while the code stays exactly as hard to read as before —
the rule exists to stop the reader inferring a type, and a placeholder
delegates the same inference. Accepting the build as the finish line is
what ships the placeholder. Ask what the construct is *for*: a collector
that only exists to be filled and returned should be built in one step
(`From<[(K, V); N]>`), not declared and mutated.

**Check whether the path is source at all.** A filesystem-walking verifier
picks up scratch trees a maintainer never ships — a gitignored `/tmp/`
holding a few dozen generated crates produced findings in files no commit
can contain. `git ls-files <path>` returning nothing settles it. Filter
in the walker (one batched `git check-ignore --stdin` over all paths) so
the count is right on every run, and apply the filter to **every** script
carrying its own copy of the walker — fixing one leaves the rest
reporting the phantom directory. Name-based exclusions are the same hazard
in reverse: skipping by path component (`*/tmp/*`) fires on the
repository's own location, so a scratch fixture created under `/tmp` — or
any checkout whose path merely contains that component — scans zero files
and reports clean. Git-ignore status is a property of the file; a
path-component match is a property of where the repo happens to sit.
Treat an unexpected exit code, a
non-work-tree root, or a missing `git` as "return the full list", never
as "zero violations": a guard that fails open reports compliance on
content it never examined.

**Know when the job is too big for one change.** A cross-repo
remediation spanning four checks and a hundred crates is not a single
task. Measure per check and per crate first, then take the mechanical
low-risk class first, and state the batch boundaries and the remainder up
front so the user can redirect the granularity before the work starts
rather than after the first oversized diff. A PR that large gets a
diffstat review, which is not review.

#### 2.1.3 Fixtures are too polite to be a test — run every new verifier on real repos before believing it

A hand-written fixture is authored by the same mind that just wrote the
verifier, so it encodes the verifier's assumptions back to it. Two defects
survive a green fixture suite every time:

- **A brace- or depth-matching helper that assumes balanced input.** It returns
  a sentinel equal to `len(lines)` for an unclosed block, and the caller's
  `range(idx, end + 1)` then indexes past the end. Every fixture has balanced
  braces; real repos have macro fragments and truncated files. Clamp the
  sentinel, then run the script over real repositories.
- **An input the classification reads that the fixture never supplies.** A
  verifier that consults a manifest, a directory listing, or a name resolving
  elsewhere behaves differently on a real workspace than on a fixture tree,
  and the difference is a wrong answer rather than a crash.

The rule that generalises: **a verifier that has never run on a real codebase
is not a verifier.** After the fixtures pass, run each new script against at
least one real repo and read the findings, not just the exit code.

```bash
for v in verify_<rule_a> verify_<rule_b>; do
  printf '%-34s ' "$v"
  python3 <skill>/scripts/"$v".py <real-repo> 2>&1 | tail -1
done
```

**A finding count in the hundreds is a bug report, not a result.** A rule with
real teeth on a codebase you believe is clean yields a double-digit number; six
hundred and eighty-eight findings is one wrong assumption multiplied across
every file. Bisect by opening three findings in their source context before
touching a threshold. The cause is almost never the rule's core comparison — it
is an input the check reads that the fixtures never provided, or a swallowed
error that silently neutralised it.

**A blanket `except OSError` around a file the rule classifies on converts one
bug into a wrong verdict for the whole corpus.** Assigning a *directory* to a
variable later `.read_text()` raises `IsADirectoryError`, which is an `OSError`,
which the handler catches — the read returns empty, the input looks like it
declares nothing, and every item in every crate classifies as the same wrong
thing. The verifier neither crashes nor reports zero; it produces a confident
wrong answer at scale. Two habits close it: print the error to stderr and return
the neutral value instead of swallowing, and assert the parsed input in one
call before trusting the output (`print(sorted(dep_roots))` — empty on a real
repo is the bug, stated plainly).

**Reconcile the rule's prose against the repo's own template before
implementing it.** A sentence like "the three stages carry no blank lines
between them" reads as banning all blank lines, and implementing it literally
flags the canonical example the template file ships. Read the template and two
real instances first: they are the ground truth the prose is a description of.
Where they disagree the template wins, and the sentence is what needs fixing.

### 2.3 A lint inside a macro DSL may be a real design defect, not a false positive

When a warning fires on an invocation of a macro you own — `html!`, a template
DSL, a builder — the reflex is "macro DSL, lint doesn't understand, suppress
it". That reflex is sometimes wrong, and the tell is that the *workaround*
becomes syntax the framework's design does not call for. A user who says "only
dynamic values should need braces here" is telling you the macro is the defect,
not the call sites.

**Test the naive fix before calling anything a false positive.** Make a backup,
apply the change the linter suggests, build, restore. Three outcomes, each
meaning something different:

| Result | Reading |
|---|---|
| still warns | the lint is wrong about the code — genuine false positive |
| warning gone, builds | the lint was right; the old form was the debt |
| warning gone, build breaks | the braces carry load-bearing meaning at parse level (§2.3.1) |

Only the third licenses "false positive", and even then it licenses *reporting*
it, not suppressing it. The braces may be required by the grammar while the
grammar itself is more restrictive than the design intends — and then the fix is
in the parser.

**Relieving the symptom at the call sites is the wrong layer.** Stripping the
offending wrapper inside the macro so the warning disappears looks finished and
leaves the design untouched: callers are still forced into the ugly form, and
the tree still teaches the wrong idiom. Ask what the construct is *for*; if the
form only exists to work around a parser limitation, fix the parser and then
convert the call sites to the form the design intends.

### 2.3.1 Fixing the parser: read the callee's contract before reusing a helper

A DSL parser usually has one helper per construct shape, and each helper's
delimiter assumption is **local to that construct**. The classic error is
reusing a helper whose contract you did not read: a helper that collects tokens
"until a top-level brace" is correct where a *body* brace delimits the
construct (`if cond { }`, `for x in .. { }`, `match x { }`), and wrong in an
attribute list, where the delimiter is the next `key:` or the enclosing block's
close — so it runs straight past a call's closing paren and swallows the
following children. That broke ~115 call sites at once, each failing with an
error pointing at an unrelated-looking line.

Before reusing a parser helper: read every existing caller, name the token
that ends the construct in *each* of them, and confirm the same token ends it
where you are adding the new use. If it does not, the helper needs a variant,
not a new call site.

**Grep for an existing helper before writing a new one.** The unwrap you are
about to add usually already exists for an adjacent construct; a near-identical
second copy is how a macro crate accumulates two subtly-diverging versions of
the same logic.

**A green build proves little for a parser change.** If the risky input form
occurs nowhere in the repo — no caller passes a struct literal, no caller uses
the disambiguated shape — then that path is untested by construction and
compiles green whether or not you broke it. Before trusting the build, answer:
*which input exercises the path I changed?* If nothing does, add one. Cover
three cases: the newly supported form, the form that must still work, and a
regression guard for the path that has no existing caller. A dedicated test
module for the DSL's edge cases is the cheapest place, since it costs no
downstream churn.

**Prove the fix in both directions and at every layer.** Warnings gone is not
the claim; the claim is *warnings gone AND the risky form still parses*. So:
`cargo check` for the whole workspace, plus the macro crate's own test suite,
plus the new cases. A change to a shared parser is blast-radius-wide — check
`grep -rn '<construct>'` for caller counts before you start, so a 115-site
breakage is a number you expected rather than a surprise.

Worked example, with the real parser diff and the test matrix: §2.3.1
`references/macro-dsl-lint-triage.md`.

### 2.2 When a subagent contradicts your prescribed fix, verify the child, do not re-prescribe

You will hand a subagent a concrete remediation shape — `X/{mod.rs, X.rs}`,
`git mv` this to there, strip the comments — and it will sometimes come back
having used a different one, with a reason. That is the most valuable result
the delegation can produce, and the reflex to suppress it is the failure.

Re-prescribing your shape because the diff differs from your instruction
reinstates exactly the defect the child just caught. Concretely: if a rule
prescribes moving a file into a directory named after it, a child that
instead uses the repo's existing sibling naming (`fn.rs`) is reporting that
your prescribed shape trips a linter — confirm that yourself before acting.

Verify the child the same way you verify any result, in two parts:

1. **Reproduce the child's claim independently.** It says the prescribed shape
   emits a warning — build both shapes in a scratch crate and count, or read
   the sibling modules it points at and confirm they already use its shape.
2. **Check the child's output against the repo's actual convention**, not
   against your instruction. Diff the new file against a pre-existing sibling
   that has the same role:

   ```bash
   cat <new-dir>/mod.rs; echo '--- vs a sibling:'; cat <sibling-dir>/mod.rs
   ```

Two things to confirm by hand in whatever the child rewrote:

- **The parent declaration still resolves.** If the child moved `inline.rs` to
  `inline/fn.rs`, the parent's `mod inline;` now points at the new
  `mod.rs` — that has to keep working, which you prove by building, not by
  reading the tree.
- **Comment-stripping did not eat test data.** A rule banning comments in
  `tests/` tempts a child into deleting every `//`, including one inside a
  raw string that is the *input* being asserted. Diff the stripped file
  against the original and confirm each deletion was a comment; a surviving
  `//` inside a literal is the shape to look for.

Report the deviation as the child's finding and attribute it, rather than
quietly letting the shape you specified be overruled by a change you did not
mention.

**A refactor that moves a file invalidates every skill that hardcodes its
path — sweep for it before declaring the refactor done.** A skill whose
verification command is `grep -c '<pattern>' src/foo.rs` does not degrade when
`foo.rs` is split across `src/*/foo.rs`; it **errors**, and the next session
reads a broken check as a broken rule. Check the moved paths three ways:

```bash
grep -rn '<old/path>' ~/.agents/skills/ ~/.hermes/skills/    # prose + commands
# then run every referenced command and every referenced path, for real
```

The reference audit needs a **path-shaped filter**, not a bare backtick match:
CSS class names, `padding-shell-top/bottom` and other `a/b` tokens in prose
resolve as paths and bury the real breakage. Match only tokens containing a
`/` and a file extension, then confirm every survivor exists (expanding globs
with `glob.glob`). Expect a handful of false positives and discard them by
reading, not by loosening the filter.

Then fix in the source of truth, not by appending a correction: rewrite the
path to its new form, restate the "single source of truth" claim so it
describes the new shape, and re-derive every **count** the skill asserts by
running the new command. Counts drift silently — after splitting one registry
file across seven, a class tally went 363 → 496 and the skill's own number was
two off my first recount because two entries take parameters and a strict
regex skipped them. When a child's count and yours disagree, **check whether
your regex is stricter than theirs** before assuming either is wrong.

Write the replacement command so it survives the shell it will be pasted into:
`grep -hc … | paste -sd+ | bc` is GNU-only and fails under BSD `paste` with a
usage error, which is indistinguishable from a rule with no matches. Prefer
`cat dir/*/fn.rs | grep -c …`, then run it to confirm the number it claims.

**Delegate the skill sweep with the code task, or do it yourself before the
child's report lands.** A child told to check a file's contents will notice its
own breakage and correctly report it as out of scope — that is good behaviour,
not a miss, and the fix still needs doing. Scope the follow-up in the same
turn you are already waiting on.

### 2.4 When you delegate the repair of a broken verdict, a FAIL is not a licence to go green

The §2 merge protocol above is deliberately conservative: prefer the skip
direction, because a false positive burns the user's trust. Delegating a
verdict-repair round applies that same bias in a direction where it is
**dangerous, not merely wasteful**.

A child told "these checks are failing, fix the checks" is being handed an
ambiguous goal, and the cheapest way to satisfy it is to relabel the failing
checks. Watch for the shape of that resolution: a FAIL that a *human* would
call a real defect reappearing as SKIP, PASS, or "not a target key", with a
note explaining why the check was wrong rather than what the app does. The
suite number improves, and a real defect is now invisible to every future
run.

**Distinguish a broken verdict from a real defect with the app's own
reference material, and let the reference decide which.**

- If a constant is declared but never read (`git grep -c '<CONST>' -- src/`
  returning exactly 1 hit), the wiring is absent, whatever the check says.
- If the reference product implements the behaviour, the app omitting it is a
  defect — keep the FAIL and report that the app side needs the fix. A
  deliberate omission is only *correct* when the reference omits it too, and
  "this project decided to skip it" is not a reference.
- A check that no app state can pass is a broken verdict. That is a
  structurally different thing from an app that will not do what you want,
  and conflating them is how a real gap gets filed as a harness bug.

**Say in the brief which of the two you believe it is, and require the
child to report the per-item adjudication rather than the total.** A child
that returns "12 pass, 2 skip" has satisfied the goal you gave it. A child
that returns "these 6 were real defects, these 9 were broken verdicts, and
this one needs an app-side change" has done the work — and that is the
report you can relay. The total alone cannot distinguish a repaired suite
from a silenced one, so pair it with the per-item list, the counts per class,
and the delta in skips.

**And when the child reports a fix, check the direction the suite moved.**
FAIL→SKIP on a check whose subject the app plainly implements, without a
change to the app, is the signature to reject. Applying this in reverse —
fixing the check so a correct app passes — is legitimate, and the diff shows
it: the app is untouched and the check now measures the real thing.

**The whole loop stalls on structurally unsatisfiable verdicts.** When a
suite can never go green, every round of the fix→verify cycle re-triages the
same red by hand and no amount of app-side fixing converges. Repair the
verdicts first: that is the only step that makes the loop terminate, and
dispatching an app fix against a broken verdict is how a correct build gets
rewritten to satisfy a check that was measuring the wrong thing.

For suites that drive a real browser — CDP, injected events, an in-page debug
state object, pixel diffs — every one of these measurement-channel faults
produces a number that looks measured and is wrong, and the repair round then
lands on correct code. **Validate the channel carries the signal before reading
any verdict from it**: prove the publish cadence, take one atomic snapshot
rather than several field reads, drive the input path the app actually listens
on, and check the test point is on the route. Where a judgement is perceptual,
a differential criterion or an explicit `SKIP` beats a threshold that passes
because the background is darker on one side. Full class in
`references/browser-automation-harness-integrity.md`.

### 2.5 A stopped child's measurements are not measurements, and three self-inflicted breakages mean the scope is wrong

Two lifecycle traps sit on top of §2.4. Both cost a full re-verification.

**Output written by a run still in progress is provisional, and stopping the
child destroys it.** A verifier that writes one artefact per worker overwrites
its previous output as it goes, so a child killed mid-round leaves a
*partial* directory that looks authoritative: fewer items, no harness-failure
rows, a better-looking pass rate. Back up before each run
(`cp -r results "results_prev_$(date +%H%M%S)"`), and treat a number read
while a run is in flight as **unquotable** — including in your own status
message, where it will be read back later as fact. The tell is a falling item
count with no failing row explaining it. The code the child changed usually
survives when its measurements do not, so on a stop, report the *code* state,
mark the numbers as needing a clean re-run, and say plainly that the earlier
figure no longer holds.

**Three consecutive self-inflicted breakages on one artefact is a
decomposition error, not a bug to steer.** The shapes recur — `await` outside
an async function, `UnboundLocalError` on a name assigned in only one branch,
a run that never reaches its first assertion — and each looks individually
steerable while each steer buys exactly one round trip. When the third
arrives, stop fixing symptoms: cut the task to the single highest-value item,
dispatch a fresh child for it, and re-run the remainder afterwards. A child
flailing in the same file for an hour is not converging, and your cost is the
wall clock, not the bugs.

**A traceback dominated by stdlib import failures is a path-shadowing bug, not
a failure of the thing under test.** Python puts the script's own directory at
`sys.path[0]`, so one stray `bisect.py` next to a probe shadows the stdlib
module and the crash surfaces somewhere unrelated —
`ImportError: cannot import name 'bisect' from 'bisect'` reached through
`email.utils` → `random`, on a task that has nothing to do with any of them.
Before believing such a report, list the directory and look for names matching
stdlib modules. The fix is to move your script into its own subdirectory (so
`sys.path[0]` is clean) or rename the offending files — **rename, never
delete**: the colliding file is usually another agent's, and removing it
destroys work that has nothing to do with yours. Tell the child which it is;
left alone, the natural move is to edit the code under test to dodge an error
it never caused.

## 3. A PR can merge under you — check PR state in the same command as the push

If you push a follow-up commit to a branch whose PR was squash-merged while
you worked, **the push succeeds and the work never ships**. Nothing tracks the
branch any more; the default branch never receives your commit.

Detection, in one shot right after the push:

```bash
git push origin <branch> 2>&1 | tail -2
gh pr view <N> --repo <o>/<r> --json state,mergedAt --jq '"state=\(.state) mergedAt=\(.mergedAt // "-")"'
git log --oneline origin/<default> | grep -c "<commit subject>" || true
```

A `grep -c` of 0 on the default branch while the push reported success is the
tell.

Recovery — never force-push to a merged branch, its tip was rewritten:

```bash
git fetch origin
git checkout -b <new-branch> origin/<default>
git cherry-pick <your-commit>     # resolve if the base moved under you
git push -u origin <new-branch>
gh pr create --base <default> --head <new-branch> ...
```

**Rule**: verify PR state *in the same command sequence as the push*, never in
a step you ran minutes earlier. A long task with subagent round-trips is
exactly how a merge slips in between.

Corollary for verification: "87 tests pass" on a branch that is not the base
proves nothing about the shipped result. After a cherry-pick onto a moved
base, re-run the gate **on the new branch** before claiming parity.

**Fetch and fast-forward the local default branch before cherry-picking
onto it.** A stale local `master` is missing commits the remote already
has, and a cherry-pick onto it conflicts against content your patch never
touched — the conflict reads as your change being incompatible when the
real defect is the stale base. `git fetch origin && git merge --ff-only`
first; the same patch then applies clean. The cherry-pick and the original
commit now diverge by hash, and that is fine: when the feature branch
holding the original later merges, git reconciles the identical patch on
its own. Do not "fix" the duplication by rewriting either branch.

## 4. Clean-tree discipline when staging narrow paths

`git add <dir>/` sweeps untracked build output into the commit. A docs crate
that emits into `dist/` will land a generated WASM blob in a source commit.

- Stage **file paths**, not directories, when the tree has build output.
- After staging, read the staged list before committing:
  `git diff --cached --name-only` — the fix is `git rm --cached <path>` plus
  `git commit --amend --no-edit` if it already landed.

### 4.1 Same-file overlap needs hunk-level staging, not file-level

The common case for a skills repo: an earlier session left **uncommitted**
edits inside the very file you are changing. `git add <file>` commits their
work under your message, and `git add -p` is unusable when your own change is
one hunk of a 100-line table row. Build the patch yourself:

```bash
git diff -U3 -- <file>                       # split on '^@@ '
# keep only hunks carrying a marker unique to YOUR change
# (a new rule name, a new function name, your own § section heading)
git apply --cached --check <patch> && git apply --cached <patch>
```

**Recompute every `@@ -a,b +c,d @@` header from the lines you kept.** Dropping
added lines while keeping the original counts yields
`error: corrupt patch at <file>:<line>` — which reads like a damaged file
rather than a stale line count, and costs a debug cycle to diagnose. Count
`old = lines not starting with '+'`, `new = lines not starting with '-'`.

Verify before committing: `git diff --cached --stat` plus the staged diff
itself, and tell the user which foreign hunks you deliberately left in the
working tree. Silently committing or silently dropping either one is the
failure.

### 4.2 A layout rule needs a per-file adapter to work in a staged-file gate

A staged-file gate works by diffing one file's violation count against itself
at HEAD. A rule whose signal lives in the **directory layout** rather than in
any file's bytes has no per-file finding to diff, so a naive registration reads
as a permanent silent zero: before = 0, after = 0, delta = 0, and the commit
sails through while the gate prints `0 new violations — commit allowed` —
worse than no check, because it looks like it verified something.

**Do not conclude from this that the rule belongs only in the whole-repo
audit.** That conclusion is what leaves the hook decorative while the spec
claims the rule is enforced. The gap is a missing adapter, not an
architectural limit: give the verifier an `audit_one(path)` that maps a file
path onto the enclosing entity the rule actually talks about, and the gate
works.

```python
def audit_one(path: Path) -> list[str]:
    """Per-file entry point so a staged-file gate can call this verifier."""
    if path.suffix != ".rs" or not path.is_file():
        return []
    findings = audit_one_dir(path.parent)      # the rule's real subject
    if not findings:
        return []
    # narrow: only report when THIS file is one the finding names
    return findings if path.name in names_in(findings) else []
```

Three things make the adapter correct rather than a new false-positive source:

- **Attribute only to the file the finding names.** Returning a directory's
  finding for every file inside it points the blame at clean files; one such
  false positive is enough to make a user disable the hook permanently.
- **Never return `[]` silently for a missing entry point.** A gate that does
  `getattr(module, "audit_one", None); if none: return []` must also log or
  count, or a verifier whose entry point went missing is indistinguishable
  from a clean repo.
- **State the residual gap in the spec.** A commit that stages a *new
  directory* while the pre-existing offending file is unstaged gives the gate
  no path to attribute the finding to, so it cannot catch that shape. Say
  which layer is authoritative for which case instead of implying full
  coverage.

Layout rules that need this: "a code file must not sit beside a
sub-directory", "every module entry declares its children", "imports are
centralized in `lib.rs`".

**Registration is a separate step from authorship, and both must happen.** The
failure mode to watch for is writing the rule, wiring it into the whole-repo
audit, and treating that as done — while the gate that the user actually runs
on every commit never invokes it. When a rule lands, grep every caller (the
gate's verifier table, the audit's check list, CI workflow command lines) and
confirm the rule is in each one that can enforce it.

**A rule enforced in the audit but not in the gate is not a rule at commit
time, and the user finds it before you do — usually by asking why one
violating file passed review.** Three shapes of the same gap appeared at once,
and the tell in each is that the rule is *specified and audited* while being
*unreachable*:

| Shape | Why the gate cannot run it | Structural fix |
|---|---|---|
| rule exists only as an inline shell template over `git diff origin/master HEAD` | no per-file entry point for the gate to call | extract a `verify_*.py`, register it |
| verifier has `audit_one()` but was never added to the gate's table | nothing invokes it | register, then prove it blocks |
| `audit_one()` returns `[]` for the one case the rule exists to catch | it runs, and reports nothing | implement the rejection branch |

That last row is the dangerous one, because the check *looks* wired up. A
filename rule whose per-file entry point returned `[]` for any basename
outside its keyword set reported a clean repo while a `cli/src/build/inline.rs`
sat in the tree. The early-exit reads as a convenience guard ("not a keyword
file, nothing to check") and it swallows the single case worth reporting.

**When you register a verifier you have never run, expect it to surface
pre-existing violations you did not author — and read the rule before fixing
them.** A purity check newly added to the gate flagged 8 findings in every
`tests/mod.rs` in the repo, and all 8 were the *required* form: one rule
mandates `use crate_name::*;` in a test module while a second rule forbids it
there. Two rules in direct contradiction, one of them unenforced the whole time
so nobody had noticed.

Settle a spec contradiction from the docs before touching a file, and when they
genuinely conflict, the exemption belongs in the *enforcer*'s scope filter, not
in the spec. Then prove both directions, or a false positive has become a false
negative:

```bash
# the mandated shape must now be silent
python3 scripts/verify_x.py <real-repo>/tests/mod.rs
# the shape the rule is actually for must still report
python3 scripts/verify_x.py <fixture-src-fn.rs-with-non-local-use>
```

**Report a rule that was unenforced as a finding in its own right.** The
user's question is "why did nothing catch this", and the honest answer names the
missing registration as the root cause rather than the file as the culprit.
Burying it inside a list of the violations you fixed leaves the impression that
the file was the problem.

### 4.2.1 A gate that baselines with `git show HEAD:<path>` loses every violation in a renamed file

A staged-file gate decides "new or not" by diffing one file's findings against
that same file **at HEAD**. That lookup is rename-blind: a rename means
`HEAD:<newpath>` does not exist, the baseline comes back empty, `before = []`,
and **every pre-existing violation in the file is reported as newly
introduced**. A pure `git mv` with zero content change can be blocked with a
four-digit count.

Diagnose it in three commands before touching the gate — this is a gate bug,
not a code bug, and "fixing" the reported lines buries the real defect under
someone else's legacy debt:

```bash
git diff --cached --name-status -M | grep '^R'      # which paths moved
git show HEAD:"<newpath>" | wc -l                   # 0  -> baseline lost
git show HEAD:"<oldpath>" | wc -l                   # the content that is actually there
python3 <skill>/scripts/verify_<rule>.py <oldpath-extracted>   # do the violations pre-exist?
```

The last command is the one that settles it. If the old path at HEAD reports
the same violations, they are legacy and the gate is miscounting.

Fix the baseline lookup, not the report: on `git show HEAD:<path>` failure,
resolve the staged rename source for that path and read the baseline from
there. A rename is a move, not a creation, and the gate's job is to attribute
findings to the change, not to the path.

**Verify the fix in both directions or you have shipped a free pass.** A pure
100% rename must now report 0, and an injected real violation into the renamed
file must still be caught:

```bash
printf '\nuse std::cell::Cell as MyAlias;\n' >> <renamed file>
git add <renamed file> && python3 <skill>/scripts/staged_file_gate.py . --staged
# expect FAIL; then restore the file and re-run to confirm it passes again
```

Reporting fewer violations is not evidence — a gate that reports nothing always
reports fewer (§2.1.2). The injected-violation run is the only thing that
distinguishes "fixed the baseline" from "disabled the check".

### 4.2.2 A SPLIT refactor loses the baseline for every target but the one git paired

The rename fix above assumes one source, one target. A structural refactor
rarely does that: one file split into N lands as `D old` plus N additions, and
git pairs **at most one** of them as a rename. The other N-1 get an empty
baseline, so all their inherited debt reports as newly introduced. The partial-
modification case is worse and quieter: `D old` + `M existing` gives the
modified file a baseline that is only a *fragment* of what it now holds, and
the fragment compares cleanly while the moved-in remainder looks new.

Recognise it by the arithmetic: sum the per-target counts and check they equal
the deleted source's count. Equality proves net-new is zero, and it is a
two-minute check that settles a four-digit report.

```bash
git diff --cached --name-status -M -- <area>       # A? D? R? — look for the asymmetry
git show HEAD:<deleted source> | grep -c '<rule pattern>'   # debt that was there
for f in <new targets>; do grep -c '<rule pattern>' "$f"; done | paste -sd+ | bc
```

Do **not** treat "the report is large so the work must be bad" as the
conclusion. When a structural change yields a suspiciously large
"new violations" count, **the baseline is the first suspect**, and the
adjudication is a per-rule **repo-level differential**, not the gate:

```bash
git archive HEAD | tar -x -C "$S/head"; rsync -a --exclude target ./ "$S/cur/"
for v in verify_<rule_a> verify_<rule_b>; do
  python3 "$SKILL/scripts/$v.py" "$S/head" | tail -1
  python3 "$SKILL/scripts/$v.py" "$S/cur"  | tail -1
done
```

Repo-wide totals going **down** while the gate reports thousands is the proof
the gate is miscounting. Compare per area as well as per rule, so a single
area's regression is not hidden by improvement elsewhere.

The fix is a **union baseline**: the file's own HEAD content *plus* any
matching split source, so the gate diffs against the full pre-commit content
set. Two details decide whether it is safe or a new source of false negatives:

- **The candidate pool must include the rename source, not only deletions.**
  Filtering on `--diff-filter=D` misses the exact case above, because the source
  is an `R`'s old path. Parse both `D<TAB>path` and `R0xx<TAB>old<TAB>new`, or
  the fallback silently never fires on the case it was written for.
- **Require real content overlap, and accept a miss rather than a mismatch.**
  Score candidates by Jaccard overlap of significant lines against a threshold
  (~0.30), and only accept directories that nest with the target — a split goes
  into a *new* sub-directory, so the source is usually the target's **parent**,
  not its sibling. If nothing clears the bar, return no baseline: over-reporting
  is recoverable, and a wrong pairing silently hides real violations.

Verify the tightened gate in both directions before trusting it — a
conservative filter that never matches restores the original four-digit report,
and one that matches too eagerly turns the gate into a free pass. Assert the
refactor now reports 0, then inject a real violation into a split target and
confirm it still reports (§4.2.1).

**Two children independently computing the false-positive arithmetic is a
signal, not noise.** When both report the gate is wrong and neither can fix it,
they are describing a gate bug — the delegation failed to be given the
authority, so take the fix yourself rather than re-dispatching.

### 4.2.3 Before deleting or moving a file a refactor reorganized, prove it is dead

A directory restructure leaves the old flat files in place, and the question is
never "should these move" but "is anything still here". Moving them propagates
dead code and stale values; deleting them may break callers. Settle it by
measurement, not by reading the file's name.

**Compute the set of declarations that exist ONLY in the files you plan to
touch.** Anything also defined in a sibling is a duplicate; anything unique is a
candidate for real removal — and each candidate needs its own reference check.

```python
import re, os
root = "src/mod"; subs = [d for d in os.listdir(root) if os.path.isdir(f"{root}/{d}")]
def decls(t):
    return {m.group(2) for m in re.finditer(
        r'^(?:pub(?:\(crate\))?\s+)?(struct|enum|trait|const|fn|impl)\s+([A-Za-z_]\w*)', t, re.M)}
in_subs = set()
for s in subs:
    for f in os.listdir(f"{root}/{s}"):
        if f.endswith(".rs"): in_subs |= decls(open(f"{root}/{s}/{f}").read())
for f in ["const.rs", "impl.rs", "struct.rs"]:            # the flat files
    unique = decls(open(f"{root}/{f}").read()) - in_subs
    print(f, "ONLY-HERE:", sorted(unique))
```

**Then classify each survivor, because "only here" is not the same as "unused":**

| Survivor shape | Verdict |
|---|---|
| A type/method the replacement has under a **different name** | dead — confirm by finding the replacement, and its doc comment often says so ("replaces the historical …") |
| A constant superseded by a typed enum | dead — **and check the old value against the upstream spec**; a stale numeric constant is a live bug, not just clutter |
| A helper referenced only by files in the same dead island | dead |
| Anything referenced from outside the island | **not dead** — it is a live dependency, and removing it means migrating those callers first |

A self-contained dead island — every unique item referenced only by its peers —
is safe to delete as a unit. The moment one item has an external caller, the
deletion stops being a cleanup and becomes a migration with a named
old→new mapping for each call site. **Write that mapping down before starting**;
it is the deliverable, and it is also what tells you whether the work is one
commit or a sequence.

The stale-constant case is the one worth flagging to the user explicitly: a
numeric constant that disagrees with the spec it encodes renders correct-looking
code that misconfigures the API at runtime, and no compiler or lint notices.

**A child told "move or delete this" will move it.** Decide dead-versus-live
yourself and put the verdict plus the per-item reference check in the brief, or
the dead code becomes a new sub-directory that a §1.3d-style rule then forbids
in the next pass.

A layout rule has a structural fix — move `const.rs` to `const/const.rs` and
add `const/mod.rs` — so one offending directory is **one** finding regardless
of how many files sit in it. Reporting per file inflates the count, implies N
separate edits, and makes a five-directory fix look like a twenty-file sweep.
Name every offending file and every sibling sub-directory in the single
message, so the finding is still actionable without inflating the total.

### 4.4 A shared worktree makes every worktree-wide git command a blast radius

When a task runs alongside another agent in the same checkout, the risky
commands are not the ones you aimed — they are the ones whose *intent* sounds
harmless. "Sync my local branch to the merged default branch" is `git reset
--hard origin/<default>` in muscle memory, and it destroys every uncommitted
file in the tree, including three files you never opened and were not asked to
touch. Same for `git checkout .`, `git restore .`, and `git clean -fd`.

**Rule: to move a local branch up to a merged default branch, use `git merge
--ff-only origin/<default>` (or `git pull --ff-only`).** It moves HEAD and
leaves the working tree untouched. Reserve `reset --hard` for a tree you
created yourself and have confirmed nobody else is using.

Cheap tells that a tree is shared, all worth one command before a destructive
git call: `git status --short` listing modified files you did not edit; a
backgrounded `cargo` / `gh` process against this repo; `.rs` mtimes advancing
while you work; a violation count or file list shrinking without you editing
anything. The last one is the strongest — a count that drops on its own means
another writer, not a fix.

**You can share a tree with yourself: a background verifier is a slow reader,
and any fixer writing while it reads manufactures transient violations.** A
repo-wide gate over ~270 files takes minutes; run a tree-writing fixer
foreground in the same window and the gate reads some files pre-fix, some
mid-write, and reports findings (e.g. an import-order +2) that no stable state
ever contained. The failures attribute to real paths and look exactly like a
regression the fixer introduced. Discipline: launch tree-wide
gate/audit/clippy runs only on a quiescent tree (no live writers, including
your own queued fixer commands), and when a background run does overlap a
write, re-run the named file alone after writers stop before believing the
finding — a transient never reproduces. The same applies in reverse: a
background clippy that errors (E0593) while you are mid-edit on the file it
compiles is provisional until re-run clean.

**Recovery is usually possible; look before reporting the loss.** `reset
--hard` moves HEAD but does not erase objects, and the discarded content was
usually staged, stashed, or committed at some point:

```bash
git reflog -8 | cat                    # what HEAD used to be
git stash list | cat                   # a popped stash is still a commit
git fsck --lost-found 2>/dev/null      # dangling blobs from the overwrite
git checkout <stash-or-commit-sha> -- <path/to/file>   # restore per path
git restore --staged <path>            # back to unstaged, as originally found
```

A stash created and popped earlier stays reachable by its commit sha, so
`git checkout <sha> -- <paths>` brings back the exact pre-reset content of
those files, and `git restore --staged` puts them in the state you found them
in. Verify the restore by content, not by exit code (`grep -c <marker> <file>`),
and tell the user plainly what was lost, what you reconstructed, and that the
reconstruction is yours rather than the other party's original tree.

### 4.4.1 `git stash -u` sweeps untracked paths that the tooling may depend on

Stashing with `-u` to reach a pristine HEAD (§2) also moves **untracked**
paths. In a repo where tooling is wired up by convention rather than
installed, an untracked directory can be load-bearing — a hooks directory
whose entries are symlinks into the tracked tree is exactly that shape, and
removing it does not fail loudly, it leaves a dangling symlink and a hook
that silently stops running.

The trap is ordering: you verify the gate, then stash for some unrelated
reason, then notice the gate went quiet and start debugging the gate.

Before stashing, enumerate what is untracked but *referenced*:

```bash
git status --porcelain --untracked-files=all | grep '^??'
# then: does anything named here appear in a config or a hook path?
git config --get core.hooksPath
realpath "$(git config --get core.hooksPath)/pre-commit"   # dangling?
```

Recover from the stash's untracked parent rather than re-creating the
files, so the bytes and any symlink targets come back exactly:

```bash
git checkout 'stash@{0}^3' -- hooks/     # ^3 holds the untracked snapshot
realpath hooks/pre-commit                # confirm it resolves again
```

Re-run the gate's negative case afterwards. A restored-looking file is not a
restored gate.

### 4.6 A rename that builds in the working tree can still ship broken — commit the declaration with the move

A module rename is two edits: the **move** (`git mv src/const/ src/protocol/`)
and the **declaration** in the parent's `lib.rs` / `mod.rs`. They land in
different files, and the index can hold one without the other — `MM` in
`git status` is the tell. Verified in the working tree, then the declaration
edited again afterwards, produces a commit that renames the directory and
leaves `mod r#old_name;` behind:

```
error[E0583]: file not found for module `old_name`
error[E0425]: cannot find value `SOME_CONST` in this scope
```

The failure surfaces only on the *next* build of the committed tree, never in
the one that approved the change. Before committing a rename, build what you
are about to commit, not what is in front of you:

```bash
git add -A                                  # index == working tree, no MM rows
git stash push -q -u                        # park it
git checkout -q HEAD -- .                   # reproduce the COMMITTED state
cargo build -p <affected-crate>             # does the commit stand on its own?
git stash pop -q
```

`git status --short` showing `MM` or ` M` on a file the rename depends on is
sufficient reason to run the check. A commit that does not build is worse than
an uncommitted change: the fixup costs a push and a review cycle, and the
`E0583` lands on whoever pulls next.

**A directory rename also decides the module's warning profile.** `X/{mod.rs,
X.rs}` where the leaf `mod.rs` declares `mod r#X;` names a module identical to
its containing directory, which clippy's `module_inception` warns on by default
— a warning the original flat layout did not have. Naming the new directory
for what it holds (`protocol/`, `signature/`, `host/`) instead of after the
keyword file makes the declaration differ from the directory name and the
warning never appears, while the file inside keeps the standard keyword name.
Verify with a count, not a build exit code (§6, and the reason a
`rc == 0` clippy gate is a free pass).

### 4.7 "Don't change the checker" is satisfiable by rewriting the source — verify the rewrite survives the formatter

A task that forbids touching the verifier ends when the checker reports zero,
but reaching zero by editing source has one trap: the edit must be *stable under
the formatter* and semantically identical. Two false-positive classes recur in
`|`-delimited syntax and each has a different stable fix.

- **An or-pattern in a matcher position is not a closure parameter list.**
  `matches!(x, A | B | C)` and a `match` arm like `'<' | '>' => …` both read as
  a closure param list to a span scanner. Splitting them across lines to dodge
  the regex does not work — `rustfmt` re-joins or-patterns, so the violation
  returns on the next `cargo fmt`. Rewrite them instead: a `const NAME: &[T]`
  of the alternatives plus `.contains(&x)`, or a `match` guard
  `x if ESCAPED.contains(&x)`. Same semantics, and both are legal Rust that the
  formatter preserves.
- **Source embedded in a multi-line raw string is not Rust at all.** A WGSL or
  GLSL literal inside `r#"…"#` gets scanned line-by-line, and any shader
  construct containing `|…|` reports as a closure. Here the stable fix *is* a
  line break: raw-string contents are never re-wrapped by `rustfmt`, so
  splitting the offending condition across two lines inside the literal removes
  the match permanently with no change to the embedded program.

So the classification is per-shape: **or-pattern → change the code; string
payload → change the layout.** Then prove both properties, not just the count:

```bash
crate fmt && crate fmt --check        # idempotent, 0 diff, violations still 0
cargo check --workspace --all-targets   # the rewrite still compiles
python3 <skill>/scripts/verify_<rule>.py .  # re-run AFTER the format pass
```

Running the checker only before `crate fmt` accepts a fix the formatter then
undoes. **A fix that only survives until the next format run is not a fix.**

**A fixer tested only on clean input has never run its rewrite path.** A
parse → transform → serialize fixer exercised on a compliant tree proves
its no-op path and nothing else; the rewrite path can still corrupt — the
transform stage drops a bookkeeping field (a trailing-blank flag) the
serialize stage depends on, and a required blank line vanishes on every
real rewrite while every clean-tree test stays green. A fix in one stage
is dead code when an earlier stage discards the field it reads. Fixture
the *out-of-order* input that forces a rewrite, assert every invariant the
companion verifier checks survives it, then run the fixer a second time
and require `Nothing to do` — a fixer that rewrites its own output
ping-pongs with the verifier forever. For the separate and more dangerous
shape — a script whose **audit** half is correct while its **fixer** half
rewrites string payloads — see `references/audit-fixer-asymmetry.md`.

## 5. Hooks that block a commit are the harshest verifiers — build the fixture suite first

A verifier wired into a git hook is the one kind with **teeth**: it aborts a
real commit in a repo the user is working in. That makes its failure modes
more expensive, and it makes the fixture suite non-optional.

### 5.1 Test a blocking hook on a copy, never in place

Copy the repo, point the copy at the real hook path, and assert on the copy:

```bash
T=$(mktemp -d "$SCRATCH/hooktest.XXXXXX")
cp -R ~/code/<repo> "$T/repo"
cd "$T/repo" && git config core.hooksPath ~/.git-hooks
# … build the fixture, assert, then:  rm -rf "$T"
```

Never stage a probe file in the user's real repo to prove a guard works. If
the guard is broken you find out by committing garbage into a live project,
and if it is *not* broken you have still committed a file whose only purpose
was testing.

**Before debugging a guard that "does nothing", confirm which hooks directory
is live — and then which FILE inside it is live.** A global `core.hooksPath`
silently shadows every repo-local `.git/hooks/`, so a guard installed per repo
looks present and never runs:

```bash
git config --get core.hooksPath     # a global value wins over .git/hooks
```

Resolving the directory is only the first half. The file inside it can be a
**symlink**, and a stale near-identical copy of the same hook can sit at the
path your own documentation names — so the sequence installs cleanly, passes
`bash -n`, and never runs. This is not hypothetical: adding a routing gate to
the documented path, then committing a change the gate should have blocked,
produced `commit rc=0` and a real commit in history. Both candidate files
looked correct and passed a syntax check; only a throwaway commit separated
them.

**Resolve the target before editing it, and prove the gate fires afterwards.**

```bash
realpath "$(git config --get core.hooksPath)/pre-commit"   # the file git runs
# then, on a throwaway branch:
printf '<a change the gate must reject>\n' > probe.rs
git add probe.rs && git commit -m "probe"
git log --oneline -1        # must NOT show probe
git reset -q --hard HEAD~1  # confirm the probe left nothing behind
```

The corollary for the docs: **a skill that hardcodes a hook path is a trap
waiting for the next session**, because the path it names is the one that goes
stale. Have it record the resolution command and `realpath` output as the
source of truth instead, and mark any hardcoded path as illustrative.

### 5.2 Assert the negative case first, and confirm HEAD did not move

A blocking hook has two failure modes that look identical from the terminal:
it blocked, or it printed a scary message and committed anyway.

```bash
git commit --no-verify -m "test(probe): deliberate violation" 2>&1 | tail -14
rc=${PIPESTATUS[0]}
echo "rc=$rc  HEAD=$(git log --oneline -1)"     # ← HEAD must be UNCHANGED
```

`rc=0` with a new HEAD means the guard is decorative. Only after the negative
case holds do you assert the positive case (`--no-verify` + a compliant change
commits cleanly), because a hook that is permanently red passes the negative
test while being useless.

### 5.3 Find the hook git will not let the user skip

A blocking hook placed in `pre-commit` is bypassable by definition — that is
what `--no-verify` is for. Enumerate the hooks empirically in a throwaway
repo rather than trusting documentation, because the set differs by git
version and the answer decides the whole design:

| Hook | Runs under `--no-verify`? |
|---|---|
| `pre-commit` | **no** — suppressed |
| `commit-msg` | **no** — suppressed |
| `prepare-commit-msg` | **yes** |
| `post-commit` | **yes** |

`prepare-commit-msg` is the enforcement point, and a non-zero exit there aborts
the commit before it is recorded.

### 5.4 Default to the restrictive verdict on every uncertainty

When the guard must decide "is this exempt", every unreachable answer must
resolve to **enforced**, never to exempt:

| Situation | Verdict |
|---|---|
| origin unresolvable, no `origin` remote | ENFORCED |
| token missing / CLI absent / API error / rate limited | ENFORCED |
| non-GitHub remote (SSH gitlab, local path) | ENFORCED |
| the listing endpoint is truncated or wrong | ENFORCED |
| the source of truth positively reports "not mine" | EXEMPT |

The exemption must be **proven**, never assumed from an absence of evidence —
a listing that came back short is not evidence that the repo is external.
Encode this as a single `ERROR` verdict that the caller maps to `ENFORCED`,
so there is exactly one place where the default lives.

A local list makes the first four rows nearly impossible; a live API makes
them the *common* case, so a guard that only works offline silently becomes a
free pass the moment auth expires. Prove the failure rows explicitly, on an
entity the source of truth confirms is owned — a broken-guard test that only
ever exercises the happy path proves nothing:

```bash
GH_TOKEN=invalid  <interpreter> scripts/guard.py --repo ~/code/<mine>   # -> ERROR
CLI=…-not-on-PATH  <interpreter> scripts/guard.py --repo ~/code/<mine>  # -> ERROR
```

**Enumerate the set you protect; never hardcode it.** "Everything under this
account and every org it belongs to" is a live question, and a snapshot of it
misses whatever was created later — the newest org, i.e. the least
established one, is the one left unguarded. Ask the source of truth on each
invocation.

### 5.4.1 Pick the property the rule actually discriminates on

Rules about repos are easy to get subtly wrong in the *safe* direction,
because a plausible proxy looks reasonable and quietly admits the cases you
wanted excluded. The proxy most often picked is **provenance** (is this a
fork? was it copied from elsewhere?) when the rule is about **ownership**
(whose namespace does it live in?). They disagree on exactly the interesting
cases:

| Repo | Provenance | Ownership | Which is right |
|---|---|---|---|
| your-ns/fork-of-someone-else | fork | **yours** | ownership |
| upstream-clone-in-your-workspace | not a fork | **not yours** | ownership |

A rule written on provenance exempts the first and enforces the second — the
inverse of the intent — and the two rows are indistinguishable by name, so
nothing looks wrong. Decide the discriminator from the rule's own words, then
build one fixture per row of the table above.

### 5.4.2 Classify the **changed lines**, not the file — a mixed file is the normal case

A classifier that asks "is this file declarative?" answers a question nobody
asked. Real files mix concerns: a macro body holds style declarations in one
block and executable statements in another, and a single commit usually
touches one of them. The file's overall nature is not the property the
verdict turns on; the nature of the **lines the diff adds and removes** is.

Two failure directions, and the second is the dangerous one:

- **Judging the whole file** lets unrelated pre-existing content veto an
  otherwise-clean change. A style block containing a perfectly ordinary
  `display: none` a hundred lines away from your edit makes a one-line
  colour tweak route as code, forever.
- **Judging the file's extension** is the same error wearing a cheaper
  disguise. `.css` is not a reliable proxy for "declarative", and `.rs` is
  not a proxy for "code" — a Rust host language carrying an embedded
  style DSL (`class! { pub c_xxx { … } }`) produces style inside a `.rs`
  file, which the extension rule routes as executable code by default.

Scope the verdict to the diff's `+`/`-` lines and ask of *those*: does each
added or removed line read as a declaration, or as a statement? Then split
the property the way §5.4.1 asks — name the declarations that stay direct and
the ones that stay gated, and build one fixture per cell:

| Line content | Verdict |
|---|---|
| declaration whose value is an interpolated expression (`border-left: format!(…)`) | declarative |
| declaration of a behavioural property (`display: none`, `pointer-events`) | gated |
| a nested selector or at-rule | gated |
| any `let` / `fn` / call statement | gated |

The interpolated-value row is the one that gets misfiled in both directions:
it looks like code because of the macro call, and it is not — the macro
produces a value at build time and nothing runs at page load. Judge the
*result*, not the syntax that builds it.

## 5.5 Write hook scripts for the *system* interpreter, not your venv

A script invoked from a git hook runs under whatever `python3` resolves to,
with no venv, no project deps, and possibly an older minor version than the
one you develop against. Annotations that parse fine can still explode at
call time:

```python
def classify(...) -> tuple[bool, str | None]:   # TypeError on Python 3.9
    ...
```

Use `typing.Optional` / `Tuple`, or omit the annotation. Check before
declaring victory:

```bash
python3 --version
python3 -c "import ast; ast.parse(open('scripts/guard.py').read()); print('parses')"
python3 scripts/guard_selftest.py               # runtime, not just syntax
```

`ast.parse` proves syntax only — a PEP 604 union is syntactically valid on
3.9 and fails at def-call time. The self-test is what catches it.

The same applies to the **environment**, not just the interpreter: git invokes
hooks with its own env, not the one you typed the command into. A guard that
reads `$GH_TOKEN` works in your shell and fails in the hook. Reproduce the
real invocation:

```bash
env -i HOME="$HOME" PATH=/usr/bin:/bin <interpreter> scripts/guard.py --repo .
```

Credentials that the tool resolves itself (a keyring-backed `gh`, `~/.netrc`,
a config file) survive a bare env; credentials you exported in your shell do
not. Anything the guard needs at commit time must be self-resolving.

### 5.6 JSON projections: `--jq` renders a missing key as the string you named

When a CLI projects a nested field with a fallback, the missing value comes
back as the **fallback string**, not `null`:

```bash
gh api repos/<o>/<r> --jq '{fork, parent: (.parent.full_name // "none")}'
# → {"fork":false,"parent":"none"}
```

So `(data.get("parent") or {}).get("full_name")` raises `AttributeError` on
the string `"none"` — the `or {}` guard does not help, because a non-empty
string is truthy. Type-check before indexing, or compare the field as a
string. The generic rule: **a jq/JSON projection is not a null-safe API**;
`isinstance(data.get("parent"), dict)` before you reach inside it.

### 5.6.1 Two endpoints, one name, different results

Sibling endpoints that differ only in path can return **different scopes**
with no error to tell you. A public-membership listing returns only the
public subset of an account's orgs, so a guard built on it protects the
visible orgs and silently exempts the private ones — the entries most worth
protecting, and the ones nobody notices missing.

Cross-check the two before building on either, by **count, not by eye**:

```bash
gh api "users/<acct>/orgs" --jq '.[].login'   # public membership only
gh api "/user/orgs"       --jq '.[].login'   # every org the token can see
```

If the counts differ, the narrower one is wrong for this purpose even though
it succeeded. Any enumeration used for an access decision needs the same
check: a short list that looks complete is the failure mode.

### 5.7 Keep a self-test next to every hook verifier

Ship `scripts/<verifier>_selftest.py` beside the verifier. It builds
throwaway repos with synthetic remotes and asserts the verdict per case, so
both the syntax trap and the error-path defaults are exercised in seconds
without touching a real repository. Run it after every edit — it is the only
cheap way to know the guard still blocks *and* still passes.

**Derive the positive fixtures from the live source of truth, not a hand-typed
table.** When the verdict comes from an API or a directory, query it in the
test and build the "should be enforced" cases from entities that really
exist. A fixed table passes forever while the enumeration is silently wrong —
and a silently truncated enumeration is exactly the bug this class of guard
exists to prevent, because it exempts the unguarded entries while looking
complete.

**A fixture that fails may be the thing that is wrong.** Decide from the
rule, not from the code's current output: re-derive the expectation, and if
it encoded a property the rule does not discriminate on, fix the fixture
rather than bending the guard to satisfy it. See §5.4.1.

### 5.8 Fixture repos must be isolated from the user's own git configuration

A self-test that builds throwaway repos (§5.7) inherits the machine's global
git setup, and two pieces of it bite:

- **Global `core.hooksPath` applies inside the fixture.** The user's real
  hooks run on every fixture commit — including `prepare-commit-msg`, which
  §5.3 shows fires even under `--no-verify`. A fixture step that commits a
  deliberately-violating file (to seed HEAD with legacy debt) gets blocked
  by the very gate under test, and the resulting staged-but-uncommitted
  file contaminates every later step while the failure reads as a fixture
  bug. Detach right after init: `git config core.hooksPath <empty-dir>`.
- **Diff-scoped audits need the remote-tracking ref to exist.** An audit
  that guards on `git diff origin/master HEAD` exits early when the ref is
  missing, before running any check. Synthesize it in the fixture:
  `git update-ref refs/remotes/origin/master HEAD` — no remote or network
  needed.

And exercise every dispatcher with **two** files in scope, never one. A
pipeline that builds `--files` by joining paths into a single string passes
a single-element fixture cleanly while every real multi-file run hands its
consumers one bogus space-containing path — the gate then reports
`0 new violations` because it examined nothing. Single-file fixtures are
blind to argv-joining, glob-splitting, and per-file aggregation bugs by
construction; the first two-file fixture is where the plumbing is tested.

### 5.10 A gate that reports PASS without reading a file is worse than a broken gate

A verifier can be green for the wrong reason: its input set is empty, its diff
window never opened, or it silently skipped every file. **A vacuous PASS is
indistinguishable from a real PASS in the output**, so it survives review and
then quietly stops gating. Three distinct mechanisms, each hit once in one
session:

| Mechanism | Symptom | Fix |
|---|---|---|
| Diff-scoped check against a ref that does not exist (fresh repo, no remote, non-default branch) | `FAIL: 0. diff window is empty: git diff <baseline> failed, so every diff-scoped check below would pass without reading a file` | Create/push the baseline ref, then re-run |
| Verifier hardcodes a layout the repo does not have (e.g. `<crate>/src/lib.rs` in a workspace with no `src/`) | `FileNotFoundError` from the fixer, or a `0 files checked` count | Point it at the real crate root, or hand-fix and note the script is broken |
| Hook copies each file **in isolation** into a scratch dir, losing cross-file context | Repo-wide run says `0 violations`, the hook reports violations on that same file | Reproduce both ways before believing either |

**The test is mechanical: prove the gate is reading files before trusting its
verdict.** Never accept a summary count on its own.

```bash
python3 verify_<rule>.py <root>          # expect "N files checked", N > 0
python3 verify_<rule>.py <fixture-dir>   # positive control: known-bad MUST be non-zero
git diff <baseline-ref> --stat | tail -1  # diff window actually opens
```

A gate never shown to FAIL something is not a gate. Skip the positive control and
the gate is decoration.

**Isolating a file to blame it can also manufacture a violation.** The same
scratch-dir trick §5.9 uses to prove a staged file is clean **creates false
positives** when the rule depends on sibling files — a manifest audited alone
loses the workspace-member list, so a local-vs-third-party ordering rule
reclassifies every dependency and reports a pile of §13.7 hits. When repo-wide
and isolated disagree, run both, then read the rule to learn which context it
needs. Do not "fix" source code to satisfy the isolated reading.

**Corollary — a hook that audits a single staged file can permanently block the
repo's first commit.** A brand-new repo has no HEAD, so `old_count` is 0 and
every staged file counts as pure new violations. Land a baseline commit first,
then the comparison works normally.

**Report gate bugs as bugs.** When a script is silently passing, crashing, or
mis-scoped, say so with the command output and state explicitly that you are not
bypassing it. Never route around it with `--no-verify`; the fix is to make the
gate correct.

### 5.9 A repo-wide hook gate blocks on someone else's file — scope it to the staged set before blaming the change

A `pre-commit` hook that runs a verifier over the **whole repo** whenever any
file of a given type is staged will block on a pre-existing violation in a file
the author never touched. The message names the check and the repo, not the
staged file, so it reads as "your change is wrong" when it is not.

**Prove the attribution before accepting or rejecting the block.** Two cheap
facts settle it:

```bash
git diff --cached --name-only            # what is actually staged
git show --stat HEAD                     # is the offending file even in the commit?
python3 <skill>/scripts/verify_<rule>.py <the-staged-file-in-isolation>   # passes alone?
```

The diagnostic that closes it: copy the staged file alone into an empty
directory and run the verifier on that. `1 file checked, 0 violations` proves
the staged change is clean and the repo-wide hit came from elsewhere. A
throwaway comment-only change to any file of the same type exiting non-zero
proves it is not delta-scoped at all.

**Then fix the offender, not the gate.** The verifier's rule is usually right
and the other file is genuinely out of order — reorder it. Do not weaken the
check to accommodate one file, and never bypass it.

**A version-string bump can reorder dependencies the rule sorts by string
length.** A dep-order rule that sorts on the character count of the version
literal will re-rank a neighbour when a version grows (`"0.28.6"` → `"0.28.15"`
is 14 → 15 chars, overtaking a 14-char neighbour). Adopt the verifier's
expected order rather than guessing, re-run it, and expect the bump commit to
carry that reorder — it is part of the change, not incidental noise.

**A dep bump is not an API migration; confirm `src/` is untouched.** Additive
version changes frequently require zero source edits, and that is worth
stating explicitly: `git diff HEAD --stat -- src/` being empty is the evidence.
A child that reports "no API migration needed" is only believable with that
diff attached, because a large `src/` diff would mean the claim is false.

**Establish the pre-bump baseline by re-running the gate at the old version in a
throwaway worktree.** Warning and lint counts are not portable across the change:
`cargo check` and `cargo clippy --all-targets` report different totals for the
same tree, so a number carried over from a different command manufactures a
fake regression. Measure both sides with the *same* command and target dir, then
compare:

```bash
git worktree add "$S/base" HEAD          # old deps still in Cargo.lock
( cd "$S/base" && CARGO_TARGET_DIR=<separate-dir> cargo clippy --all-targets 2>&1 | grep -c '^warning' )
```

Report "no new lint" only when both numbers came from the same command.

## 6. When your own first result is wrong

A verified result is not the same as a *first* result, and this class of work
produces claims that look verified because a script printed a verdict.

- **A green suite can encode the wrong rule.** When a fixture fails, first ask
  whether the *expectation* encodes a property the rule does not discriminate
  on. Fixing the code to satisfy a bad fixture makes the suite green and the
  guard wrong.
- **An exact expected count is an output of the run, not an input to it.** The
  assertion encodes your prediction, so a failure has two candidates: the
  verifier mis-flagged, or your *compliant fixture is itself a violation*
  because it encodes a mental model you never checked case by case. The second
  surfaces as "the verifier is broken" and invites bending working code to
  match a wrong expectation. So: run first, observe the count, then confirm by
  hand that it equals the rule's semantics before adopting it — and confirm it
  **decomposes** into one hit per intended violation plus one per exempt shape
  you meant to pass. A count that does not decompose means you mis-modelled
  the rule, whatever the number says. Recursive trees are where this bites:
  exempting an entry file does not exempt its whole directory, so a "compliant"
  tree two levels deep can hold real violations at every level. Name the
  corrected expectation in your report — a silently fixed fixture teaches the
  next reader that any count is acceptable. Never bend the verifier to satisfy
  a fixture unless a counterfactual run of the pre-patch verifier on the same
  input proves the old code flagged it too (§2.1.1).
- **A tool field you can query is worth querying.** "CI is green" read from a
  cached API field, a stale ref, or a run list scoped to the wrong event is a
  guess; the workflow-runs list for the commit SHA is the authority. When two
  sources disagree, believe the one keyed on the object you actually shipped.
- **State the residual risk you did not close.** If the PR-triggered workflow
  did not re-fire and you substituted a local run, say so — a local gate on
  the new commits is not the same claim as CI on them.
- **Say when you should have caught it earlier.** When a fix round reveals
  a sibling defect you never tested, that is a scope failure, not a discovery.
- **A redacted tool result is not a valid `old_string`.** Credential-shaped
  literals are replaced with `***` in what a read/diff tool hands back, so
  text you copy out of one carries the mask, not the real token. Pasting that
  masked form into an edit writes the mask to disk — a live
  `Authorization: token $GH_TOKEN` silently becomes `token ***`, the call
  401s, and the diff still reports success because every hunk applied. Rebuild
  the context yourself with the real variable in place, then re-read the
  touched lines (`grep -n 'token\|secret\|key' <file>`) and sweep for masks
  that arrived uninvited (`grep -rn '\*\*\*' <changed files>`).
  **Telltale:** the diff shows a line you did not mean to touch changing
  anyway — an untouched `-$TOKEN` / `+token ***` pair is the mask, and the
  moment you see it, roll that hunk back.
- **A successful edit is not the same as an intended one.** After any batch of
  patches, diff the *whole* change against what you meant to change, not just
  the hunks you aimed at. Uninvited line changes are the only evidence of this
  class of corruption, and they are one `git diff` away.

## 7. A verifier change ships with its callers

When a commit changes a script, check that everything that *calls* it ships in
the same change: the spec sentence it enforces, and the audit wrapper that
invokes it. A verifier no pipeline invokes is a hole in the coverage that
reads as full compliance, and the skill's own script table is what the next
session trusts — a rule described there but not enforced anywhere is worse
than an undocumented one.

Note the asymmetry with §4.2: "ships with its callers" means the verifier and
the *right* caller land together, not that every check joins every layer. A
layout rule needs a per-file adapter (§4.2) before the gate can run it, and
where one layer is authoritative for a case the other cannot see, the spec must
say which — an unstated division reads as full coverage from both sides.

**Rule: verifier + gate registration + spec sentence land together, in the
skill repo, in one commit, with the user's repo untouched.** Three artefacts
that drift apart is the same class of bug as a pipeline pointing at an
untracked file: it works on the machine that wrote it and fails everywhere
else.

### 7.1 Adding a check to a numbered suite is a document-wide reconciliation

An audit that numbers its checks makes every count in the prose a hostage to
the next insertion. Adding one check means sweeping for: the "N checks"
totals in the spec, the audit-summary count, the phase-table row, the file
layout comment, the false-positive-list range. Miss one and a future session
greps a number that no longer exists.

Two numbering traps in the same sweep: 

- **A semantic check number is not the list position.** Source comments usually
  read `# check 44` (the rule's identity, stable across insertions) while the
  runner numbers by position with `enumerate(CHECKS, start=1)`. The two agree
  only until something is inserted above. When a grep for `FAIL: 44.` finds
  nothing, check the position before concluding the check is not running.
- **Run the audit once and read the real output before writing any number.**
  Predicted totals are how a wrong count becomes documentation.
- **Appending to a list-of-tuples registry: the previous last element's
  terminator is part of your edit.** An `old_string` that ends at the final
  `''']),` and a `new_string` that adds your tuple *after* it has moved your
  tuple outside the list — everything from there on is a syntax error at a
  confusing offset. After any registry-tail edit, immediately
  `python3 -c "import ast; ast.parse(open('<script>').read())"` and run the
  audit once on a real repo: the check total must increment by exactly 1 and
  your new check must appear in the output. Both numbering mistakes this
  section warns about (list closed early, tuple orphaned) are invisible until
  that run.
- **The pitfalls/registry file has the same collision class.** Appending a
  `## §N` entry without scanning existing headings can reuse a live number —
  grep the highest `§N` first and take the next one; a duplicate number makes
  every `pitfalls §N` cross-reference ambiguous.

Batched into one pass: add the check, run it against the real repos, then
update every count and every range in one edit rather than incrementally.

## 8. Cleanup

Verifier work leaves scratch repos, copies, and fixture directories behind.

```bash
rm -rf "$SCRATCH"/{hooktest,guardlive,final}.*
```

If a probe file appeared in a real repo while you were testing, say so and
leave it for the user to judge — it may be someone's in-progress work, and
deleting another process's uncommitted file is not yours to do.

**But `git reset --hard` in someone else's worktree is not the same category**
— §4.4. That one destroys their work with no way for them to know it happened,
so recover it from the object database if you can (§4.4) and report it plainly
rather than filing it under scratch cleanup.

