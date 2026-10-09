"""
hopper_wagon -- 14 m bogie open hopper wagon, four discharge chutes.

A hopper is defined by what happens UNDERNEATH it, so this model is mostly
sloping panels: vertical sides down to a 2,100 mm shoulder, then panels raked
in to a 520 mm discharge line, with chutes below that. Built from separate
watertight panels rather than one solid minus a cavity -- two concentric
extrusions would share a vertex count and the EXACT solver answers coincident
facets by deleting the body.

`raked_panel()` rotates about the panel's own centre and then `move()`s it, so
the raked geometry cannot pivot about the world origin and leave the hopper.

Chute bottoms clear the ballast at 200 mm, which is the real constraint: a
hopper whose chutes touch the ground is not a hopper, it is a skip.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=14000.0,
    body_width=2900.0,
    top_rail_z=3000.0,
    discharge_z=520.0,
    chute_bottom_z=200.0,
    volume_m3=70.0,
    wheel_diameter=840.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="length_over_buffers", mm=14000.0, tol=3.0, how="bbox_x",
         part="HopperFrame"),
    dict(name="body_width", mm=2900.0, tol=3.0, how="bbox_y", part="HopperBody"),
    dict(name="top_rail_z", mm=3000.0, tol=3.0, how="top_z", part="HopperBody"),
    dict(name="shoulder_plate_top_z", mm=2130.0, tol=3.0, how="top_z",
         part="HopperShoulder"),
    dict(name="wheel_flange_diameter", mm=896.0, tol=3.0, how="bbox_z",
         part="HopperAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="HopperAxles"),
]

LENGTH = 14000.0
HALF_W = 1450.0
DECK_Z = 1250.0
TOP_Z = 3000.0
SHOULDER_Z = 2100.0
DISCHARGE_Z = 520.0
WHEEL_D = 840.0
BOGIE_X = 3500.0
BOGIE_WB = 2000.0


def build():
    frame_m = bkit.pbr("HopperFramePaint", base=(0.30, 0.19, 0.12), rough=0.60)
    body_m = bkit.pbr("HopperBodyPaint", base=(0.34, 0.22, 0.14), rough=0.58)
    steel = bkit.preset("dark_metal")
    rust_steel = bkit.pbr("HopperRust", base=(0.33, 0.25, 0.19), metal=0.72,
                          rough=0.64)

    R.underframe("HopperFrame", LENGTH, half_w=HALF_W, z_bot=950.0,
                 depth=300.0, mat=frame_m)

    body_len = LENGTH - 300.0
    t = 60.0
    parts = []

    # --- vertical upper sides and ends, plus the capping angle ------------
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        parts.append(bkit.rounded_box("HopperSide" + tag, body_len, t,
                                      TOP_Z - SHOULDER_Z, r=14.0, segments=2,
                                      centre=(0.0, s * (HALF_W - t / 2.0),
                                              (SHOULDER_Z + TOP_Z) / 2.0),
                                      mat=body_m))
        parts.append(bkit.rounded_box("HopperCap" + tag, body_len, 110.0,
                                      120.0, r=18.0, segments=2,
                                      centre=(0.0, s * (HALF_W - 55.0),
                                              TOP_Z - 60.0), mat=body_m))
    end_x = LENGTH / 2.0 - 150.0
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        parts.append(bkit.rounded_box("HopperEnd" + tag, t,
                                      2.0 * HALF_W - 200.0,
                                      TOP_Z - SHOULDER_Z, r=14.0, segments=2,
                                      centre=(s * end_x, 0.0,
                                              (SHOULDER_Z + TOP_Z) / 2.0),
                                      mat=body_m))
    body = bkit.join(parts, "HopperBody")
    bkit.recalc(body)

    # --- the shoulder ring: the horizontal plate the slopes hang from ------
    shoulder = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        shoulder.append(bkit.rounded_box("HopperShoulder" + tag, body_len,
                                         2.0 * (HALF_W - t), t, r=10.0,
                                         segments=2,
                                         centre=(0.0, 0.0, SHOULDER_Z),
                                         mat=body_m))
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        shoulder.append(bkit.rounded_box("HopperShoulder" + tag, t,
                                         2.0 * (HALF_W - t), t, r=10.0,
                                         segments=2,
                                         centre=(s * (body_len / 2.0 + t / 2.0),
                                                 0.0, SHOULDER_Z),
                                         mat=body_m))
    sh_ob = bkit.join(shoulder, "HopperShoulder")
    bkit.recalc(sh_ob)

    # --- raked slopes down to the discharge line --------------------------
    # The rake angle is measured FROM HORIZONTAL. Quoting it from vertical --
    # atan2(dy, dz) instead of atan2(dz, dy) -- rotates the panel the wrong
    # way round by nearly 70 degrees and buries it 1 m under the ballast.
    dz = SHOULDER_Z - DISCHARGE_Z
    dy = HALF_W - 350.0
    slope_len = (dz * dz + dy * dy) ** 0.5
    ang = math.degrees(math.atan2(dz, dy))
    slopes = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        slopes.append(R.raked_panel("HopperSlope" + tag, body_len, slope_len,
                                    t, s * ang, axis="X",
                                    centre=(0.0, s * (HALF_W + 350.0) / 2.0,
                                            (SHOULDER_Z + DISCHARGE_Z) / 2.0),
                                    r=10.0, mat=body_m))
    dx = end_x - 2200.0
    ang_e = math.degrees(math.atan2(dz, dx))
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        slopes.append(R.raked_panel("HopperSlope" + tag,
                                    (dz * dz + dx * dx) ** 0.5, 2.0 * HALF_W - t,
                                    t, -s * ang_e, axis="Y",
                                    centre=(s * (end_x + 2200.0) / 2.0, 0.0,
                                            (SHOULDER_Z + DISCHARGE_Z) / 2.0),
                                    r=10.0, mat=body_m))
    sl_ob = bkit.join(slopes, "HopperSlopes")
    bkit.recalc(sl_ob)

    # --- four discharge chutes --------------------------------------------
    chutes = []
    for i, x in enumerate(R.evenly(4, 9000.0)):
        chutes.append(bkit.rounded_box("HopperChute%d" % i, 1500.0, 800.0,
                                       DISCHARGE_Z - 200.0, r=30.0,
                                       segments=2,
                                       centre=(x, 0.0,
                                               (DISCHARGE_Z + 200.0) / 2.0),
                                       mat=frame_m))
    ch_ob = bkit.join(chutes, "HopperChutes")
    bkit.recalc(ch_ob)

    # --- external ribs, running gear, gear ---------------------------------
    ribs = []
    for i, x in enumerate(R.evenly(9, body_len - 400.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            ribs.append(bkit.rounded_box("HopperRib%s%d" % (tag, i), 110.0,
                                         120.0, TOP_Z - DECK_Z,
                                         r=18.0, segments=2,
                                         centre=(x, s * (HALF_W + 20.0),
                                                 (DECK_Z + TOP_Z) / 2.0),
                                         mat=body_m))
    rib_ob = bkit.join(ribs, "HopperRibs")
    bkit.recalc(rib_ob)

    R.running_gear("Hopper", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=steel)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("HopperBuffers" + tag, s * (LENGTH / 2.0), z=1065.0,
                  pitch=1750.0, mat_body=frame_m, mat_head=rust_steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("HopperStep%s%s" % (tag, ytag), s * 6550.0, sy * 1330.0,
                    480.0, DECK_Z - 20.0, steel, width=420.0, n=3)
    hb = R.spoked_ring("HopperBrakeWheel", 265.0, 5, axis="Y", rim_r=26.0,
                       hub_r=62.0, spoke_w=52.0, spoke_t=52.0,
                       mat=rust_steel, seg=32)
    bkit.move(hb, -6250.0, 1340.0, 2150.0)

    return dict(spec=SPEC, parts=13)