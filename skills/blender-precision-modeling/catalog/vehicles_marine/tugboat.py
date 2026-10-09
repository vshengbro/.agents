"""
tugboat -- 32 m harbour tug, 32000 x 12000 x 6200 mm.

A tug's proportions are aggressive on purpose: 12 m of beam on 32 m of length
is 2.7:1 against a ferry's 3.8:1, and the sheer is high (4200 mm) with a
shallow draught (2600 mm), so the freeboard is half the depth of the hull. The
second decision is the fender -- a 500 mm rubber belt right round the sheer,
which is the only part of a tug that ever touches anything. The third is the
towing winch on the after deck with a staple and a fairlead.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=32000.0,
    beam=12000.0,
    hull_depth=4200.0,
    draught=2600.0,
    fender_height=500.0,
    wheelhouse_top_z=6200.0,
    funnel_top_z=5400.0,
)

CHECKS = [
    dict(name="length", mm=32000.0, tol=10.0, how="bbox_x", part="TugHull"),
    dict(name="beam", mm=12000.0, tol=10.0, how="bbox_y", part="TugHull"),
    dict(name="hull_depth", mm=4200.0, tol=10.0, how="bbox_z", part="TugHull"),
    dict(name="sheer_z", mm=4200.0, tol=10.0, how="top_z", part="TugHull"),
    dict(name="fender_height", mm=500.0, tol=20.0, how="bbox_z",
         part="TugFenderP"),
    dict(name="wheelhouse_top_z", mm=6200.0, tol=15.0, how="top_z",
         part="TugWheelhouse"),
    dict(name="funnel_top_z", mm=5400.0, tol=15.0, how="top_z",
         part="TugFunnel"),
]

# (x, half beam, keel, sheer, bottom ratio) -- full sections, hard shoulders
STATIONS = [
    (-16000.0, 4400.0, 2600.0, 3900.0, 0.80),
    (-14000.0, 5600.0, 2200.0, 4100.0, 0.88),
    (-8000.0, 6000.0, 1600.0, 4200.0, 0.92),
    (0.0, 6000.0, 1400.0, 4200.0, 0.92),
    (6000.0, 5900.0, 1200.0, 4100.0, 0.90),
    (11000.0, 5400.0, 700.0, 3900.0, 0.82),
    (14500.0, 4200.0, 300.0, 3600.0, 0.70),
    (16000.0, 2200.0, 0.0, 3300.0, 0.60),
]


def build():
    topside = bkit.pbr("TugTopside", base=(0.70, 0.09, 0.07), rough=0.30,
                       coat=0.3)
    boot = bkit.pbr("TugBoot", base=(0.06, 0.07, 0.09), rough=0.45)
    deck_mat = bkit.pbr("TugDeck", base=(0.30, 0.31, 0.29), rough=0.68)
    house = bkit.pbr("TugHouse", base=(0.88, 0.87, 0.83), rough=0.24)
    glass = bkit.pbr("TugGlass", base=(0.05, 0.06, 0.08), rough=0.05)
    rubber = bkit.preset("rubber")
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    hull = V.hull("TugHull", STATIONS, mat=topside, smooth=28.0)
    bkit.assign_faces_by(hull, boot, lambda c, n: c.z / bkit.MM < 1500.0)
    bkit.assign_faces_by(hull, deck_mat, lambda c, n: n.z > 0.75)

    # fender belt: a rounded box down each flank, its own object because it is
    # a different material and a different thickness (500 mm) from the plating
    fender = bkit.rounded_box("TugFenderP", 27000.0, 700.0, 500.0, r=240.0,
                              segments=4, centre=(0.0, 6050.0, 3900.0),
                              mat=rubber)
    bkit.mirror(fender, "Y")

    wh = bkit.rounded_box("TugWheelhouse", 7000.0, 8000.0, 2600.0, r=200.0,
                          segments=3, centre=(-2000.0, 0.0, 4900.0), mat=house)
    V.window_band(wh, 4600.0, 5700.0, glass, max_nz=0.6)
    bkit.rounded_box("TugWheelhouseRoof", 7400.0, 8400.0, 160.0, r=80.0,
                     segments=2, centre=(-2000.0, 0.0, 6120.0), mat=house)
    bkit.rounded_box("TugFunnel", 2600.0, 3000.0, 1800.0, r=200.0,
                     segments=3, centre=(-7000.0, 0.0, 4500.0),
                     mat=bkit.pbr("TugFunnelMat", base=(0.10, 0.10, 0.12),
                                  rough=0.35))
    bkit.cylinder("TugExhaust", 260.0, 900.0, segments=14, axis="Z",
                  centre=(-7000.0, 900.0, 5800.0), mat=dark)
    bkit.rounded_box("TugAccommodation", 7000.0, 8000.0, 2100.0, r=200.0,
                     segments=3, centre=(-11500.0, 0.0, 5000.0), mat=house)
    bkit.cylinder("TugMast", 130.0, 2200.0, segments=12, axis="Z",
                  centre=(-2000.0, 0.0, 7000.0), mat=steel)
    bkit.cylinder("TugSearchlight", 340.0, 420.0, segments=20, axis="Z",
                  centre=(-2000.0, 0.0, 7900.0), mat=steel)

    # towing gear on the after deck: winch, staple, fairlead and a hook
    bkit.cylinder("TugTowingWinch", 800.0, 2600.0, segments=24, axis="Y",
                  centre=(9000.0, 0.0, 4700.0), mat=dark)
    bkit.rounded_box("TugWinchFrame", 2400.0, 3400.0, 700.0, r=120.0,
                     segments=2, centre=(9000.0, 0.0, 4300.0), mat=steel)
    bkit.rounded_box("TugStaple", 600.0, 3200.0, 900.0, r=120.0, segments=2,
                     centre=(12900.0, 0.0, 4400.0), mat=steel)
    bkit.rounded_box("TugBitt", 700.0, 1800.0, 900.0, r=100.0, segments=2,
                     centre=(13800.0, 0.0, 4400.0), mat=dark)
    for i, (x, _w) in enumerate(bkit.lay_out([4000.0, 4000.0], gap=6000.0)):
        for s in (1, -1):
            bkit.cylinder("TugCleat%d%s" % (i, "P" if s > 0 else "S"),
                          130.0, 900.0, segments=12, axis="Z",
                          centre=(x, s * 2100.0, 4300.0), mat=steel)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=18)
