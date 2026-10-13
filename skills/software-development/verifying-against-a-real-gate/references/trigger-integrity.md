# Trigger integrity: proving the thing you poked actually happened

Three failure modes in soak/stress harnesses that all present as a **clean
report**. Each one lets a test suite certify coverage it never had.

## 1. "Fired" is not "completed"

A soak that prints each trigger with a `True`/`False` fired-flag has silently
promoted *dispatch* to *effect*. A visibility override can be accepted and never
suspend the page. A lifecycle call exists on one browser build and is a no-op
stub on the next. Both yield a clean column of `True`s while the half that
matters — **restore, not hide** — never ran.

**Assert a side effect, from a channel independent of the trigger itself:**

| trigger | required side-effect proof |
|---|---|
| suspend / freeze | frame counter **stops advancing** — read twice across a beat, require equality |
| resize | reported canvas dimensions actually **differ** between legs |
| visibility | `document.visibilityState` reads `hidden` *before* any downstream call |

If you cannot make the assertion, the table entry is `fired=unknown` and the run
is a partial run. Say so; do not print a boolean you did not earn.

**Coverage of a cycle means the second half.** Hide/show means *resume*; resize
means *the frame after*; a degenerate size means *recovery*. Proving the
transition shows the harness can cause trouble, not that the system survives it.
Report recovery as its own reading.

An unsupported API is a missing tool, not a missing property — say plainly
"cannot exercise unfreeze in this build" and describe what you did test. A
partial run, honestly labelled, is useful; a partial run presented as complete
is worse than no run.

## 2. A measuring helper that asserts on the normal case breaks on the edge case it exists to probe

Pixel readers usually assume the normal shape: a PNG magic number, a non-empty
buffer, a positive dimension. Probing a **zero-size or degenerate** state
violates exactly that assumption, so the probe crashes **on the case it was
written to examine** — and the crash looks like the defect it was hunting.

Same class as a parser that silently drops malformed records and then reports
the channel as empty: the harness fails to measure, and the absence gets read as
a property of the system.

**A probe targeting a boundary state must return that state, not raise it.**
Three outcomes, always distinct:

1. measured and healthy
2. measured and unhealthy
3. **not measurable in this state** — its own reportable outcome

Never wrap it in a bare `except: continue`: that reproduces the silent-drop
failure and leaves zero evidence. If a 0-sized surface legitimately cannot be
sampled, report "not rasterizable at WxH" and then **keep sampling** — whether
output returns once the surface is drawable again is the property under test.

## 3. A gate that stops reporting is not a gate that passed

Some runtimes cap diagnostics per device/session and announce the cap in the
log (`too many warnings, no more warnings will be reported`). Everything after
that line is silence, indistinguishable from success — and it retroactively
invalidates any earlier "clean run" claim from the same session, because you
cannot tell where the cap landed.

**Verify an absence from the start of the run, or count explicitly.** Surface a
monotonic violation counter in the channel the application already reports
per-frame state, so the number survives log truncation. The claim is "zero
violations over N frames", never "no errors appeared toward the end".

Same rule for any truncated, rotated, or sampled log: prove the sample covered
the region you are calling quiet.

## Dispatching these checks

When briefing a worker on a soak or stress task, require a per-trigger table
with three columns — `fired` (call accepted), `effective` (side effect observed),
`recovered` (state returned to healthy) — and state that a missing `effective`
or `recovered` must be reported as such rather than omitted. Silence in the
table reads as a pass to whoever reads the summary.
