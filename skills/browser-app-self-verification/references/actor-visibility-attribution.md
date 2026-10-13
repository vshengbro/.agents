# Proving an object is actually rasterised

Depth for the class of bug where an object's state, transform, and bounding
data are all correct and it is still absent from the frame. Reads of the debug
payload, mesh tables, and projection boxes all say "should be visible"; only
the pixels disagree. Screenshots and vision cannot settle this — a vision model
describes what it thinks it saw, and a whole-frame pixel diff is swamped by
everything else in the scene.

The method is a controlled pixel A/B with a control experiment in front of it.

## Order of elimination: cheapest disqualifier first

Each step below is a whole-class elimination, so run them in this order and stop
when one fires. The first two cost one page load; the pixel work costs three.

| Reading | Disqualified when | What it means |
|---|---|---|
| per-part instance count | any part has `n == 0` | the instance table was never written for that part, or the batch index is out of range |
| per-part model-matrix translation | `n > 0` but the translation is not the object's position | the transform is wrong — a pivot that did not follow the object, a scale of zero, a stale matrix |
| CPU asset count vs GPU asset table length | the two differ, or the OOB counter is non-zero | see the silent-return class below |
| projected screen box | the box is off-canvas, or the object fills most of the frame | culled, or a scale/transform blow-up — a full-frame box is a bug, not a close-up |
| pixel A/B | the box is empty under the control below | genuine rendering-path problem; go to the draw call |

The first two rows are why the payload should export **every** part, not the
first one. A single exported matrix is consistent with both "one part is
broken" and "every part is fine", so it cannot discriminate. This is the same
shape as the projection-box trap above it: a field that is plausible in the
broken case carries no evidence.

## The silent-return class: a CPU index into a GPU table

A batched renderer typically holds a CPU asset list and uploads it to the GPU
once. Draw calls then index the GPU list with a per-batch `mesh_index`. When
that index is out of range the draw path commonly returns early — **no
triangles, no exception, no warning** — and the object vanishes while every
piece of its state still looks correct.

Two counts settle it:

- CPU asset count vs GPU table length must be **exactly equal**; one extra or
  one missing upload shifts every later index by one, and the symptom is
  "some objects render, the rest do not" rather than a total failure.
- A per-draw out-of-range counter. Non-zero means the tables are already
  misaligned; zero means index range is exonerated and the problem is
  downstream (vertex data, culling, depth, or the instance table).

A non-zero draw-call count at the expected frame rate is the evidence that the
path is alive; combine it with a zero-pixel reading and **the read is what is
wrong** — retake it inside rAF before reporting a regression.

## Validate the debug toggle before trusting its zero

A `?hide=`-style parameter is the cheapest way to A/B the render path, and it
is silent when it is inert. **Before concluding anything from a zero-pixel
result, prove the mechanism removes pixels**: run it against a target known to
be on screen. If hiding the suspect and hiding *everything* change the same
number of pixels, the toggle is swamped and the experiment decides nothing.

Then calibrate the floor. Two snapshots of a live scene differ by a few
hundred pixels from animation alone — clouds, peds, cars, the clock, camera
shake, antialiasing on moving edges. That is the floor, and a difference below
it is not evidence of anything.

```
whole-frame changed = N  ->  below the floor, inconclusive
boxed changed        = 0  ->  conclusive ONLY if the floor is small
```

`scripts/pixel_ab.py` does the decode, the whole-frame and boxed diff, and the
floor call in one command.

## Invert the A/B when the floor is too high

Hiding the suspect against a live background is the weak form. The strong form
is to **hide everything except the suspect**: the object's own box is then the
only place a pixel of it can appear, so any non-zero count proves it and zero is
conclusive. A control that hides all batches must remove far more pixels than
one that hides a single batch — if it does not, the toggle is inert and the
result is void.

Two conditions for the inversion to work:

- **The toggle is read every frame.** A per-frame read of `location.search`
  means the list can be flipped from JS mid-session with no reload; a
  load-time read costs a full boot per condition. Check which one the app has
  before planning the run.
- **The world is nearly frozen.** Drive the simulation's time scale to a
  fraction of normal, then let it settle, so the two conditions differ only by
  the toggle. At full speed the object itself has moved between the two
  snapshots and the diff measures motion, not visibility.

## Scope the diff to the object box, from the engine

The box should come from the engine's own projection, not from a script constant
— a hard-coded box drifts the moment the camera or projection changes, and the
failure then reads as "the object is not drawn" when it was measured in the
wrong rectangle. Box height as a fraction of canvas height is also a cheap
independent check: an object occupying most of the frame is a transform
blow-up, and one at 45% or beyond is a distinct verdict from "not drawn".

## Report three verdicts, not one boolean

"Invisible" conflates three different bugs with three different fixes. Report
separately:

1. **not in the instance table** — the sync/write path, or a batch index
2. **in the table with a wrong transform** — the model matrix or its pivot
3. **correct in the table and on screen but occluded, sub-pixel, or behind
   another object** — depth, resolution scale, draw order

A single `charVisible: true` derived from a projection box proves none of them.
