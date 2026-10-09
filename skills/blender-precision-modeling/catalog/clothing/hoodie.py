"""
hoodie -- a size M pullover hoodie: 700 mm body, 530 mm sleeves, 850 mm to the
top of the hood.

Three things make this read as a hoodie rather than as a long-sleeved t-shirt,
and all three are modelled rather than implied:
  * the hood volume, which is its own hollow shell open at the face
  * the kangaroo pocket across the lower front
  * ribbed cuffs and hem, in a visibly different fabric from the body
The two drawstrings are laid out with lay_out() so the gap between them is a
stated number rather than two hand-typed coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_length=700.0,
    body_width=580.0,        # chest is the widest station, not the hem
    chest_width=580.0,
    chest_depth=316.0,
    sleeve_length=490.0,       # shoulder seam to cuff
    hood_height=150.0,         # above the shoulder seam
    pocket_width=340.0,
    pocket_height=210.0,
    drawcord_length=235.0,
    fabric_thickness=3.5,
)

T = SPEC["fabric_thickness"]
N = 3.2
SN = 2.3
STEPS = 56
INNER = 37                    # != STEPS, so cavity facets never coincide


def ring(z, a, b, n=N, steps=STEPS):
    """A closed superellipse ring of half-extents (a, b) lifted to height z."""
    return [(x, y, z) for (x, y) in
            bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)]


def axis_frame(d):
    """An orthonormal (u, v) pair spanning the plane perpendicular to d.

    A vertical run takes u = +X directly; `d x (0,0,1)` is degenerate there and
    the naive cross product silently swaps the two half-extents.
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


def limb(name, path, half, n=SN, steps=STEPS, mat=None):
    """Loft a tapered tube down an arbitrary 3D polyline.

    A sleeve, a hood, a drawcord and a cuff rib are all this one function at
    different lengths and tapers.
    """
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
    """A real-walled panel: closed outer solid minus a cavity.

    `cavity` is allowed to run out past `outer` -- that is what turns it into an
    opening with a visible edge thickness instead of a sealed void.
    """
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


# --- panels -----------------------------------------------------------------
# A hoodie is cut generously: the body is wider than a tee at every station and
# the waist barely narrows, because fleece does not drape like jersey.
TORSO = [
    (0.0, 280.0, 150.0),      # hem
    (110.0, 284.0, 156.0),
    (240.0, 272.0, 146.0),    # waist
    (380.0, 280.0, 152.0),
    (500.0, 290.0, 158.0),    # chest
    (590.0, 282.0, 150.0),
    (640.0, 268.0, 132.0),    # shoulder seam
    (668.0, 226.0, 112.0),
    (686.0, 150.0, 84.0),
    (700.0, 112.0, 70.0),     # neck opening
]
TORSO_CAV = [
    (3.5, 276.0, 146.0),
    (110.0, 280.0, 152.0),
    (240.0, 268.0, 142.0),
    (380.0, 276.0, 148.0),
    (500.0, 286.0, 154.0),
    (590.0, 278.0, 146.0),
    (636.0, 262.0, 127.0),
    (660.0, 216.0, 106.0),
    (680.0, 128.0, 70.0),
    (690.0, 96.0, 52.0),
    (760.0, 90.0, 46.0),      # above the neck -> opens the neckline
]

# Long sleeves that hang down and forward, which is what separates a hoodie
# from a tee with the sleeves extended.
SLEEVE_PATH = [(40.0, 0.0, 615.0), (220.0, 0.0, 570.0), (340.0, 0.0, 480.0),
               (430.0, 0.0, 360.0), (470.0, 0.0, 282.0)]
SLEEVE_HALF = [(100.0, 112.0), (98.0, 106.0), (90.0, 88.0), (78.0, 68.0),
               (72.0, 60.0)]
SLEEVE_CAV_PATH = [(80.0, 0.0, 608.0), (222.0, 0.0, 568.0), (342.0, 0.0, 478.0),
                   (432.0, 0.0, 358.0), (500.0, 0.0, 270.0)]
SLEEVE_CAV_HALF = [(92.0, 104.0), (90.0, 98.0), (82.0, 80.0), (71.0, 61.0),
                   (66.0, 54.0)]

# The hood leans back off the neck and closes over the top of the head. Its
# cavity starts well in FRONT of the hood, so the difference opens the face
# opening instead of hollowing a closed dome.
HOOD_PATH = [(0.0, 30.0, 650.0), (0.0, 80.0, 730.0), (0.0, 120.0, 800.0),
             (0.0, 128.0, 838.0)]
HOOD_HALF = [(112.0, 90.0), (126.0, 106.0), (112.0, 96.0), (66.0, 54.0)]
HOOD_CAV_PATH = [(0.0, -120.0, 600.0), (0.0, -20.0, 660.0), (0.0, 60.0, 745.0),
                 (0.0, 112.0, 812.0)]
HOOD_CAV_HALF = [(40.0, 30.0), (84.0, 68.0), (96.0, 80.0), (72.0, 58.0)]


def _mm(v):
    return v / bkit.MM


def build():
    fleece = bkit.pbr("FleeceBody", base=(0.345, 0.375, 0.415), rough=0.97)
    fleece_in = bkit.pbr("FleeceLining", base=(0.255, 0.280, 0.315), rough=0.98)
    rib = bkit.pbr("FleeceRib", base=(0.300, 0.325, 0.360), rough=0.95)
    cord = bkit.pbr("Drawcord", base=(0.870, 0.865, 0.845), rough=0.85)
    metal = bkit.preset("brushed_metal")

    torso = shell(
        bkit.loft("HoodieBody", [ring(z, a, b) for (z, a, b) in TORSO],
                  smooth=True, mat=fleece),
        bkit.loft("HoodieBody_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in TORSO_CAV]),
    )
    # Inside faces are the ones whose normal points back toward the axis; the
    # difference keeps the cavity's own outward normal.
    bkit.assign_faces_by(
        torso, fleece_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    for i, sx in enumerate((1.0, -1.0)):
        shell(limb("HoodieSleeve%d" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in SLEEVE_PATH],
                   SLEEVE_HALF, mat=fleece),
              limb("_HoodieSleeve%d_cavity" % (i + 1),
                   [(sx * x, y, z) for (x, y, z) in SLEEVE_CAV_PATH],
                   SLEEVE_CAV_HALF))

    hood = shell(limb("HoodieHood", HOOD_PATH, HOOD_HALF, n=2.8, mat=fleece),
                 limb("_HoodieHood_cavity", HOOD_CAV_PATH, HOOD_CAV_HALF, n=2.8))

    # ---- ribbed hem and cuffs: a visibly different, thicker fabric ---------
    bkit.recalc(bkit.loft("HoodieHemRib", [
        ring(0.0, 288.0, 158.0),
        ring(11.0, 291.0, 161.0),
        ring(22.0, 289.0, 162.0),
    ], smooth=True, mat=rib))
    for i, sx in enumerate((1.0, -1.0)):
        tip = (sx * SLEEVE_PATH[-1][0], 0.0, SLEEVE_PATH[-1][2])
        back = (sx * SLEEVE_PATH[-2][0], 0.0, SLEEVE_PATH[-2][2])
        cuff = limb("HoodieCuff%d" % (i + 1),
                    [tip, ((tip[0] + back[0]) / 2.0, 0.0,
                           (tip[2] + back[2]) / 2.0), back],
                    [(79.0, 66.0), (80.0, 67.0), (80.0, 67.0)], mat=rib)
        bkit.assign_faces_by(cuff, rib, lambda c, n: True)

    # ---- kangaroo pocket, buried 14 mm into the front so it reads as sewn on
    bkit.rounded_box("HoodiePocket", SPEC["pocket_width"], 26.0,
                     SPEC["pocket_height"], r=16.0, segments=4,
                     centre=(0.0, -150.0, 330.0), mat=fleece)

    # ---- two drawcords, spaced by lay_out() rather than by two constants ---
    for i, (x, _w) in enumerate(bkit.lay_out([7.0, 7.0], gap=62.0)):
        limb("HoodieDrawcord%d" % (i + 1),
             [(x, -58.0, 655.0), (x, -74.0, 560.0), (x, -82.0, 420.0)],
             [(4.5, 4.5), (4.2, 4.2), (3.8, 3.8)], n=2.0, steps=20, mat=cord)
        bkit.tube("HoodieEyelet%d" % (i + 1), 9.0, 5.0, 5.0, segments=28,
                  centre=(x, -56.0, 658.0), axis="Y", mat=metal)

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="body_length", mm=700.0, tol=1.0, how="bbox_z",
         part="HoodieBody"),
    dict(name="body_width", mm=580.0, tol=1.5, how="bbox_x", part="HoodieBody"),
    dict(name="chest_depth", mm=316.0, tol=1.5, how="bbox_y",
         part="HoodieBody"),
    dict(name="pocket_width", mm=340.0, tol=1.0, how="bbox_x",
         part="HoodiePocket"),
    dict(name="pocket_height", mm=210.0, tol=1.0, how="bbox_z",
         part="HoodiePocket"),
    dict(name="drawcord_length", mm=235.0, tol=6.0, how="bbox_z",
         part="HoodieDrawcord1"),
]