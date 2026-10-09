"""
human_hand_skeleton -- 27 bones: 8 carpals on a 2x4 grid, 5 metacarpals on a
measured pitch, and 14 phalanges.

The easiest object in the human domain, because a skeleton is nothing but
repeated elements with a correct count, and that is precisely what the layout
helpers are for:

  * the carpals come from `bkit.grid_positions(cols=2, rows=4)`, because a
    carpus really is a 2 x 4 block of small bones;
  * the metacarpal heads come from `bkit.lay_out` over the real head widths
    (21, 22, 21, 18 mm) with a 4 mm gap;
  * the phalanges are per-digit sweeps whose lengths are the phalanx table.

Every bone is its own closed solid. Overlapping carpals are fine -- they are
separate shells, not a boolean -- and the whole assembly stays manifold.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    bones        = 27,
    carpals      = 8,
    metacarpals  = 5,
    phalanges    = 14,
    hand_length  = 185.0,
)

# metacarpal head width, then the three phalanx lengths per digit
DIGITS = [(21.0, 45.0, 26.0, 20.0), (22.0, 48.0, 28.0, 19.0),
          (21.0, 44.0, 27.0, 19.0), (18.0, 33.0, 21.0, 17.0)]
THUMB = (32.0, 26.0)


def _bone(name, a, b, r0, r1, mat, steps=14):
    """One long bone: a closed tapered solid between two points."""
    a, b = Vector(a), Vector(b)
    d = (b - a)
    L = d.length or 1.0
    d = d / L
    ob = bkit.cylinder(name, r0, L, segments=steps, r2=r1, mat=mat)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    ob.location = bkit.v(*tuple((a + b) / 2.0))
    return ob


def build():
    bone = bkit.pbr("Bone", base=(0.840, 0.795, 0.690), rough=0.44)
    bone_m = bkit.pbr("BoneMarrow", base=(0.640, 0.480, 0.400), rough=0.62)
    joint = bkit.pbr("Cartilage", base=(0.720, 0.730, 0.700), rough=0.38)

    # ---- carpals: a real 2 x 4 block, from the station grid
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=4,
                                                   pitch_x=17.0, pitch_y=19.0)):
        bkit.uv_sphere("Carpal%d" % i, 1.0, segments=16, rings=8,
                       centre=(x, 0.0, 176.0 + y), mat=bone).scale = \
            (8.0, 9.0, 8.0)

    # ---- metacarpals: heads on a measured pitch, fanning from the carpus
    xs = [x for (x, w) in bkit.lay_out([d[0] for d in DIGITS], gap=4.0)]
    for i, x in enumerate(xs):
        w = DIGITS[i][0]
        _bone("Metacarpal%d" % i, (x * 0.55, 0.0, 168.0),
              (x, 0.0, 168.0 - (88.0 + 0.0)), 5.0, 4.2, bone)
        bkit.uv_sphere("McpHead%d" % i, 1.0, segments=16, rings=8,
                       centre=(x, 0.0, 80.0), mat=joint).scale = \
            (w / 2.0, w / 2.0, w / 2.0)

    # ---- phalanges: three per finger, laid out down the digit
    for i, x in enumerate(xs):
        z = 80.0
        for (j, L) in enumerate(DIGITS[i][1:]):
            _bone("Phalanx%d_%d" % (i, j), (x, 0.0, z), (x, 0.0, z - L),
                  4.4 - 0.7 * j, 3.7 - 0.7 * j, bone)
            bkit.uv_sphere("IpJoint%d_%d" % (i, j), 1.0, segments=12, rings=6,
                           centre=(x, 0.0, z), mat=joint).scale = \
                (4.6 - 0.7 * j, 4.6 - 0.7 * j, 3.2)
            z -= L

    # ---- thumb: one metacarpal and two phalanges, rotated out of the plane
    tb = [(0.0, 0.0, 150.0), (30.0, -14.0, 112.0)]
    _bone("Metacarpal4", tb[0], tb[1], 5.4, 4.6, bone)
    for j, L in enumerate(THUMB):
        a = tb[1] if j == 0 else prev
        b = (a[0] + 16.0 + 6.0 * j, a[1] - 20.0, a[2] - (L - 10.0))
        _bone("Phalanx4_%d" % j, a, b, 4.6 - 0.8 * j, 3.9 - 0.8 * j, bone)
        prev = b
    bkit.uv_sphere("ThumbJoint", 1.0, segments=12, rings=6,
                   centre=tb[1], mat=joint).scale = (5.0, 5.0, 3.4)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8 + 10 + 20 + 4)


CHECKS = [
    dict(name="hand_length",  mm=227.5, tol=1.14, how="top_z"),
    # A single metacarpal head is 21 mm across, not a knuckle ROW: the row is
    # five of them, so its span is a scene measurement with no `part`.
    dict(name="knuckle_row",  mm=117.3,  tol=0.59, how="bbox_x"),
    dict(name="carpal_size",  mm=18.0,  tol=0.5, how="diameter", part="Carpal0"),
    dict(name="middle_phalanx", mm=28.0, tol=0.6, how="longest",
         part="Phalanx1_1"),
]
