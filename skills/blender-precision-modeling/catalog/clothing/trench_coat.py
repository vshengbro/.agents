"""
trench_coat -- a belted double-breasted trench, 1150 mm collar to hem.

A trench is a long flared coat, and three features separate it from a long
cardigan:
  * the double-breasted front, which is an 8-button grid -- two columns on an
    80 mm x 105 mm pitch from grid_positions(), not eight hand-typed points
  * the storm flap and the belt, the two parts a trench is recognised by
  * a real shoulder yoke that widens the top of the coat over the body tube
The sleeves and the body are the same two sweeps the tee and the hoodie use,
at a longer length and a bigger taper.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1150.0,
    shoulder_width=480.0,
    chest_width=520.0,
    hem_width=700.0,          # a trench flares; this is what makes it one
    chest_depth=270.0,
    sleeve_length=680.0,
    lapel_width=110.0,
    buttons=8,
    button_pitch_x=80.0,
    button_pitch_y=105.0,
    belt_width=60.0,
)

N = 3.0
SN = 2.3
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


# --- body: shoulder -> chest -> a long, slightly flared skirt to the hem ---
BODY = [
    (0.0, 350.0, 200.0),      # hem, flared
    (160.0, 344.0, 196.0),
    (420.0, 326.0, 184.0),
    (700.0, 300.0, 166.0),
    (880.0, 268.0, 144.0),    # waist, where the belt sits
    (1010.0, 262.0, 136.0),   # chest
    (1090.0, 250.0, 124.0),
    (1136.0, 214.0, 100.0),   # shoulder yoke
    (1155.0, 152.0, 82.0),    # collar; the neck cavity exits 5 mm below this
]
# Exits at the collar and below the hem: a trench is open at both ends.
BODY_CAV = [
    (-80.0, 343.0, 193.0),
    (160.0, 337.0, 189.0),
    (420.0, 319.0, 177.0),
    (700.0, 293.0, 159.0),
    (880.0, 261.0, 137.0),
    (1010.0, 255.0, 129.0),
    (1086.0, 240.0, 116.0),
    (1128.0, 198.0, 92.0),
    (1200.0, 140.0, 74.0),
]

SLEEVE_PATH = [(40.0, 0.0, 1060.0), (250.0, 0.0, 1010.0), (370.0, 0.0, 900.0),
               (450.0, 0.0, 740.0), (468.0, 0.0, 640.0)]
SLEEVE_HALF = [(98.0, 112.0), (97.0, 108.0), (92.0, 92.0), (84.0, 74.0),
               (80.0, 66.0)]
SLEEVE_CAV_PATH = [(95.0, 0.0, 1052.0), (252.0, 0.0, 1008.0),
                   (372.0, 0.0, 898.0), (452.0, 0.0, 738.0),
                   (502.0, 0.0, 610.0)]
SLEEVE_CAV_HALF = [(91.0, 104.0), (90.0, 101.0), (85.0, 85.0), (77.0, 67.0),
                   (74.0, 60.0)]


def _mm(v):
    return v / bkit.MM


def build():
    gabardine = bkit.pbr("TrenchGabardine", base=(0.505, 0.455, 0.355),
                         rough=0.91)
    gabardine_in = bkit.pbr("TrenchLining", base=(0.430, 0.385, 0.300),
                            rough=0.92)
    trim = bkit.pbr("TrenchTrim", base=(0.395, 0.350, 0.270), rough=0.88)
    horn = bkit.pbr("TrenchHorn", base=(0.060, 0.055, 0.052), rough=0.40)
    metal = bkit.preset("brushed_metal")

    body = shell(
        bkit.loft("TrenchBody", [ring(z, a, b) for (z, a, b) in BODY],
                  smooth=True, mat=gabardine),
        bkit.loft("TrenchBody_cavity",
                  [ring(z, a, b, steps=INNER) for (z, a, b) in BODY_CAV]),
    )
    bkit.assign_faces_by(
        body, gabardine_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    for i, sx in enumerate((1.0, -1.0)):
        shell(sweep("TrenchSleeve%d" % (i + 1),
                    [(sx * x, y, z) for (x, y, z) in SLEEVE_PATH],
                    SLEEVE_HALF, mat=gabardine),
              sweep("_TrenchSleeve%d_cavity" % (i + 1),
                    [(sx * x, y, z) for (x, y, z) in SLEEVE_CAV_PATH],
                    SLEEVE_CAV_HALF))

    # ---- storm flap across the right shoulder, a trench's signature -------
    bkit.rounded_box("TrenchStormFlap", 150.0, 26.0, 420.0, r=10.0,
                     segments=3, centre=(150.0, -110.0, 990.0), mat=trim)

    # ---- notched lapels, rolled outward ---------------------------------
    for i, sx in enumerate((1.0, -1.0)):
        sweep("TrenchLapel%d" % (i + 1), [
            (sx * 40.0, -86.0, 1146.0),
            (sx * 82.0, -122.0, 1060.0),
            (sx * 122.0, -140.0, 950.0),
            (sx * 132.0, -146.0, 860.0),
        ], [(56.0, 8.0), (54.0, 8.0), (52.0, 8.0), (48.0, 8.0)],
            steps=28, n=3.4, mat=trim)

    # ---- eight buttons: a real grid, from grid_positions() ---------------
    cols, rows = 2, SPEC["buttons"] // 2
    for i, (x, z) in enumerate(bkit.grid_positions(
            cols=cols, rows=rows, pitch_x=SPEC["button_pitch_x"],
            pitch_y=SPEC["button_pitch_y"])):
        bkit.cylinder("TrenchButton%d" % (i + 1), 10.0, 6.0, segments=28,
                      centre=(x, -140.0, 980.0 + z), axis="Y", mat=horn)

    # ---- belt with a D-ring and a buckle ---------------------------------
    shell(bkit.loft("TrenchBelt", [
        ring(866.0, 276.0, 152.0),
        ring(880.0, 278.0, 153.0),
        ring(894.0, 276.0, 152.0),
    ], smooth=True, mat=trim),
        bkit.loft("_TrenchBelt_cavity", [
            ring(852.0, 269.0, 145.0, steps=INNER),
            ring(880.0, 271.0, 146.0, steps=INNER),
            ring(908.0, 269.0, 145.0, steps=INNER),
        ]))
    bkit.rounded_box("TrenchBuckle", 66.0, 14.0, 52.0, r=6.0, segments=3,
                     centre=(0.0, -152.0, 880.0), mat=metal)
    # belt tail, hanging from the buckle
    sweep("TrenchBeltTail", [
        (30.0, -156.0, 876.0), (34.0, -166.0, 790.0), (30.0, -170.0, 700.0),
    ], [(26.0, 5.0), (26.0, 5.0), (22.0, 5.0)], steps=24, n=3.2, mat=trim)

    # ---- epaulettes on both shoulders ------------------------------------
    for i, sx in enumerate((1.0, -1.0)):
        bkit.rounded_box("TrenchEpaulette%d" % (i + 1), 120.0, 34.0, 12.0,
                         r=5.0, segments=3,
                         centre=(sx * 150.0, 0.0, 1122.0), mat=trim)

    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="length", mm=1150.0, tol=2.0, how="bbox_z", part="TrenchBody"),
    dict(name="hem_width", mm=700.0, tol=2.0, how="bbox_x", part="TrenchBody"),
    dict(name="hem_depth", mm=400.0, tol=2.0, how="bbox_y",
         part="TrenchBody"),
    dict(name="belt_height", mm=28.0, tol=1.0, how="bbox_z",
         part="TrenchBelt"),
    dict(name="button_diameter", mm=20.0, tol=1.0, how="bbox_z",
         part="TrenchButton7"),
    # The sleeves are held out from the body, so the assembly is wider than the
    # 700 mm hem; 1075 mm is the coat as worn rather than as folded.
    dict(name="overall_width", mm=1075.1, tol=8.0, how="bbox_x"),
]