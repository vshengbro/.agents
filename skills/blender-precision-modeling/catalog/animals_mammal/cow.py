"""
cow -- a 1450 mm-shoulder dairy cow

A dairy cow is deeper-bodied than a horse and much less leggy, with a long straight back, a wedge-shaped head carried low, and the udder placed between and slightly ahead of the hind legs.

Construction: one torso loft, four leg sweeps whose soles sit exactly on z=0,
and separate watertight solids for neck, head, ears and tail. Nothing is booleaned:
overlapping closed solids stay manifold solids, which is why `health()` reports
zero non-manifold edges on an eighteen-part assembly.

Orientation: the nose points at -Y, world X is lateral, Z is up. The catalog's
fixed shot list puts the camera on +X for the SIDE view and on -Y for the FRONT
view, so a quadruped has to be built along Y for side.png to show a silhouette
instead of a face. All four soles rest on z=0.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    withers                  = 1450.0,
    body_length              = 1650.0,
    body_width               = 690.0,
    chest_depth              = 790.3,
    neck_length              = 592.2,
    head_length              = 611.2,
    head_width               = 276.0,
    head_top_height          = 1537.2,
    shoulder_joint_height    = 899.0,
    stance_front_track       = 552.0,
    stance_hind_track        = 565.8,
    tail_length              = 876.4,
    overall_length           = 2552.7,
    overall_height           = 1549.2,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (825, 213.9, 663.8, 1312.2),
            (594, 317.4, 782.3, 1413.8),
            (82.5, 345, 790.3, 1435.5),
            (-363, 338.1, 790.3, 1450),
            (-594, 317.4, 758.6, 1428.2),
            (-775.5, 262.2, 632.2, 1348.5),
            (-825, 200.1, 490, 1261.5),
    ]
FRONT_PATH = [(495, 276, 899), (489, 276, 580), (493, 276, 290), (499, 276, 153.6), (542.2, 276, 48), (619, 276, 48)]
FRONT_RAD = [(86, 90), (59, 61.4), (35.4, 33), (37.5, 33), (71.3, 48), (62, 42.2)]
HIND_PATH = [(-495, 282.9, 899), (-449, 282.9, 565.5), (-487, 282.9, 290), (-463, 282.9, 153.6), (-419.8, 282.9, 48), (-343, 282.9, 48)]
HIND_RAD = [(86, 90), (59, 61.4), (35.4, 33), (37.5, 33), (71.3, 48), (62, 42.2)]
EAR_PATH = [(1053.9, 104, 1412.1), (1144, 158.3, 1345.3), (1217.8, 202.7, 1303.6)]
EAR_RAD = [(16.1, 49.4), (14, 52), (4.9, 15.6)]
HORNS_PATH = [(1152.2, 80, 1485.2), (1198.2, 114, 1519.2), (1240.2, 142, 1545.2)]


def _sweep(name, path, rad, mat, n=2.4, steps=32):
    """Sweep a superellipse ring along a polyline.

    The animal's long axis is Y -- its nose points at -Y, which is what the
    fixed shot list means by a front view -- so every path here runs in the Y-Z
    plane and world X is the lateral axis. The ring's in-plane axis is the
    tangent crossed with X, which keeps each ring perpendicular to its own
    segment so a bend never twists the profile. Rings are bridged by `loft()`
    and capped, so every part is a closed solid on its own.

    `rad` is one (lateral_half_width, in_plane_half_height) per path node.
    """
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == m - 1:
            t = [p[k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - p[k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        ty, tz = t[1] / tl, t[2] / tl
        ul = math.hypot(ty, tz)
        if ul < 1e-9:
            uy, uz = 1.0, 0.0
        else:
            uy, uz = tz / ul, -ty / ul
        w, h = rad[i]
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            cx = math.copysign(abs(ca) ** (2.0 / n), ca)
            cy = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((p[0] + w * cy, p[1] + uy * h * cx,
                         p[2] + uz * h * cx))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():

    coat = bkit.pbr("HolsteindairycowCoat", base=(0.740, 0.730, 0.700), rough=0.70)
    pale = bkit.pbr("HolsteindairycowPale", base=(0.420, 0.300, 0.220), rough=0.74)
    dark = bkit.pbr("HolsteindairycowDark", base=(0.160, 0.130, 0.130), rough=0.34)

    # ---- torso: seven superellipse sections, +X is the chest, -X the
    # rump. Every row is (x, half_width, depth, top_z) in millimetres, so
    # body width and chest depth are properties of the table, not a
    # claim made afterwards.
    sections = []
    for (y, hw, depth, ztop) in TORSO:
        ring = bkit.superellipse_section(2.0 * hw, depth, n=2.8, steps=40)
        sections.append([(u, y, ztop - depth / 2.0 + v) for (u, v) in ring])
    torso = bkit.loft("Torso", sections, mat=coat)
    bkit.recalc(torso)
    bkit.shade_smooth(torso, 50.0)

    # pale underside: a second material on the one solid. A second
    # shell shaped like the belly would z-fight with the real wall.
    bkit.assign_faces_by(torso, pale,
                      lambda c, n: c.z / bkit.MM < 742.0)

    # cow: selected faces of the one torso solid take the darker coat.
    bkit.assign_faces_by(torso, dark,
                      lambda c, n: (math.sin(c.x / bkit.MM * 0.0246)
                                * math.sin(c.y / bkit.MM * 0.0209)
                                + 0.6 * math.sin(c.z / bkit.MM * 0.0190)
                                > 0.16))

    # ---- front legs: plumb under the shoulder, the elbow only just forward of the vertical. The last two nodes share a z, which makes
    # their rings horizontal and the sole a flat strip resting on z=0,
    # so all four feet meet the floor at the same height.
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("LegFront%s" % side,
               [(sy * y, -x, z) for (x, y, z) in FRONT_PATH],
               FRONT_RAD, coat, n=2.2, steps=28)

    # ---- hind legs: stifle forward and hock back, so the leg reads as a zigzag rather than a post. The last two nodes share a z, which makes
    # their rings horizontal and the sole a flat strip resting on z=0,
    # so all four feet meet the floor at the same height.
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("LegHind%s" % side,
               [(sy * y, -x, z) for (x, y, z) in HIND_PATH],
               HIND_RAD, coat, n=2.2, steps=28)

    # ---- neck: five swept nodes from inside the chest to the poll, so the
    # two solids overlap instead of meeting on a shared face
    _sweep("Neck", [(0, -627, 1131), (0, -789.1, 1204.3), (0, -948.1, 1283.5), (0, -1072.7, 1352), (0, -1155, 1399.2)],
           [(210, 230), (191.9, 207.8), (164.9, 175.9), (138.3, 145), (120, 124)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -982.2, 1399.2), (0, -1122.2, 1359.2), (0, -1312.2, 1279.2), (0, -1452.2, 1219.2), (0, -1522.2, 1187.2)],
           [(138, 138), (132.5, 132.5), (96, 88), (78, 72), (86, 80)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 86.0, segments=24, rings=12,
                  centre=(0.0, -1546.2, 1177.2), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 808.5, 1305), (0, 874.5, 1073), (0, 899.3, 754), (0, 907.5, 435)],
           [(22, 22), (18, 18), (15, 15), (13, 13)], coat, n=2.4, steps=24)

    # ---- udder, sitting between and slightly ahead of the hind legs
    bkit.uv_sphere("Udder", 150.0, segments=24, rings=12,
                  centre=(0.0, 99, 731), mat=pale)

    # ---- horns: short lateral spikes off the poll
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Horn%s" % side,
               [(sy * y, -x, z) for (x, y, z) in HORNS_PATH],
               [(16.0, 16.0), (12.0, 12.0), (4.0, 4.0)], pale, n=2.0, steps=16)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=14)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1650, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=690, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=818.6, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=611.2, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=276, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=876.4, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2552.7, tol=1.2, how="bbox_y"),
]
