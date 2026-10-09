"""
bonsai_pot -- a 150 mm cascade pot: an oval unglazed cascade bowl with a
spout lip, two cabriole feet and a small mounded cascade planting.

The pot is a `lathe` of a round cascade profile that is then scaled 0.72 in Y,
which is how a real cascade pot is made (oval, not round) while keeping the
profile a single surface of revolution -- so the wall thickness stays real and
the solid stays watertight. The spout and the two feet are `extrude_profile`
outlines, because they are the two features that are not circular.

The planting is deliberately asymmetric: a cascade pot planted symmetrically
reads as a bowl of moss.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length       = 150.0,
    width        = 108.0,
    height       = 40.0,
    depth        = 30.0,
    foot_height  = 12.0,
)

R_MAJ = 75.0
Y_SCALE = 0.72
WALL = 5.0

# (radius, z) -- outside, over the lip, back down the inside, across the floor.
PROFILE = [
    (0.0, 0.0),
    (40.0, 0.0),
    (46.0, 3.0),
    (62.0, 16.0),
    (72.0, 30.0),
    (R_MAJ, 40.0),
    (R_MAJ, 44.0),
    (R_MAJ - WALL, 44.0),
    (R_MAJ - WALL, 40.0),
    (60.0, 20.0),
    (42.0, 8.0),
    (0.0, 8.0),
]


def _mound(name, centre, radii, mat):
    ob = bkit.uv_sphere(name, 1.0, segments=24, rings=12, centre=centre, mat=mat)
    ob.scale = radii
    return ob


def build():
    clay = bkit.pbr("CascadePotClay", base=(0.290, 0.150, 0.100), rough=0.74)
    clay_d = bkit.pbr("CascadePotClayDark", base=(0.200, 0.098, 0.068), rough=0.78)
    soil = bkit.preset("soil")
    needle = bkit.pbr("CascadeNeedle", base=(0.085, 0.215, 0.075), rough=0.66)
    needle_y = bkit.pbr("CascadeNeedleLight", base=(0.135, 0.290, 0.100), rough=0.68)

    pot = bkit.lathe("Pot", PROFILE, segments=64, mat=clay)
    # An oval cascade pot: the same solid of revolution, drawn in 0.72 in Y.
    # Scaling the object (not the profile) keeps the wall a real wall and the
    # mesh watertight, and the check is on how=Y, which is the true width.
    pot.scale = (1.0, Y_SCALE, 1.0)
    bkit.move(pot, 0.0, 0.0, 0.0)
    bkit.assign_faces_by(pot, clay_d, lambda c, n: c.z / bkit.MM < 12.0)

    # ---- the cascade spout: a lip that reaches out over the front edge.
    # extrude_profile() does not orient normals either, and this outline is
    # wound clockwise as written, so the solid needs a recalc to be positive.
    spout = bkit.extrude_profile("Spout",
                                 [(-30.0, -4.0), (30.0, -4.0), (34.0, -22.0),
                                  (16.0, -30.0), (-16.0, -30.0), (-34.0, -22.0)],
                                 16.0, centre=(0.0, -78.0, 33.0), mat=clay)
    bkit.recalc(spout)

    # ---- two cabriole feet
    for side, sx in enumerate((1.0, -1.0)):
        bkit.extrude_profile("Foot%d" % side,
                             [(-9.0, 0.0), (9.0, 0.0), (7.0, 7.0), (5.0, 12.0),
                              (-5.0, 12.0), (-7.0, 7.0)],
                             13.0, centre=(sx * 40.0, 0.0, 0.0), axis="Y",
                             mat=clay_d)

    # ---- soil surface
    soil_ob = bkit.lathe("Soil", [(0.0, 30.0), (30.0, 29.0), (52.0, 26.0),
                                  (66.0, 21.0)],
                        segments=48, centre=(0.0, 0.0, 0.0), mat=soil)
    bkit.recalc(soil_ob)          # descending profile: normals need orienting
    soil_ob.scale = (1.0, Y_SCALE, 1.0)
    soil_ob.name = "Soil"

    # ---- the planting: five pads, tipped down the front, so the pot reads as
    # a cascade pot rather than as a bowl of moss.
    pads = [((-18.0, 12.0, 40.0), 26.0), ((16.0, -6.0, 42.0), 24.0),
            ((-40.0, -14.0, 36.0), 22.0), ((38.0, 14.0, 36.0), 21.0),
            ((0.0, -26.0, 33.0), 19.0)]
    for i, ((x, y, z), r) in enumerate(pads):
        _mound("Pad%d" % i, (x, y, z), (r, r * 0.8, 12.0),
               needle if i % 2 == 0 else needle_y)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 2 + 1 + len(pads))


CHECKS = [
    dict(name="length",      mm=150.0, tol=1.0, how="bbox_x",   part="Pot"),
    dict(name="width",       mm=108.0, tol=1.0, how="bbox_y",   part="Pot"),
    dict(name="height",      mm=44.0,  tol=1.0, how="bbox_z",   part="Pot"),
    dict(name="soil_surface", mm=30.0, tol=1.0, how="top_z",    part="Soil"),
    dict(name="spout",       mm=68.0,  tol=0.5, how="bbox_x",   part="Spout"),
]
