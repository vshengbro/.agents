"""
jeans -- a size M straight-leg pair of jeans, 1050 mm waistband to hem.

Denim is the hardest clothing silhouette in this domain because the waist is
NOT the top: a pair of jeans is a seat, two tapering legs and a waistband, and
a model that lofts one tube from waist to floor reads as a skirt.

So it is built in three pieces that share one tube recipe:
  * seat block, from the waistband down to the crotch
  * two legs, each the same `limb()` sweep at a different taper
  * a waistband band on top
The crotch overlap is deliberate and generous -- the two solids interpenetrate
by 90 mm so the join is never tangent. Belt loops come from lay_out() so their
spacing is even, and the fly is a real part because a jean front without one
reads as leggings.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    inseam=640.0,             # crotch to hem, one leg of the standing pair
    waist_width=400.0,        # across the top of the waistband
    seat_width=490.0,         # across the seat
    thigh_width=280.0,        # front to back through one thigh
    knee_width=236.0,
    hem_width=224.0,          # front to back across a leg opening
    waistband_height=55.0,
    fly_length=230.0,
    belt_loops=7,
    fabric_thickness=3.0,
)

T = SPEC["fabric_thickness"]
N = 3.0                      # denim is stiff: a squarer section than jersey
LN = 2.6                     # legs are rounder than the seat
STEPS = 56
INNER = 37


def ring(z, a, b, n=N, steps=STEPS):
    return [(x, y, z) for (x, y) in
            bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)]


def axis_frame(d):
    """An orthonormal (u, v) pair spanning the plane perpendicular to d.

    A vertical run takes u = +X directly; `d x (0,0,1)` is degenerate there and
    the naive cross product silently swaps the two half-extents, which turns a
    trouser leg 300 mm wide across instead of 300 mm deep.
    """
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


def limb(name, path, half, n=LN, steps=STEPS, mat=None):
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


# --- seat block, waistband down to the crotch --------------------------------
# Widest at the seat, narrowest at the waist, and it does NOT taper to a point
# at the crotch: the legs take over from there.
SEAT = [
    (1050.0, 200.0, 122.0),   # waistband top
    (995.0, 204.0, 126.0),
    (900.0, 222.0, 138.0),    # hip
    (800.0, 245.0, 148.0),    # seat, widest
    (700.0, 240.0, 142.0),
    (620.0, 226.0, 132.0),
    (560.0, 205.0, 120.0),    # crotch
]
SEAT_CAV = [
    (1050.0, 194.0, 116.0),  # 6 mm inside the seat's own top ring: an exactly
    (995.0, 200.0, 122.0),   # coincident ring here puts vertices on top of
    (900.0, 218.0, 134.0),   # vertices and the solver returns bad edges
    (800.0, 241.0, 144.0),
    (700.0, 236.0, 138.0),
    (620.0, 222.0, 128.0),
    (560.0, 201.0, 116.0),
]
SEAT_CAV_TOP = 1120.0         # above the waistband: opens it

# --- legs: one tube recipe, mirrored, tapering thigh -> knee -> hem ----------
# The legs sit at x = +-130 with a half-width of ~112 so the pair is just under
# the seat width; a wider pair would break the hip silhouette.
LEG_PATH = [(130.0, 0.0, 640.0), (130.0, 0.0, 520.0), (127.0, 0.0, 340.0),
            (123.0, 0.0, 170.0), (121.0, 0.0, 0.0)]
LEG_HALF = [(112.0, 140.0), (110.0, 136.0), (104.0, 126.0), (98.0, 118.0),
            (94.0, 112.0)]
# Root is buried 80 mm up inside the seat block, and the cavity runs out through
# the hem so the leg opening has a real edge.
LEG_CAV_PATH = [(130.0, 0.0, 640.0), (130.0, 0.0, 520.0), (127.0, 0.0, 340.0),
                (123.0, 0.0, 170.0), (121.0, 0.0, -70.0)]
LEG_CAV_HALF = [(107.0, 134.0), (105.0, 130.0), (99.0, 120.0), (93.0, 112.0),
                (89.0, 106.0)]


def _mm(v):
    return v / bkit.MM


def build():
    denim = bkit.pbr("DenimBody", base=(0.180, 0.245, 0.360), rough=0.94)
    denim_in = bkit.pbr("DenimLining", base=(0.290, 0.330, 0.400), rough=0.95)
    denim_dark = bkit.pbr("DenimDeep", base=(0.135, 0.190, 0.290), rough=0.95)
    stitch = bkit.pbr("Topstitch", base=(0.780, 0.700, 0.360), rough=0.70)
    metal = bkit.preset("brushed_metal")

    seat = shell(
        bkit.loft("JeansSeat", [ring(z, a, b) for (z, a, b) in SEAT],
                  smooth=True, mat=denim),
        bkit.loft("JeansSeat_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in SEAT_CAV]
                  + [ring(SEAT_CAV_TOP, 192.0, 114.0, steps=INNER)]),
    )
    bkit.assign_faces_by(
        seat, denim_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )
    # Seat panel seam across the back, in contrast thread.
    bkit.assign_faces_by(
        seat, denim_dark,
        lambda c, n: _mm(c.y) > 90.0 and 940.0 < _mm(c.z) < 975.0,
    )

    for i, sx in enumerate((1.0, -1.0)):
        shell(limb("JeansLeg%d" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in LEG_PATH],
                   LEG_HALF, mat=denim),
              limb("_JeansLeg%d_cavity" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in LEG_CAV_PATH],
                   LEG_CAV_HALF))

    # ---- waistband: a band that wraps the seat, hollowed so the waist stays open
    shell(bkit.loft("JeansWaistband", [
        ring(995.0, 210.0, 132.0),
        ring(1022.0, 208.0, 130.0),
        ring(1050.0, 206.0, 128.0),
        ring(1056.0, 204.0, 126.0),
    ], smooth=True, mat=denim_dark),
        bkit.loft("_JeansWaistband_cavity", [
            ring(980.0, 204.0, 126.0, steps=INNER),
            ring(1022.0, 202.0, 124.0, steps=INNER),
            ring(1050.0, 200.0, 122.0, steps=INNER),
            ring(1120.0, 198.0, 120.0, steps=INNER),  # out the top -> open
        ]))

    # ---- fly: the front rise, a real part with topstitching beside it -------
    bkit.rounded_box("JeansFly", 34.0, 16.0, SPEC["fly_length"], r=8.0,
                     segments=3, centre=(-14.0, -132.0, 1000.0),
                     mat=denim_dark)
    for i, x in enumerate((-34.0, -14.0, 6.0)):
        bkit.cylinder("JeansFlyStitch%d" % (i + 1), 1.6,
                      SPEC["fly_length"] - 16.0, segments=10,
                      centre=(x, -141.0, 1000.0), axis="Z", mat=stitch)

    # ---- belt loops: even spacing from lay_out(), 7 of them -----------------
    widths = [18.0] * SPEC["belt_loops"]
    for i, (x, w) in enumerate(bkit.lay_out(widths, gap=44.0)):
        bkit.rounded_box("JeansBeltLoop%d" % (i + 1), w, 12.0, 64.0, r=4.0,
                         segments=3, centre=(x, 0.0, 1026.0), mat=denim_dark)

    # ---- hem turn-ups, so the leg openings are not bare cut edges ----------
    for i, sx in enumerate((1.0, -1.0)):
        p = [(sx * LEG_PATH[3][0], 0.0, LEG_PATH[3][2]),
             (sx * LEG_PATH[4][0], 0.0, LEG_PATH[4][2] - 10.0),
             (sx * LEG_PATH[4][0], 0.0, LEG_PATH[4][2] - 46.0)]
        h = [(119.0, 110.0), (119.0, 104.0), (119.0, 104.0)]
        limb("JeansHem%d" % (i + 1), p, h, mat=denim_dark)

    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="leg_length", mm=640.0, tol=2.0, how="bbox_z", part="JeansLeg1"),
    dict(name="seat_height", mm=490.0, tol=2.0, how="bbox_z", part="JeansSeat"),
    dict(name="seat_width", mm=490.0, tol=1.5, how="bbox_x", part="JeansSeat"),
    dict(name="seat_depth", mm=296.0, tol=1.5, how="bbox_y", part="JeansSeat"),
    dict(name="fly_length", mm=230.0, tol=1.0, how="bbox_z", part="JeansFly"),
    dict(name="waistband_height", mm=61.0, tol=1.5, how="bbox_z",
         part="JeansWaistband"),
    dict(name="overall_width", mm=490.0, tol=2.0, how="bbox_x"),
]