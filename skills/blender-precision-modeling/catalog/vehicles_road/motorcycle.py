"""
motorcycle -- standard 600 cc roadster, 2100 x 812 x 1116 mm.

The hardest proportion job in the domain after nothing, because a motorcycle has
almost no body: the silhouette IS the frame, the tank, the seat and the two
wheels, and any one of them being the wrong size ruins the read.

Real figures used here:
  * 1400 mm wheelbase with a 700 mm front axle and a 700 mm rear axle offset,
    so the rear wheel sits directly under the seat -- that is why the classic
    side view is a right triangle;
  * front 590 mm / rear 630 mm wheels, only 40 mm apart. A bicycle's wheels are
    identical and a car's differ by much more; a motorcycle sits between the two;
  * 150 mm ground clearance under the engine on 110/150 mm tyres;
  * 812 mm across the bars, which is what sets the overall width.

The frame is built from `strut()` tubes between real joint points -- headstock,
top tube, down tube, swingarm pivot -- because a motorcycle frame literally is a
set of struts and a bkit primitive cannot express one. Both mudguards are arcs
about the wheel axis, not flat plates: a straight plate across a round tyre
floats at its ends and instantly reads as wrong.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=2100.0,
    width=812.0,
    height=1116.0,
    wheelbase=1400.0,
    front_wheel_diameter=590.0,
    rear_wheel_diameter=630.0,
    front_tyre_width=110.0,
    rear_tyre_width=150.0,
    bar_width=812.0,
    seat_height=830.0,
    ground_clearance=150.0,
)

CHECKS = [
    dict(name="length", mm=2100.0, tol=8.0, how="bbox_x", part=None),
    dict(name="bar_width", mm=812.0, tol=4.0, how="bbox_y", part="MotorcycleBars"),
    dict(name="height", mm=1116.0, tol=6.0, how="bbox_z", part=None),
    dict(name="front_wheel_diameter", mm=590.0, tol=2.0, how="diameter",
         part="Wheel0"),
    dict(name="rear_wheel_diameter", mm=630.0, tol=2.0, how="diameter",
         part="Wheel1"),
    dict(name="tank_length", mm=560.0, tol=4.0, how="bbox_x",
         part="MotorcycleTank"),
]

AX_F = 700.0
AX_R = -700.0


def build():
    paint = bkit.pbr("MotoPaint", base=(0.58, 0.09, 0.05), rough=0.14,
                     metal=0.30, coat=0.9)
    frame = bkit.pbr("MotoFrame", base=(0.62, 0.63, 0.66), metal=0.75, rough=0.28)
    engine = bkit.pbr("MotoEngine", base=(0.30, 0.31, 0.33), metal=0.60,
                      rough=0.40)
    seat = bkit.pbr("MotoSeat", base=(0.055, 0.055, 0.058), rough=0.55)
    chrome = bkit.preset("polished_metal")
    dark = bkit.preset("dark_metal")

    rf = SPEC["front_wheel_diameter"] / 2.0
    rr = SPEC["rear_wheel_diameter"] / 2.0

    # ---- frame ------------------------------------------------------------
    head_top = (430.0, 0.0, 1070.0)
    head_bot = (470.0, 0.0, 900.0)
    pivot = (-60.0, 0.0, 420.0)
    parts = [
        V.strut("F_TopTube", head_top, (-620.0, 0.0, 800.0), 26.0, frame, 16),
        V.strut("F_DownTube", head_bot, pivot, 28.0, frame, 16),
        V.strut("F_Strut", head_bot, (-60.0, 0.0, 730.0), 22.0, frame, 14),
        V.strut("F_Swingarm", pivot, (AX_R, 0.0, rr), 42.0, frame, 20),
        V.strut("F_ForkL", (430.0, 95.0, 1070.0), (AX_F, 95.0, rf), 24.0,
                chrome, 16),
        V.strut("F_ForkR", (430.0, -95.0, 1070.0), (AX_F, -95.0, rf), 24.0,
                chrome, 16),
    ]
    bkit.join(parts, "MotorcycleFrame")

    # ---- engine, exhaust, radiator ----------------------------------------
    bkit.rounded_box("MotorcycleEngine", 380.0, 380.0, 420.0, r=40.0,
                     segments=3, centre=(60.0, 0.0, 400.0), mat=engine)
    V.mirror_y(bkit.cylinder("MotoExhaust", 32.0, 780.0, segments=20, axis="X",
                             centre=(-420.0, 135.0, 250.0), mat=chrome))
    bkit.rounded_box("MotoRadiator", 90.0, 340.0, 320.0, r=25.0, segments=2,
                     centre=(520.0, 0.0, 760.0), mat=dark)

    # ---- tank, seat, tail -------------------------------------------------
    bkit.rounded_box("MotorcycleTank", 560.0, 420.0, 260.0, r=110.0,
                     segments=4, centre=(430.0, 0.0, 900.0), mat=paint)
    bkit.rounded_box("MotorcycleSeat", 800.0, 300.0, 130.0, r=60.0,
                     segments=3, centre=(-440.0, 0.0, 830.0), mat=seat)
    bkit.rounded_box("MotorcycleTail", 440.0, 240.0, 190.0, r=60.0,
                     segments=3, centre=(-870.0, 0.0, 900.0), mat=paint)

    # mudguards follow the tyre: an arc about the wheel axis, not a flat plate
    bkit.arc_torus("MotoFrontGuard", rf + 23.0, 14.0, 20.0, 160.0,
                   centre=(AX_F, 0.0, rf), plane="XZ", mat=paint)
    bkit.arc_torus("MotoRearGuard", rr + 18.0, 14.0, 25.0, 155.0,
                   centre=(AX_R, 0.0, rr), plane="XZ", mat=paint)

    # ---- bars, lamp, instruments -------------------------------------------
    V.strut("MotoBarStem", head_top, (330.0, 0.0, 1100.0), 18.0, chrome, 14)
    bkit.cylinder("MotorcycleBars", 16.0, SPEC["bar_width"], segments=16,
                  axis="Y", centre=(330.0, 0.0, 1100.0), mat=chrome)
    V.mirror_y(bkit.rounded_box("MotoMirror", 40.0, 150.0, 90.0, r=20.0,
                                segments=2, centre=(390.0, 245.0, 1040.0),
                                mat=seat))
    bkit.cylinder("MotoHeadlamp", 110.0, 90.0, segments=32, axis="X",
                  centre=(560.0, 0.0, 900.0),
                  mat=bkit.pbr("MotoLens", base=(0.85, 0.86, 0.90), rough=0.07,
                               transmission=0.5))
    bkit.rounded_box("MotoInstrument", 160.0, 180.0, 90.0, r=30.0,
                     segments=3, centre=(360.0, 0.0, 1030.0), mat=seat)
    V.mirror_y(bkit.rounded_box("MotoFootpeg", 200.0, 120.0, 40.0, r=14.0,
                                segments=2, centre=(-60.0, 235.0, 380.0),
                                mat=chrome))

    # ---- wheels -----------------------------------------------------------
    wf = V.spoked_wheel("MotoWheelF", SPEC["front_wheel_diameter"],
                        SPEC["front_tyre_width"], 457.0, spokes=18,
                        hub_dia=90.0)
    V.place_wheels(wf, [(AX_F, 0.0, rf)], names=["Wheel0"])
    wr = V.spoked_wheel("MotoWheelR", SPEC["rear_wheel_diameter"],
                        SPEC["rear_tyre_width"], 464.0, spokes=18,
                        hub_dia=110.0)
    V.place_wheels(wr, [(AX_R, 0.0, rr)], names=["Wheel1"])

    return dict(spec=SPEC, parts=15)