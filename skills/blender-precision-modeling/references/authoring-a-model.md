# Authoring a model

A model is one Python file at `catalog/<domain>/<item_id>.py` that defines
`SPEC`, optionally `CHECKS`, and `build()`. Nothing else. The harness supplies
the scene reset, the studio, the camera, the renders and the report, so two
models can never disagree about how they were photographed.

## The contract

```python
"""coffee_mug -- cylindrical ceramic mug with a real wall thickness."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
import bkit

SPEC = dict(body_diameter=84.0, body_height=98.0, wall=4.0)   # millimetres

CHECKS = [
    dict(name="body_diameter", mm=84.0, tol=0.3, how="diameter", part="MugBody"),
    dict(name="body_height",   mm=98.0, tol=0.3, how="bbox_z",   part="MugBody"),
]

def build():
    ...
    return dict(spec=SPEC, parts=2)
```

`build()` returns a dict that is merged into the report. Returning `spec=SPEC`
keeps the declared dimensions attached to the result.

## Rules that are not negotiable

**Millimetres, always.** `SPEC` is mm. Recipe arguments are mm. `bkit.v()`
converts to metres exactly once. If you find yourself multiplying by `0.001`
in your own script, you are bypassing the safety net.

**Name every part.** `bkit.health()` reports per-part problems; an unnamed part
makes the failure impossible to locate.

**Declare CHECKS with a `part`.** `how="bbox_z"` on the whole assembly will
happily confirm a sub-part height against the bounding box of something that
includes a handle. Point the check at the object that actually owns the
dimension.

**Prefer one solid over many shells.** A second object that sits just inside
the first z-fights with it and doubles the non-manifold count. For a different
colour inside a vessel, use `bkit.assign_faces_by()` on one watertight body.

**Close every solid.** After `extrude_profile`, `lathe`, `loft`, `arc_torus` or
a boolean, the result must report `healthy`. If it does not, call `recalc()`
(inward normals) and `weld()` (coincident vertices at an axis or seam) before
looking anywhere else.

**Compute repeated layout.** See `recipes.md`. Hand-placed port and hole
coordinates are the single most common cause of a destroyed boolean.

**Rotate with `bkit.rotate_about()`, never `rotation_euler`.**

```python
bkit.rotate_about(leg, deg_z=25.0)     # turns the leg on its own axis
ob.rotation_euler = (0, 0, radians(25))  # turns it around the SCENE origin
```

`bkit` leaves each object's origin at the world origin — deliberately, so that
`move()`, `array_linear(world=True)` and the measurement helpers all work in one
coordinate space. Several recipes bake `centre` into vertex data rather than
setting `location`, so the object's origin is nowhere near the part.

That makes `rotation_euler` a trap whose damage scales with the model. A part
200 mm off centre is thrown 200 mm and nobody notices; the same line on a clock
tower hand authored 24 m up throws the hand 22 m across the scene. A lint over
the shipped catalog found **120 of 717 models visibly disfigured this way**,
the worst displacing a knife blade by 127% of the knife's entire size — and
every one of them still passed the objective gate, because each part is
individually clean.

`rotate_about()` turns the part about its own mesh centroid, bakes the result
into the mesh and leaves `rotation_euler` at zero, so a later `move()` cannot
compose with a leftover rotation.

`rotation_euler` is still correct for a part authored **at** the world origin,
which is why this is a helper rather than a ban. If you use it, the part must
be near (0, 0, 0).

Check your model before you ship it:

```sh
blender -b --factory-startup --python scripts/lint_rotation.py -- <your model>
```

`ROTPIVOT` lines list the offending objects and how far the rotation actually
moves them. Anything that moves a part by more than about 1% of the model's own
size is a defect, not a style choice.

## Choosing recipes

| The object is | Start from |
|---|---|
| a vessel, bottle, wheel, knob, lamp shade | `lathe` on a closed profile |
| anything whose cross-section changes along its length | `loft` over sections |
| a box with soft edges | `rounded_box`, not `box` + guess |
| a curved panel with a hole pattern | `perforated_panel` |
| a handle, hook, arch | `arc_torus` |
| a bolt, screw, threaded rod | `thread` |
| teeth on a wheel | `gear`, or an explicit involute-ish ring |
| something organic | `superellipse_section` + `loft`, then subdivision |


## What `measure()` can express

`how` is either a **size** or a **coordinate**. Confusing the two is the single
most common cause of a failing `CHECKS` entry: an agent measures a sub-part's
whole extent against the whole-assembly bounding box, and the number never
matches. One remediation pass fixed 14 models that way.

| sizes | coordinates |
|---|---|
| `bbox_x` `bbox_y` `bbox_z` | `x_min` `x_max` `y_min` `y_max` |
| `bbox_max` `bbox_min` | `z_min` `z_max` (also `bottom_z` / `top_z`) |
| `diameter` `longest` | |

`top_z` is what you want for "how high is the collar above the floor" — no bbox
size can express a coordinate. And **always pass `part`** when the dimension
describes a sub-component; otherwise you are measuring the whole assembly and
naming it something else.

When a check is fighting the model, decide which side is wrong before moving
anything:

- the check measures a sub-part against the assembly, or against the wrong axis
  -> repoint the `part` and `how` (this is usually right)
- the model contradicts a dimension you are confident about -> fix the geometry
- the SPEC value simply does not describe what you built -> correct the SPEC

**Never** fix a mismatch by loosening `tol`. That hides the difference instead
of resolving it.

### Height is measured after seating, not before

`top_z` / `z_max` / `z_min` are read **after** `sit_on_floor()` has raised the
assembly so its lowest point rests on z=0. A deck or mast height declared in the
build frame is therefore short by exactly the seat lift. Six checks across three
vessels died of this, with deltas that matched their seat offsets precisely
(+420.6, +65, +10).

Two ways to be correct: build the part at its final seated height so the lift is
zero, or declare the coordinate in the seated frame and verify it against a
re-render rather than against the build script.

### Rotors need a swept diameter, not a bounding box

A three-blade propeller at 120 degree spacing spans 1.5R x 1.73R -- its bounding
box never reaches 2R, and `diameter` reports the axial chord instead. Declare a
rotor with a swept mode, which measures true distance from the rotor axis:

```python
dict(name="propeller_diameter", mm=360.0, tol=2.0, how="swept_z", part="Propeller")
```

`measure()` also accepts `swept_x`, `swept_y` and `swept_xy` (the bounding sphere
diameter, useful for globular parts).

**`swept_*` returns a swept RADIUS** -- the greatest distance from the parent's
bbox-centre axis to any vertex -- so a rotor whose blades reach R reads R, and
its diameter is twice that. Declare `mm` accordingly: a 360 mm propeller has a
swept radius of 180. `swept_xy` is the bounding-sphere radius and means the same
thing, so the two are directly comparable.

**`swept_*` sweeps about the parent's bounding-box centre.** For a rotor with
four or more symmetrically spaced blades that centre is the hub and the value is
the true diameter. For three blades it is offset, because three blades are not
symmetric about their own bounding box — arrange blades symmetrically, or name a
hub object in `part`. What the mode always gets right, and a bounding box never
does, is parts spread around the axis: `bbox_x`/`bbox_y` report the axial
envelope, not the rotor.


## Before you call it done

1. `scripts/blrun.py` exits 0 and `report.json` says `status: ok`.
2. `nonmanifold == 0`, `loose_verts == 0`, `negative_volume == 0`.
3. Every `CHECKS` entry is `ok: true`.
4. You have looked at all six renders.
