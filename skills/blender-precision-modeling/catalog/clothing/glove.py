"""
glove -- a size M wool glove, 190 mm cuff to middle fingertip.

Fingers are the reason this item exists. A mitten-shaped tube reads as a
boxing glove, so the four fingers are separate tapered sweeps, spaced with
lay_out() from real finger widths plus a stated gap -- which is also what keeps
four near-identical solids from being hand-placed on top of each other.

The thumb is the same sweep at a different angle, and every digit is hollowed
with a cavity that runs out past the fingertip, so each one shows a real open
end rather than a sealed rounded cap.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=189.0,             # cuff to middle fingertip
    palm_width=108.0,
    palm_depth=56.0,
    cuff_height=44.0,
    fingers=4,
    finger_gap=12.0,
    thumb_reach=52.0,
    fabric_thickness=4.0,
)

N = 2.6
STEPS = 40
INNER = 25                   # != STEPS, so cavity facets never coincide

# (z, half_x, half_y) cuff to the knuckle line
PALM = [
    (0.0, 44.0, 26.0),       # cuff opening
    (30.0, 48.0, 28.0),
    (70.0, 52.0, 28.0),      # widest point of the palm
    (100.0, 54.0, 27.0),
    (122.0, 48.0, 23.0),     # knuckle line
]
PALM_CAV = [
    (-60.0, 41.0, 23.0),     # out the bottom -> open cuff
    (0.0, 45.0, 25.0),
    (30.0, 45.0, 25.0),
    (70.0, 49.0, 25.0),
    (100.0, 51.0, 24.0),
    (140.0, 44.0, 20.0),     # out the top -> open into the fingers
]

# Four fingers: real widths, in index -> little order.
FINGER_W = [18.0, 18.0, 16.0, 14.0]
FINGER_L = [64.0, 70.0, 64.0, 50.0]
FINGER_R = [9.0, 9.5, 8.5, 7.5]


def ring(z, a, b, n=N, steps=STEPS):
    return [(x, y, z) for (x, y) in
            bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)]


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


def digit(name, base, tip, r0, r1, mat, cav_over=26.0):
    """One finger or thumb: a short tapered sweep, hollowed out at the tip."""
    mid = ((base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0,
           (base[2] + tip[2]) / 2.0)
    path = [base, mid, tip]
    half = [(r0, r0 * 0.92), ((r0 + r1) / 2.0, (r0 + r1) / 2.0 * 0.92),
            (r1, r1 * 0.92)]
    out = (tip[0] + (tip[0] - mid[0]) / max(1e-6, tip[2] - mid[2]) * cav_over,
           tip[1] + (tip[1] - mid[1]) / max(1e-6, tip[2] - mid[2]) * cav_over,
           tip[2] + cav_over)
    shell(limb(name, path, half, n=2.4, steps=24, mat=mat),
          limb("_%s_cavity" % name, [base, mid, out],
               [(r0 - 3.0, (r0 - 3.0) * 0.92), ((r0 + r1) / 2.0 - 3.0,
                                                 (r0 + r1) / 2.0 * 0.92 - 3.0),
                (r1 - 3.0, (r1 - 3.0) * 0.92)], n=2.4, steps=21))


def limb(name, path, half, n=2.4, steps=STEPS, mat=None):
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


def _mm(v):
    return v / bkit.MM


def build():
    wool = bkit.pbr("GloveWool", base=(0.520, 0.140, 0.155), rough=0.96)
    cuff_rib = bkit.pbr("GloveRib", base=(0.430, 0.115, 0.130), rough=0.95)

    palm = shell(
        bkit.loft("GlovePalm", [ring(z, a, b) for (z, a, b) in PALM],
                  smooth=True, mat=wool),
        bkit.loft("GlovePalm_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in PALM_CAV]),
    )
    bkit.assign_faces_by(
        palm, cuff_rib,
        lambda c, n: _mm(c.z) < 14.0,     # knit rib at the wrist
    )

    # ---- four fingers, spaced by lay_out() from real widths --------------
    xs = bkit.lay_out(FINGER_W, gap=SPEC["finger_gap"])
    for i, ((x, _w), ln, r) in enumerate(zip(xs, FINGER_L, FINGER_R)):
        digit("GloveFinger%d" % (i + 1),
              (x, -4.0, 116.0), (x * 1.06, -18.0, 116.0 + ln),
              r, r * 0.82, wool)

    # ---- thumb: the same sweep, angled out and up ------------------------
    digit("GloveThumb", (-44.0, -12.0, 66.0), (-86.0, -36.0, 104.0),
          13.0, 10.0, wool)

    # ---- ribbed cuff, hollowed so the wrist stays open -------------------
    shell(bkit.loft("GloveCuff", [
        ring(-2.0, 46.0, 28.0),
        ring(20.0, 50.0, 31.0),
        ring(44.0, 51.0, 31.0),
    ], smooth=True, mat=cuff_rib),
        bkit.loft("_GloveCuff_cavity", [
            ring(-70.0, 42.0, 24.0, steps=INNER),
            ring(20.0, 46.0, 27.0, steps=INNER),
            ring(60.0, 47.0, 27.0, steps=INNER),
        ]))

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="length", mm=189.4, tol=1.0, how="bbox_z"),
    dict(name="palm_width", mm=108.0, tol=1.5, how="bbox_x", part="GlovePalm"),
    dict(name="palm_depth", mm=56.0, tol=1.5, how="bbox_y", part="GlovePalm"),
    dict(name="cuff_height", mm=46.0, tol=1.5, how="bbox_z", part="GloveCuff"),
    dict(name="thumb_reach", mm=59.0, tol=1.5, how="bbox_x", part="GloveThumb"),
]