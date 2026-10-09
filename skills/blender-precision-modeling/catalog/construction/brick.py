"""
brick -- a standard stretcher brick, 215 x 102.5 x 65 mm, with its half-brick
starter and the bed joint between them.

Real UK brick: 215 mm long, 102.5 mm high, 65 mm deep, on a 10 mm bed joint.
The frog is what makes a brick read as a brick rather than a box -- two pockets
recessed 20 mm into the bed face, which is why the hollow core of a brick does
not run its full length.

Two bricks, not a wall. The catalog classifies this item `small` (30..150 mm,
scored with a 2x leeway), and a 24-brick panel is 1340 mm long -- three and a
half times outside the band the item is declared in. So this models what the
item is: ONE brick, plus the HALF BRICK STARTER that goes on top of it. That
is still the bond -- a half brick spanning the joint of two whole bricks is the
first pair of courses of any stretcher-bond wall -- and it comes to 215 mm,
inside the band.

Both halves come from one `lay_out` on the real brick width plus the real
joint, so the half brick is genuinely half and the joint is genuinely 10 mm.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    brick_length=215.0,
    brick_height=102.5,
    brick_thickness=65.0,
    frog_depth=20.0,
    joint=10.0,
    half_brick=True,
)

BL = SPEC["brick_length"]
BH = SPEC["brick_height"]
BT = SPEC["brick_thickness"]
J = SPEC["joint"]
FD = SPEC["frog_depth"]

# a whole brick, then a half brick on top of it: the half sits ON the bed joint
# The two courses are STACKED, so the pack is as wide as a whole brick
# (215 mm) and as tall as two courses plus the joint (215 mm).
STACK_W = BL
STACK_H = 2.0 * BH + J
# the half brick is centred over the whole one, which is what a starter does
LAYOUT = [BL, BL / 2.0]

CHECKS = [
    dict(name="brick_length", mm=215.0, tol=0.5, how="bbox_x", part="Brick0"),
    dict(name="brick_height", mm=102.5, tol=0.5, how="bbox_z", part="Brick0"),
    dict(name="brick_thickness", mm=65.0, tol=0.5, how="bbox_y", part="Brick0"),
    dict(name="half_brick_length", mm=107.5, tol=1.0, how="bbox_x",
         part="HalfBrick"),
    dict(name="stack_height", mm=215.0, tol=2.0, how="bbox_z", part=None),
    dict(name="stack_width", mm=215.0, tol=2.0, how="bbox_x", part=None),
]


def build():
    clay = bkit.pbr("BrickClay", base=(0.55, 0.26, 0.17), rough=0.72)
    mortar = bkit.pbr("MortarBed", base=(0.60, 0.59, 0.55), rough=0.88)

    # ---- one frogged brick, origin-centred so a half is a half ------
    brick = bkit.rounded_box("Brick0", BL, BT, BH, r=3.0, segments=2,
                             centre=(0.0, 0.0, 0.0), mat=clay)
    # two frog pockets, each spanning half the brick length
    fw = BL / 2.0 - 20.0
    fl = (BT - 30.0) / 2.0
    for sx in (-1, 1):
        cut = bkit.rounded_box("_frog", fw, fl, FD + 8.0, r=4.0, segments=2,
                              centre=(sx * (BL / 4.0), 0.0, BH / 2.0 - FD / 2.0))
        bkit.boolean(brick, cut, "DIFFERENCE")
    bkit.recalc(brick)
    bkit.centre_origin(brick)

    # ---- the half-brick starter on top ------------------------------
    # The starter spans the joint of two whole bricks: it is centred over the
    # brick below and sits ONE COURSE UP, on the 10 mm bed joint. Scaling by
    # w/BL has to be assigned before it is applied -- see bpy_scale below.
    z = BH + J + BH / 2.0
    bkit.duplicate(brick, "HalfBrick", offset_mm=(0.0, 0.0, z))
    bpy_scale("HalfBrick", (BL / 2.0 / BL, 1.0, 1.0))
    bkit.move(brick, 0.0, 0.0, BH / 2.0)

    # ---- the bed joint between the two courses ----------------------
    bkit.box("MortarBed", STACK_W, BT - 2.0, J,
             centre=(0.0, 0.0, BH + J / 2.0), mat=mortar)

    return dict(spec=SPEC, parts=3, bond="stretcher, half-brick starter",
                note="single brick + starter; catalog class is 'small'")


def bpy_scale(name, factors):
    """Set a scale on the copy and bake it into its mesh data.

    `duplicate` COPIES the source's rotation and SETS its location, so the source
    must be origin-centred first or the half brick arrives turned. And a scale
    has to be ASSIGNED before it can be applied -- applying a scale that was
    never set is a no-op, which is how the half brick ends up 215 mm long.
    """
    import bpy
    ob = bpy.data.objects.get(name)
    ob.scale = factors
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.select_set(False)
    return ob