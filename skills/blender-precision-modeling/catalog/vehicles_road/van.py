"""
van -- panel van, 5100 x 1950 x 2250 mm on a 3200 mm wheelbase.

A van is a box with a nose: 70 % of the body is one uninterrupted slab from
behind the windscreen to the tail, and that slab is what a loft over
superellipse sections gives for free with a high exponent (n ~ 5-7, far
squarer than a car's n ~ 3.5).

Real figures that stop it reading as a bus or a truck:
  * one continuous glazed band 1750 mm long at the front only -- everything
    behind the B-pillar is panel, which is what `glass_band(x_hi=...)` is for;
  * 2250 mm tall against a 700 mm wheel: 3.2 wheel diameters of body;
  * a 45-degree windscreen, 350 mm of rise over 350 mm of run.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=5100.0,
    width=1950.0,
    height=2250.0,
    wheelbase=3200.0,
    track=1620.0,
    wheel_diameter=700.0,
    rim_diameter=381.0,
    tyre_width=215.0,
    sill_height=320.0,
    cargo_length=3100.0,
)

CHECKS = [
    dict(name="length", mm=5100.0, tol=3.0, how="bbox_x", part=None),
    dict(name="width", mm=1950.0, tol=3.0, how="bbox_y", part="VanBody"),
    dict(name="height", mm=2250.0, tol=3.0, how="bbox_z", part=None),
    dict(name="sill_to_roof", mm=1930.0, tol=3.0, how="bbox_z", part="VanBody"),
    dict(name="wheel_diameter", mm=700.0, tol=1.0, how="diameter", part="Wheel0"),
]

STATIONS = [
    (2550.0, 930.0, 420.0, 1600.0, 4.4),
    (2420.0, 962.0, 385.0, 1690.0, 4.6),
    (2150.0, 972.0, 352.0, 1775.0, 4.7),
    (1800.0, 975.0, 330.0, 1900.0, 4.7),
    (1450.0, 975.0, 322.0, 2250.0, 5.0),
    (1150.0, 975.0, 320.0, 2250.0, 5.2),
    (-300.0, 975.0, 320.0, 2250.0, 5.4),
    (-1400.0, 975.0, 320.0, 2250.0, 5.4),
    (-2100.0, 972.0, 330.0, 2230.0, 5.2),
    (-2350.0, 960.0, 352.0, 2150.0, 5.0),
    (-2480.0, 930.0, 382.0, 2000.0, 4.7),
    (-2550.0, 862.0, 420.0, 1850.0, 4.5),
]


def build():
    paint = bkit.pbr("VanPaint", base=(0.86, 0.86, 0.84), rough=0.28, coat=0.4)
    glass = bkit.pbr("VanGlass", base=(0.050, 0.056, 0.064), rough=0.05)
    trim = bkit.preset("black_plastic")
    chrome = bkit.preset("polished_metal")
    lamp_w = bkit.pbr("VanHeadlamp", base=(0.84, 0.84, 0.88), rough=0.09,
                      transmission=0.5)
    lamp_r = bkit.pbr("VanTaillamp", base=(0.48, 0.032, 0.028), rough=0.11,
                      transmission=0.3)

    body = V.shell("VanBody", STATIONS, mat=paint, steps=64)
    r_wheel = SPEC["wheel_diameter"] / 2.0
    V.arch_cut(body, SPEC["wheelbase"] / 2.0, 220.0, 1055.0, r_wheel, 398.0)
    V.arch_cut(body, -SPEC["wheelbase"] / 2.0, 220.0, 1055.0, r_wheel, 398.0)
    bkit.recalc(body)
    # glazed band is front-only: x > 1150, belt 1750, headroom 2100
    V.glass_band(body, 1750.0, 2100.0, glass, max_nz=0.93, x_lo=1150.0)

    bkit.rounded_box("VanGrille", 100.0, 1240.0, 380.0, r=40.0, segments=3,
                     centre=(2500.0, 0.0, 1120.0), mat=chrome)
    V.mirror_y(V.box_lamp("VanHeadlamps", 120.0, 300.0, 260.0,
                          (2485.0, 720.0, 1180.0), lamp_w, r=30.0))
    V.mirror_y(V.box_lamp("VanTaillamps", 90.0, 200.0, 520.0,
                          (-2500.0, 870.0, 1520.0), lamp_r, r=22.0))
    V.mirror_y(bkit.rounded_box("VanMirrors", 220.0, 110.0, 320.0, r=45.0,
                                segments=3, centre=(1700.0, 1030.0, 1720.0),
                                mat=trim))
    # side rub rail: flush with the flank, which is what stops the slab reading
    # as a featureless wall
    V.mirror_y(bkit.rounded_box("VanSideRail", 3100.0, 40.0, 120.0, r=18.0,
                                segments=2, centre=(-350.0, 955.0, 1000.0),
                                mat=trim))
    bkit.rounded_box("VanRearStep", 100.0, 1500.0, 140.0, r=30.0, segments=2,
                     centre=(-2500.0, 0.0, 480.0), mat=trim)

    w = V.wheel("VanWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=6, seg=48)
    V.place_wheels(w, V.corners(SPEC["wheelbase"], SPEC["track"], r_wheel))

    return dict(spec=SPEC, parts=9)