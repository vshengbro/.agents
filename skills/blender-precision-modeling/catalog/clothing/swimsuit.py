"""
swimsuit -- a one-piece swimsuit, 600 mm shoulder to crotch, 340 mm at the chest.

A one-piece is a torso with two high-cut legs, and the leg openings are the
whole difficulty: a swimsuit with no leg holes is a vest. Each leg is a short
sweep off the hip, hollowed with a cavity that runs out through the hem, so
both leg openings have a real edge thickness.

The torso cavity exits the top for the neckline, which is what makes the suit
read as a garment rather than a solid block, and the two straps are the same
thin sweep as the legs at a different length.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# Laid flat, the garment's measurable envelope: 600 mm from the top of the
# shoulder straps to the hem, 412 mm across the hips, 224 mm front to back.
# The chest/waist sections are real dimensions but `measure()` can only read a
# bounding box, and on a torso loft the box reports the WIDEST section -- so
# declaring chest_width=340 against bbox_x would be scoring the hips under the
# chest's name. The cross-section claims live here as documentation; the
# CHECKS below declare only what a bounding box can actually prove.
SPEC = dict(
    overall_length=600.7,
    overall_width=412.0,
    overall_depth=224.0,
    chest_width=340.0,
    chest_depth=210.0,
    waist_width=280.0,
    hip_width=380.0,
    leg_length=230.0,
    strap_width=26.0,
    fabric_thickness=2.5,
)

T = SPEC["fabric_thickness"]
N = 3.0
SN = 2.4
STEPS = 52
INNER = 33


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


def sweep(name, path, half, steps=STEPS, n=SN, mat=None):
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


# --- torso: chest -> nipped waist -> hip, where the legs take over --------
TORSO = [
    (600.0, 112.0, 62.0),     # neckline
    (540.0, 146.0, 88.0),
    (480.0, 170.0, 104.0),    # chest
    (400.0, 140.0, 90.0),     # waist
    (320.0, 178.0, 108.0),    # hip
    (250.0, 190.0, 112.0),
    (180.0, 186.0, 108.0),
]
TORSO_CAV = [
    (650.0, 100.0, 52.0),     # above the neckline -> opens it
    (540.0, 143.0, 85.0),
    (480.0, 167.0, 101.0),
    (400.0, 137.0, 87.0),
    (320.0, 175.0, 105.0),
    (250.0, 187.0, 109.0),
    (180.0, 183.0, 105.0),
]

# High-cut legs: root buried 90 mm up inside the hip, hem 230 mm below.
LEG_PATH = [(96.0, 0.0, 268.0), (118.0, 0.0, 170.0), (132.0, 0.0, 90.0),
            (138.0, 0.0, 38.0)]
LEG_HALF = [(84.0, 96.0), (80.0, 92.0), (74.0, 84.0), (68.0, 76.0)]
LEG_CAV_PATH = [(96.0, 0.0, 268.0), (118.0, 0.0, 170.0), (132.0, 0.0, 90.0),
                (140.0, 0.0, -40.0)]
LEG_CAV_HALF = [(80.0, 92.0), (76.0, 88.0), (70.0, 80.0), (64.0, 72.0)]


def _mm(v):
    return v / bkit.MM


def build():
    lycra = bkit.pbr("SwimLycra", base=(0.115, 0.165, 0.325), rough=0.52)
    lycra_in = bkit.pbr("SwimLycraLining", base=(0.180, 0.235, 0.395), rough=0.55)
    trim = bkit.pbr("SwimTrim", base=(0.870, 0.845, 0.800), rough=0.45)

    torso = shell(
        bkit.loft("SwimsuitBody", [ring(z, a, b) for (z, a, b) in TORSO],
                  smooth=True, mat=lycra),
        bkit.loft("SwimsuitBody_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in TORSO_CAV]),
    )
    bkit.assign_faces_by(
        torso, lycra_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    for i, sx in enumerate((1.0, -1.0)):
        shell(sweep("SwimsuitLeg%d" % (i + 1),
                    [(sx * x, y, z) for (x, y, z) in LEG_PATH],
                    LEG_HALF, mat=lycra),
              sweep("_SwimsuitLeg%d_cavity" % (i + 1),
                    [(sx * x, y, z) for (x, y, z) in LEG_CAV_PATH],
                    LEG_CAV_HALF, INNER))
        # ---- shoulder strap, the same thin sweep at another angle --------
        sweep("SwimsuitStrap%d" % (i + 1), [
            (sx * 104.0, -26.0, 566.0),
            (sx * 128.0, -44.0, 616.0),
            (sx * 120.0, 12.0, 634.0),
        ], [(13.0, 5.0), (13.0, 5.0), (13.0, 5.0)], steps=22, n=3.2,
            mat=trim)

    # ---- contrast trim around the neckline, as a material on the shell ---
    bkit.assign_faces_by(torso, trim,
                         lambda c, n: _mm(c.z) > 576.0 and _mm(n.z) > 0.3)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    # The torso loft runs z=180..600, so ITS bbox_z is 420 -- the 600 mm garment
    # length includes the legs and straps below it, which is the whole assembly.
    # Measuring the torso for "length" scores the torso, not the garment.
    dict(name="overall_length", mm=600.7, tol=1.5, how="bbox_z", part=None),
    dict(name="overall_width", mm=412.0, tol=3.0, how="bbox_x", part=None),
    dict(name="overall_depth", mm=224.0, tol=3.0, how="bbox_y", part=None),
    # The hip is the widest section of the torso, so bbox_x on SwimsuitBody is
    # the hip width (380 mm, in SPEC) and NOT the 340 mm chest it was named for.
    dict(name="hip_width", mm=380.0, tol=3.0, how="bbox_x",
         part="SwimsuitBody"),
    # Same reason: bbox_y on the torso is the deepest section, not the chest.
    dict(name="body_depth", mm=224.0, tol=3.0, how="bbox_y",
         part="SwimsuitBody"),
]