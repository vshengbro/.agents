# Verifying visuals when the renderer produces no pixels

A visual defect ("the car has only wheels", "the character vanished", "the NPC
hops") is normally settled by looking. In a headless harness that may be
impossible, and the wrong response is to report the fix on the strength of
`cargo test` alone. This is the fallback ladder: what to measure when the
canvas comes back blank, and how to prove the blankness is the environment's
fault rather than your change's.

## 1. Establish whether the blank frame is yours

Do this **before** attributing anything to your fix, because a blank canvas
makes every pixel metric read as "identical" and silently converts an A/B into
a pass.

| Signal | Reading |
|---|---|
| `Page.captureScreenshot` returns an image that is >90% one identical luma value | the canvas was never composited |
| that luma equals the context's `clear_color` | nothing drew after the clear |
| `canvas.toDataURL()` returns an all-blank PNG | the drawing buffer was already presented and discarded — the context lacks `preserveDrawingBuffer` |
| **an unmodified checkout at HEAD captures the same blank image** | **the blankness is environmental** |

That last row is the one that matters. The decisive measurement is the
**pixel difference between your build and HEAD**: two images that are both blank
differ by well under 0.1%, so "my change made it worse" is refuted, while "my
change fixed it" is simply **unmeasurable here**. Say exactly that, and hand the
visual confirmation back rather than substituting a numeric proxy and calling
it verified.

## 2. Substitute a structural channel, and label it as a proxy

The renderer keeps a batch table — one entry per draw group, each with a mesh
index, flags, and an instance count. That table is readable from the debug
channel and it survives a dead canvas, so it can settle "is this thing being
drawn at all" even when nothing can be seen.

- **"The car body is missing"** → read the per-batch instance counts, decompose
  the table into its parts, and compare against the expected composition:
  `2 (ground+water) + static_len + 13 player limbs + N car bodies + 4·W wheel
  batches + pickups`. If the body group is short by exactly the number of
  duplicated shapes, that is the defect and the arithmetic is the evidence.
- **"The character disappeared"** → the limb group is 13 entries; if their
  instance count drops to 0 at a specific event, that event is the cause.
- **Batch *indices* are not identities.** The table is rebuilt whenever the
  streaming centre changes and its size is data-dependent, so the same logical
  group carries a different index in a different part of the city. Assert on
  the **set** (count + membership) and on per-group instance counts. Never
  hardcode an index, never compare an index across runs, and never carry one
  into a new probe — read it in the session you measure in.

A structural proxy is legitimate evidence for *"is it submitted"*. It is **not**
evidence for *"does it look right"*. Those are different claims; deliver both
or deliver only the one you measured.

## 3. When the defect is animation phase, compare against the event

"Looks wrong" motion is measurable without pixels: sample the animated quantity
and the gait/phase driver over many frames of the same action, then compare the
extremum of one against the occurrence of the other.

- Two failures are independent and must be separated: **wrong frequency**
  (oscillating twice as often as the thing it should track) and **wrong phase**
  (right frequency, extrema offset from the event). Fixing the frequency and
  leaving the phase produces motion that is still visibly wrong.
- Quantify the offset in the units of the driver — degrees of gait phase — not
  in "looks better". A fix is proven when the peak sits within a degree or so
  of the event.
- Sample **many frames of a single subject**, and identify the subject by a
  stable per-run key. Averaging across different pedestrians mixes their phases
  and smooths the very signal you are trying to measure.
- **Route the debug read through the same function the renderer calls.** Lift
  the animated quantity into a helper and have both the draw path and the debug
  channel call it. Then the reading *is* the written value, and no future
  refactor can leave the probe reporting a stale or parallel computation.

## 4. Gate the substitute, or you have measured nothing

A structural read is only as valid as the moment you take it. Assert the
**precondition** of the sample — the subject is on screen, the camera is at the
distance you think, the mode is the one under test — at the same instant you
read the value. A sample taken before the subject is loaded, or after the mode
changed, is a valid number for a different scene and will be reported as a
failure of the thing under test.

Pair every structural A/B with a **control that must move**: one input known to
change the quantity, measured through the identical path in the same session.
Without it you cannot separate "the probe read nothing" from "the app did
nothing".