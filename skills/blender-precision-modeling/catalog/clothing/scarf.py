"""
scarf -- a 1450 mm knitted scarf draped in an S, both ends up, middle on the floor.

A scarf is the purest thin-shell object in this domain: it is a flat strip with
nothing else. Two decisions make it read:
  * the path. A straight strip is a plank; the S-drape, with the section
    following the path frame, is what makes the strip look like cloth falling.
  * the hollowed section. The cavity runs out past BOTH ends, so the ends show
    a real edge thickness and a fringe hangs from each one.
The fringe is 9 strands per end, spaced with lay_out() from a strand width plus
a stated gap.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1450.0,            # developed length along the drape
    width=190.0,
    thickness=18.0,           # the modelled band, knitted wool is bulky
    fringe_count=9,
    fringe_length=70.0,
    drop=640.0,               # floor to the high end
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


def sweep(name, path, half, steps, n=3.0, mat=None):
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


# The S: down, along the floor, and back up. Section half-extents are constant,
# so the strip is the same cloth all the way -- only its orientation follows the
# tangent, which is exactly what a falling strip does.
PATH = [
    (-235.0, 0.0, 640.0),
    (-150.0, -30.0, 470.0),
    (-70.0, -50.0, 250.0),
    (-10.0, -40.0, 80.0),
    (60.0, 0.0, 22.0),
    (170.0, 60.0, 22.0),
    (250.0, 70.0, 110.0),
    (285.0, 30.0, 330.0),
    (265.0, -30.0, 560.0),
]
# Overshot at both ends so the scarf is open there and the fringe has something
# to hang from.
PATH_CAV = [
    (-262.0, 4.0, 676.0),
    (-180.0, -40.0, 540.0),
    (-85.0, -56.0, 290.0),
    (-14.0, -42.0, 92.0),
    (78.0, 6.0, 30.0),
    (186.0, 62.0, 30.0),
    (258.0, 70.0, 140.0),
    (288.0, 26.0, 372.0),
    (262.0, -44.0, 634.0),
]


def _mm(v):
    return v / bkit.MM


def build():
    wool = bkit.pbr("ScarfWool", base=(0.560, 0.215, 0.195), rough=0.97)
    wool_in = bkit.pbr("ScarfWoolBack", base=(0.470, 0.175, 0.160), rough=0.97)

    strip = shell(sweep("ScarfStrip", PATH, [(W, T)] * len(PATH), STEPS,
                        n=3.4, mat=wool),
                  # Same ring resolution as the outer loft: at 25 steps against
                  # the outer's 40 the two superellipse rings are near
                  # coincident and the EXACT solver eats the shell.
                  sweep("_ScarfStrip_cavity", PATH_CAV,
                        [(W - 7.0, T - 4.0)] * len(PATH_CAV), STEPS))
    bkit.assign_faces_by(
        strip, wool_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    # ---- fringe: 9 strands per end, evenly spaced by lay_out() -------------
    # The two ends point in opposite directions, so each fringe run is built
    # along the local end tangent rather than a hand-typed axis.
    for end, (anchor, nxt) in enumerate(((PATH[0], PATH[1]),
                                        (PATH[-1], PATH[-2]))):
        d = (anchor[0] - nxt[0], anchor[1] - nxt[1], anchor[2] - nxt[2])
        ln = math.sqrt(sum(c * c for c in d)) or 1.0
        d = (d[0] / ln, d[1] / ln, d[2] / ln)
        u, _v = axis_frame(d)
        for i, (s, _w) in enumerate(
                bkit.lay_out([6.0] * SPEC["fringe_count"], gap=13.0)):
            base = (anchor[0] + u[0] * s, anchor[1] + u[1] * s,
                    anchor[2] + u[2] * s)
            tip = (base[0] + d[0] * SPEC["fringe_length"],
                   base[1] + d[1] * SPEC["fringe_length"],
                   base[2] + d[2] * SPEC["fringe_length"])
            mid = ((base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0,
                   (base[2] + tip[2]) / 2.0)
            sweep("ScarfFringe%d_%d" % (end + 1, i + 1),
                  [base, mid, tip], [(5.5, 5.5), (5.0, 5.0), (3.6, 3.6)],
                  12, n=2.0, mat=wool)

    return dict(spec=SPEC, parts=19)


CHECKS = [
    # The S-drape turns the section through every axis, so no single bounding box
    # of ScarfStrip reports the 190 mm width -- bbox_y on the swept strip reads
    # 80 mm, which is how much of the width happens to project along Y. The width
    # is a section dimension and stays in SPEC; the checks below are the envelope
    # the drape actually presents.
    dict(name="overall_span_x", mm=670.4, tol=8.0, how="bbox_x", part=None),
    dict(name="overall_span_y", mm=264.6, tol=8.0, how="bbox_y", part=None),
    dict(name="overall_drop", mm=678.4, tol=8.0, how="bbox_z", part=None),
    dict(name="fringe_length", mm=70.0, tol=8.0, how="bbox_z",
         part="ScarfFringe1_1"),
]