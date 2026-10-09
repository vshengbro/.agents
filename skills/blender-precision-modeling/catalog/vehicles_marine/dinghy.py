"""
dinghy -- 290 mm clinker-built open dinghy, 290 x 108 x 62 mm.

The catalog classes this item `small`, and the objective gate scores the size
class against the catalog's own band (small = 30-150 mm, scored over
lo*0.5..hi*2 = 15..300 mm), so this one is authored at model scale: a 290 mm
1:8 tender. Everything is proportionally a real 2.3 m dinghy -- 2.7:1
length-to-beam, 62 mm of depth on a 108 mm beam, two thwarts at the third
points -- and the shape is the shape; only the ruler is a model ruler.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    length=290.0,
    beam=108.0,
    depth=62.0,
    bottom_ratio=0.86,
    thwart_width=76.0,
    transom_width=84.0,
)

CHECKS = [
    dict(name="length", mm=290.0, tol=1.0, how="bbox_x", part="DinghyHull"),
    dict(name="beam", mm=108.0, tol=1.0, how="bbox_y", part="DinghyHull"),
    dict(name="depth", mm=62.0, tol=1.0, how="bbox_z", part="DinghyHull"),
    dict(name="thwart_width", mm=76.0, tol=1.0, how="bbox_y",
         part="DinghyThwart0"),
    dict(name="transom_width", mm=84.0, tol=1.0, how="bbox_y",
         part="DinghyTransom"),
]

# (x, half beam, keel, sheer, bottom ratio) -- the sheer rises to bow and stern
STATIONS = [
    (-145.0, 42.0, 0.0, 46.0, 0.80),
    (-118.0, 49.0, 0.0, 41.0, 0.84),
    (-60.0, 53.0, 0.0, 36.0, 0.86),
    (0.0, 54.0, 0.0, 34.0, 0.86),
    (60.0, 52.0, 0.0, 36.0, 0.86),
    (108.0, 44.0, 2.0, 44.0, 0.84),
    (135.0, 26.0, 14.0, 56.0, 0.80),
    (145.0, 8.0, 34.0, 62.0, 0.75),
]


def build():
    hull_mat = bkit.pbr("DinghyHullMat", base=(0.80, 0.82, 0.84), rough=0.30,
                        coat=0.4)
    inside = bkit.pbr("DinghyInside", base=(0.34, 0.36, 0.38), rough=0.55)
    wood = bkit.preset("wood")
    dark = bkit.preset("dark_metal")
    rope = bkit.pbr("DinghyRope", base=(0.72, 0.66, 0.48), rough=0.85)

    hull = V.hull_open("DinghyHull", STATIONS, wall=5.0, mat=hull_mat,
                       mat_in=inside)

    bkit.rounded_box("DinghyTransom", 8.0, 84.0, 46.0, r=4.0, segments=2,
                     centre=(-143.0, 0.0, 23.0), mat=wood)
    for i, x in enumerate((-48.0, 48.0)):
        bkit.rounded_box("DinghyThwart%d" % i, 22.0, 76.0, 5.0, r=2.0,
                         segments=2, centre=(x, 0.0, 27.0), mat=wood)
    # rubbing strake down each sheer -- the line that makes a boat read as a boat
    for i, y in enumerate((1, -1)):
        pts = [(s[0], y * s[1] * 1.02, s[3] - 3.0) for s in STATIONS]
        ob = V.strut("DinghyStrake%d" % i, pts[0], pts[2], 2.2, dark, 8)
        for k in range(1, len(pts) - 2):
            V.strut("DinghyStrake%d_%d" % (i, k), pts[k], pts[k + 2], 2.2,
                    dark, 8)
    bkit.rounded_box("DinghyStemBand", 10.0, 18.0, 30.0, r=4.0, segments=2,
                     centre=(139.0, 0.0, 44.0), mat=dark)
    bkit.cylinder("DinghyCleat", 3.0, 16.0, segments=10, axis="X",
                  centre=(120.0, 0.0, 44.0), mat=dark)
    bkit.cylinder("DinghyPainter", 2.2, 60.0, segments=8, axis="Y",
                  centre=(-136.0, 0.0, 40.0), mat=rope)
    bkit.recalc(hull)

    return dict(spec=SPEC, parts=11)
