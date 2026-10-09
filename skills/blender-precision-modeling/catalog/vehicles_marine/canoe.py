"""
canoe -- 5.2 m flat-water racing canoe, 5200 x 420 x 300 mm.

A racing canoe is a 12:1 blade, so almost everything here is one decision: the
half beam is 210 mm and never varies by more than 20 mm over the middle three
metres, and the sections are near-circular (bottom ratio 0.40) because a
slender deck has no flat. What makes it a canoe rather than a torpedo is the
rocker -- the keel lifts 250 mm at each end -- plus a 45 mm cockpit cut into the
top and a pair of seat pads. The whole boat is symmetric fore and aft; a
`mirror_y` strake line and the two pads are the only asymmetry.
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
    beam=420.0,
    depth=300.0,
    cockpit_length=1100.0,
    cockpit_width=360.0,
    seat_height=255.0,
    bottom_ratio=0.40,
)

CHECKS = [
    dict(name="length", mm=5200.0, tol=3.0, how="bbox_x", part="CanoeHull"),
    dict(name="beam", mm=420.0, tol=3.0, how="bbox_y", part="CanoeHull"),
    dict(name="depth", mm=300.0, tol=3.0, how="bbox_z", part="CanoeHull"),
    dict(name="seat_height", mm=255.0, tol=3.0, how="top_z", part="CanoeSeat0"),
    dict(name="cockpit_width", mm=360.0, tol=4.0, how="bbox_y",
         part="CanoeCockpit"),
]

# (x, half beam, keel, sheer, bottom ratio) -- 12:1, so the beam is nearly
# constant and all the shape is in the keel rise and the sheer line
STATIONS = [
    (-2600.0, 128.0, 108.0, 196.0, 0.55),
    (-2450.0, 178.0, 30.0, 232.0, 0.50),
    (-1900.0, 202.0, 0.0, 268.0, 0.44),
    (-900.0, 210.0, 0.0, 296.0, 0.40),
    (0.0, 210.0, 0.0, 300.0, 0.40),
    (900.0, 208.0, 0.0, 296.0, 0.40),
    (1900.0, 198.0, 0.0, 266.0, 0.44),
    (2400.0, 152.0, 22.0, 228.0, 0.52),
    (2600.0, 62.0, 128.0, 196.0, 0.60),
]


def build():
    gel = bkit.pbr("CanoeGelcoat", base=(0.86, 0.30, 0.06), rough=0.14,
                   coat=0.6)
    inside = bkit.pbr("CanoeCockpitMat", base=(0.10, 0.11, 0.13), rough=0.60)
    pad = bkit.pbr("CanoePad", base=(0.06, 0.07, 0.09), rough=0.70)
    trim = bkit.preset("dark_metal")

    hull = V.hull_open("CanoeHull", STATIONS, wall=30.0, mat=gel, mat_in=inside,
                       k=0.40)

    # cockpit coaming: a raised ring is what makes the opening read as an
    # opening rather than a slot, and it hides the cut edge of the cavity.
    # A closed ring is `tube()`, never `lathe()` on a profile that repeats its
    # first point -- that degenerate face row is 40 non-manifold edges.
    bkit.tube("CanoeCockpit", 180.0, 150.0, 22.0, segments=44,
              centre=(0.0, 0.0, 252.0), mat=trim)

    for i, x in enumerate((-260.0, 260.0)):
        bkit.rounded_box("CanoeSeat%d" % i, 190.0, 300.0, 12.0, r=5.0,
                         segments=2, centre=(x, 0.0, 249.0), mat=pad)
    for i, x in enumerate((-560.0, 560.0)):
        bkit.rounded_box("CanoeFootBrace%d" % i, 60.0, 300.0, 60.0, r=10.0,
                         segments=2, centre=(x, 0.0, 190.0), mat=trim)
    bkit.rounded_box("CanoeDeckStripe", 2400.0, 26.0, 8.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 300.0), mat=bkit.preset("white_plastic"))
    bkit.torus("CanoeBowEye", 26.0, 5.0, seg_major=32, seg_minor=12,
               centre=(2560.0, 0.0, 196.0), axis="X", mat=trim)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=8)
