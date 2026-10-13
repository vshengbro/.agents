---
name: verifying-before-dispatching-repairs
description: Use before fixing a defect. Validate the channel first.
---

# Verify the channel before dispatching a repair

A confident "this is a defect" verdict built on one unexamined reading is
more expensive than no verdict at all: it sends a writer to edit correct
code, burns an agent-cycle, and the "fix" then gets verified by a harness
built on the same broken premise.

Rule: **before dispatching a repair for any abnormal reading, prove the
measurement channel is valid.** A surprising value is far more often a bad
probe than a bad app.

## Channel failures seen in a single session

Each of these produced a confident, wrong defect verdict.

| Symptom read as a defect | Actual channel fault |
|---|---|
| "walks 2 frames, freezes 1" | debug object published every 3rd frame; sampling read one snapshot 3x. Real run: 0 stationary frames |
| "player cannot shoot" (20 shots, hp unchanged) | probe sent a key event; the game bound `canvas mousedown`. No shot was ever fired |
| "sprint is 0.96x walking" | probe wrote `{speed: 8}` = time-warp multiplier, and that field had **no reader at all**. Real ratio exactly 1.0 |
| "cannot enter vehicle" | actor was 12.3 m away; refusal was correct behaviour |
| "look direction is reversed" | scene centroid is not monotonic under rotation; one point gave a reversed sign |
| "falls through the stairwell" | probe was 110 m from the stairs; the actor never arrived |
| "camera clips through walls" | three runs disagreed; the metric compared against a hand-copied AABB with no source shown |

## The checks

1. **Frame continuity.** Report the sampled frame-number sequence and its
   gaps. A non-zero gap means the read spans snapshots and proves
   nothing. Throttled debug objects must not be used for
   per-frame/stationarity verdicts.
2. **Source the listener.** Grep where the input is actually bound before
   blaming the handler. In-page comments frequently already document the
   trap.
3. **Trace the field to a reader.** Declaration → write → *reader*. Writes
   with no readers are a dead channel; the probe was measuring nothing.
4. **Check the geometry.** Re-read the actor's coordinates from the same
   snapshot the probe used, and confirm the scenario was actually staged
   before reading a null result as a failure.
5. **Prefer engine-side probes.** Project a static world anchor through
   the game's own view-projection instead of analysing pixels. Validate
   the probe first by confirming it reproduces a value the game already
   publishes (e.g. a screen-space box coordinate) exactly.
6. **Cross-validate the metric.** Run two independent derivations of the
   same verdict and require agreement. A metric whose implementation you
   cannot show is not evidence.

## When measurements disagree

Do not average them. Rank by how directly the method touches the engine,
prefer the method that validates its own probe, and re-run the others only
if the surviving one is ambiguous. Re-measure in a *different* shape
(analytically vs pixel vs projection) — a rerun of the same method adds
nothing.

## Harness self-checks

- **Prove a red verdict is satisfiable before you dispatch a repair for
  it.** Ask: *could any input make this check green?* A verdict computed
  as `max()` over candidate transforms that are all orthogonal (or
  sign-flipped duplicates) of the true quantity is identically zero, so
  no application change can ever flip it — the check is void, not
  red. Cheap proof: substitute a known-good value the app itself
  publishes, compute the metric by hand, and confirm it clears the
  threshold. A structurcturally void check reports a correct app as
  broken forever, so it costs more than no check at all.

- A `Verdict(..., False, ...)` literal, or a frozen "expected missing
  features" list, survives the feature being implemented. If a note says
  "no such branch exists", `grep` the source and count: named constants
  (`KEY_SPACE`, not `"Space"`) make a literal grep return empty and look
  like a missing feature. **The tell that the conclusion is hardcoded
  rather than measured is that the worker's own A/B rows contradict
  it** — a worker reporting "Space missing" on the same run that logged
  `y 0 -> 0.6933, grounded true -> false` is replaying a stored verdict,
  and the evidence is sitting in its own output.

- **Corroborate a described root cause against the artifact that defines
  truth, and check which layer disagrees with which.** When a defect is
  described with a confident mechanism, find the source-of-truth file
  (asset, schema, spec) and read it. The point is not to confirm the
  describer but to reclassify the bug: a collision layer that had been
  wrong for weeks while the visual layer built from the same asset was
  always correct means the defect is older, and lives somewhere else,
  than the description implies — and it tells you which of the two
  layers to trust when they conflict.

- Diff each result file's mtime against the commits it claims to cover
  before quoting it as a baseline.
- A crash is a harness failure, never an app PASS or FAIL. Report the
  category honestly.
- **A child's ambiguous reading is theirs to flag, not yours to launder.**
  When a verifier marks a reading "expected sampling, not a defect" and
  declines to call it clean, keep that caveat in the report. Do not let a
  hedged result become a PASS in your summary — the hedge is the finding.

## "Done" is unreachable while the loop's verdicts are void

An acceptance loop is only as good as the verdicts it consumes. When the
suite carries hardcoded failures and frozen missing-feature tables, the
app-side work can genuinely be complete while every run still reports
red — and each cycle then burns a round of manual triage sorting real
defects from artifacts. **Fixing the harness is not a detour from the
task; it is the next iteration of it.** Declare the application side
complete, then state plainly that the loop cannot terminate until the
checks are trustworthy, and go fix the checks.

## Recording the lesson

When a reading is overturned, write down *why the first reading was
wrong*, not just the correct value. The next session will re-derive the
same tempting mistake from a plausible-looking number otherwise.
