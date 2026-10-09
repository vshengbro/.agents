"""
bulldozer -- crawler bulldozer with a straight blade, 6270 x 3200 x 3200 mm.

A tracked machine is a different geometry problem from a wheeled one: there are
no wheels to ground, so the CONTACT PATCH is the track, and the whole machine
sits on two 4000 x 1000 mm track frames whose top is 900 mm up. Everything else
hangs off that -- the blade is a curved plate built from a real extruded profile
rather than a box, the hood is a loft with a sloped nose, and the cab is a
glass box whose front screen is a separate part because the cab body is opaque.

Real figures: 4000 mm track frames at a 2100 mm centre-to-centre gauge, a blade
3200 mm wide and 1100 mm tall, and the blade's cutting edge 1500 mm ahead of
the track nose.
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
    length=6250.0,
    width=3200.0,
    height=3200.0,
    track_length=4000.0,
    track_width=1000.0,
    track_gauge=2200.0,
    blade_width=3200.0,
    blade_height=1100.0,
    blade_thickness=90.0,
)

CHECKS = [
    dict(name="length", mm=6250.0, tol=10.0, how="bbox_x", part=None),
    dict(name="width", mm=3200.0, tol=10.0, how="bbox_y", part=None),
    dict(name="height", mm=3200.0, tol=10.0, how="bbox_z", part=None),
    dict(name="track_length", mm=4000.0, tol=5.0, how="bbox_x",
         part="DozerTrackL"),
    dict(name="track_width", mm=1000.0, tol=5.0, how="bbox_y",
         part="DozerTrackL"),
    dict(name="blade_height", mm=1100.0, tol=5.0, how="bbox_z",
         part="DozerBlade"),
]

TRACK_X = -200.0
BLADE_X = 3050.0
# Keep A_MAX below pi/2. A normalised sine that overshoots past the quarter turn
# peaks BEFORE the last sample, so the blade came out 13.6 mm taller than the
# profile's nominal height.
A_MAX = math.pi * 0.45


def blade_profile(reach=700.0, thick=90.0, height=1100.0):
    """A dozer blade cross-section: a curved face and a flat back.

    A flat plate instead of this reads as a wall leaning against the machine --
    the curve is the whole reason a blade rolls material instead of blocking it.
    """
    pts = []
    for i in range(13):
        a = A_MAX * (i / 12.0)
        pts.append((-reach * (1.0 - math.cos(a)),
                    height * math.sin(a) / math.sin(A_MAX)))
    back = pts[-1][0] - thick
    pts.append((back, pts[-1][1]))
    pts.append((back, 0.0))
    return pts


def build():
    paint = bkit.pbr("DozerPaint", base=(0.80, 0.62, 0.03), rough=0.26,
                     coat=0.5)
    steel = bkit.pbr("DozerSteel", base=(0.36, 0.37, 0.39), metal=0.55,
                     rough=0.42)
    dark = bkit.preset("dark_metal")
    glass = bkit.pbr("DozerGlass", base=(0.055, 0.062, 0.070), rough=0.06)

    def track(tag, y):
        bkit.rounded_box("DozerTrack" + tag, SPEC["track_length"],
                         SPEC["track_width"], 900.0, r=430.0, segments=4,
                         centre=(TRACK_X, y, 450.0), mat=steel)
        V.strut("DozerIdler" + tag, (TRACK_X - 1700.0, y, 450.0),
                (TRACK_X + 1700.0, y, 450.0), 60.0, dark, 14)

    track("L", SPEC["track_gauge"] / 2.0)
    track("R", -SPEC["track_gauge"] / 2.0)

    bkit.rounded_box("DozerChassis", 3400.0, 2200.0, 500.0, r=70.0, segments=3,
                     centre=(-300.0, 0.0, 1200.0), mat=dark)
    hood = [
        (1400.0, 780.0, 1150.0, 1700.0, 4.6),
        (1900.0, 860.0, 1150.0, 1820.0, 4.6),
        (2300.0, 900.0, 1150.0, 1760.0, 4.4),
        (2600.0, 900.0, 1180.0, 1560.0, 4.0),
        (2750.0, 860.0, 1200.0, 1380.0, 3.6),
    ]
    V.shell("DozerHood", hood, mat=paint, steps=48)

    bkit.rounded_box("DozerCab", 1500.0, 1900.0, 1400.0, r=90.0, segments=3,
                     centre=(-600.0, 0.0, 2100.0), mat=paint)
    V.mirror_y(bkit.rounded_box("DozerCabGlass", 1300.0, 30.0, 1150.0, r=14.0,
                                segments=2, centre=(-600.0, 965.0, 2150.0),
                                mat=glass))
    bkit.rounded_box("DozerScreen", 30.0, 1700.0, 1150.0, r=14.0, segments=2,
                     centre=(165.0, 0.0, 2150.0), mat=glass)
    bkit.rounded_box("DozerRoof", 1600.0, 2000.0, 90.0, r=40.0, segments=2,
                     centre=(-600.0, 0.0, 2830.0), mat=steel)
    bkit.cylinder("DozerExhaust", 70.0, 1500.0, segments=18, axis="Z",
                  centre=(1500.0, 0.0, 2450.0), mat=dark)

    blade = bkit.extrude_profile("DozerBlade", blade_profile(),
                                 SPEC["blade_width"], axis="Y", mat=steel)
    V.freeze(blade)
    blade.location = (0.0, 0.0, 0.0)
    bkit.move(blade, BLADE_X, 0.0, 0.0)
    bkit.recalc(blade)
    bkit.rounded_box("DozerCuttingEdge", 200.0, SPEC["blade_width"], 130.0,
                     r=30.0, segments=2, centre=(BLADE_X - 30.0, 0.0, 65.0),
                     mat=dark)
    V.mirror_y(bkit.rounded_box("DozerPushArm", 1200.0, 160.0, 260.0, r=40.0,
                                segments=2, centre=(2500.0, 800.0, 400.0),
                                mat=dark))

    V.mirror_y(V.box_lamp("DozerHeadlamps", 90.0, 240.0, 200.0,
                          (2800.0, 560.0, 1300.0),
                          bkit.pbr("DozerLens", base=(0.86, 0.86, 0.90),
                                   rough=0.08, transmission=0.5), r=24.0))
    bkit.rounded_box("DozerRipper", 900.0, 1600.0, 400.0, r=50.0, segments=2,
                     centre=(-2680.0, 0.0, 500.0), mat=dark)

    return dict(spec=SPEC, parts=17)