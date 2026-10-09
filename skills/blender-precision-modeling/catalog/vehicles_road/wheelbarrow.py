"""
wheelbarrow -- builder's wheelbarrow, 1700 x 700 x 620 mm.

A wheelbarrow is one wheel, two legs and a tapered tray, and its proportions are
almost entirely the tray: a 900 mm long, 600 mm wide, 250 mm deep pressed-steel
pan that tapers to 350 mm at the nose, sitting 470 mm off the ground with the
handles 620 mm above it.

Real figures that matter: the single 400 mm pneumatic wheel sits forward of the
tray's centre of gravity, and the legs at the REAR carry the load when it is
parked -- which is why the whole thing leans back on its handles, and why the
wheel is not under the middle of the pan.

The pan is a loft rather than a box because the taper is the whole read: a
rectangular tub with a wheel in front of it looks like a cart, not a barrow.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=1700.0,
    width=700.0,
    height=670.0,
    wheel_diameter=400.0,
    tyre_width=100.0,
    tray_length=900.0,
    tray_width=600.0,
    tray_depth=250.0,
    rim_height=670.0,
)

CHECKS = [
    dict(name="length", mm=1700.0, tol=6.0, how="bbox_x", part=None),
    dict(name="width", mm=700.0, tol=6.0, how="bbox_y", part=None),
    dict(name="height", mm=670.0, tol=6.0, how="bbox_z", part=None),
    dict(name="wheel_diameter", mm=400.0, tol=2.0, how="diameter",
         part="Wheel0"),
    dict(name="tray_length", mm=900.0, tol=4.0, how="bbox_x", part="BarrowTray"),
    dict(name="tray_width", mm=600.0, tol=4.0, how="bbox_y", part="BarrowTray"),
]


def build():
    steel = bkit.pbr("BarrowSteel", base=(0.46, 0.48, 0.50), metal=0.35,
                     rough=0.42)
    paint = bkit.pbr("BarrowPaint", base=(0.66, 0.16, 0.05), rough=0.34)
    frame = bkit.pbr("BarrowFrame", base=(0.30, 0.31, 0.33), rough=0.44)
    grip = bkit.preset("black_plastic")

    # ---- tray: a loft, so it actually tapers to the nose ------------------
    V.shell("BarrowTray", [
        (-450.0, 250.0, 420.0, 670.0, 4.6),
        (-250.0, 295.0, 420.0, 670.0, 4.6),
        (100.0, 300.0, 420.0, 670.0, 4.6),
        (330.0, 250.0, 430.0, 650.0, 4.2),
        (450.0, 175.0, 450.0, 610.0, 3.6),
    ], mat=steel, steps=48)

    # ---- frame: bent tube, built from struts between real joints ----------
    for tag, y in (("L", 250.0), ("R", -250.0)):
        V.strut("BarrowFrame" + tag, (-460.0, y, 380.0), (430.0, y, 430.0),
                20.0, frame, 14)
        V.strut("BarrowHandle" + tag, (-430.0, y, 390.0), (-1060.0, y, 560.0),
                22.0, frame, 14)
        V.strut("BarrowLeg" + tag, (-400.0, y, 400.0), (-420.0, y, 18.0),
                18.0, frame, 14)
        V.strut("BarrowStay" + tag, (150.0, y, 420.0), (-420.0, y, 390.0),
                16.0, frame, 12)
    bkit.cylinder("BarrowAxle", 20.0, 560.0, segments=14, axis="Y",
                  centre=(0.0, 0.0, 200.0), mat=frame)
    for tag, y in (("L", 324.0), ("R", -324.0)):
        V.strut("BarrowGrip" + tag, (-1033.0, y, 570.0), (-1247.0, y, 594.0),
                26.0, grip, 14)
    bkit.rounded_box("BarrowPlate", 260.0, 420.0, 24.0, r=10.0, segments=2,
                     centre=(-330.0, 0.0, 360.0), mat=paint)

    w = V.wheel("BarrowWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                200.0, spokes=5, seg=40)
    V.place_wheels(w, [(0.0, 0.0, 200.0)], names=["Wheel0"])

    return dict(spec=SPEC, parts=12)