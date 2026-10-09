"""
jet_ski -- 1.18 m stand-up personal watercraft, 1180 x 480 x 900 mm.

The catalog classes this item `medium` (150-600 mm, scored to a 1200 mm cap),
so it is built at the size of the real machine that class names: a pool /
mini stand-up PWC at 1.18 m rather than a 3.4 m touring ski. The read is
three things: a deep-V planing hull with a hard chine, a single tall handlebar
on a leaning front console, and a jet nozzle with a steering deflector instead
of a propeller -- no screw anywhere in the model.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=1180.0,
    beam=480.0,
    hull_depth=300.0,
    handlebar_height=880.0,
    bar_width=480.0,
    seat_height=420.0,
)

CHECKS = [
    dict(name="length", mm=1180.0, tol=3.0, how="bbox_x", part="JetSkiHull"),
    dict(name="beam", mm=480.0, tol=3.0, how="bbox_y", part="JetSkiHull"),
    dict(name="hull_depth", mm=300.0, tol=3.0, how="bbox_z", part="JetSkiHull"),
    dict(name="handlebar_height", mm=880.0, tol=6.0, how="top_z",
         part="JetSkiHandlebar"),
    dict(name="bar_width", mm=480.0, tol=4.0, how="bbox_y",
         part="JetSkiHandlebar"),
    dict(name="seat_height", mm=420.0, tol=5.0, how="top_z",
         part="JetSkiSeat"),
]

# (x, half beam, keel, deck, bottom ratio) -- hard chine, flat transom
STATIONS = [
    (-590.0, 150.0, 60.0, 200.0, 0.88),
    (-520.0, 200.0, 30.0, 230.0, 0.86),
    (-300.0, 235.0, 0.0, 280.0, 0.84),
    (0.0, 240.0, 0.0, 300.0, 0.82),
    (280.0, 225.0, 0.0, 285.0, 0.72),
    (480.0, 165.0, 20.0, 250.0, 0.52),
    (580.0, 80.0, 70.0, 210.0, 0.36),
    (590.0, 30.0, 110.0, 190.0, 0.30),
]


def build():
    shell = bkit.pbr("JetSkiShell", base=(0.06, 0.20, 0.52), rough=0.14,
                     coat=0.7)
    accent = bkit.pbr("JetSkiAccent", base=(0.82, 0.86, 0.90), rough=0.18,
                      coat=0.6)
    dark = bkit.preset("dark_metal")
    seat = bkit.pbr("JetSkiSeat", base=(0.07, 0.08, 0.10), rough=0.62)

    hull = V.hull("JetSkiHull", STATIONS, mat=shell, smooth=32.0)
    bkit.assign_faces_by(hull, accent,
                         lambda c, n: (c.x / bkit.MM > 150.0 and n.z > 0.2))
    bkit.rounded_box("JetSkiDeck", 900.0, 420.0, 40.0, r=18.0, segments=2,
                     centre=(60.0, 0.0, 290.0), mat=accent)
    bkit.rounded_box("JetSkiSeat", 420.0, 300.0, 60.0, r=26.0, segments=3,
                     centre=(-60.0, 0.0, 390.0), mat=seat)
    bkit.rounded_box("JetSkiSeatBack", 90.0, 320.0, 200.0, r=40.0,
                     segments=3, centre=(-260.0, 0.0, 400.0), mat=seat)
    bkit.rounded_box("JetSkiConsole", 260.0, 260.0, 380.0, r=70.0, segments=3,
                     centre=(250.0, 0.0, 480.0), mat=shell)
    bkit.rounded_box("JetSkiHandlebar", 90.0, 480.0, 70.0, r=32.0, segments=3,
                     centre=(255.0, 0.0, 845.0), mat=dark)
    bkit.rounded_box("JetSkiBarPad", 110.0, 200.0, 90.0, r=40.0, segments=3,
                     centre=(255.0, 0.0, 845.0), mat=seat)
    for i, s in enumerate((1, -1)):
        V.strut("JetSkiGrip%d" % i, (255.0, s * 150.0, 845.0),
                (245.0, s * 240.0, 855.0), 26.0, seat, 12)
        bkit.rounded_box("JetSkiSponson%d" % i, 700.0, 90.0, 130.0, r=60.0,
                         segments=3, centre=(-60.0, s * 230.0, 150.0),
                         mat=accent)
    # jet pump: intake grate forward, nozzle and steering deflector aft
    bkit.rounded_box("JetSkiIntake", 260.0, 240.0, 30.0, r=12.0, segments=2,
                     centre=(-380.0, 0.0, 250.0), mat=dark)
    # a nozzle is a short truncated cone: `cylinder(r2=)` does it with an axis
    # in one call. `lathe()` has no `axis` argument, and a profile that
    # repeats its first point leaves a degenerate face row.
    bkit.cylinder("JetSkiNozzle", 86.0, 170.0, r2=60.0, segments=28,
                  centre=(-460.0, 0.0, 130.0), axis="X", mat=dark)
    bkit.rounded_box("JetSkiDeflector", 150.0, 170.0, 60.0, r=26.0,
                     segments=3, centre=(-480.0, 0.0, 300.0), mat=accent)
    bkit.rounded_box("JetSkiTowEye", 90.0, 90.0, 40.0, r=18.0, segments=2,
                     centre=(560.0, 0.0, 180.0), mat=dark)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=13)
