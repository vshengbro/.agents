---
name: parallel-worker-verification
description: "Use when N agents verify a build in parallel."
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [verification, fan-out, cdp, harness, delegation]
    related_skills:
      - delegate-task-contract-pitfalls
      - delegated-result-verification
      - main-agent-delegation-rule
---

# N-way parallel worker verification

## When to Use

- "派 N 个 agent 同时验证" / "N agents to verify in parallel"
- Several subsystems each need an independent read path over one finished build
- A visual/browser build needs multi-angle screenshot + description auditing

The user's shape for this class of task: **fix serially, verify N-way in
parallel, record every failure rather than fixing as you go, fix in a
follow-up round, repeat until the target is matched.** That loop is the point
— the deliverable is a converged state, not one green run.

## The harness is shared; the workers are not

Write the shared library **first and land it before dispatching any worker.**
Workers written against an unwritten interface will each invent a slightly
different one, and the mismatch surfaces later as runtime errors rather than
import errors.

Give the library one **stable, minimal** surface. Everything a worker needs to
vary — thresholds, budgets, targets — is a parameter, not a subclass.

**Accept both call conventions on any method the workers will call.** One
signature choice strands half of them:

```python
# strands workers that follow the sibling harness's style
async def cmd(self, method, **params) -> dict
# serves both; merges positional dict then keywords
async def cmd(self, method, params: dict | None = None, **kwargs) -> dict:
    merged = dict(params or {}); merged.update(kwargs)
```

Grep the neighbouring harness in the same repo **before** designing yours — a
new `tools/verify8/vlib.py` sitting next to `tools/sweep/sweep_lib.py` will
absorb the old call style, and only the sibling's signature says so.

**A signature change verified by "it imports" is unverified.** The bad call
lives inside a coroutine. Drive the fixed method with a stub transport that
records outgoing payloads and assert every call shape: positional dict, keyword
args, no params, and both merged. An import that merely succeeds has *moved* the
crash past startup, where it reads as an app failure.

**In the brief: report harness gaps, do not patch the library.** "If the session
object lacks a method or a field name is wrong, name the missing signature in
your report — do not edit the shared lib." N workers editing one library
serialise badly and invalidate each other's runs. Collect gaps, fix once.

## Harness failures must be named as harness failures

A worker must be able to say "the harness broke" and have that survive into the
summary. Require a distinct verdict kind (e.g. `fail_harness(worker, why)`) so
an environment problem is never tallied as an application defect. Otherwise one
worker's dead Chrome reads as "the build is broken" and sends the next round
chasing a phantom.

**A killed run is not a verdict.** SIGTERM (exit 143) or any non-zero that is
not the script's own exit code means no results file was written. Do not fold it
into a pass/fail count; report it as killed.

## Port and profile isolation is a hard requirement

Every worker gets its own CDP port and its own `user-data-dir`. Concurrent
workers kill each other's debug ports and temp profiles, which looks exactly
like the app breaking.

- Write the port range into the brief as absolute numbers, not as "pick a free
  one" — trial-and-error discovery means two workers pick the same port.
- Also state which ports are **already taken by other lanes** and are off-limits.
- Workers must tear down their own browser on exit, including on failure. A
  verification script that leaves eight orphaned Chromes is a worse outcome
  than a slow one.
- Never add `--disable-gpu`: it makes `requestAdapter()` return null, the page
  still runs, and every worker fails for a reason that looks like the renderer.

## Honest talling

Design the verdict as **three-state, not boolean**: pass / fail / *could not
determine*. A worker that cannot reach a state must say so rather than guessing,
and "could not determine" must stay visible in the summary — a run where
everything is a definite pass is usually a run where nothing actually measured.

**A worker crashing on its own harness is spending the lane's budget.** In one
8-way round, three lanes each burned multiple runs on their own bugs — a missing
`await` at module scope, an `UnboundLocalError` from an if/else where one branch
never assigned, a `KeyError` from a parser indexing a field the payload does not
guarantee, `min()` on an empty slice, an `IndexError` from treating a greyscale
crop as 3-channel. None of these are findings about the app, and each one costs a
full browser boot, teleport and frame wait.

- **Require a cheap static pass before a long run**, and require output to be
  flushed per-record so a wall-clock kill does not discard everything already
  measured. A run that hits a wall-clock limit with a one-line log has produced
  no data, only the artifacts it happened to dump on the way out.
- **After the second self-inflicted crash, stop the worker from re-running and
  ask for delivery of what it has.** A worker that has already judged every row
  does not need a sixth run; steering it to "report now, and write down the
  criterion you used" is worth more than another probe.
- **Read the crash before intervening.** Most are self-explanatory to the child
  and it will fix them without a steer; a steer is for the pattern (keep using a
  shape that keeps breaking), not the traceback.

Per-category coverage beats aggregate totals: a healthy "58 assets / PASS"
absorbs a category that was never built. Re-derive the per-category breakdown
against the original request list yourself.

## A periodic stall verdict is a claim about the sampler until audited

A page that publishes its debug snapshot every N frames has a **reporting**
cadence, not the simulation cadence. A worker that walks the published counter
and calls each skipped publish "a frame where nothing moved" **manufactures a
perfectly periodic stall out of smooth motion** — and the invented period equals
the throttle stride, so it arrives as a convincing periodic bug rather than a
sampling artifact.

Measured: the throttled trace stepped frame numbers by 3 (`267, 270, 273`), the
unthrottled one stepped by 1 with no gaps, and both were "the same walk". A
worker reported "12 of 24 frames completely static" and nearly shipped a fix
for a bug that did not exist.

**Require per-frame traces built in-page, unthrottled** — a sampler appending
to an array on every rAF, read back in one round trip. Never reconstruct
per-frame behaviour by polling a published snapshot from outside.

- Make the worker **print the raw frame-number sequence** and check for a
  fixed stride before believing any stall, no-decrement, or "frozen input"
  verdict. Constant gap = throttled writer. Varying gap = investigate. No gaps
  = the stall is real.
- The same artifact surfaces under many names — frozen input, dead loop,
  frames not advancing, "it updates every 3rd frame". All are throttle
  signatures until the numbering says otherwise.
- **A defect disproved this way deletes a task from the board.** Say so
  explicitly and do not carry the phantom into the next round — and name the
  mechanism that disproved it, because "moved the fixture and it vanished" and
  "sampled unthrottled and it vanished" are the same clean result from
  different causes, and only one generalises.

## Perception, not numbers

For anything with an appearance, a numeric gate is satisfiable by garbage:
stddev, triangle counts, `HTTP 200`, clean console, and frame counters all hold
while nothing readable is on screen. Require workers to **load the image and
describe what is in it** in their own words, and quote that description back.

Numeric signals are legitimate only as cheap liveness guards ("did anything
render at all"), never as acceptance.

**A per-subject pixel threshold measures the background, not the subject.** The
canonical version is "does the subject's screen box have contrast and non-black
pixels?" — and a sky gradient satisfies both. Make the gate **relative to its own
surroundings**: compare content inside the subject's box against content just
outside it, and hold an isolated render against a known flat clear colour.

**Check the subject is as many pixels wide as the threshold demands.** A 3-px
box can never satisfy a 5000-px threshold, and a worker that wrote that
threshold is reporting its own miscalibration as a product defect. The same
trace showed a bare `range > 40` gate passing on an empty frame (the sky passed
it) while a box-vs-surround comparison correctly read the box as empty — one
frame, two gates, opposite verdicts. When a worker's numeric gate and its own
vision description disagree, **the description is the finding**; require it to
say so in the report rather than quietly keeping the number.

## Before/after comparisons need a controlled baseline

Freeze the pre-change copy before editing, and never use `HEAD` as the baseline —
other agents edit concurrently, so `HEAD` moves under you. Record the frame
rate on both runs and only compare equal-fps runs; re-measure after the edit
rather than trusting the earlier number.

## Prove your measurement channel works before you trust what it says

The strongest worker in a fan-out is the one that validates its own
instrument before reading a verdict through it. The cheap form: **build a
negative control** — change the input in a direction whose answer you already
know, and confirm the channel reports it.

A visibility worker that hid the subject's draw batches, measured a 69.6%
whole-frame change, and thereby *proved the channel was live* could then trust
its own A/B pair (in-box variance 22.01 → 17.14, plus 152 distinct RGB values
behind the box). Without the control the same numbers are unreadable — a
channel that cannot see 107 hidden batches cannot see the subject either.

- **Put the control in the brief.** "First demonstrate your measurement can
  detect a known change; then measure the subject" turns a plausible number
  into a load-bearing one.
- **A worker that skips the control and reports a number is not wrong, it is
  unfalsifiable** — which is the same failure as a numeric gate, one level up.
- The same discipline kills a whole category of bogus FAIL: a worker whose
  forward-vector candidates are orthogonal to the app's real camera basis
  measures a dot product of zero **forever**, and reports the correct app as
  broken. Have workers derive the expected basis from source rather than
  assume it, and sanity-check that a known-good input scores highly — a gate
  that cannot pass is as broken as one that cannot fail.

- **A verdict authored by assertion instead of measurement is the same defect
  in a different costume.** A worker whose `Verdict(...)` passes `False`
  literally — with a note citing a grep that no longer holds — and another
  whose hand-written "missing keys" table lists features that the file's own
  readings already proved working, both ship a confident FAIL for correct
  code. The tell is identical: **the verdict is not a function of a reading.**
  Grep results, source comments and static tables are diagnostics to paste into
  a note, never the thing that decides the verdict.
- **A failure note that argues against itself is the loudest signal there is.**
  "cameraMode should not change, and should not change — judging FAIL" describes
  a criterion with no satisfiable state. When the note contradicts its own
  verdict, the note is the finding.
- **Do not let a worker turn a real finding green.** A defect correctly located
  at `const.rs:1097` stays FAIL. If the brief says "prefer SKIP over false
  PASS", a worker can comply by reclassifying a genuine defect as a criterion
  problem; require each FAIL to be labelled *real defect* or *criterion*, with
  the evidence for the label, and check the split yourself before tallying.

## Simulated values are ranges; exported fields are only as good as their projection

Workers keep writing criteria against quantities that jitter every frame, then
reporting the instability as a product defect. Both failure modes below were
dispatched as bugs before being caught in source.

- **Use a range, never a float equality, on anything the simulation
  produces.** Foot height, camera distance and eye height all carry ground
  support, pitch, avoidance and interpolation jitter. An equality check
  returns the opposite verdict on two runs of the *same* build — the app did
  not change, the criterion's input did. When a criterion flips between two
  runs of one build, **the criterion is the bug**; adding more samples to
  stabilise it only averages noise.
- **Read the code that exports a field before using it to detect change.** A
  debug payload that publishes only a matrix's translation columns is
  *structurally constant* under a pure rotation — a `0.0000` delta is
  guaranteed, and says nothing about whether the animation ran. To prove an
  animation drives the renderer, read the scalar that drives it: a gait phase
  and amplitude climbing from 0 to ~0.97 while moving is hard evidence, where
  per-pixel alignment is a guess.
- **One malformed record must not destroy the round.** Probe fields are not
  guaranteed present (a probe reports only colliders within its query radius, and
  entries legitimately lack fields). Use `.get()` plus skip, wrap printing in
  `try/except`, and **check a slice for emptiness before `min()`/`max()`**.
  Otherwise one oddly-shaped record loses every good reading taken before it.
- **Keep a worker's scripts out of a shared directory's root.** Python puts the
  script's own directory first on `sys.path`, so one `bisect.py` next to it
  shadows the standard library and the traceback lands in `email.utils` and
  `random` — reading like a crash in the code under test. Give each worker its
  own subdirectory.

## A worker with enough evidence that keeps running is spending your budget

Workers drift from "verify this row" to "add one more probe", and every probe
re-opens a browser, re-teleports and re-waits frames. By the fifth the extra
work is usually not new information.

- **Watch whether it is filling a gap or re-measuring a decided row.** Filling
  a gap is the job; re-measuring a row it already judged is not.
- Once the readings that a PASS requires are in hand, ask for delivery and for
  the *criterion* to be written down — more resolutions, more camera positions
  and more control groups are not what makes the next round faster.
- A defect already pinned to a constant and a line does not need another run
  of the scenario to confirm it exists.

## Verify the fix at the level the symptom lives

A whole-screen pixel diff has a noise floor that can exceed the signal. Measure
the floor first (hide a known-visible group, read the change, and if that
number is near what you get when you hide *everything*, the method is
useless), then invert the experiment so the region of interest can only contain
the subject: isolate the subject's own draw batches and read **inside** its
screen-space box.

## Related

- `delegate-task-contract-pitfalls` — how to split a delegation, and the
  false-finish / re-dispatch patterns
- `delegated-result-verification` — re-measuring a child's claims
- `cdp-acceptance-harness`, `cdp-browser-harness-speed` — user-owned; they
  cover harness *speed*, this skill covers harness *contracts and fan-out*
