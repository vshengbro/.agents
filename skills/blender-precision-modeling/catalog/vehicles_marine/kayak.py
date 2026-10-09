"""
kayak -- 5.0 m sea kayak with a cockpit, 5000 x 560 x 430 mm.

A touring sea kayak is a canoe with volume: the section is a low superellipse
rather than a circle (bottom ratio 0.62), the deck line is nearly flat because
a paddler has to lie on it, and there is exactly one opening -- a 700 x 480 mm
cockpit with a raised coaming, positioned where the paddler's hips go, not
centred. The bow and stern both rise to knife edges; the ends are the only place
the beam goes below 200 mm.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=5000.0,
    beam=560.0,
    deck_height=430.0,
    hull_depth=280.0,
    cockpit_length=740.0,
    cockpit_width=480.0,
    coaming_height=60.0,
)

CHECKS = [
    dict(name="length", mm=5000.0, tol=3.0, how="bbox_x", part="KayakHull"),
    dict(name="beam", mm=560.0, tol=3.0, how="bbox_y", part="KayakHull"),
    dict(name="height", mm=430.0, tol=3.0, how="bbox_z", part="KayakHull"),
    dict(name="cockpit_width", mm=480.0, tol=4.0, how="bbox_y",
         part="KayakCoaming"),
    dict(name="coaming_height", mm=60.0, tol=3.0, how="bbox_z",
         part="KayakCoaming"),
]

# (x, half beam, keel, deck, bottom ratio) -- the deck line is nearly flat
STATIONS = [
    (-2500.0, 34.0, 150.0, 380.0, 0.70),
    (-2350.0, 130.0, 70.0, 405.0, 0.66),
    (-1900.0, 224.0, 20.0, 420.0, 0.62),
    (-1000.0, 272.0, 0.0, 428.0, 0.62),
    (0.0, 280.0, 0.0, 430.0, 0.62),
    (1000.0, 276.0, 0.0, 428.0, 0.62),
    (1800.0, 244.0, 8.0, 418.0, 0.64),
    (2300.0, 148.0, 46.0, 396.0, 0.68),
    (2500.0, 40.0, 130.0, 360.0, 0.72),
]

# the one opening: a vertical cylinder is the safest cut there is -- no
# tangential faces, no shared facets with the deck
COCKPIT_X = -150.0
COCKPIT_R = 240.0


def build():
    shell = bkit.pbr("KayakShell", base=(0.90, 0.88, 0.84), rough=0.12,
                     coat=0.7)
    deck = bkit.pbr("KayakDeck", base=(0.86, 0.34, 0.05), rough=0.20,
                    coat=0.5)
    dark = bkit.pbr("KayakCockpit", base=(0.07, 0.08, 0.10), rough=0.55)
    trim = bkit.preset("dark_metal")

    hull = V.hull("KayakHull", STATIONS, mat=shell, smooth=34.0)
    # deck panel: the closed foredeck and afterdeck, painted, not a second
    # solid -- a second object there would z-fight with the hull
    sheer = 430.0
    bkit.assign_faces_by(hull, deck,
                         lambda c, n: (abs(c.x / bkit.MM) > 520.0
                                       and n.z > 0.30))

    # cut the cockpit straight down through the deck
    cut = bkit.cylinder("_cockpit", COCKPIT_R, 520.0, segments=48,
                        centre=(COCKPIT_X, 0.0, 240.0), axis="Z")
    bkit.boolean(hull, cut, "DIFFERENCE")
    bkit.recalc(hull)
    bkit.assign_faces_by(hull, dark, lambda c, n: (abs(c.x / bkit.MM -
                                                      COCKPIT_X) < 250.0
                                                   and n.z < -0.3))

    bkit.tube("KayakCoaming", 240.0, 216.0, 60.0, segments=48,
              centre=(COCKPIT_X, 0.0, 358.0), mat=trim)
    bkit.rounded_box("KayakSeat", 420.0, 300.0, 60.0, r=25.0, segments=3,
                     centre=(COCKPIT_X, 0.0, 40.0), mat=dark)
    # deck lines: a bungee run and two grab handles, the sea kayak's read
    for i, x in enumerate((-1500.0, 1500.0)):
        bkit.rounded_box("KayakBungee%02d" % i, 700.0, 40.0, 12.0, r=6.0,
                         segments=2, centre=(x, 0.0, 424.0), mat=trim)
    bkit.rounded_box("KayakGrab", 260.0, 60.0, 24.0, r=12.0, segments=2,
                     centre=(300.0, 0.0, 434.0), mat=trim)
    bkit.torus("KayakBowLoop", 30.0, 6.0, seg_major=28, seg_minor=10,
               centre=(2440.0, 0.0, 372.0), axis="X", mat=trim)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=9)
