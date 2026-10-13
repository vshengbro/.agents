# Browser-automation harnesses: proving the measurement before trusting the verdict

Applies when a suite drives a real browser to assert on app behaviour —
CDP sessions, injected key/mouse events, an in-page debug state object,
screenshots, pixel diffs. Every failure mode here produces a number that
looks measured, and the number is wrong.

## The rule that governs all of them

**Validate the measurement channel before you read a verdict from it.** A
harness that reports "the app is stuck" because it sampled a field the app
only publishes every 3 frames has told you nothing about the app. Prove the
channel carries the signal — one known-good input, one known-good output —
before any FAIL from that channel reaches a report. The cost is one probe; the
cost of not doing it is a repair round aimed at correct code.

## Throttled publish cadence silently deletes frames

An in-page debug object rewritten every N frames (the idiom is
`if frame_count.is_multiple_of(3) { publish() }`) looks like a live state
snapshot. It is not. Any measurement that assumes it can read consecutive
frames skips two of every three, and the gaps it does see are an artefact of
its own polling — so "player stood still for 12 frames" is usually "the
harness read a field twice inside one publish window."

- Establish the cadence before trusting any per-frame claim: log consecutive
  frame counters and look at the *deltas*, not the values.
- Prefer a channel that is rewritten unconditionally each frame. A HUD text
  node updated per frame, carrying its own frame counter, is a per-frame
  truth channel; the debug object is not.
- A sampling stride that does not divide evenly produces false periodicity.
  Check for a spike at the publish interval *before* believing you found a
  physical stutter — a long run with no such spike means the stutter is not
  there and the harness invented it.
- Divide out the confound before comparing: compute the effective `dt` implied
  by each run (`distance / speed`) and check the two sides of any ratio
  actually ran at comparable `dt`. Two runs whose effective `dt` differs by
  3x cannot be compared per-frame, and a ratio built from them is meaningless.

## Cross-snapshot reads race the publisher

Reading several related fields in separate round trips is not an atomic
snapshot. The publisher can replace the whole object between your reads, so
key A from frame *n* pairs with key B from frame *n+1* — which is how a
stable value intermittently reads as `null`, and a `KeyError` names a key that
was demonstrably present a moment earlier.

- Take **one** snapshot, then read every field out of that local value.
- A `KeyError` on a key that exists in the source is a symptom of this, not of
  a missing feature.
- A value of `null` on the first read and present on the second is the same
  bug. Do not report it as flakiness.

## Assert the channel matches the app's real input path

A harness that injects `keydown` to test a feature the app enters through
`mousedown` measures a path the app does not have. The verdict is always
"the feature does not work," and it is always wrong. Find the app's actual
entry point — `git grep` the event name, read the listener — and drive that.

- A constant declared but never read (`git grep -c '<CONST>' -- src/`
  returning exactly `1`) means the wiring is absent. That is a **real defect**,
  and no harness result can overturn it. See §2.4.
- Symmetrically, a harness that drives a path the app does not use is
  evidence of nothing; fix the harness, not the app.

## A test point is not a route

Several classes of "the app cannot do X" are the harness walking the wrong
line, not the app failing:

- **Spawn distance.** An interact key tested from further away than the
  interaction range cannot succeed. Check the distance before blaming the key.
- **Scene drift.** A waypoint that a scene change invalidated sends the run
  into open ground. When a scripted run ends somewhere wholly wrong, read the
  *endpoint* first: a subject that ran to `x=-85` was never near the target
  at `x=27`.
- **Momentum carry-over.** A held input persists into the next measured leg,
  so leg two starts with leg one's velocity and its first recorded frame is
  already off-route. Clear the input explicitly and sample continuously,
  rather than parking frames that the sampler keeps recording.
- **Aborting a whole run on one leg's precondition** silently produces *no*
  result for every leg after it. Scope an abort to its own leg, and prefer a
  loose positional tolerance: a small readback error on a wide surface is not
  a failure, and refusing to report is not a virtue.

## Fixture worlds that flatter the code under test

A unit test whose helper constructs a simplified geometry will pass while the
real layout fails — the fixture is the specification, and a fixture drawn
from what the code already handles can never contradict it.

- Query the **real builder** in at least one test, not only the fixture.
- Prove the new test fails on the old behaviour: check it out, run it, see it
  go red, then restore. A test that never went red proves nothing.
- When a test fails, ask which is wrong — code or expectation — before
  editing either. Sometimes the *old* expectation encoded the accidental
  geometry and the real intent is better stated; say so in the change rather
  than bending geometry to preserve a stale assertion.
- When the discrepancy is a **sign or range error in a placement expression**,
  check the asset files for what the player actually sees. Collision and
  visual geometry can disagree for months; the asset is the arbiter. Fixing
  collision to match a slab the player can see through is worse than the bug.

## Static checks and vision are not the same as a numeric threshold

Where a judgement is perceptual, a pixel-mean comparison on a gradient
background measures the background, not the subject. The honest options are a
**differential** criterion (compare the region with the subject rendered
against the same region with it hidden) or an explicit `SKIP` whose note says
a human or vision pass is required to settle it. Do not emit a threshold that
passes because the sky is darker on one side.

A depth or normalised-device-coordinate channel that saturates to a constant
(`z` pinned at 1.0 everywhere) has **zero resolving power** for the quantity
being tested. Recognise that shape and mark it undetermined; do not turn it
into a threshold that happens to pass.

## Anti-patterns worth refusing explicitly

- **Hardcoded verdicts.** `Verdict(name, False, "…the match arm does not
  exist…")` with the reason computed at authoring time rather than measured.
  If the note can be produced without running anything, it is not a verdict.
- **Stale negative tables.** A literal list of "missing features" baked into
  the script, bypassing measurement. Any absence claim needs an A/B reading
  in support; source greps are diagnostic notes, never the evidence.
- **Self-degrading criteria.** When a fix round arrives with failing checks,
  the cheapest way to improve the number is to relabel them. Require the
  child's per-item adjudication ("these N were real defects, these M were
  broken verdicts") rather than the total, and reject FAIL→SKIP on a subject
  the app plainly implements.

## Budget, ports, and the honesty of the summary line

- Parallel browser runs need one port and one profile directory per worker, and
  a single-threaded static file server serving eight simultaneous Chrome boots
  will drop connections. Solo the failing worker to separate an environment
  failure from a verdict.
- Kill by profile path, not by process name, so you never take down another
  worker's browser and call the resulting dropped connection a result.
- Release every port at the end and say that you did.
- Report harness timeouts, connection resets, and pages that never booted
  **as their own category**, never folded into a pass or fail count. A suite
  that reports "N failures" where two are its own crashes is a number nobody
  can act on.
