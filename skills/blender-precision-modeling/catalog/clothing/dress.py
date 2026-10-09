"""
dress -- a knee-length A-line shift dress, 1150 mm shoulder to hem.

The silhouette of a dress is one continuous flare from the bust to the hem, and
the one number that decides whether it reads is the ratio of hem width to
bust width. A tube that keeps its width is a pencil skirt with straps; a tube
that flares from a narrow bust is a dress.

So the body is a single loft whose section grows from 340 mm at the bust to
760 mm at the hem, with the waist pinched in between. The straps, the waistband
seam and the row of five buttons are separate parts: the buttons are spaced with
grid_positions() so they sit on a real pitch.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1150.0,            # shoulder to hem
    bust_width=340.0,
    waist_width=290.0,
    hem_width=760.0,          # the flare ratio that makes it a dress
    bust_depth=230.0,
    strap_width=34.0,
    button_pitch=54.0,
    buttons=5,
    fabric_thickness=3.0,
)

N = 2.8
STEPS = 56
INNER = 37


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


# --- body: bust -> pinched waist -> hard A-line flare to the hem -------------
BODY = [
    (1150.0, 130.0, 88.0),    # neckline / top of the bodice
    (1090.0, 152.0, 104.0),
    (1010.0, 168.0, 114.0),   # bust
    (930.0, 145.0, 100.0),    # waist, pinched
    (820.0, 196.0, 126.0),    # hip begins
    (620.0, 272.0, 162.0),
    (380.0, 340.0, 196.0),
    (160.0, 372.0, 212.0),
    (0.0, 380.0, 216.0),      # hem: 760 wide
]
# The cavity runs out of the top so the neckline is open, and out of the bottom
# so the hem shows a real edge rather than a sealed drum.
BODY_CAV = [
    (1180.0, 118.0, 76.0),
    (1090.0, 149.0, 101.0),
    (1010.0, 165.0, 111.0),
    (930.0, 142.0, 97.0),
    (820.0, 193.0, 123.0),
    (620.0, 269.0, 159.0),
    (380.0, 337.0, 193.0),
    (160.0, 369.0, 209.0),
    (-70.0, 377.0, 213.0),
]


def _mm(v):
    return v / bkit.MM


def build():
    cloth = bkit.pbr("DressCloth", base=(0.560, 0.255, 0.290), rough=0.93)
    cloth_in = bkit.pbr("DressLining", base=(0.470, 0.205, 0.240), rough=0.94)
    trim = bkit.pbr("DressTrim", base=(0.235, 0.135, 0.160), rough=0.88)
    button = bkit.pbr("DressButton", base=(0.900, 0.880, 0.840), rough=0.35)

    body = shell(
        bkit.loft("DressBody", [ring(z, a, b) for (z, a, b) in BODY],
                  smooth=True, mat=cloth),
        bkit.loft("DressBody_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in BODY_CAV]),
    )
    bkit.assign_faces_by(
        body, cloth_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    # ---- two shoulder straps, the same limb() recipe at two transforms -----
    for i, sx in enumerate((1.0, -1.0)):
        limb("DressStrap%d" % (i + 1), [
            (sx * 92.0, -14.0, 1132.0),
            (sx * 92.0, -30.0, 1168.0),
            (sx * 92.0, -14.0, 1186.0),
        ], [(17.0, 9.0), (17.0, 9.0), (17.0, 9.0)], n=3.0, steps=24, mat=trim)

    # ---- waistband seam: a band that marks where the flare starts ----------
    shell(bkit.loft("DressWaistband", [
        ring(918.0, 152.0, 106.0),
        ring(936.0, 151.0, 105.0),
        ring(954.0, 153.0, 106.0),
    ], smooth=True, mat=trim),
        bkit.loft("_DressWaistband_cavity", [
            ring(906.0, 146.0, 100.0, steps=INNER),
            ring(936.0, 145.0, 99.0, steps=INNER),
            ring(966.0, 147.0, 100.0, steps=INNER),
        ]))

    # ---- five buttons down the bodice front, on a stated pitch ------------
    pitch = SPEC["button_pitch"]
    for i, z in enumerate(976.0 - i * pitch for i in range(SPEC["buttons"])):
        bkit.cylinder("DressButton%d" % (i + 1), 8.0, 4.0, segments=24,
                      centre=(0.0, -122.0, z), axis="Y", mat=button)

    # ---- a belt at the waist, with a buckle -------------------------------
    for i, sx in enumerate((1.0, -1.0)):
        limb("DressBeltTail%d" % (i + 1), [
            (sx * 150.0, -108.0, 936.0),
            (sx * 152.0, -126.0, 860.0),
            (sx * 150.0, -140.0, 790.0),
        ], [(15.0, 5.0), (15.0, 5.0), (13.0, 5.0)], n=3.0, steps=20, mat=trim)
    bkit.rounded_box("DressBuckle", 46.0, 10.0, 34.0, r=5.0, segments=3,
                     centre=(0.0, -116.0, 936.0), mat=button)

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="length", mm=1150.0, tol=1.0, how="bbox_z", part="DressBody"),
    dict(name="hem_width", mm=760.0, tol=2.0, how="bbox_x", part="DressBody"),
    dict(name="hem_depth", mm=432.0, tol=1.5, how="bbox_y", part="DressBody"),
    dict(name="waistband_height", mm=36.0, tol=1.0, how="bbox_z",
         part="DressWaistband"),
    dict(name="strap_width", mm=34.0, tol=1.0, how="bbox_x",
         part="DressStrap1"),
    dict(name="overall_height", mm=1195.0, tol=12.0, how="bbox_z"),
]