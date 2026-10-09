"""
apron -- a 900 mm bib apron, 516 mm at the hem, with neck strap and waist ties.

An apron is the one garment that is genuinely FLAT, so its real thickness comes
from the section rather than from a boolean: the sweep is 12 mm through, and
because the cap is kept the panel is already a closed solid. A `shell()` cavity
would be wrong here -- it would turn a flat piece of cloth into a bag.

The outline is what makes it an apron and not a tea towel: a narrow bib, a pinch
at the waist, then a wide skirt. The pocket, straps and ties are separate parts
because they are the features that read.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=900.0,
    hem_width=516.0,
    waist_width=470.0,
    bib_width=276.0,
    thickness=12.0,
    pocket_width=400.0,
    pocket_height=170.0,
    neck_strap_rise=80.0,
)

T = SPEC["thickness"] / 2.0
STEPS = 44


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


# The apron outline, as (z, half_width). Two tapers, not one: out to the skirt
# and back in to the bib, with a pinch at the waist between them.
OUTLINE = [
    (0.0, 258.0),      # hem
    (200.0, 258.0),
    (420.0, 250.0),
    (560.0, 235.0),    # waist
    (680.0, 205.0),
    (800.0, 165.0),
    (880.0, 142.0),
    (900.0, 138.0),    # bib top
]


def _mm(v):
    return v / bkit.MM


def build():
    canvas = bkit.pbr("ApronCanvas", base=(0.360, 0.330, 0.300), rough=0.94)
    canvas_pocket = bkit.pbr("ApronPocket", base=(0.310, 0.285, 0.258),
                             rough=0.95)
    webbing = bkit.pbr("ApronWebbing", base=(0.235, 0.215, 0.195), rough=0.88)

    path = [(0.0, 0.0, z) for (z, _w) in OUTLINE]
    half = [(w, T) for (_z, w) in OUTLINE]
    panel = sweep("ApronPanel", path, half, n=3.6, mat=canvas)
    bkit.assign_faces_by(
        panel, canvas_pocket,
        lambda c, n: _mm(c.z) < 300.0 and abs(_mm(c.y)) > 2.0,
    )

    # ---- pocket across the skirt, standing 14 mm off the panel ------------
    bkit.rounded_box("ApronPocket", SPEC["pocket_width"], 30.0,
                     SPEC["pocket_height"], r=8.0, segments=3,
                     centre=(0.0, -14.0, 330.0), mat=canvas_pocket)

    # ---- neck strap: the mug-handle trick, tips buried in the bib top ----
    a, rise = 138.0, SPEC["neck_strap_rise"]
    k = (a * a - rise * rise) / (2.0 * rise)
    rmaj = rise + k
    ang = math.degrees(math.atan2(k, a))
    bkit.arc_torus("ApronNeckStrap", rmaj, 5.0, ang, 180.0 - ang,
                   centre=(0.0, 0.0, 900.0 - k), plane="XZ", seg_major=40,
                   mat=webbing, caps=True)

    # ---- two waist ties, the same sweep at two transforms ----------------
    for i, sx in enumerate((1.0, -1.0)):
        sweep("ApronTie%d" % (i + 1), [
            (sx * 230.0, -6.0, 566.0),
            (sx * 300.0, -22.0, 540.0),
            (sx * 360.0, -30.0, 512.0),
        ], [(14.0, 5.0), (13.0, 5.0), (12.0, 5.0)], steps=24, n=3.2,
            mat=webbing)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="length", mm=900.0, tol=1.0, how="bbox_z", part="ApronPanel"),
    dict(name="hem_width", mm=516.0, tol=2.0, how="bbox_x", part="ApronPanel"),
    dict(name="thickness", mm=12.0, tol=1.0, how="bbox_y", part="ApronPanel"),
    dict(name="pocket_width", mm=400.0, tol=1.0, how="bbox_x",
         part="ApronPocket"),
    dict(name="pocket_height", mm=170.0, tol=1.0, how="bbox_z",
         part="ApronPocket"),
    # The tie straps hang outboard of the 516 mm panel, so the whole apron is
    # 726 mm across even though the hem itself is 516.
    dict(name="overall_width", mm=725.9, tol=6.0, how="bbox_x"),
]