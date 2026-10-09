"""
planer -- 12 inch hand planer, 320 mm sole, 190 mm to the top of the tote.

A hand planer is a SOLE PLATE, a body that is deliberately a wedge, and two
handles whose height sets the whole silhouette. The numbers that fix it: a
320 x 86 mm sole (the 12 inch sole), a 60 mm cutter sitting 1 mm proud of it,
and a rear tote whose top edge is 190 mm above the sole.

The sole's underside is z = 0 by construction, so the plane rests on its sole
the way it rests on a board.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    sole_length=320.0,
    sole_width=86.0,
    sole_thickness=9.0,
    blade_width=60.0,
    body_height=96.0,
    tote_height=185.0,
    front_knob_diameter=62.0,
    depth_diameter=64.0,
    heel_depth=58.0,
)

CHECKS = [
    dict(name="sole_length", mm=320.0, tol=0.8, how="bbox_x", part="PlanSole"),
    dict(name="sole_width", mm=86.0, tol=0.8, how="bbox_y", part="PlanSole"),
    dict(name="sole_thickness", mm=9.0, tol=0.5, how="bbox_z",
         part="PlanSole"),
    dict(name="blade_width", mm=60.0, tol=0.6, how="bbox_y",
         part="PlanCutter"),
    dict(name="body_height", mm=96.0, tol=1.0, how="bbox_z", part="PlanBody"),
    dict(name="tote_height", mm=185.0, tol=2.0, how="top_z", part="PlanTote"),
    dict(name="front_knob_diameter", mm=62.0, tol=0.8, how="diameter",
         part="PlanFrontKnob"),
    dict(name="depth_diameter", mm=64.0, tol=0.8, how="diameter",
         part="PlanDepthKnob"),
]

ST = SPEC["sole_thickness"]


def build():
    cast = bkit.pbr("PlaneCast", base=(0.30, 0.31, 0.33), metal=0.72,
                    rough=0.44, coat=0.15)
    steel = bkit.preset("polished_metal")
    dark = bkit.preset("black_plastic")
    wood = bkit.pbr("PlaneHandle", base=(0.40, 0.22, 0.10), rough=0.38,
                    coat=0.3)

    # ---- sole: the floor datum -------------------------------------------
    T.shell("PlanSole", SPEC["sole_length"], SPEC["sole_width"], ST,
            centre=(0.0, 0.0, ST / 2.0), r=1.6, mat=cast, segments=2)
    bkit.rounded_box("PlanHeel", 62.0, SPEC["sole_width"], SPEC["heel_depth"],
                     r=2.0, segments=2, centre=(-138.0, 0.0,
                                                ST + SPEC["heel_depth"] / 2.0),
                     mat=cast)

    # ---- body: a wedge, deeper at the tote end --------------------------
    body = bkit.rounded_box("PlanBody", 250.0, 80.0, SPEC["body_height"],
                            r=6.0, segments=3,
                            centre=(-16.0, 0.0, ST + SPEC["body_height"] / 2.0),
                            mat=cast)
    bkit.rounded_box("PlanNose", 74.0, 66.0, 58.0, r=5.0, segments=2,
                     centre=(126.0, 0.0, ST + 29.0), mat=cast)

    # ---- cutter + lever cap + throat plate -------------------------------
    bkit.rounded_box("PlanCutter", 84.0, SPEC["blade_width"], 4.0, r=0.6,
                     segments=1, centre=(-24.0, 0.0, ST + 12.0), mat=steel)
    bkit.rounded_box("PlanLeverCap", 96.0, 48.0, 40.0, r=8.0, segments=3,
                     centre=(-24.0, 0.0, ST + 30.0), mat=cast)
    bkit.cylinder("PlanLeverScrew", 7.0, 10.0, segments=14,
                  centre=(-24.0, 0.0, ST + 52.0), mat=steel)
    bkit.rounded_box("PlanThroatPlate", 60.0, 62.0, 3.0, r=1.0, segments=1,
                     centre=(-24.0, 0.0, ST + 6.0), mat=steel)

    # ---- front knob + depth adjustment wheel ------------------------------
    knob = bkit.lathe("PlanFrontKnob",
                      [(0.0, 0.0), (26.0, 0.0), (31.0, 14.0), (31.0, 30.0),
                       (24.0, 44.0), (0.0, 44.0)],
                      segments=36, centre=(0, 0, 0), mat=wood)
    bkit.move(knob, 96.0, 0.0, ST + 44.0)
    bkit.cylinder("PlanKnobStem", 11.0, 50.0, segments=18,
                  centre=(96.0, 0.0, ST + 30.0), mat=steel)
    depth = bkit.lathe("PlanDepthKnob",
                       [(0.0, 0.0), (32.0, 0.0), (32.0, 24.0), (26.0, 28.0),
                        (0.0, 28.0)],
                       segments=28, centre=(0, 0, 0), mat=dark)
    bkit.move(depth, -142.0, 0.0, ST + SPEC["heel_depth"] - 4.0)

    # ---- rear tote: a D-handle lofted over the heel ----------------------
    bkit.arc_torus("PlanTote", 62.0, 15.0, -12.0, 192.0,
                   centre=(-142.0, 0.0, 108.0), plane="XZ", seg_major=30,
                   mat=wood)
    T.strut("PlanToteNeck", (-142.0, 0.0, 108.0),
            (-146.0, 0.0, ST + SPEC["heel_depth"]), 40.0, 46.0, mat=wood,
            r=8.0, segments=3)

    return dict(spec=SPEC, parts=11)