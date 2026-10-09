"""
pickup_truck -- double-cab pickup, 5600 x 1980 x 1850 mm, 3350 mm wheelbase.

A pickup is two volumes, not one: a boxy cab over the front axle and an open
bed behind it. The loft handles the cab; the bed is built from real panels
because a loft cannot make an open box, and an open box is the entire point of
a pickup -- a closed bed would read as a van with a short bonnet.

Proportions that carry the type:
  * wheelbase/length 3350/5600 = 0.60, but the front overhang is only 900 mm
    and the rear is 1350 -- that asymmetry, not the ratio, is what reads;
  * 780 mm wheels on a 265 mm tyre under a 1850 mm roof;
  * bed floor at 1250 mm, bed rail 200 mm above it, which is why a pickup's
    load lip is at hip height and the body sides look so deep.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=5600.0,
    width=1980.0,
    height=1850.0,
    wheelbase=3350.0,
    track=1720.0,
    wheel_diameter=780.0,
    rim_diameter=457.0,
    tyre_width=265.0,
    bed_floor_height=1250.0,
    bed_inner_width=1780.0,
    bed_length=3560.0,
)

CHECKS = [
    dict(name="length", mm=5600.0, tol=3.0, how="bbox_x", part=None),
    dict(name="width", mm=1980.0, tol=3.0, how="bbox_y", part="TruckBedSide"),
    dict(name="height", mm=1850.0, tol=3.0, how="bbox_z", part=None),
    dict(name="bed_floor_length", mm=3560.0, tol=3.0, how="bbox_x",
         part="TruckBedFloor"),
    dict(name="bed_floor_height", mm=90.0, tol=2.0, how="bbox_z",
         part="TruckBedFloor"),
    dict(name="wheel_diameter", mm=780.0, tol=1.0, how="diameter", part="Wheel0"),
]

# cab: front (+X) to the back of the cab
CAB = [
    (2820.0, 860.0, 500.0, 1200.0, 4.2),
    (2700.0, 930.0, 470.0, 1300.0, 4.4),
    (2450.0, 980.0, 452.0, 1380.0, 4.5),
    (2150.0, 990.0, 442.0, 1450.0, 4.6),
    (1900.0, 990.0, 436.0, 1520.0, 4.6),
    (1650.0, 990.0, 432.0, 1610.0, 4.6),
    (1420.0, 988.0, 430.0, 1850.0, 4.8),
    (1180.0, 980.0, 430.0, 1850.0, 4.8),
    (950.0, 962.0, 430.0, 1846.0, 4.6),
    (850.0, 940.0, 430.0, 1830.0, 4.2),
]


def build():
    paint = bkit.pbr("TruckPaint", base=(0.055, 0.115, 0.175), rough=0.22,
                     metal=0.35, coat=0.6)
    glass = bkit.pbr("TruckGlass", base=(0.050, 0.056, 0.064), rough=0.05)
    trim = bkit.preset("black_plastic")
    chrome = bkit.preset("polished_metal")
    bed_mat = bkit.pbr("TruckBed", base=(0.30, 0.31, 0.33), rough=0.42)
    lamp_w = bkit.pbr("TruckHeadlamp", base=(0.84, 0.84, 0.88), rough=0.09,
                      transmission=0.5)
    lamp_r = bkit.pbr("TruckTaillamp", base=(0.45, 0.03, 0.026), rough=0.11,
                      transmission=0.3)

    cab = V.shell("TruckCab", CAB, mat=paint, steps=64)
    V.arch_cut(cab, 1900.0, 220.0, 1070.0, 390.0, 452.0)
    V.arch_cut(cab, -1450.0, 220.0, 1070.0, 390.0, 452.0)
    bkit.recalc(cab)
    V.glass_band(cab, 1330.0, 1790.0, glass, max_nz=0.95)

    # chassis rail: the structure that carries the bed and gives the truck its
    # length without a loft having to span cab-to-tail
    bkit.rounded_box("TruckChassis", 5400.0, 1400.0, 210.0, r=40.0, segments=2,
                     centre=(0.0, 0.0, 585.0), mat=trim)

    bed_z = SPEC["bed_floor_height"]
    bkit.rounded_box("TruckBedFloor", SPEC["bed_length"], 1900.0, 90.0, r=18.0,
                     segments=2, centre=(-920.0, 0.0, bed_z), mat=bed_mat)
    V.mirror_y(bkit.rounded_box("TruckBedSide", SPEC["bed_length"], 110.0, 500.0,
                                r=22.0, segments=2,
                                centre=(-920.0, 935.0, bed_z + 295.0),
                                mat=paint))
    bkit.rounded_box("TruckBedFront", 110.0, 1780.0, 500.0, r=22.0, segments=2,
                     centre=(890.0, 0.0, bed_z + 295.0), mat=paint)
    bkit.rounded_box("TruckTailgate", 110.0, 1780.0, 500.0, r=22.0, segments=2,
                     centre=(-2595.0, 0.0, bed_z + 295.0), mat=paint)

    bkit.rounded_box("TruckGrille", 90.0, 1320.0, 420.0, r=40.0, segments=3,
                     centre=(2805.0, 0.0, 900.0), mat=chrome)
    V.mirror_y(V.box_lamp("TruckHeadlamps", 140.0, 300.0, 200.0,
                          (2770.0, 700.0, 880.0), lamp_w, r=30.0))
    V.mirror_y(V.box_lamp("TruckTaillamps", 130.0, 170.0, 420.0,
                          (-2685.0, 860.0, 1000.0), lamp_r, r=20.0))
    V.mirror_y(bkit.rounded_box("TruckMirrors", 190.0, 110.0, 250.0, r=40.0,
                                segments=3, centre=(1500.0, 1090.0, 1560.0),
                                mat=trim))
    bkit.rounded_box("TruckBullBar", 140.0, 1900.0, 700.0, r=50.0, segments=3,
                     centre=(2700.0, 0.0, 780.0), mat=trim)

    w = V.wheel("TruckWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=6, seg=48)
    V.place_wheels(w, [(1900.0, -860.0, 390.0), (1900.0, 860.0, 390.0),
                       (-1450.0, -860.0, 390.0), (-1450.0, 860.0, 390.0)])

    return dict(spec=SPEC, parts=14)