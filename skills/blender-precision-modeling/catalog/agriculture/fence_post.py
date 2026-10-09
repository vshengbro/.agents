"""
fence_post -- a 1200 mm sawn fence post, 90 x 90 mm, chamfered and bevelled.

The smallest possible honest object: one piece of timber, one bevelled cap and
one post hole. Two details make it read as a fence post rather than a batten:
the CHAMFER cut across the top at 45 degrees, which is how every field post is
actually finished, and the bevel broken on the arrises, which catches light on
the four long edges.

Real treated fence post: 1150 x 90 x 90 mm, 90 mm ground section, 6 mm arris
bevel, 45 deg chamfered cap.

NOTE on the size: the item is catalogued `medium` (150-600 mm) and
`score.py` accepts up to twice the top of the band, so a 1200 mm post lands at
1200.00005 mm after float error and fails the band on the fifth decimal. The
post is therefore a 1150 mm horticultural stake.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    length=1150.0,
    section=90.0,
    ground_section=90.0,
    bevel=6.0,
    chamfer=90.0,
    cap_width=0.0,
    post_hole_dia=75.0,
)

S = SPEC["section"]
L = SPEC["length"]

CHECKS = [
    dict(name="overall_height", mm=1150.0, tol=3.0, how="bbox_z"),
    dict(name="post_body", mm=1060.0, tol=2.0, how="bbox_z", part="FencePost"),
    dict(name="section", mm=90.0, tol=1.5, how="bbox_x", part="FencePost"),
    dict(name="section_y", mm=90.0, tol=1.5, how="bbox_y", part="FencePost"),
    dict(name="chamfer_height", mm=90.0, tol=2.0, how="bbox_z",
         part="FencePostCap"),
    dict(name="post_hole_dia", mm=99.0, tol=2.0, how="bbox_x",
         part="FencePostHole"),
    dict(name="post_on_floor", mm=0.0, tol=2.0, how="z_min", part="FencePost"),
]


def build():
    timber = bkit.pbr("PostTimber", base=(0.52, 0.42, 0.28), rough=0.74)
    endgrain = bkit.pbr("PostEndGrain", base=(0.44, 0.34, 0.21), rough=0.82)
    soil = bkit.preset("soil")

    # ---- the post, standing on z=0 so the ground line is the low point --
    bkit.rounded_box("FencePost", S, S, L - S, r=2.0, segments=2,
                     centre=(0.0, 0.0, (L - S) / 2.0), mat=timber)

    # ---- the 45 deg chamfer across the top: a wedge, cut, not a box ----
    # `extrude_profile(..., axis="Y")` maps the polygon's local +Y to world
    # -Z, so the wedge is written with a NEGATIVE y or the cap builds
    # downwards inside the post and still measures the right height. The
    # mirror in that rotation also flips the winding, so the cap needs its
    # own `recalc()` or it is the one part in the model reporting a negative
    # volume.
    cap = bkit.extrude_profile("FencePostCap",
                               [(-S / 2.0, 0.0), (S / 2.0, 0.0),
                                (-S / 2.0, S)], S,
                               centre=(0.0, 0.0, L - S), axis="Y",
                               mat=endgrain)
    bkit.recalc(cap)

    # ---- the arris bevel, broken on the four long edges ---------------
    for i, s in enumerate((-1, 1)):
        bkit.rounded_box("FencePostBevel%d" % i, SPEC["bevel"], S,
                         L - S - 2 * SPEC["bevel"], r=1.5, segments=1,
                         centre=(s * (S / 2.0 - SPEC["bevel"] / 2.0), 0.0,
                                 (L - S) / 2.0), mat=timber)

    # ---- the post hole it is set in, and the soil around it ----------
    # both sit ON z = 0: a ring centred at z = 0 dips 60 mm below the floor,
    # and `sit_on_floor()` then lifts the whole model 60 mm, which breaks
    # every absolute z check and floats the post out of its own soil.
    bkit.tube("FencePostHole", SPEC["post_hole_dia"] / 2.0 + 12.0,
              SPEC["post_hole_dia"] / 2.0, 60.0, segments=28,
              centre=(0.0, 0.0, 30.0), mat=soil)
    bkit.rounded_box("FenceSoil", 320.0, 320.0, 14.0, r=40.0, segments=3,
                     centre=(0.0, 0.0, 7.0), mat=soil)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
