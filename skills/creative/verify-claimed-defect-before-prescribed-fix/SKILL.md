---
name: verify-claimed-defect-before-prescribed-fix
description: Use when an audit prescribes a fix. Measure first.
license: MIT
---

# Verify a claimed defect before applying a prescribed fix

An audit's finding and its prescribed remedy are **two separate claims**. Both
can be wrong, and when they are, the prescribed edit makes the asset strictly
worse. Measure first, then fix the measured cause.

## 1. Verify the defect exists

Audits get defects wrong in both directions. Do not "fix" a non-defect.

- **Measure it, don't read the sign.** In vice-city-web's building kit the
  audit reported "window reveal is sub-pixel at 40 m". The real defect was an
  inverted sign: the glass pane was placed at `y_wall - sgn*GLASS_SET`,
  landing 15 mm *inside* a solid wall. Raycasting from the real camera showed
  the pane was **0.0% self-visible** — not sub-pixel, entirely invisible — and
  deleting every glass part moved only 0.2-0.6% of pixels. Raising the
  constant as prescribed would have buried the windows deeper.
- **The prescribed check can encode the bug.** `check_window_recess.py`
  asserted `glass_y > wall_y` as its invariant and its docstring presented
  that as the fix for a sign error. It was reporting a broken asset as
  healthy. When a checker disagrees with a render, suspect the checker.

## 2. Verify the prescribed fix fixes it

Apply it, then re-measure the thing the defect was about — not just the
parameter. In the same repo, a prescribed fix (`TRACK_R 0.13 -> 0.20`) landed
cleanly and changed the measured quantity (band 0.39 -> 0.60 m, now thicker
than the wheels) while the actual symptom ("wheels read as floating blobs with
no continuous track") was **unchanged**: the real cause was an axis swap at
the `tube()` call putting the band crosswise through the hull.

**Evidence ladder, cheapest first:** static measure (extents, signed volume,
degenerate-triangle count) -> ablation (delete the part, diff the pixels) ->
raycast from the real camera -> render + look. A render alone cannot tell you
*why*; a measurement alone cannot tell you if it looks right.

## 3. Trust nothing you did not measure yourself

Subagent reports are self-reports. Two workers editing one file concurrently
produced a commit whose message described only one of the two changes, and
each claimed the other's fix. Re-derive the facts from the artifact.

## Pitfalls

- **Never iterate blind on a shape/winding error.** Brute-force the finite
  space and pick the winner: all four `cap_start_flip`/`cap_end_flip`
  combinations printed a negative signed volume, which proved the *side walls*
  were reversed and no cap flag could fix it. Four cheap prints beat four
  full Blender rebuilds.
- **Isolate the failing component.** "3 of 5 shells inverted" means 3 specific
  primitives are wrong. Group faces into welded components and report each
  one's signed volume; the offenders were the 3 batten quads, not the 2 sails.
- **Two coincident planes are still zero-thickness.** A "double-sided" decal
  built from two coplanar triangles vanishes edge-on. Give it thickness.
- **Ablation scripts are a no-op until they prove they removed something.**
  Assert the removal count and raise if it does not match.