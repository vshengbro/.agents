"""
connecting_rod -- 306 mm I-section con-rod with a split big end and a small end.

Three things carry this: the big end is a real ring with a bearing bore, the
shank is relieved on BOTH faces into an I section (a single flat plate is what
makes a modelled rod look like a bar of soap), and the big end is split through
the bore centre on a plane perpendicular to the rod axis, which is where the cap
joint really is. The rod lies in XY so the side elevation shows the full length.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=306.0,                 # overall, big end OD to small end OD
    big_end_outer_diameter=84.0,
    big_end_bore_diameter=56.0,
    big_end_width=26.0,
    small_end_outer_diameter=48.0,
    small_end_bore_diameter=30.0,
    small_end_width=22.0,
    shank_width=30.0,
    shank_thickness=18.0,
    shank_relief_depth=2.0,
    cap_split_width=0.8,
    centre_distance=240.0,
)


def build():
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    x_big = -SPEC["centre_distance"] / 2.0
    x_small = SPEC["centre_distance"] / 2.0

    big = bkit.tube("BigEnd", SPEC["big_end_outer_diameter"] / 2.0,
                    SPEC["big_end_bore_diameter"] / 2.0, SPEC["big_end_width"],
                    segments=96, centre=(x_big, 0, 0), mat=steel)
    small = bkit.tube("SmallEnd", SPEC["small_end_outer_diameter"] / 2.0,
                      SPEC["small_end_bore_diameter"] / 2.0, SPEC["small_end_width"],
                      segments=96, centre=(x_small, 0, 0), mat=steel)

    # ---- shank: reaches 6 mm INSIDE each ring wall so the union is clean
    r_big_o = SPEC["big_end_outer_diameter"] / 2.0
    r_s_o = SPEC["small_end_outer_diameter"] / 2.0
    x0 = x_big + r_big_o - 6.0
    x1 = x_small - r_s_o + 6.0
    shank = bkit.rounded_box("Shank", x1 - x0, SPEC["shank_width"],
                             SPEC["shank_thickness"], r=4.0, segments=3,
                             centre=((x0 + x1) / 2.0, 0, 0), mat=steel)
    bkit.boolean(big, shank, "UNION")
    bkit.boolean(big, small, "UNION")

    # ---- I-section relief on both faces --------------------------------
    for zc in (SPEC["shank_thickness"] / 2.0 - SPEC["shank_relief_depth"] / 2.0,
               -SPEC["shank_thickness"] / 2.0 + SPEC["shank_relief_depth"] / 2.0):
        cut = bkit.box("Relief", (x1 - x0) - 26.0, SPEC["shank_width"] - 12.0,
                       SPEC["shank_relief_depth"] * 1.4,
                       centre=((x0 + x1) / 2.0, 0, zc))
        bkit.boolean(big, cut, "DIFFERENCE")

    # ---- cap joint: a slot through the big-end bore centre --------------
    split = bkit.box("CapSplit", SPEC["cap_split_width"], 120.0, 44.0,
                     centre=(x_big, 0, 0))
    bkit.boolean(big, split, "DIFFERENCE")

    # ---- cap bolt counterbores in the outboard face --------------------
    for by in (35.0, -35.0):
        cb = bkit.cylinder("BoltCbore", 6.0, 6.0, segments=32, axis="X",
                           centre=(x_big - r_big_o + 1.0, by, 0.0))
        bkit.boolean(big, cb, "DIFFERENCE")

    bkit.recalc(big)
    big.name = "ConnectingRod"
    bkit.assign_faces_by(big, dark, lambda c, n: c.x < x_big)
    # Lie along Y: the studio's side elevation is az=2, i.e. straight down +X,
    # so a rod built along X is photographed end-on.
    big.rotation_euler = (0.0, 0.0, math.radians(90.0))
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="overall_length", mm=306.0, tol=0.6, how="bbox_y", part="ConnectingRod"),
    dict(name="big_end_outer_diameter", mm=84.0, tol=0.5, how="bbox_x", part="ConnectingRod"),
    dict(name="big_end_width", mm=26.0, tol=0.4, how="bbox_z", part="ConnectingRod"),
]
