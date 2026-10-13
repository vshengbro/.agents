# Low frame rate turns sampled behaviour into different behaviour

Depth for the case where a headless run advances a fixed number of substeps
per rendered frame. The app is not broken; the *sampling rate* has changed
which states exist, so a design that is correct at 60 Hz produces failures,
passes, and wrong answers at 3 Hz.

> **Companion:** `headless-sim-time-and-movement-probes.md` covers measuring
> the throttle and polling on displacement. This file covers what the reduced
> rate *changes about the app's behaviour*, and the two determinism failures
> it creates that look like ordinary bugs.

## The mechanism

A clamped delta (`dt.min(fixed * k)`) makes each frame advance a fixed slice
of simulated time. Per-frame displacement becomes `speed * clamped_dt`,
independent of the requested rate:

```
walk speed 4.6 m/s, clamp 0.0667 s   ->  0.307 m per frame
```

At 60 Hz the actor takes ~160 frames to cross 50 m and lands on each stair
tread. At 3 Hz it takes ~5 frames, and **0.307 m per step against a 0.305 m
tread rise is the failure boundary**: an actor that steps 0.31 m/frame can
still walk up, and one that steps 0.40 m/frame skips treads and falls back to
the floor. Neither run is wrong; the same code passes at one rate and fails at
the other.

**Rule: any geometry the harness must cross is frame-rate dependent.** Stairs,
kerbs, low ledges, gaps, ramps, ledges you step onto — all of them have a
per-frame step size, and a sub-step test is a *timestep* test wearing a
geometry costume. When such a test fails only in headless, compute the two
numbers before touching the code: `speed * clamped_dt` and the rise/width of
the obstacle. If the first exceeds the second, you have found the mechanism
and the fix belongs in the app (a swept support query, or interpolation across
the step), not in the harness.

## Determinism failure 1: a pinned actor and an unseeded world

Three runs of "stand still in the room and sweep the camera" produced three
different pictures of the same room, and the disagreement was about
*geometry*, not about the camera. The cause: **the interior collision volume
is built up along the path walked**, so a harness that teleports into a room
and samples immediately queries a world that is only partly built — and the
neighbouring probe hits the *next* building over. An actor that was walked in
along the proper route gets a different (correct) shell.

**Rule: build the world along the path before querying it.** Walk the legs,
then sweep. And when a geometric verdict matters, compute the bounds twice by
independent paths and require agreement:

| path | how it gets the bounds |
|---|---|
| transcribed | hand-copied from source constants — a *hypothesis* |
| measured | the app's own published values at runtime |

Two paths agreeing is evidence; one path agreeing with itself is not. This
also explains an "actor escaped the building" verdict that turned out to be a
threshold anchored to a waypoint rather than to a wall — the actor was inside
the shell the whole time.

## Determinism failure 2: a state that is a function of frame history

Some state is not a function of position at all, and no single-frame probe can
see it:

- a support-height cache, a "last grounded" latch, a "was occluded recently"
  timer — each reads the *previous* frame, so a frame that crosses a boundary
  produces a value no steady state would;
- a smoothed camera distance that is clamped toward a target over time, so
  the same input yields a different distance depending on how long it has been
  held;
- a modal panel whose `display` is toggled rather than set.

**Rule: assert the trajectory, not the endpoint.** Sample every frame and
keep the series, then check the properties a trajectory must have —
monotonic where it must be monotone, no overshoot, convergence to a target,
and contiguity of the frame indices. A single-value read of a frame-history
state is a sample from an unknown distribution.

```
frames 314..343  frame_gap=[0]  contiguous
d = 2.536, 0.300, 0.300, 0.300, 2.200, 2.200
```

That series is the finding: three frames frozen then a jump is not
convergence, and it is invisible in a before/after pair. Report the shape.

## When to accept the low-frame-rate result

Some behaviours genuinely cannot be observed at 3 Hz, and the honest output is
INCONCLUSIVE, not FAIL:

| claim | honest verdict at low fps |
|---|---|
| a sub-frame collision was resolved | test it at a rate where the step is smaller than the obstacle, or as a unit test |
| smooth camera damping / easing | report the trajectory shape, not a convergence value |
| anything gated on a "recently" window | drive the state directly, or widen the window for the probe and say so |

Say which of these applied. The cost of filing the low-fps result as an app
defect is a fix aimed at code that is correct, plus a retraction later.
