"""
paint_can -- 5 litre round paint can: a tapered tin body with a rolled rim, a
seated lid and a wire bail handle.

The body is a shell, not a solid, so the rim has real tin thickness and the
handle has something to hook over. The handle arc is *solved*, not eyeballed:
given two attachment points and a rise, the centre and radius follow.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=183.0,      # the rolled rim is the widest point
    top_diameter=180.0,
    base_diameter=172.0,
    body_height=175.0,        # base to the rim
    wall=1.2,
    lid_diameter=180.0,
    lid_height=7.0,
    handle_rise=55.0,         # bail rise above the rim
    overall_height=230.0,
    volume_l=5.0,
)

TOP_R = SPEC["top_diameter"] / 2.0
BASE_R = SPEC["base_diameter"] / 2.0
BH = SPEC["body_height"]
RIM_R = SPEC["body_diameter"] / 2.0


def build():
    tin = bkit.pbr("PaintCanTin", base=(0.82, 0.83, 0.85), metal=0.45, rough=0.32)
    # The lid is a broad horizontal disc with nothing bright above it to reflect;
    # at metal=0.88 it mirrors the dark backdrop and renders as a black hole.
    lid_mat = bkit.pbr("PaintCanLid", base=(0.86, 0.87, 0.88), metal=0.30,
                      rough=0.30)
    wire = bkit.pbr("PaintCanWire", base=(0.55, 0.57, 0.60), metal=0.55, rough=0.30)
    label = bkit.pbr("PaintCanLabel", base=(0.90, 0.86, 0.30), rough=0.46)

    # ---- body: base -> outside -> rolled rim -> inside -> inner floor -------
    prof = [
        (0.0, 0.0),
        (82.0, 0.0),
        (BASE_R, 2.0),
        (BASE_R + 0.5, 10.0),
        (TOP_R, 90.0),                    # the taper
        (TOP_R, 168.0),
        (RIM_R, 171.5),                   # rolled rim bead
        (RIM_R, 175.0),
        (89.0, 175.0),                    # across the rim
        (88.8, 168.0),                    # down the inside
        (85.5, 12.0),
        (82.0, 4.0),
        (0.0, 4.0),
    ]
    body = bkit.lathe("PaintCanBody", prof, segments=96, mat=tin)
    bkit.assign_faces_by(
        body, label,
        lambda c, n: 16.0 < c.z / bkit.MM < 150.0,
    )

    # ---- lid seated on the rim ---------------------------------------------
    lid_prof = [
        (0.0, 0.0),
        (88.0, 0.0),
        (TOP_R, 1.4),
        (TOP_R, 5.4),
        (84.0, 7.0),
        (0.0, 7.0),
    ]
    lid = bkit.lathe("PaintCanLid", lid_prof, segments=96,
                     centre=(0.0, 0.0, BH - 0.2), mat=lid_mat)

    # ---- wire bail: solve the arc from the two anchors and the rise ---
    # The arc's ENDS sit at (+-a, rim) and its PEAK is `rise` above the rim.
    # A circle centred k below the rim satisfies
    #     a^2 + k^2 = (rise + k)^2   =>   k = (a^2 - rise^2) / (2 * rise)
    # and the sweep runs from phi to 180-phi so it passes over the top.
    a, rise = RIM_R + 1.0, SPEC["handle_rise"] - 2.6
    k = (a * a - rise * rise) / (2.0 * rise)
    rmaj = rise + k
    ang = math.degrees(math.atan2(k, a))
    handle = bkit.arc_torus("PaintCanHandle", rmaj, 2.6, ang, 180.0 - ang,
                            centre=(0.0, 0.0, BH - k), plane="XZ",
                            seg_major=48, mat=wire, caps=True)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_diameter", mm=183.0, tol=0.5, how="diameter",
         part="PaintCanBody"),
    dict(name="lid_diameter", mm=180.0, tol=0.5, how="diameter",
         part="PaintCanLid"),
    dict(name="overall_height", mm=230.0, tol=1.5, how="bbox_z"),
]
