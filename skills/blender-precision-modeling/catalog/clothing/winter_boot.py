"""
winter_boot -- a size 10 insulated lace-up boot: 320 mm long, 300 mm to the top
of the shaft.

A boot is an L, not a tube: a horizontal foot and a vertical shaft, so it is two
sweeps that interpenetrate deeply rather than one bent path. The overlap is
deliberate -- the shaft root is 70 mm down inside the foot -- because two solids
that merely touch produce bad edges, and two solids that merely cross read as a
bent sausage.

The shaft is the widest part at the top, which is what a winter boot is for,
and the shearling cuff is a material on the real shell rather than a second
solid that would z-fight and seal the opening.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=320.0,
    width=112.0,
    shaft_height=300.0,
    shaft_width=116.0,        # winter shafts are wider at the top
    sole_thickness=26.0,
    cuff_height=42.0,
    eyelets=8,
    eyelet_pitch=30.0,
)

N = 3.0
STEPS = 44
INNER = 29


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


def sweep(name, path, half, steps=STEPS, n=2.6, mat=None):
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


def sole_ring(x, a, z0, z1, steps=STEPS, n=N):
    """A vertical slab section: flat at z0, domed at z1, half-width a."""
    pts = []
    zm, zh = (z0 + z1) / 2.0, (z1 - z0) / 2.0
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        y = math.copysign(abs(ct) ** (2.0 / n), ct) * a
        z = zm + math.copysign(abs(st) ** (2.0 / n), st) * zh
        pts.append((x, y, z))
    return pts


# x, half-width, bottom z, top z
SOLE = [
    (-158.0, 44.0, 8.0, 26.0),
    (-110.0, 52.0, 2.0, 26.0),
    (-30.0, 56.0, 0.0, 26.0),
    (50.0, 56.0, 0.0, 26.0),
    (120.0, 52.0, 0.0, 26.0),
    (158.0, 40.0, 6.0, 26.0),
    (168.0, 22.0, 22.0, 30.0),     # toe spring
]

FOOT_PATH = [(-146.0, 0.0, 66.0), (-96.0, 0.0, 68.0), (-20.0, 0.0, 66.0),
             (60.0, 0.0, 58.0), (130.0, 0.0, 46.0), (158.0, 0.0, 38.0)]
FOOT_HALF = [(46.0, 46.0), (52.0, 46.0), (56.0, 42.0), (50.0, 34.0),
             (40.0, 26.0), (24.0, 16.0)]
FOOT_CAV_PATH = [(-146.0, 0.0, 62.0), (-96.0, 0.0, 62.0), (-20.0, 0.0, 60.0),
                 (60.0, 0.0, 52.0), (130.0, 0.0, 40.0), (156.0, 0.0, 34.0)]
FOOT_CAV_HALF = [(41.0, 41.0), (47.0, 41.0), (51.0, 37.0), (45.0, 29.0),
                 (35.0, 21.0), (18.0, 10.0)]

# The shaft flares: 104 across at the ankle, 116 at the top.
SHAFT_PATH = [(-96.0, 0.0, 120.0), (-96.0, 0.0, 190.0), (-98.0, 0.0, 258.0),
              (-100.0, 0.0, 300.0)]
SHAFT_HALF = [(52.0, 52.0), (55.0, 55.0), (57.0, 57.0), (58.0, 58.0)]
SHAFT_CAV_PATH = [(-96.0, 0.0, 120.0), (-96.0, 0.0, 190.0),
                  (-98.0, 0.0, 258.0), (-100.0, 0.0, 360.0)]
SHAFT_CAV_HALF = [(48.0, 48.0), (51.0, 51.0), (53.0, 53.0), (54.0, 54.0)]


def _mm(v):
    return v / bkit.MM


def build():
    rubber = bkit.pbr("BootRubber", base=(0.075, 0.075, 0.082), rough=0.78)
    leather = bkit.pbr("BootLeather", base=(0.255, 0.195, 0.140), rough=0.72)
    leather_in = bkit.pbr("BootLining", base=(0.190, 0.150, 0.115), rough=0.85)
    shearling = bkit.pbr("BootShearling", base=(0.720, 0.665, 0.575),
                         rough=0.99)
    lace = bkit.pbr("BootLace", base=(0.480, 0.400, 0.300), rough=0.90)
    metal = bkit.preset("brushed_metal")

    bkit.recalc(bkit.loft("BootSole",
                          [sole_ring(*p) for p in SOLE], smooth=True,
                          mat=rubber))

    foot = shell(sweep("BootFoot", FOOT_PATH, FOOT_HALF, mat=leather),
                 sweep("_BootFoot_cavity", FOOT_CAV_PATH, FOOT_CAV_HALF, INNER))

    shaft = shell(sweep("BootShaft", SHAFT_PATH, SHAFT_HALF, mat=leather),
                  sweep("_BootShaft_cavity", SHAFT_CAV_PATH, SHAFT_CAV_HALF,
                        INNER))
    # Shearling cuff as a material on the real shell. A second solid cuff would
    # z-fight the shaft and cap the opening the cavity just made.
    bkit.assign_faces_by(shaft, shearling, lambda c, n: _mm(c.z) > 258.0)
    bkit.assign_faces_by(
        shaft, leather_in,
        lambda c, n: _mm(c.z) < 258.0
        and (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    # ---- 8 eyelets on a 30 mm pitch, from grid_positions() ---------------
    pitch = SPEC["eyelet_pitch"]
    rows = SPEC["eyelets"] // 2
    for i, (dx, dz) in enumerate(
            bkit.grid_positions(cols=2, rows=rows, pitch_x=34.0,
                                pitch_y=pitch)):
        bkit.tube("BootEyelet%d" % (i + 1), 6.5, 3.5, 5.0, segments=18,
                  centre=(-96.0 + dx, -56.0, 222.0 + dz), axis="Y", mat=metal)
    for i, (_dx, dz) in enumerate(
            bkit.grid_positions(cols=1, rows=rows, pitch_x=0.0,
                                pitch_y=pitch)):
        for j, sx in enumerate((-1.0, 1.0)):
            bkit.cylinder("BootLace%d%d" % (i + 1, j + 1), 3.0, 40.0,
                          segments=10, centre=(-96.0 + sx * 17.0, -58.0,
                                               222.0 + dz), axis="X",
                          mat=lace)

    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="length", mm=326.0, tol=4.0, how="bbox_x"),
    dict(name="shaft_height", mm=300.0, tol=2.0, how="bbox_z"),
    dict(name="shaft_width", mm=116.0, tol=2.0, how="bbox_y", part="BootShaft"),
    dict(name="sole_thickness", mm=30.0, tol=2.0, how="bbox_z",
         part="BootSole"),
    dict(name="foot_width", mm=112.0, tol=2.0, how="bbox_y", part="BootFoot"),
]