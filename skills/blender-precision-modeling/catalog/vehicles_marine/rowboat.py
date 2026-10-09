"""
rowboat -- 4.8 m clinker rowing boat with three thwarts, 4800 x 1500 x 810 mm.

The read on a rowing boat is beam against length (3.2:1 -- three people abreast)
and rocker: the keel lifts 120 mm at the transom and 180 mm at the stem, so the
bottom is a curve and not a line. A 30 mm shell thickness cut as a cavity gives
the open boat; the three thwarts at 34 %, 50 % and 66 % of the length and the
pair of oars in their rowlocks are what stop it reading as a punt.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=4800.0,
    beam=1500.0,
    depth=810.0,
    shell_thickness=30.0,
    thwart_count=3,
    thwart_top_z=700.0,
    oar_length=3000.0,
)

CHECKS = [
    dict(name="length", mm=4800.0, tol=4.0, how="bbox_x", part="RowboatHull"),
    dict(name="beam", mm=1500.0, tol=4.0, how="bbox_y", part="RowboatHull"),
    dict(name="depth", mm=810.0, tol=4.0, how="bbox_z", part="RowboatHull"),
    dict(name="thwart_top_z", mm=700.0, tol=5.0, how="top_z",
         part="RowboatThwart1"),
    dict(name="oar_blade_length", mm=900.0, tol=6.0, how="bbox_x",
         part="RowboatBlade0"),
]

# (x, half beam, keel, sheer, bottom ratio) -- flat working bottom, hard sheer
STATIONS = [
    (-2400.0, 610.0, 120.0, 660.0, 0.72),
    (-2150.0, 700.0, 40.0, 700.0, 0.68),
    (-1200.0, 746.0, 0.0, 780.0, 0.66),
    (0.0, 750.0, 0.0, 810.0, 0.66),
    (1200.0, 730.0, 0.0, 790.0, 0.66),
    (2000.0, 630.0, 40.0, 720.0, 0.68),
    (2350.0, 400.0, 120.0, 620.0, 0.72),
    (2400.0, 190.0, 190.0, 560.0, 0.75),
]

THWART_X = (-1630.0, 0.0, 1580.0)


def build():
    topside = bkit.pbr("RowboatTopside", base=(0.20, 0.34, 0.52), rough=0.22,
                       coat=0.5)
    inside = bkit.pbr("RowboatInterior", base=(0.10, 0.11, 0.13), rough=0.55)
    wood = bkit.preset("wood")
    dark = bkit.preset("dark_metal")
    oar_mat = bkit.pbr("OarShaft", base=(0.78, 0.72, 0.58), rough=0.42)

    hull = V.hull_open("RowboatHull", STATIONS, wall=SPEC["shell_thickness"],
                       mat=topside, mat_in=inside)

    bkit.rounded_box("RowboatTransom", 60.0, 1180.0, 520.0, r=18.0,
                     segments=2, centre=(-2370.0, 0.0, 380.0), mat=wood)
    # the keel rabbet: its underside IS the floor datum, so it starts at z=0.
    # Anything authored below z=0 is lifted by sit_on_floor() and every
    # coordinate check in the file silently moves with it.
    bkit.rounded_box("RowboatKeel", 4200.0, 70.0, 60.0, r=20.0, segments=2,
                     centre=(-100.0, 0.0, 30.0), mat=dark)
    for i, x in enumerate(THWART_X):
        bkit.rounded_box("RowboatThwart%d" % i, 240.0, 1240.0, 30.0, r=6.0,
                         segments=2, centre=(x, 0.0, 685.0), mat=wood)
    # gunwale capping rail: the line that follows the sheer round the boat
    rail_pts = [(s[0], s[1] + 4.0, s[3] - 12.0) for s in STATIONS]
    parts = []
    for k in range(len(rail_pts) - 1):
        parts.append(V.strut("RowboatGunwale%02d" % k, rail_pts[k],
                             rail_pts[k + 1], 22.0, wood, 10))
    rail = bkit.join(parts, "RowboatGunwale")
    V.freeze(rail)
    bkit.mirror(rail, "Y")
    rail.name = "RowboatGunwale"

    for i, (sx, sy) in enumerate(((-1, 1), (1, -1))):
        oar = V.strut("RowboatOar%d" % i, (620.0 * sx, 300.0 * sy, 690.0),
                      (1620.0 * sx, 900.0 * sy, 700.0), 26.0, oar_mat, 12)
        V.freeze(oar)
        bkit.rounded_box("RowboatBlade%d" % i, 900.0, 150.0, 18.0, r=8.0,
                         segments=2, centre=(2020.0 * sx, 1000.0 * sy, 700.0),
                         mat=oar_mat)
        bkit.cylinder("RowboatRowlock%d" % i, 34.0, 90.0, segments=14,
                      axis="X", centre=(560.0 * sx, 560.0 * sy, 700.0),
                      mat=dark)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=12)
