# Per-face feature placement

How to prove a surface feature is on the faces it belongs to, and how to remove
one when the user says the vendor's own view is not what they want.

## The ambiguous middle: a correct mask that the probe still flags

A ray grid fired normal to a side panel also sees past the rear corner arc, so a
face that is genuinely solid can report a small non-zero share of feature hits.
Measured: 14 of 441 rays on the left face, every one at y = 8.46..9.40 — inside
the rear panel's own extent, reached through the corner. The model was correct.

Acting on that number re-tunes a working mask and breaks it. Two ways to tell a
graze from a leak:

1. **Print the hit coordinates.** A leak puts hits spread across the face; a
   graze clusters them at the neighbour's coordinates and in the corner band.
2. **Run the flat-region vertex census** (below). It has no artifacts at all.

## The flat-region vertex census

```python
FLAT_HALF = 8.0        # inside the straight part of a panel, clear of corners
for name in bpy.data.objects.keys():
    if "Grille" not in name:
        continue
    o = bpy.data.objects[name]
    M = o.matrix_world
    side  = sum(1 for v in o.data.vertices if abs((M @ v.co).y) < FLAT_HALF)
    front = sum(1 for v in o.data.vertices if (M @ v.co).y < -FLAT_HALF)
    assert not side, f"{name}: {side} vertices on the side panel"
```

**Never classify a vertex's face by "which coordinate is larger."** `abs(x) >
abs(y)` calls the rear panel's own corner vertices LEFT, because the rear panel
spans the full width including the corners. That mistake turned a correct model
into a 2460-vertex false alarm that looked like a real leak. Restrict by extent
instead.

This census is the check to trust when the ray grid and the reference disagree,
and it is the one to add to a build that must be reproducible in CI — it has no
scene state to hide behind.

## When the user's topology contradicts the vendor's diagram

The vendor's own hardware image showed a perforated band across the bottom of
the front panel; the user asked for perforations on the rear face only. That is
their call, and it is not the model's to argue.

Procedure:

1. **Confirm the conflict once, with evidence.** Magnify the crop and quote a
   pixel statistic (measured: mean luminance drops from 192 to 76 over the
   bottom 8%, with std 61-71 where a flat surface reads 13). One question, with
   the evidence attached.
2. **Take the answer and delete the feature completely** — the hole field, its
   recess, and any support geometry (measured: 12 objects for four underside
   intakes).
3. **Sweep every reference to the deleted feature in the same pass.** It
   survives in four places, and each fails a later gate on its own:
   - the model script's build function and its constants;
   - the verifier's assertion (measured: a check for "exactly four intakes" has
     to become "no intakes", not be deleted quietly);
   - the published copy describing the feature;
   - the render list, whose view names still encode the old layout.
4. **Set the probe threshold for the now-solid face to 0.0**, and keep the
   per-face printout so a partial regression fails loudly.
5. **State the deviation in the report.** The front panel no longer matches the
   published view, by the user's instruction. Say which faces deviate; do not let
   "1:1" stand unqualified over a knowingly altered face.

## Reporting per-face results

Per-face numbers, not a single pass/fail: which faces carry the feature, which
are solid, and the measured share on each. A reader who has to ask "and the
sides?" did not get a usable report, and on this class of task they always ask.
