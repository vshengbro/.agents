"""
sedan -- D-segment saloon, 4750 x 1820 x 1450 mm on a 2820 mm wheelbase.

Three-box proportions, and the three boxes are the whole difference from the
hatchback: a 1520 mm flat roof, a rear screen that falls 27 degrees from
vertical onto a boot deck at 1090 mm, and a boot that is 400 mm long before the
tail panel. The wheelbase/length ratio (2820/4750 = 0.594) is noticeably lower
than the hatchback's 0.62, which is why the overhangs look long rather than
cab-forward.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=4750.0,
    width=1820.0,
    height=1450.0,
    wheelbase=2820.0,
    track=1570.0,
    wheel_diameter=640.0,
    rim_diameter=431.0,
    tyre_width=215.0,
    sill_height=238.0,
    boot_deck_height=1090.0,
)

CHECKS = [
    dict(name="length", mm=4750.0, tol=2.0, how="bbox_x", part=None),
    dict(name="width", mm=1820.0, tol=4.0, how="bbox_y", part="SedanBody"),
    dict(name="height", mm=1450.0, tol=2.0, how="bbox_z", part=None),
    dict(name="sill_to_roof", mm=1212.0, tol=2.0, how="bbox_z", part="SedanBody"),
    dict(name="boot_lip_height", mm=40.0, tol=1.0, how="bbox_z",
         part="SedanBootLip"),
    dict(name="wheel_diameter", mm=640.0, tol=1.0, how="diameter", part="Wheel0"),
]

STATIONS = [
    (2375.0, 800.0, 330.0, 800.0, 3.8),
    (2290.0, 852.0, 302.0, 830.0, 3.8),
    (2140.0, 878.0, 278.0, 862.0, 3.8),
    (1930.0, 890.0, 262.0, 892.0, 3.8),
    (1650.0, 900.0, 250.0, 940.0, 3.8),
    (1410.0, 910.0, 244.0, 1000.0, 3.8),
    (1120.0, 902.0, 240.0, 1250.0, 3.6),
    (880.0, 892.0, 238.0, 1400.0, 3.4),
    (640.0, 884.0, 238.0, 1450.0, 3.3),
    (200.0, 880.0, 238.0, 1450.0, 3.3),
    (-380.0, 886.0, 238.0, 1450.0, 3.3),
    (-880.0, 892.0, 240.0, 1448.0, 3.3),
    (-1180.0, 892.0, 244.0, 1430.0, 3.4),
    (-1420.0, 888.0, 250.0, 1330.0, 3.5),
    (-1660.0, 880.0, 258.0, 1160.0, 3.6),
    (-1850.0, 868.0, 268.0, 1090.0, 3.7),
    (-2100.0, 848.0, 286.0, 1075.0, 3.8),
    (-2300.0, 812.0, 316.0, 1050.0, 3.8),
    (-2375.0, 760.0, 360.0, 1020.0, 3.7),
]


def build():
    paint = bkit.pbr("SedanPaint", base=(0.66, 0.67, 0.70), rough=0.20,
                     metal=0.45, coat=0.7)
    glass = bkit.pbr("SedanGlass", base=(0.050, 0.056, 0.066), rough=0.05)
    trim = bkit.preset("black_plastic")
    chrome = bkit.preset("polished_metal")
    lamp_w = bkit.pbr("SedanHeadlamp", base=(0.82, 0.82, 0.86), rough=0.08,
                      transmission=0.55)
    lamp_r = bkit.pbr("SedanTaillamp", base=(0.44, 0.030, 0.028), rough=0.10,
                      transmission=0.35)

    body = V.shell("SedanBody", STATIONS, mat=paint, steps=64)
    r_wheel = SPEC["wheel_diameter"] / 2.0
    V.arch_cut(body, SPEC["wheelbase"] / 2.0, 190.0, 985.0, r_wheel, 364.0)
    V.arch_cut(body, -SPEC["wheelbase"] / 2.0, 190.0, 985.0, r_wheel, 364.0)
    bkit.recalc(body)
    V.glass_band(body, 1030.0, 1390.0, glass, max_nz=0.90)

    # Boot lip, not a boot lid: the deck is part of the loft and falls away
    # toward the tail, so a flat panel laid over it pokes out past the body and
    # stretches the overall length by 300 mm.
    bkit.rounded_box("SedanBootLip", 420.0, 1480.0, 40.0, r=18.0, segments=2,
                     centre=(-2080.0, 0.0, 1065.0), mat=paint)
    bkit.rounded_box("SedanGrille", 70.0, 980.0, 190.0, r=26.0, segments=3,
                     centre=(2340.0, 0.0, 620.0), mat=chrome)
    V.mirror_y(V.box_lamp("SedanHeadlamps", 130.0, 320.0, 150.0,
                          (2300.0, 640.0, 730.0), lamp_w, r=28.0))
    V.mirror_y(V.box_lamp("SedanTaillamps", 90.0, 300.0, 190.0,
                          (-2300.0, 660.0, 900.0), lamp_r, r=24.0))
    V.mirror_y(bkit.rounded_box("SedanMirrors", 140.0, 100.0, 82.0, r=26.0,
                                segments=3, centre=(980.0, 900.0, 1080.0),
                                mat=paint))
    V.mirror_y(bkit.rounded_box("SedanBumpers", 300.0, 1660.0, 150.0, r=45.0,
                                segments=3, centre=(2200.0, 0.0, 300.0),
                                mat=trim))
    bkit.rounded_box("SedanRearBumper", 300.0, 1660.0, 150.0, r=45.0,
                     segments=3, centre=(-2200.0, 0.0, 300.0), mat=trim)

    w = V.wheel("SedanWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=5, seg=48)
    V.place_wheels(w, V.corners(SPEC["wheelbase"], SPEC["track"], r_wheel))

    return dict(spec=SPEC, parts=9)