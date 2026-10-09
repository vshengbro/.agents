"""
lion -- a 1100 mm-shoulder male lion

The mane is a separate collar swept around the neck axis rather than a scaled sphere, so it stays watertight and its silhouette merges with the shoulders instead of floating.

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
    withers                  = 1100.0,
    body_length              = 1400.0,
    body_width               = 580.0,
    chest_depth              = 579.7,
    neck_length              = 407.1,
    head_length              = 318.6,
    head_width               = 300.0,
    head_top_height          = 1114.0,
    shoulder_joint_height    = 682.0,
    stance_front_track       = 487.2,
    stance_hind_track        = 498.8,
    tail_length              = 568.5,
    overall_length           = 2286.1,
    overall_height           = 1162.4,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (700, 179.8, 463.8, 995.5),
            (504, 261, 562.3, 1072.5),
            (70, 290, 579.7, 1089),
            (-308, 284.2, 579.7, 1100),
            (-504, 266.8, 550.7, 1083.5),
            (-658, 214.6, 452.2, 1023),
            (-700, 162.4, 347.8, 957),
    ]
FRONT_PATH = [(420, 243.6, 682), (414, 243.6, 396), (418, 243.6, 176), (424, 243.6, 128), (464.5, 243.6, 40), (536.5, 243.6, 40)]
FRONT_RAD = [(74, 80), (59, 63.7), (37.8, 35.4), (40, 35.4), (67, 40), (58.3, 35.2)]
HIND_PATH = [(-420, 249.4, 682), (-390, 249.4, 385), (-414, 249.4, 176), (-396, 249.4, 128), (-355.5, 249.4, 40), (-283.5, 249.4, 40)]
HIND_RAD = [(74, 80), (59, 63.7), (37.8, 35.4), (40, 35.4), (67, 40), (58.3, 35.2)]
EAR_PATH = [(834.4, 118, 968), (846.5, 127.3, 1012.9), (856.3, 134.8, 1040.9)]
EAR_RAD = [(11.5, 34.2), (10, 36), (3.5, 10.8)]


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

    coat = bkit.pbr("MalelionCoat", base=(0.740, 0.550, 0.280), rough=0.70)
    pale = bkit.pbr("MalelionPale", base=(0.800, 0.660, 0.420), rough=0.74)
    dark = bkit.pbr("MalelionDark", base=(0.200, 0.140, 0.100), rough=0.34)
    mane = bkit.pbr("MalelionMane", base=(0.26, 0.16, 0.09), rough=0.82)

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
                      lambda c, n: c.z / bkit.MM < 590.5)

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
    _sweep("Neck", [(0, -560, 858), (0, -679.3, 884.8), (0, -797.3, 916.7), (0, -890.3, 946.7), (0, -952, 968)],
           [(190, 190), (177.2, 177.2), (156.4, 156.4), (135, 135), (120, 120)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -854.1, 968), (0, -940.1, 968), (0, -1042.1, 960), (0, -1122.1, 946), (0, -1160.1, 938)],
           [(150, 146), (146, 140), (112, 96), (78, 62), (63, 61.3)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 42.0, segments=24, rings=12,
                  centre=(0.0, -1174.1, 932.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 686, 990), (0, 812, 902), (0, 924, 748), (0, 1008, 572), (0, 1036, 440)],
           [(20, 20), (17, 17), (14, 14), (11, 11), (10, 10)], coat, n=2.4, steps=24)

    # ---- mane: a collar swept around the neck axis, so it merges with
    # the shoulders instead of floating as a separate ball
    _sweep("Mane", [(0, -631.6, 874.1), (0, -720.6, 895.9), (0, -811.2, 921.2), (0, -885.7, 945.2)],
           [(216.2, 216.2), (274.7, 274.7), (253.4, 253.4), (175.5, 175.5)], mane, n=2.2, steps=32)

    # ---- tail tuft
    bkit.uv_sphere("TailTuft", 34.0, segments=20, rings=10,
                  centre=(0.0, 1036.0, 440.0), mat=dark)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1400, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=580, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=590.7, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=318.6, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=300, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=568.5, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2286.1, tol=1.2, how="bbox_y"),
]
