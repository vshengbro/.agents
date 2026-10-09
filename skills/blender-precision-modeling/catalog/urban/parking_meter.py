"""
parking_meter -- 180 x 120 x 1380 mm kerbside parking meter: a 64 mm post on a
base, a 180 x 120 x 280 mm head with a recessed display and card reader, a solar
panel on the cap, a coin slot and a flag lever.

Like the bollard, this is modelled at its real installed height of 1380 mm
rather than shrunk into the catalog's `small` band -- a parking meter at 200 mm
is not a parking meter. What sells it is the furniture: the solar cap, the
recessed readout, the card slot and the flag.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    post_diameter=64.0,
    post_length=1100.0,
    head_width=180.0,
    head_depth=120.0,
    head_height=280.0,
    screen_width=110.0,
    screen_height=70.0,
    overall_height=1380.0,
)

POST_R = SPEC["post_diameter"] / 2.0
HEAD_Z = SPEC["post_length"] + 135.0      # head centre above the floor
HEAD_FRONT = -SPEC["head_depth"] / 2.0   # -60


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, HEAD_FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, HEAD_FRONT + 1.5, cz), mat=mat)


def build():
    body = bkit.pbr("ParkMeterBody", base=(0.30, 0.32, 0.30), metal=0.60,
                    rough=0.44)
    dark = bkit.pbr("ParkMeterDark", base=(0.065, 0.065, 0.070), rough=0.42)
    steel = bkit.preset("brushed_metal")
    lcd = bkit.pbr("ParkMeterLcd", base=(0.08, 0.12, 0.10), rough=0.09,
                   emission=(0.50, 0.74, 0.42), emission_strength=1.2)
    solar = bkit.pbr("ParkMeterSolar", base=(0.05, 0.06, 0.14), metal=0.60,
                     rough=0.14)

    # ---- base and post. The post is sunk 20 mm into the base. ------------
    bkit.cylinder("MeterBase", 80.0, 40.0, segments=40, centre=(0.0, 0.0, 20.0),
                  mat=body)
    bkit.cylinder("MeterPost", POST_R, SPEC["post_length"], segments=32,
                  centre=(0.0, 0.0, 570.0), mat=body)
    door = bkit.rounded_box("AccessDoor", 90.0, 6.0, 140.0, r=4.0, segments=2,
                            centre=(0.0, -POST_R - 1.0, 700.0), mat=dark)

    # ---- head, cap and solar panel ---------------------------------------
    bkit.rounded_box("MeterHead", SPEC["head_width"], SPEC["head_depth"],
                     SPEC["head_height"], r=16.0, segments=3,
                     centre=(0.0, 0.0, HEAD_Z), mat=body)
    bkit.rounded_box("HeadCap", SPEC["head_width"] - 10.0,
                     SPEC["head_depth"] - 10.0, 40.0, r=12.0, segments=2,
                     centre=(0.0, 0.0, 1360.0), mat=dark)
    bkit.rounded_box("SolarPanel", 150.0, 100.0, 12.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 1372.0), mat=solar)

    # ---- recessed display, card slot and coin slot ------------------------
    _recess("MeterScreen", bpy.data.objects["MeterHead"],
            SPEC["screen_width"], SPEC["screen_height"], 0.0, HEAD_Z + 60.0,
            lcd)
    _recess("CardSlot", bpy.data.objects["MeterHead"], 46.0, 10.0, -40.0,
            HEAD_Z - 40.0, dark, depth=6.0, proud=3.0, margin=3.0)
    bkit.rounded_box("CoinSlot", 26.0, 8.0, 44.0, r=3.0, segments=2,
                     centre=(46.0, HEAD_FRONT + 1.0, HEAD_Z - 46.0), mat=steel)

    # ---- flag lever on the right cheek and two status lamps --------------
    bkit.cylinder("FlagPivot", 8.0, 30.0, segments=20, axis="X",
                  centre=(SPEC["head_width"] / 2.0 + 8.0, 0.0,
                          HEAD_Z + 90.0), mat=steel)
    bkit.rounded_box("FlagLever", 8.0, 22.0, 90.0, r=4.0, segments=2,
                     centre=(SPEC["head_width"] / 2.0 + 20.0, 0.0,
                             HEAD_Z + 90.0), mat=dark)
    lamps = []
    for i, lz in enumerate(bkit.lay_out([12.0, 12.0], gap=10.0)):
        lamps.append(bkit.cylinder("_lamp%d" % i, 5.0, 4.0, segments=16,
                                   axis="Y", mat=dark,
                                   centre=(40.0, HEAD_FRONT - 1.0,
                                           HEAD_Z + 100.0 + lz[0])))
    bkit.join(lamps, name="StatusLamps")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="post_diameter", mm=64.0, tol=0.5, how="diameter",
         part="MeterPost"),
    dict(name="post_length", mm=1100.0, tol=1.0, how="bbox_z",
         part="MeterPost"),
    dict(name="head_width", mm=180.0, tol=0.6, how="bbox_x", part="MeterHead"),
    dict(name="head_depth", mm=120.0, tol=0.6, how="bbox_y", part="MeterHead"),
    dict(name="screen_width", mm=110.0, tol=0.6, how="bbox_x",
         part="MeterScreen"),
    dict(name="overall_height", mm=1380.0, tol=2.0, how="bbox_z"),
]