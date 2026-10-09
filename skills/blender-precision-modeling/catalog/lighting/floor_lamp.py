"""
floor_lamp -- tall arc floor lamp: wide weighted base, slim stem, a visible
gooseneck and a wide drum shade.

The proportions are the whole job, and two earlier attempts got them wrong in
instructive ways:

* A quarter arc centred ON THE STEM AXIS produces an arm that leaves the column
  horizontally and ends pointing straight up -- a spike above the lamp with the
  shade nowhere near it. The arc must be centred at (arc_radius, 0, stem_top):
  a = 180 then lands on the column axis and a = 90 lands out at the arc's reach
  with a horizontal tangent.
* If the arc's radius is SMALLER than the shade's diameter, the shade swallows
  the entire arm and the lamp renders as a shade balanced on a pole. The arm
  has to be wider than the shade it carries, and the shade hangs from a short
  drop at the arm's end rather than overlapping it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    base_diameter=320.0,
    base_height=34.0,
    stem_diameter=26.0,
    stem_height=1300.0,
    arc_radius=520.0,        # must exceed shade_diameter / 2 to stay visible
    arc_tube_diameter=24.0,
    drop_length=74.0,        # hanger between the arm end and the shade
    shade_diameter=380.0,
    shade_height=250.0,
    overall_height=1890.0,
)

ARC_R = SPEC["arc_radius"]


def _shell(name, loop_profile, centre, mat, segments=96):
    """Lathe a CLOSED profile loop into a walled shell."""
    prof = list(loop_profile) + [loop_profile[0]]
    ob = bkit.lathe(name, prof, segments=segments, centre=centre,
                    mat=mat, cap_ends=False)
    bkit.recalc(ob)
    return ob


def build():
    steel = bkit.preset("brushed_metal")
    cast = bkit.preset("dark_metal")
    linen = bkit.pbr("ShadeLinen", base=(0.88, 0.85, 0.76), rough=0.80)
    glow = bkit.pbr("BulbGlow", base=(1.0, 0.93, 0.78), rough=0.30,
                    emission=(1.0, 0.89, 0.70), emission_strength=7.0)

    base_h = SPEC["base_height"]
    stem_h = SPEC["stem_height"]
    sh = SPEC["shade_height"]
    rim_r = SPEC["shade_diameter"] / 2.0
    stem_top = base_h + stem_h

    # ---- wide weighted base ---------------------------------------------
    base = bkit.lathe("FloorLampBase", [
        (0.0, 0.0),
        (148.0, 0.0),
        (160.0, 3.0),
        (160.0, 20.0),
        (150.0, 29.0),
        (110.0, 33.0),
        (48.0, base_h),
        (26.0, base_h),
        (0.0, base_h),
    ], segments=96, mat=cast)

    stem = bkit.cylinder("FloorLampStem", SPEC["stem_diameter"] / 2.0,
                         stem_h, segments=32,
                         centre=(0.0, 0.0, base_h + stem_h / 2.0), mat=steel)

    # ---- gooseneck ------------------------------------------------------
    neck = bkit.arc_torus("FloorLampNeck", ARC_R, SPEC["arc_tube_diameter"] / 2.0,
                          90.0, 180.0, centre=(ARC_R, 0.0, stem_top),
                          plane="XZ", seg_major=48, mat=steel, caps=True)

    arm_end_z = stem_top + ARC_R

    # ---- drop hanger from the arm end down to the shade -----------------
    drop = bkit.cylinder("FloorLampDrop", 9.0, SPEC["drop_length"], segments=20,
                         centre=(ARC_R, 0.0, arm_end_z - SPEC["drop_length"] / 2.0),
                         mat=steel)

    shade_top = arm_end_z - SPEC["drop_length"] + 6.0
    shade_bottom = shade_top - sh

    # ---- drum shade, hung clear BELOW the arm --------------------------
    shade = _shell("FloorLampShade", [
        (rim_r - 3.0, 0.0),
        (rim_r - 3.0, sh),      # straight drum wall, inside
        (rim_r, sh),            # across the top rim
        (rim_r, 0.0),           # outside
    ], centre=(ARC_R, 0.0, shade_bottom), mat=linen)

    # warm lining inside the drum: a second material on the same solid
    lining = bkit.pbr("ShadeLining", base=(0.96, 0.90, 0.78), rough=0.35,
                      emission=(1.0, 0.90, 0.72), emission_strength=3.0)
    bkit.assign_faces_by(shade, lining,
                         lambda c, n: (c.x - ARC_R) ** 2 + c.y ** 2
                         < (rim_r - 2.0) ** 2
                         and c.z / bkit.MM < shade_top - 2.0)

    bulb = bkit.lathe("FloorLampBulb", [
        (0.0, 0.0),
        (18.0, 4.0),
        (24.0, 18.0),
        (25.0, 46.0),
        (20.0, 72.0),
        (10.0, 90.0),
        (0.0, 96.0),
    ], segments=48, centre=(ARC_R, 0.0, shade_bottom + 40.0), mat=glow)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="base_diameter", mm=320.0, tol=0.6, how="diameter", part="FloorLampBase"),
    dict(name="base_height", mm=34.0, tol=0.4, how="bbox_z", part="FloorLampBase"),
    dict(name="stem_height", mm=1300.0, tol=0.5, how="bbox_z", part="FloorLampStem"),
    dict(name="shade_diameter", mm=380.0, tol=0.6, how="diameter", part="FloorLampShade"),
    dict(name="shade_height", mm=250.0, tol=0.5, how="bbox_z", part="FloorLampShade"),
]