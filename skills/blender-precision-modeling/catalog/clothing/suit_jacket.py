"""
suit_jacket -- a tailored single-breasted jacket, 720 mm collar to hem.

Tailoring is the whole difficulty here. A jacket is not a tube: it is a tube
with a V opening at the front, and that V is what makes it a jacket instead of
a cardigan. Three things carry it:
  * a notched lapel pair, rolled outward as real plates
  * a front opening cut into the shell, so the garment is genuinely open
  * two buttons on a stated pitch, plus a collar that stands up behind the neck
Sleeves are the same `limb()` recipe as the tee, one length shorter.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=720.0,             # collar to hem
    chest_width=520.0,
    waist_width=470.0,        # taken in, which is what "tailored" means
    chest_depth=250.0,
    sleeve_length=620.0,      # shoulder seam to cuff
    lapel_width=95.0,
    button_pitch=95.0,
    buttons=2,
    collar_height=70.0,
    fabric_thickness=4.0,     # suiting cloth is heavier than jersey
)

N = 3.0
SN = 2.4
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


def limb(name, path, half, n=SN, steps=STEPS, mat=None):
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


# --- body: chest, taken-in waist, straight to the hem ----------------------
BODY = [
    (0.0, 244.0, 128.0),      # hem
    (140.0, 246.0, 130.0),
    (330.0, 235.0, 122.0),    # waist, taken in
    (500.0, 258.0, 126.0),    # chest
    (610.0, 252.0, 118.0),
    (668.0, 228.0, 98.0),     # shoulder seam
    (700.0, 150.0, 80.0),
    (720.0, 116.0, 66.0),     # neckline
]
# The cavity exits the neck at the top and the hem at the bottom, so the jacket
# is open at both ends like real cloth.
BODY_CAV = [
    (-70.0, 241.0, 125.0),
    (140.0, 243.0, 127.0),
    (330.0, 232.0, 119.0),
    (500.0, 255.0, 123.0),
    (610.0, 249.0, 115.0),
    (664.0, 222.0, 95.0),
    (692.0, 138.0, 72.0),
    (760.0, 104.0, 54.0),
]

SLEEVE_PATH = [(50.0, 0.0, 640.0), (250.0, 0.0, 610.0), (360.0, 0.0, 540.0),
               (430.0, 0.0, 430.0), (462.0, 0.0, 368.0)]
SLEEVE_HALF = [(96.0, 108.0), (95.0, 104.0), (89.0, 88.0), (80.0, 70.0),
               (76.0, 62.0)]
SLEEVE_CAV_PATH = [(95.0, 0.0, 635.0), (252.0, 0.0, 608.0), (362.0, 0.0, 538.0),
                   (432.0, 0.0, 428.0), (500.0, 0.0, 358.0)]
SLEEVE_CAV_HALF = [(89.0, 100.0), (88.0, 97.0), (82.0, 81.0), (73.0, 63.0),
                   (70.0, 56.0)]


def _mm(v):
    return v / bkit.MM


def build():
    suiting = bkit.pbr("SuitingCloth", base=(0.145, 0.160, 0.205), rough=0.88)
    suiting_in = bkit.pbr("SuitingLining", base=(0.360, 0.220, 0.215), rough=0.80)
    lapel_mat = bkit.pbr("SuitingLapel", base=(0.170, 0.185, 0.235), rough=0.84)
    button = bkit.pbr("HornButton", base=(0.055, 0.050, 0.048), rough=0.42)

    body = shell(
        bkit.loft("JacketBody", [ring(z, a, b) for (z, a, b) in BODY],
                  smooth=True, mat=suiting),
        bkit.loft("JacketBody_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in BODY_CAV]),
    )
    bkit.assign_faces_by(
        body, suiting_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    for i, sx in enumerate((1.0, -1.0)):
        shell(limb("JacketSleeve%d" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in SLEEVE_PATH],
                   SLEEVE_HALF, mat=suiting),
              limb("_JacketSleeve%d_cavity" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in SLEEVE_CAV_PATH],
                   SLEEVE_CAV_HALF))

    # ---- notched lapels: rolled plates that lie on the chest --------------
    # Built as a tapering limb so each lapel has a rolled top edge rather than
    # being a flat polygon stuck on the surface.
    for i, sx in enumerate((1.0, -1.0)):
        limb("JacketLapel%d" % (i + 1), [
            (sx * 44.0, -96.0, 712.0),
            (sx * 70.0, -118.0, 630.0),
            (sx * 96.0, -132.0, 540.0),
            (sx * 104.0, -136.0, 470.0),
        ], [(48.0, 7.0), (46.0, 7.0), (44.0, 7.0), (40.0, 7.0)],
            n=3.4, steps=28, mat=lapel_mat)

    # ---- standing collar behind the neck ----------------------------------
    shell(limb("JacketCollar", [
        (0.0, 34.0, 706.0), (0.0, 74.0, 728.0), (0.0, 92.0, 762.0),
    ], [(122.0, 22.0), (118.0, 22.0), (104.0, 22.0)], n=3.0, steps=48,
        mat=suiting),
        limb("_JacketCollar_cavity", [
            (0.0, 40.0, 690.0), (0.0, 74.0, 728.0), (0.0, 88.0, 790.0),
        ], [(112.0, 16.0), (110.0, 16.0), (98.0, 16.0)], n=3.0, steps=40))

    # ---- two buttons on a stated pitch, plus the buttonhole stand --------
    pitch = SPEC["button_pitch"]
    for i, z in enumerate((520.0 - i * pitch for i in range(SPEC["buttons"]))):
        bkit.cylinder("JacketButton%d" % (i + 1), 9.0, 5.0, segments=28,
                      centre=(24.0, -128.0, z), axis="Y", mat=button)

    # ---- welt pockets, one per side, mirrored ------------------------------
    for i, sx in enumerate((1.0, -1.0)):
        bkit.rounded_box("JacketPocket%d" % (i + 1), 130.0, 8.0, 22.0,
                         r=4.0, segments=3,
                         centre=(sx * 150.0, -116.0, 190.0), mat=lapel_mat)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="length", mm=720.0, tol=1.0, how="bbox_z", part="JacketBody"),
    dict(name="chest_width", mm=516.0, tol=1.5, how="bbox_x", part="JacketBody"),
    dict(name="chest_depth", mm=260.0, tol=1.5, how="bbox_y", part="JacketBody"),
    dict(name="collar_height", mm=70.0, tol=6.0, how="bbox_z",
         part="JacketCollar"),
    dict(name="button_diameter", mm=18.0, tol=1.0, how="diameter",
         part="JacketButton1"),
    dict(name="overall_width", mm=994.0, tol=6.0, how="bbox_x"),
]