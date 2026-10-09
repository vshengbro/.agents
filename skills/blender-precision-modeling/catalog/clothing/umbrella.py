"""
umbrella -- an open golf umbrella: 900 mm canopy, 660 mm to the ferrule.

The canopy is the only thin shell here that a lathe can do honestly, because a
canopy IS a solid of revolution: the profile walks out over the top, round the
scalloped rim, and back under the inside, which is what gives it a real 18 mm
panel thickness.

The eight ribs are the repeated feature. They are built as one rib at its own
radius and then swept round by array_radial(), which is the only way to get eight
identical spokes without eight hand-typed positions.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    canopy_diameter=900.0,
    canopy_height=620.0,
    panel_thickness=18.0,
    ribs=8,
    shaft_diameter=18.0,
    handle_height=180.0,
    overall_height=660.0,
)

# (r, z) over the top of the panel, round the rim, back under the panel.
CANOPY = [
    (0.0, 620.0),      # apex, outside
    (60.0, 608.0),
    (160.0, 570.0),
    (270.0, 508.0),
    (360.0, 442.0),
    (420.0, 372.0),
    (450.0, 316.0),    # rim, top
    (450.0, 300.0),    # rim, rounded
    (436.0, 306.0),
    (396.0, 360.0),
    (336.0, 424.0),
    (252.0, 488.0),
    (148.0, 548.0),
    (56.0, 584.0),
    (0.0, 596.0),      # apex, inside
]


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


def spoke(name, path, half, steps=16, n=2.0, mat=None):
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


def _mm(v):
    return v / bkit.MM


def build():
    nylon = bkit.pbr("UmbrellaNylon", base=(0.165, 0.320, 0.470), rough=0.42)
    nylon_in = bkit.pbr("UmbrellaNylonUnder", base=(0.120, 0.245, 0.375),
                        rough=0.48)
    steel = bkit.preset("steel")
    grip = bkit.pbr("UmbrellaGrip", base=(0.135, 0.095, 0.070), rough=0.70)

    canopy = bkit.lathe("UmbrellaCanopy", CANOPY, segments=96, mat=nylon)
    bkit.recalc(canopy)
    bkit.assign_faces_by(
        canopy, nylon_in,
        lambda c, n: _mm(n.z) < -0.25,      # the underside of the panel
    )

    # ---- eight ribs, swept round by array_radial() -----------------------
    rib = spoke("UmbrellaRib", [
        (30.0, 0.0, 592.0), (220.0, 0.0, 500.0), (360.0, 0.0, 396.0),
        (444.0, 0.0, 310.0),
    ], [(7.0, 5.0), (6.0, 4.0), (5.0, 4.0), (4.0, 3.0)], mat=steel)
    bkit.array_radial(rib, count=SPEC["ribs"])

    # ---- shaft, ferrule and tip ------------------------------------------
    bkit.cylinder("UmbrellaShaft", SPEC["shaft_diameter"] / 2.0, 430.0,
                  segments=32, centre=(0.0, 0.0, 300.0), axis="Z", mat=steel)
    bkit.cylinder("UmbrellaFerrule", 5.0, 46.0, segments=20,
                  centre=(0.0, 0.0, 637.0), axis="Z", mat=steel)
    bkit.uv_sphere("UmbrellaTip", 9.0, centre=(0.0, 0.0, 660.0), mat=steel)

    # ---- runner and spring, so the shaft is not a bare rod ----------------
    bkit.cylinder("UmbrellaRunner", 15.0, 46.0, segments=24,
                  centre=(0.0, 0.0, 430.0), axis="Z", mat=steel)
    bkit.tube("UmbrellaRunnerCollar", 22.0, 12.0, 14.0, segments=28,
              centre=(0.0, 0.0, 452.0), axis="Z", mat=steel)

    # ---- crook handle: the mug-handle trick, tips buried in the grip ------
    bkit.cylinder("UmbrellaGrip", 17.0, 150.0, segments=32,
                  centre=(0.0, 0.0, 82.33), axis="Z", mat=grip)
    a, rise = 74.0, 96.0
    k = (a * a - rise * rise) / (2.0 * rise)
    bkit.arc_torus("UmbrellaHandle", rise + k, 17.0,
                   math.degrees(math.atan2(k, a)),
                   180.0 - math.degrees(math.atan2(k, a)),
                   centre=(0.0, 0.0, 4.33 - k), plane="XZ", seg_major=36,
                   mat=grip, caps=True)

    # ---- eight stretchers from the runner to the rib tips ----------------
    st = spoke("UmbrellaStretcher", [
        (16.0, 0.0, 448.0), (200.0, 0.0, 452.0), (360.0, 0.0, 430.0),
    ], [(5.0, 4.0), (4.0, 3.0), (4.0, 3.0)], mat=steel)
    bkit.array_radial(st, count=SPEC["ribs"])

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="canopy_diameter", mm=900.0, tol=3.0, how="diameter",
         part="UmbrellaCanopy"),
    dict(name="canopy_height", mm=320.0, tol=3.0, how="bbox_z",
         part="UmbrellaCanopy"),
    dict(name="shaft_diameter", mm=18.0, tol=1.0, how="bbox_x",
         part="UmbrellaShaft"),
    dict(name="overall_height", mm=669.0, tol=3.0, how="bbox_z"),
    dict(name="canopy_span", mm=900.0, tol=4.0, how="bbox_x"),
]