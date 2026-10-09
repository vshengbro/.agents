"""
food_processor -- 240 x 220 x 400 mm countertop food processor: a moulded motor
base with three keys, a lathed bowl with a real wall and a handle, a lid with a
feed chute, and a central drive shaft carrying a curved slicing disc.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=230.0,
    base_depth=210.0,
    base_height=140.0,
    overall_height=400.0,
    corner_radius=16.0,
    bowl_diameter=220.0,
    bowl_height=196.0,
    bowl_wall=4.0,
    chute_width=62.0,
    handle_reach=32.0,
    handle_tube=11.0,
    key_count=3,
    key_diameter=22.0,
    key_pitch=38.0,
)

BW = SPEC["base_width"]
BD = SPEC["base_depth"]
BH = SPEC["base_height"]
BR = SPEC["bowl_diameter"] / 2.0
BH_ = SPEC["bowl_height"]
WALL = SPEC["bowl_wall"]
BOWL_Z = BH - 6.0
FRONT = -(BD / 2.0)


def build():
    plastic = bkit.preset("white_plastic")
    dark = bkit.preset("black_plastic")
    bowl_mat = bkit.pbr("ProcessorBowl", base=(0.84, 0.86, 0.87), rough=0.12,
                        coat=0.4)
    steel = bkit.preset("brushed_metal")

    # ---- motor base -------------------------------------------------------
    bkit.rounded_box("ProcessorBase", BW, BD, BH, r=SPEC["corner_radius"],
                     segments=6, centre=(0.0, 0.0, BH / 2.0), mat=plastic)

    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["key_count"], gap=SPEC["key_pitch"] - kd)):
        bkit.cylinder("BaseKey%d" % i, kd / 2.0, 12.0, segments=32, axis="Y",
                      centre=(x, FRONT - 6.0 + 4.0, 78.0), mat=dark)

    # ---- bowl -------------------------------------------------------------
    prof = [
        (0.0, 0.0),
        (BR - 22.0, 0.0),
        (BR - 6.0, 4.0),
        (BR, 18.0),
        (BR, BH_ - 22.0),
        (BR - 4.0, BH_ - 6.0),
        (BR - 1.0, BH_),                # rolled rim
        (BR - 1.0 - WALL, BH_),
        (BR - 5.0 - WALL, BH_ - 8.0),
        (BR - 8.0 - WALL, 20.0),
        (BR - 26.0 - WALL, 9.0),
        (0.0, 8.0),
    ]
    bkit.lathe("ProcessorBowl", prof, segments=96, centre=(0.0, 0.0, BOWL_Z),
               mat=bowl_mat)

    # ---- lid with feed chute ----------------------------------------------
    LID_Z = BOWL_Z + BH_ - 4.0
    bkit.lathe("ProcessorLid",
               [(0.0, 0.0), (BR - 3.0, 0.0), (BR + 1.0, 5.0),
                (BR - 2.0, 16.0), (60.0, 22.0), (0.0, 24.0)],
               segments=96, centre=(0.0, 0.0, LID_Z), mat=dark)
    # Chute pushed off-centre, the way a processor's really is, so the pusher
    # clears the drive shaft.
    bkit.rounded_box("FeedChute", SPEC["chute_width"], 78.0, 62.0, r=8.0,
                     segments=4, centre=(-52.0, 0.0, LID_Z + 32.0), mat=dark)
    bkit.cylinder("ChutePusher", 24.0, 44.0, segments=32,
                  centre=(-52.0, 0.0, LID_Z + 52.0), mat=plastic)

    # ---- bowl handle ------------------------------------------------------
    reach = SPEC["handle_reach"] - SPEC["handle_tube"]
    bkit.arc_torus("BowlHandle", reach, SPEC["handle_tube"], -80.0, 80.0,
                   centre=(0.0, BR - 8.0, BOWL_Z + BH_ * 0.55), plane="YZ",
                   seg_major=44, mat=dark, caps=True)

    # ---- drive shaft and slicing disc -------------------------------------
    bkit.cylinder("DriveShaft", 13.0, 190.0, segments=28,
                  centre=(0.0, 0.0, BOWL_Z + 100.0), mat=dark)
    disc = bkit.rounded_box("SlicingDisc", 150.0, 9.0, 44.0, r=4.0, segments=2,
                            mat=steel)
    disc.rotation_euler = (math.radians(22.0), 0.0, math.radians(35.0))
    bkit.move(disc, 0.0, 0.0, BOWL_Z + 92.0)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="base_width", mm=230.0, tol=0.4, how="bbox_x", part="ProcessorBase"),
    dict(name="base_depth", mm=210.0, tol=0.4, how="bbox_y", part="ProcessorBase"),
    dict(name="overall_height", mm=400.0, tol=0.6, how="bbox_z"),
    dict(name="bowl_diameter", mm=220.0, tol=0.5, how="diameter",
         part="ProcessorBowl"),
    dict(name="bowl_height", mm=196.0, tol=0.5, how="bbox_z", part="ProcessorBowl"),
]