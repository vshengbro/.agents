"""
bicycle -- lightweight road bicycle, 1740 x 600 x 1050 mm.

A bicycle has no body at all: it is two 690 mm wheels and a diamond of tubes,
so every millimetre of it is frame geometry. The proportions that make it read:

  * 1050 mm wheelbase on 690 mm wheels. Wheelbase/wheel-diameter = 1.52. Get
    this below about 1.45 and the wheels overlap and it reads as a folding
    bike; above 1.6 and it reads as a cargo bike;
  * 690 mm wheels (622 rim plus a 34 mm tyre) and a 50 mm bottom bracket,
    780 mm to the top of the bars;
  * the top tube slopes DOWN from the head tube to the seat tube by about 70 mm,
    which is what separates a modern compact geometry from a classic diamond.

The 32 spokes are laid out radially through `array_radial` about the wheel
axis, not hand-placed: 32 hand-typed coordinates is 32 chances to put two of
them on top of each other.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=1740.0,
    width=600.0,
    height=1050.0,
    wheelbase=1050.0,
    wheel_diameter=690.0,
    rim_diameter=622.0,
    tyre_width=36.0,
    bar_width=600.0,
    bottom_bracket_height=330.0,
    saddle_height=800.0,
    spoke_count=32,
)

CHECKS = [
    dict(name="length", mm=1740.0, tol=4.0, how="bbox_x", part=None),
    dict(name="width", mm=600.0, tol=4.0, how="bbox_y", part=None),
    dict(name="height", mm=1050.0, tol=4.0, how="bbox_z", part=None),
    dict(name="wheel_diameter", mm=690.0, tol=2.0, how="diameter", part="Wheel0"),
    dict(name="saddle_length", mm=280.0, tol=3.0, how="bbox_x",
         part="BikeSaddle"),
]

AX_F = 525.0
AX_R = -525.0
BB = (60.0, 0.0, 330.0)          # bottom bracket
HEAD_TOP = (400.0, 0.0, 900.0)   # head tube upper
HEAD_BOT = (430.0, 0.0, 700.0)   # head tube lower
SEAT_TOP = (-330.0, 0.0, 780.0)  # top of the seat tube


def build():
    frame = bkit.pbr("BikeFrame", base=(0.10, 0.36, 0.46), rough=0.20,
                     metal=0.40, coat=0.7)
    alloy = bkit.preset("brushed_metal")
    dark = bkit.preset("black_plastic")
    saddle = bkit.pbr("BikeSaddle", base=(0.05, 0.05, 0.055), rough=0.5)

    r = SPEC["wheel_diameter"] / 2.0

    # ---- diamond frame ----------------------------------------------------
    parts = [
        V.strut("B_TopTube", HEAD_TOP, SEAT_TOP, 15.0, frame, 14),
        V.strut("B_DownTube", HEAD_BOT, BB, 17.0, frame, 14),
        V.strut("B_SeatTube", BB, SEAT_TOP, 15.0, frame, 14),
        V.strut("B_HeadTube", HEAD_BOT, HEAD_TOP, 20.0, frame, 16),
        V.strut("B_Chainstay", BB, (AX_R, 55.0, r), 12.0, frame, 12),
        V.strut("B_Chainstay2", BB, (AX_R, -55.0, r), 12.0, frame, 12),
        V.strut("B_Seatstay", SEAT_TOP, (AX_R, 42.0, r), 11.0, frame, 12),
        V.strut("B_Seatstay2", SEAT_TOP, (AX_R, -42.0, r), 11.0, frame, 12),
        V.strut("B_Fork", HEAD_BOT, (AX_F, 0.0, r), 13.0, alloy, 12),
        V.strut("B_Steerer", HEAD_TOP, HEAD_BOT, 15.0, alloy, 12),
    ]
    bkit.join(parts, "BikeFrame")

    bkit.cylinder("BikeCrank", 26.0, 330.0, segments=24, axis="Y",
                  centre=(BB[0], 0.0, BB[2]), mat=alloy)
    V.mirror_y(bkit.rounded_box("BikePedal", 190.0, 90.0, 22.0, r=8.0,
                                segments=2, centre=(60.0, 175.0, 300.0),
                                mat=dark))
    V.mirror_y(bkit.rounded_box("BikeChainring", 24.0, 210.0, 210.0, r=100.0,
                                segments=3, centre=(60.0, 62.0, 330.0),
                                mat=alloy))

    bkit.cylinder("BikeBars", 15.0, 570.0, segments=16, axis="Y",
                  centre=(415.0, 0.0, 1035.0), mat=alloy)
    V.mirror_y(bkit.rounded_box("BikeGrip", 110.0, 34.0, 34.0, r=14.0,
                                segments=2, centre=(415.0, 282.0, 1035.0),
                                mat=dark))
    V.strut("BikeStem", HEAD_TOP, (415.0, 0.0, 1035.0), 14.0, alloy, 12)

    bkit.cylinder("BikeSeatpost", 16.0, 200.0, segments=16,
                  centre=(-330.0, 0.0, 800.0), mat=alloy)
    bkit.rounded_box("BikeSaddle", 280.0, 145.0, 45.0, r=20.0, segments=3,
                     centre=(-330.0, 0.0, 895.0), mat=saddle)
    bkit.rounded_box("BikeRack", 300.0, 140.0, 18.0, r=8.0, segments=2,
                     centre=(-330.0, 0.0, 940.0), mat=alloy)

    w = V.spoked_wheel("BikeWheel", SPEC["wheel_diameter"],
                       SPEC["tyre_width"], SPEC["rim_diameter"],
                       spokes=SPEC["spoke_count"], hub_dia=50.0, seg=48)
    V.place_wheels(w, [(AX_F, 0.0, r), (AX_R, 0.0, r)],
                   names=["Wheel0", "Wheel1"])

    return dict(spec=SPEC, parts=10)