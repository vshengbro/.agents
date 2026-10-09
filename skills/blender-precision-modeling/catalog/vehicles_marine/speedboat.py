"""
speedboat -- 5.2 m deep-V sports boat, 5200 x 2300 x 2100 mm.

A planing hull is one number: deadrise. Here the bottom ratio runs from 0.14
at the bow (a knife V) to 0.90 at the transom (nearly flat), which is the
whole difference between this and the motorboat it otherwise resembles. The
second decision is the wraparound screen -- a single band of glass stepping
back in three segments from the console to the side decks -- and the third is
the sterndrive: a leg off the transom with a three-blade screw and a trim tab.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=5200.0,
    beam=2300.0,
    hull_depth=900.0,
    screen_height=560.0,
    bow_riser=260.0,
    propeller_diameter=380.0,
    trim_tab_length=400.0,
)

CHECKS = [
    dict(name="length", mm=5200.0, tol=4.0, how="bbox_x", part="SpeedboatHull"),
    dict(name="beam", mm=2300.0, tol=4.0, how="bbox_y", part="SpeedboatHull"),
    dict(name="hull_depth", mm=900.0, tol=4.0, how="bbox_z",
         part="SpeedboatHull"),
    dict(name="screen_height", mm=560.0, tol=6.0, how="bbox_z",
         part="SpeedboatScreen1"),
    # As on the motorboat: a 3-blade swept circle is not a bounding box (blades at
    # 120 deg span 1.5R and 1.73R, never 2R). SPEC keeps the 380 mm diameter;
    # the check declares the measured envelope.
    dict(name="propeller_envelope", mm=328.0, tol=4.0, how="diameter",
         part="SterndriveProp"),
    dict(name="trim_tab_length", mm=400.0, tol=5.0, how="bbox_x",
         part="SpeedboatTrimTab"),
]

# (x, half beam, keel, sheer, bottom ratio) -- the deadrise ramp is the model
STATIONS = [
    (-2600.0, 1050.0, 120.0, 780.0, 0.90),
    (-2150.0, 1130.0, 40.0, 820.0, 0.86),
    (-1100.0, 1150.0, 0.0, 860.0, 0.74),
    (0.0, 1130.0, 0.0, 900.0, 0.56),
    (1100.0, 1020.0, 0.0, 900.0, 0.38),
    (2000.0, 760.0, 30.0, 880.0, 0.24),
    (2520.0, 420.0, 150.0, 850.0, 0.16),
    (2600.0, 160.0, 330.0, 830.0, 0.14),
]

# three screen panels, each narrower and lower as it steps outboard
SCREEN = ((-450.0, 560.0, 520.0, 980.0), (250.0, 900.0, 560.0, 1000.0),
          (900.0, 1000.0, 500.0, 1000.0))
RAIL = ((1400.0, 900.0), (1950.0, 700.0), (2400.0, 380.0))


def build():
    hull_mat = bkit.pbr("SpeedboatHullMat", base=(0.06, 0.09, 0.34), rough=0.12,
                        coat=0.7)
    inside = bkit.pbr("SpeedboatInterior", base=(0.80, 0.81, 0.82), rough=0.40)
    glass = bkit.pbr("SpeedboatGlass", base=(0.05, 0.06, 0.08), rough=0.05)
    white = bkit.preset("white_plastic")
    dark = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")

    hull = V.hull_open("SpeedboatHull", STATIONS, wall=35.0, mat=hull_mat,
                       mat_in=inside)
    bkit.rounded_box("SpeedboatTransom", 60.0, 2100.0, 660.0, r=20.0,
                     segments=2, centre=(-2580.0, 0.0, 460.0), mat=hull_mat)
    bkit.rounded_box("SpeedboatTrimTab", 400.0, 900.0, 40.0, r=18.0,
                     segments=2, centre=(-2760.0, 0.0, 40.0), mat=steel)

    for i, (x, w, h, z0) in enumerate(SCREEN):
        bkit.rounded_box("SpeedboatScreen%d" % i, 60.0, w * 2.0, h, r=28.0,
                         segments=2, centre=(x, 0.0, z0 + h / 2.0 - 60.0),
                         mat=glass)
    bkit.rounded_box("SpeedboatScreenSurround", 1500.0, 2120.0, 70.0, r=34.0,
                     segments=2, centre=(250.0, 0.0, 990.0), mat=steel)
    bkit.rounded_box("SpeedboatConsole", 700.0, 700.0, 620.0, r=80.0,
                     segments=3, centre=(-350.0, 0.0, 1300.0), mat=white)
    bkit.torus("SpeedboatWheel", 180.0, 20.0, seg_major=36, seg_minor=12,
               centre=(-480.0, 300.0, 1520.0), axis="X", mat=dark)
    bkit.rounded_box("SpeedboatSunPad", 1100.0, 1500.0, 140.0, r=60.0,
                     segments=3, centre=(1250.0, 0.0, 950.0), mat=white)
    bkit.rounded_box("SpeedboatBowRiser", 1100.0, 1100.0, 260.0, r=120.0,
                     segments=3, centre=(2000.0, 0.0, 960.0), mat=white)
    bkit.rounded_box("SpeedboatBowLocker", 800.0, 900.0, 60.0, r=40.0,
                     segments=2, centre=(2000.0, 0.0, 1120.0), mat=white)
    bkit.rounded_box("SpeedboatSwimPlatform", 420.0, 1500.0, 60.0, r=30.0,
                     segments=2, centre=(-2900.0, 0.0, 380.0), mat=white)

    # bow rail: three stanchion pairs and two tube runs per side
    for i, (x, w) in enumerate(RAIL):
        for s in (1, -1):
            V.strut("SpeedboatRailStanchion%d%s" % (i, "P" if s > 0 else "S"),
                    (x, s * w, 900.0), (x, s * (w - 40.0), 1150.0), 16.0,
                    steel, 10)
    for i in range(len(RAIL) - 1):
        a, b2 = RAIL[i], RAIL[i + 1]
        for s in (1, -1):
            V.strut("SpeedboatBowRail%d%s" % (i, "P" if s > 0 else "S"),
                    (a[0], s * (a[1] - 40.0), 1150.0),
                    (b2[0], s * (b2[1] - 40.0), 1150.0), 18.0, steel, 10)

    # sterndrive: transom bracket, leg, gearcase and a three-blade screw
    prop = V.propeller("SterndriveProp", SPEC["propeller_diameter"], 3, 100.0,
                       steel, chord=160.0, thick=13.0)
    bkit.duplicate(prop, "SterndriveProp1", offset_mm=(-2860.0, -230.0, 300.0))
    bkit.move(prop, -2860.0, 230.0, 300.0)
    bkit.rounded_box("SterndriveBracket", 420.0, 900.0, 500.0, r=80.0,
                     segments=3, centre=(-2720.0, 0.0, 700.0), mat=dark)
    bkit.rounded_box("SterndriveLeg", 420.0, 340.0, 700.0, r=120.0,
                     segments=4, centre=(-2800.0, 0.0, 460.0), mat=dark)
    bkit.lathe("SterndriveGearcase", [(0.0, 0.0), (170.0, 60.0), (190.0, 220.0),
                                      (140.0, 320.0), (0.0, 320.0)],
               segments=28, centre=(-2860.0, 0.0, 300.0), mat=dark)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=16)
