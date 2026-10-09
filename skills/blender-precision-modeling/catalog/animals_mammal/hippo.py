"""
hippo -- a 1500 mm-shoulder hippo

Hippos are the barrel: the body is 1.7x the shoulder height, the head is nearly a quarter of the animal's length and sits on a very short neck, the legs are short thick columns, and the ears and tail are vestigial.

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
    withers                  = 1500.0,
    body_length              = 2500.0,
    body_width               = 1350.0,
    chest_depth              = 1050.0,
    neck_length              = 599.6,
    head_length              = 627.8,
    head_width               = 680.0,
    head_top_height          = 1650.0,
    shoulder_joint_height    = 930.0,
    stance_front_track       = 1134.0,
    stance_hind_track        = 1161.0,
    tail_length              = 136.2,
    overall_length           = 3555.8,
    overall_height           = 1649.9,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (1250, 499.5, 903, 1357.5),
            (850, 641.2, 1050, 1462.5),
            (125, 675, 1050, 1485),
            (-550, 668.2, 1050, 1500),
            (-900, 634.5, 1008, 1477.5),
            (-1175, 540, 861, 1395),
            (-1250, 445.5, 714, 1320),
    ]
FRONT_PATH = [(750, 567, 930), (740, 567, 495), (746, 567, 225), (756, 567, 336), (823.5, 567, 105), (943.5, 567, 105)]
FRONT_RAD = [(170, 180), (172.3, 179.4), (148.7, 148.7), (157.6, 148.7), (178.2, 105), (155.1, 92.4)]
HIND_PATH = [(-750, 580.5, 930), (-720, 580.5, 480), (-746, 580.5, 225), (-728, 580.5, 336), (-660.5, 580.5, 105), (-540.5, 580.5, 105)]
HIND_RAD = [(170, 180), (172.3, 179.4), (148.7, 148.7), (157.6, 148.7), (178.2, 105), (155.1, 92.4)]
EAR_PATH = [(1588.5, 250, 1322.6), (1595, 258.7, 1395.6), (1600.3, 265.8, 1441)]
EAR_RAD = [(20.7, 47.5), (18, 50), (6.3, 15)]


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

    coat = bkit.pbr("CommonhippopotamusCoat", base=(0.500, 0.290, 0.300), rough=0.70)
    pale = bkit.pbr("CommonhippopotamusPale", base=(0.660, 0.450, 0.420), rough=0.74)
    dark = bkit.pbr("CommonhippopotamusDark", base=(0.160, 0.100, 0.110), rough=0.34)

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
    _sweep("Neck", [(0, -1000, 1200), (0, -1176.2, 1236), (0, -1352.5, 1272), (0, -1493.5, 1300.8), (0, -1587.5, 1320)],
           [(360, 350), (352.3, 341.8), (329.8, 319.2), (301.3, 291), (280, 270)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -1408.3, 1320), (0, -1578.3, 1316), (0, -1768.3, 1280), (0, -1908.3, 1244), (0, -1968.3, 1224)],
           [(340, 330), (340, 318), (312, 272), (268, 214), (248, 190)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 175.0, segments=24, rings=12,
                  centre=(0.0, -2008.3, 1202.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 1250, 1350), (0, 1362.5, 1260)],
           [(22, 22), (16, 16)], coat, n=2.4, steps=24)

    # ---- lower jaw: the square muzzle that separates a hippo from a
    # very large pig. A separate overlapping solid, never a boolean.
    _sweep("Jaw", [(0, -1668.3, 1204), (0, -1838.3, 1180), (0, -2008.3, 1172)],
           [(230, 150), (215, 140), (195, 120)], coat, n=2.6, steps=28)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=2500, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=1350, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=1087.5, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=627.8, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=680, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=136.2, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=3555.8, tol=1.2, how="bbox_y"),
]
