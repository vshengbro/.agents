"""
beehive -- a Langstroth hive: two brood boxes, a super and a telescoping lid.

A Langstroth hive is a STACK with one dimension, so every box is the same
solid repeated at the box pitch. The pitch is the box height plus the 3 mm
bee space, not the box height: stack them flush and the boxes look welded, which
is the whole reason the standard has a gap in it.

The frames inside are the second repeated feature, on a 32 mm pitch across the
box, and they hang from the top -- which is why the hive has hand holds cut in
the second box down.

Real 10-frame Langstroth: 508 x 419 mm outside, 241 mm box height, 48 mm frames
on a 32 mm pitch, 8-way entrance.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    box_length=508.0,
    box_width=419.0,
    box_height=241.0,
    boxes=3,
    bee_space=3.0,
    frames=9,
    frame_pitch=32.0,
    frame_height=230.0,
    lid_overhang=60.0,
    stand_height=200.0,
    overall_height=1180.0,
)

BX = SPEC["box_length"]
BY = SPEC["box_width"]
BH = SPEC["box_height"]
PITCH = BH + SPEC["bee_space"]      # the pitch is the box PLUS the bee space
N = SPEC["boxes"]

CHECKS = [
    dict(name="box_length", mm=508.0, tol=3.0, how="bbox_x",
         part="HiveBox00"),
    dict(name="box_width", mm=419.0, tol=3.0, how="bbox_y",
         part="HiveBox00"),
    dict(name="box_height", mm=241.0, tol=3.0, how="bbox_z",
         part="HiveBox00"),
    dict(name="box_pitch", mm=474.0, tol=2.0, how="z_min", part="HiveBox01"),
    dict(name="frame_row_length", mm=716.0, tol=3.0, how="bbox_x",
         part="HiveFrame00"),
    dict(name="frame_height", mm=230.0, tol=3.0, how="bbox_z",
         part="HiveFrame00"),
    dict(name="stand_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="HiveStandLeg0_0"),
    dict(name="lid_top", mm=1022.0, tol=6.0, how="top_z", part="HiveLid"),
]


def build():
    cedar = bkit.pbr("HiveCedar", base=(0.66, 0.52, 0.32), rough=0.62)
    paint = bkit.pbr("HivePaint", base=(0.80, 0.76, 0.66), rough=0.44)
    dark = bkit.pbr("HiveDark", base=(0.16, 0.12, 0.08), rough=0.55)
    metal = bkit.preset("brushed_metal")

    # ---- the stand: two rails on four short legs ----------------------
    for i, x in enumerate((-170.0, 170.0)):
        bkit.rounded_box("HiveStandRail%d" % i, 120.0, BY + 60.0, 60.0,
                         r=8.0, segments=2, centre=(x, 0.0, SPEC["stand_height"]),
                         mat=dark)
        for j, s in enumerate((-1, 1)):
            bkit.rounded_box("HiveStandLeg%d_%d" % (i, j), 80.0, 80.0,
                             SPEC["stand_height"], r=6.0, segments=2,
                             centre=(x, s * (BY / 2.0 - 30.0),
                                     SPEC["stand_height"] / 2.0), mat=dark)

    # ---- the box stack, on the box + bee-space pitch ------------------
    for i in range(N):
        z = SPEC["stand_height"] + 30.0 + BH / 2.0 + i * PITCH
        bkit.rounded_box("HiveBox%02d" % i, BX, BY, BH, r=6.0, segments=2,
                         centre=(0.0, 0.0, z), mat=cedar)
        # the hand holds: the two scallops a beekeeper grips
        for j, s in enumerate((-1, 1)):
            bkit.rounded_box("HiveHandHold%d_%d" % (i, j), 260.0, 70.0, 40.0,
                             r=18.0, segments=3,
                             centre=(0.0, s * (BY / 2.0 - 10.0),
                                     z + 60.0), mat=cedar)

    # ---- the frames hanging in the top box, on a 32 mm pitch -----------
    # `duplicate()` SETS location, so a copy made before the array is placed
    # lands at the array's offset relative to the world origin instead of
    # inside the hive -- and, at z = -115, drags the whole hive 115 mm up
    # when `sit_on_floor()` seats it. Array first, then rename.
    z0 = SPEC["stand_height"] + 30.0 + (N - 1) * PITCH
    proto = bkit.rounded_box("HiveFrame00", 460.0, 24.0,
                             SPEC["frame_height"], r=3.0, segments=1,
                             mat=paint)
    bkit.array_linear(proto, SPEC["frames"], (SPEC["frame_pitch"], 0, 0),
                      world=True)
    bkit.move(proto, -(SPEC["frames"] - 1) * SPEC["frame_pitch"] / 2.0, 0.0,
              z0 + 60.0)
    # `array_linear` bakes into ONE mesh, so the nine frames are one object:
    # the row is 8 pitches plus one frame, and there is no per-frame part to
    # point a pitch check at.
    # the wax comb inside the frames
    for i in range(SPEC["frames"]):
        y = -(SPEC["frames"] - 1) * SPEC["frame_pitch"] / 2.0 + i * SPEC["frame_pitch"]
        bkit.rounded_box("HiveComb%d" % i, 440.0, 6.0, 200.0, r=1.0,
                         segments=1,
                         centre=(0.0, y, z0 + 120.0), mat=dark)

    # ---- the telescoping lid, with a metal rim -----------------------
    ov = SPEC["lid_overhang"]
    bkit.rounded_box("HiveLid", BX + 2 * ov, BY + 2 * ov, 60.0, r=10.0,
                     segments=2,
                     centre=(0.0, 0.0, SPEC["stand_height"] + 30.0
                             + N * PITCH + 30.0), mat=metal)
    bkit.rounded_box("HiveInnerLid", BX, BY, 40.0, r=6.0, segments=2,
                     centre=(0.0, 0.0, SPEC["stand_height"] + 30.0
                             + N * PITCH - 10.0), mat=paint)

    # ---- the entrance reducer and the bee landing --------------------
    bkit.rounded_box("HiveEntrance", BX - 120.0, 90.0, 20.0, r=4.0,
                     segments=2,
                     centre=(0.0, -BY / 2.0 - 20.0,
                             SPEC["stand_height"] + 10.0), mat=metal)
    bkit.rounded_box("HiveLanding", 260.0, 200.0, 14.0, r=6.0, segments=2,
                     centre=(0.0, -BY / 2.0 - 110.0,
                             SPEC["stand_height"] + 40.0), mat=paint)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + N * 3 + SPEC["frames"] * 2 + 4)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
