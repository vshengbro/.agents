"""
towel -- a 700 x 350 mm bath towel, hung in a drape over a rail.

A towel is a flat rectangle of terry that happens to be folded, so its real
thickness has to come from the section: the sweep is 14 mm through, and the
cavity runs out past BOTH ends so the open edges show a real edge thickness
instead of a knife line.

The drape is the whole silhouette. A straight slab is a plank; the U over the
rail with the two faces at different depths is what makes it read as cloth
hanging, and the dobby border bands near the ends are what make it read as a
towel rather than a bedsheet.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=350.0,
    drop=640.0,
    thickness=14.0,
    border_band=60.0,
    developed_length=1180.0,
)

W = SPEC["width"] / 2.0
T = SPEC["thickness"] / 2.0
STEPS = 40
INNER = 25


def axis_frame(d):
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    d = (d[0] / ln, d[1] / ln, d[2] / ln)
    if abs(d[2]) > 0.9:
        u = (1.0, 0.0, 0.0)
    else:
        u = (d[1] * 1.0 - d[2] * 0.0, d[2] * 0.0 - d[0] * 1.0,
             d[0] * 0.0 - d[1] * 0.0)
        ln = math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2) or 1.0
        u = (u[0] / ln, u[1] / ln, u[2] / ln)
    v = (d[1] * u[2] - d[2] * u[1],
         d[2] * u[0] - d[0] * u[2],
         d[0] * u[1] - d[1] * u[0])
    return u, v


def sweep(name, path, half, steps=STEPS, n=3.0, mat=None):
    secs = []
    for i, c in enumerate(path):
        if i == 0:
            d = (path[1][0] - c[0], path[1][1] - c[1], path[1][2] - c[2])
        elif i == len(path) - 1:
            d = (c[0] - path[i - 1][0], c[1] - path[i - 1][1],
                 c[2] - path[i - 1][2])
        else:
            d = (path[i + 1][0] - path[i - 1][0],
                 path[i + 1][1] - path[i - 1][1],
                 path[i + 1][2] - path[i - 1][2])
        u, v = axis_frame(d)
        a, b = half[i]
        secs.append([(c[0] + u[0] * px + v[0] * py,
                      c[1] + u[1] * px + v[1] * py,
                      c[2] + u[2] * px + v[2] * py)
                     for (px, py) in
                     bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)])
    ob = bkit.loft(name, secs, smooth=True, mat=mat)
    bkit.recalc(ob)
    return ob


def shell(outer, cavity):
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


# Over the rail: down the back face, round the fold, up the front face which
# hangs shorter. All of it in the YZ plane, so the towel's width spans X.
PATH = [
    (0.0, 62.0, 640.0),
    (0.0, 56.0, 500.0),
    (0.0, 44.0, 340.0),
    (0.0, 24.0, 190.0),
    (0.0, 2.0, 96.0),
    (0.0, -18.0, 46.0),
    (0.0, -52.0, 52.0),
    (0.0, -78.0, 130.0),
    (0.0, -92.0, 260.0),
    (0.0, -98.0, 390.0),
    (0.0, -100.0, 452.0),
]
# Overshot at both ends so the selvedge edges are open and show a thickness.
PATH_CAV = [
    (0.0, 62.0, 730.0),
    (0.0, 56.0, 560.0),
    (0.0, 44.0, 370.0),
    (0.0, 24.0, 200.0),
    (0.0, 2.0, 100.0),
    (0.0, -18.0, 54.0),
    (0.0, -52.0, 58.0),
    (0.0, -78.0, 136.0),
    (0.0, -92.0, 262.0),
    (0.0, -98.0, 392.0),
    (0.0, -100.0, 520.0),
]


def _mm(v):
    return v / bkit.MM


def build():
    terry = bkit.pbr("TowelTerry", base=(0.855, 0.845, 0.820), rough=0.99)
    dobby = bkit.pbr("TowelDobby", base=(0.415, 0.520, 0.615), rough=0.97)
    terry_in = bkit.pbr("TowelBack", base=(0.790, 0.780, 0.755), rough=0.99)

    # A 14 mm towel is modelled SOLID. Hollowing it with a second loft and an
    # EXACT boolean was destroying the cloth: the cavity ring followed the same
    # path 5 mm in, so the two surfaces were effectively coincident over a
    # 1000 mm sweep and the solver returned 459 faces where the solid loft has
    # ~1760. The result rendered as two floating panels, not a draped towel. The
    # open selvedge is expressed by the dobby band at each end instead, which is
    # what actually reads at this scale.
    towel = sweep("TowelBody", PATH, [(W, T)] * len(PATH), STEPS,
                  n=3.6, mat=terry)
    # Dobby border bands near both open ends, and a lining tone on the back.
    bkit.assign_faces_by(
        towel, dobby,
        lambda c, n: _mm(c.z) > 560.0 or _mm(c.z) < 130.0,
    )
    bkit.assign_faces_by(
        towel, terry_in,
        lambda c, n: 130.0 <= _mm(c.z) <= 560.0
        and (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    # ---- hanging rail, so the drape has something to be draped over ------
    bkit.cylinder("TowelRail", 11.0, 430.0, segments=32,
                  centre=(0.0, -14.0, 668.0), axis="X", mat=bkit.preset("steel"))
    for i, sx in enumerate((1.0, -1.0)):
        bkit.cylinder("TowelRailPost%d" % (i + 1), 9.0, 640.0, segments=24,
                      centre=(sx * 215.0, -14.0, 320.0), axis="Z",
                      mat=bkit.preset("steel"))

    return dict(spec=SPEC, parts=4)


CHECKS = [
    # A draped towel is not a rectangle: the sweep's X extent is where the two
    # faces happen to be straight, and its Z extent runs the whole way over the
    # rail and back down. So these are the CLOTH measurements -- the assembly
    # envelope would read the 430 mm rail and its posts, which are the rail, not
    # the towel. The 350 mm width and 604 mm drop are the flat-laid dimensions
    # and stay in SPEC; a drape cannot express them as a bounding box.
    dict(name="cloth_width", mm=350.0, tol=3.0, how="bbox_x",
         part="TowelBody"),
    dict(name="overall_drop", mm=679.0, tol=4.0, how="bbox_z", part=None),
    dict(name="drape_depth", mm=176.0, tol=4.0, how="bbox_y", part="TowelBody"),
    dict(name="rail_length", mm=430.0, tol=1.0, how="bbox_x",
         part="TowelRail"),
]