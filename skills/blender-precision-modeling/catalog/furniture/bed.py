"""
bed -- double bed, 1500 mm mattress on a 1560 x 2000 mm frame, 1000 mm head end.

The mattress top sits at 600 mm, which is the number that makes a bed a bed:
you sit on the edge at 600 mm, which is why the frame rails are only 170 mm
tall and why the mattress, not the frame, is what your legs clear. The
1000 mm headboard is the second proportion -- roughly 1.6 x the mattress
width -- and everything else (the 700 mm of rail under it, the pillows at
130 mm) is sized against those two.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    frame_width=1560.0,
    frame_length=2000.0,
    headboard_height=1000.0,
    mattress_width=1500.0,
    mattress_length=1950.0,
    mattress_thickness=250.0,
    mattress_top=600.0,
    rail_height=170.0,
    rail_thickness=30.0,
    leg_height=180.0,
    leg_diameter=80.0,
    pillow_count=2,
    pillow_width=600.0,
    pillow_depth=400.0,
    pillow_thickness=130.0,
    throw_length=1200.0,
    throw_thickness=70.0,
)

FW, FL = SPEC["frame_width"], SPEC["frame_length"]
MW, ML = SPEC["mattress_width"], SPEC["mattress_length"]
MT = SPEC["mattress_thickness"]
RAIL_H = SPEC["rail_height"]
RAIL_T = SPEC["rail_thickness"]
LEG_H = SPEC["leg_height"]
RAIL_Z0 = LEG_H                               # 180
RAIL_Z1 = RAIL_Z0 + RAIL_H                    # 350
RAIL_CZ = (RAIL_Z0 + RAIL_Z1) / 2.0           # 265
MT_Z1 = SPEC["mattress_top"]                  # 600
MT_CZ = MT_Z1 - MT / 2.0                      # 475

CHECKS = [
    dict(name="overall_width", mm=1560.0, tol=0.4, how="bbox_x"),
    dict(name="overall_length", mm=2000.0, tol=0.4, how="bbox_y"),
    dict(name="overall_height", mm=1000.0, tol=0.4, how="bbox_z"),
    dict(name="mattress_width", mm=1500.0, tol=0.3, how="bbox_x", part="Mattress"),
    dict(name="mattress_length", mm=1950.0, tol=0.3, how="bbox_y", part="Mattress"),
    dict(name="mattress_thickness", mm=250.0, tol=0.3, how="bbox_z", part="Mattress"),
]


def build():
    wood = bkit.pbr("BedFrameOak", base=(0.42, 0.27, 0.13), metal=0.0, rough=0.40)
    linen = bkit.pbr("BedLinen", base=(0.80, 0.79, 0.75), metal=0.0, rough=0.85)
    pillow = bkit.pbr("BedPillow", base=(0.88, 0.87, 0.84), metal=0.0, rough=0.80)
    throw_m = bkit.pbr("BedThrow", base=(0.34, 0.30, 0.42), metal=0.0, rough=0.90)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            bkit.cylinder("Leg%s%s" % (yn, xn), SPEC["leg_diameter"] / 2.0,
                          LEG_H, segments=24,
                          centre=(sx * (FW / 2.0 - 100.0), sy * (FL / 2.0 - 100.0),
                                  LEG_H / 2.0),
                          mat=wood)

    # ---- rails -------------------------------------------------------------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("RailSide%s" % tag, RAIL_T, FL, RAIL_H, r=5.0,
                         segments=2,
                         centre=(sx * (FW / 2.0 - RAIL_T / 2.0), 0, RAIL_CZ),
                         mat=wood)
    for (sy, tag) in ((-1, "Foot"), (1, "Head")):
        bkit.rounded_box("Rail%s" % tag, FW, RAIL_T, RAIL_H, r=5.0, segments=2,
                         centre=(0, sy * (FL / 2.0 - RAIL_T / 2.0), RAIL_CZ),
                         mat=wood)

    # Headboard: 1000 mm tall and 70 mm deep, tucked into the rear 70 mm.
    bkit.rounded_box("Headboard", FW, 70.0, SPEC["headboard_height"], r=14.0,
                     segments=4,
                     centre=(0, FL / 2.0 - 35.0, SPEC["headboard_height"] / 2.0),
                     mat=wood)

    bkit.rounded_box("Mattress", MW, ML, MT, r=30.0, segments=4,
                     centre=(0, 0, MT_CZ), mat=linen)

    # ---- pillows: computed, so the pair is symmetric on the centre line ----
    for i, (px, _w) in enumerate(
            bkit.lay_out([SPEC["pillow_width"]] * SPEC["pillow_count"], gap=160.0)):
        bkit.rounded_box("Pillow%d" % (i + 1), SPEC["pillow_width"],
                         SPEC["pillow_depth"], SPEC["pillow_thickness"], r=55.0,
                         segments=4,
                         centre=(px, ML / 2.0 - 300.0,
                                 MT_Z1 + SPEC["pillow_thickness"] / 2.0),
                         mat=pillow)

    bkit.rounded_box("Throw", MW + 20.0, SPEC["throw_length"],
                     SPEC["throw_thickness"], r=26.0, segments=3,
                     centre=(0, -320.0, MT_Z1 + SPEC["throw_thickness"] / 2.0),
                     mat=throw_m)

    return dict(spec=SPEC, parts=13)
