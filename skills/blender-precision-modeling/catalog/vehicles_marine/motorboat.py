"""
motorboat -- 5.5 m outboard motorboat with a cuddy cabin, 5500 x 2200 x 1900 mm.

The read on a small motorboat is beam against length (2.5:1) and the pair of
outboard cowls hanging off a short transom. Everything above the sheer is
secondary: a cuddy cabin forward whose window band is the only glazing, a
split windscreen, a steering console, and a pair of hinged seats. The hull is
a hard-chine open boat (bottom ratio 0.80) with 200 mm of rocker, so the
bottom is a curve and the flare at the bow is a separate decision from it.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=5500.0,
    beam=2200.0,
    hull_depth=1100.0,
    cabin_height=780.0,
    screen_height=420.0,
    outboard_dia=420.0,
    propeller_diameter=360.0,
)

CHECKS = [
    dict(name="length", mm=5500.0, tol=4.0, how="bbox_x", part="MotorboatHull"),
    dict(name="beam", mm=2200.0, tol=4.0, how="bbox_y", part="MotorboatHull"),
    dict(name="hull_depth", mm=1100.0, tol=4.0, how="bbox_z",
         part="MotorboatHull"),
    # `top_z` is a COORDINATE above the floor, and sit_on_floor lifts the model
    # 10 mm to seat it -- so the cabin crown measures 10 mm higher than the
    # model's own build frame puts it.
    dict(name="cabin_top_z", mm=1790.0, tol=6.0, how="top_z",
         part="MotorboatCabin"),
    # A 3-blade screw's swept circle cannot be expressed as a bounding box: the
    # blades sit at 120 deg, so bbox_y and bbox_z span 1.5R and 1.73R, never the
    # 2R tip circle, and `diameter` (the larger of bbox_x/bbox_y) reads the axial
    # chord instead. The 360 mm swept diameter stays in SPEC; the check declares
    # the prop's measured envelope.
    dict(name="propeller_envelope", mm=310.3, tol=4.0, how="diameter",
         part="OutboardPropeller"),
]

# (x, half beam, keel, sheer, bottom ratio) -- hard chine, 200 mm of rocker
STATIONS = [
    (-2750.0, 900.0, 200.0, 1000.0, 0.86),
    (-2400.0, 1030.0, 60.0, 1050.0, 0.84),
    (-1200.0, 1095.0, 0.0, 1100.0, 0.82),
    (0.0, 1100.0, 0.0, 1100.0, 0.82),
    (1200.0, 1060.0, 0.0, 1070.0, 0.80),
    (2100.0, 900.0, 40.0, 1000.0, 0.74),
    (2650.0, 620.0, 160.0, 900.0, 0.70),
    (2750.0, 300.0, 320.0, 840.0, 0.68),
]

CABIN_X0, CABIN_X1 = 250.0, 2100.0


def build():
    hull_mat = bkit.pbr("MotorboatHullMat", base=(0.82, 0.83, 0.84), rough=0.18,
                        coat=0.5)
    inside = bkit.pbr("MotorboatInterior", base=(0.12, 0.13, 0.15), rough=0.55)
    cabin_mat = bkit.pbr("MotorboatCabinMat", base=(0.86, 0.87, 0.88), rough=0.16,
                         coat=0.6)
    glass = bkit.pbr("MotorboatGlass", base=(0.05, 0.06, 0.07), rough=0.06)
    dark = bkit.preset("dark_metal")
    cowl = bkit.pbr("OutboardCowl", base=(0.05, 0.06, 0.08), rough=0.24,
                    coat=0.5)
    wood = bkit.preset("wood")

    hull = V.hull_open("MotorboatHull", STATIONS, wall=40.0, mat=hull_mat,
                       mat_in=inside)
    bkit.rounded_box("MotorboatTransom", 60.0, 1800.0, 620.0, r=20.0,
                     segments=2, centre=(-2730.0, 0.0, 780.0), mat=hull_mat)
    bkit.rounded_box("MotorboatKeel", 4800.0, 90.0, 70.0, r=25.0, segments=2,
                     centre=(-150.0, 0.0, 25.0), mat=dark)

    # cuddy cabin: a lofted house with a window band, sunk into the deck
    cabin = V.deckhouse("MotorboatCabin", CABIN_X0, CABIN_X1, 780.0, 1000.0,
                        1780.0, cabin_mat, mat_glass=glass,
                        glass_z=(1420.0, 1660.0), steps=44, n=4.6)
    bkit.rounded_box("MotorboatCabinRoof", 1900.0, 1620.0, 60.0, r=30.0,
                     segments=2, centre=((CABIN_X0 + CABIN_X1) / 2.0, 0.0,
                                        1740.0), mat=cabin_mat)
    bkit.rounded_box("MotorboatScreen", 60.0, 1200.0, 420.0, r=30.0,
                     segments=2, centre=(200.0, 0.0, 1900.0), mat=glass)
    bkit.rounded_box("MotorboatScreenFrame", 90.0, 1260.0, 80.0, r=35.0,
                     segments=2, centre=(215.0, 0.0, 1680.0), mat=cabin_mat)
    bkit.rounded_box("MotorboatConsole", 500.0, 700.0, 780.0, r=60.0,
                     segments=3, centre=(-150.0, 0.0, 1390.0), mat=cabin_mat)
    bkit.torus("MotorboatWheel", 190.0, 22.0, seg_major=40, seg_minor=12,
               centre=(-260.0, 340.0, 1560.0), axis="X", mat=dark)
    bkit.rounded_box("MotorboatSeat", 900.0, 1300.0, 120.0, r=50.0,
                     segments=3, centre=(-1000.0, 0.0, 1030.0), mat=wood)
    bkit.rounded_box("MotorboatSofaBack", 200.0, 1300.0, 420.0, r=70.0,
                     segments=3, centre=(-1420.0, 0.0, 1200.0), mat=wood)
    bkit.rounded_box("MotorboatForedeckHatch", 700.0, 620.0, 50.0, r=40.0,
                     segments=2, centre=(2450.0, 0.0, 1000.0), mat=cabin_mat)

    # bow rail: three stanchions and a tube, computed on the deck edge
    for i, x in enumerate((2300.0, 2600.0)):
        hw = 700.0 - 0.18 * (x - 2300.0)
        for s in (1, -1):
            V.strut("MotorboatRailStanchion%d%s" % (i, "P" if s > 0 else "S"),
                    (x, s * hw, 960.0), (x, s * (hw - 60.0), 1280.0), 18.0,
                    dark, 10)
    V.strut("MotorboatBowRail", (2300.0, 640.0, 1280.0), (2600.0, 520.0, 1240.0),
            20.0, dark, 10)

    # outboards: cowl, midsection, lower unit, propeller. One propeller is
    # built at the origin and repeated -- `duplicate` SETS location, so the
    # original is moved into place afterwards, never offset twice.
    prop = V.propeller("OutboardPropeller", SPEC["propeller_diameter"], 3,
                       90.0, bkit.preset("brushed_metal"),
                       chord=150.0, thick=12.0)
    bkit.duplicate(prop, "OutboardPropeller1", offset_mm=(-3050.0, -420.0,
                                                           300.0))
    bkit.move(prop, -3050.0, 420.0, 300.0)
    for i, s in enumerate((1, -1)):
        y = s * 420.0
        bkit.rounded_box("OutboardCowl%d" % i, 620.0, 480.0, 520.0, r=140.0,
                         segments=4, centre=(-2960.0, y, 1130.0), mat=cowl)
        bkit.rounded_box("OutboardMidsection%d" % i, 460.0, 300.0, 700.0,
                         r=90.0, segments=3, centre=(-2900.0, y, 640.0),
                         mat=dark)
        bkit.lathe("OutboardLowerUnit%d" % i,
                   [(0.0, 120.0), (110.0, 200.0), (130.0, 420.0),
                    (90.0, 520.0), (0.0, 520.0)], segments=28,
                   centre=(-2900.0, y, 190.0), mat=dark)
    bkit.rounded_box("MotorboatSwimPlatform", 900.0, 1500.0, 70.0, r=35.0,
                     segments=2, centre=(-3050.0, 0.0, 420.0), mat=wood)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=18)
