"""
deer -- a 700 mm-shoulder roe deer

A deer is a leggy animal with a short body: shoulder height 0.9x the body length, a fine neck, a narrow wedge head and short cylindrical legs. The antlers are two main beams with two tines each, built from the same swept-solid routine as everything else.

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
    withers                  = 700.0,
    body_length              = 760.0,
    body_width               = 380.0,
    chest_depth              = 448.0,
    neck_length              = 277.1,
    head_length              = 324.3,
    head_width               = 144.0,
    head_top_height          = 763.5,
    shoulder_joint_height    = 434.0,
    stance_front_track       = 304.0,
    stance_hind_track        = 311.6,
    tail_length              = 117.3,
    overall_length           = 1209.3,
    overall_height           = 1006.3,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (380, 117.8, 358.4, 633.5),
            (258.4, 171, 434.6, 682.5),
            (38, 190, 448, 693),
            (-167.2, 184.3, 448, 700),
            (-273.6, 171, 425.6, 689.5),
            (-357.2, 136.8, 340.5, 651),
            (-380, 102.6, 259.8, 609),
    ]
FRONT_PATH = [(228, 152, 434), (224, 152, 252), (227, 152, 119), (231, 152, 64), (256.2, 152, 20), (301, 152, 20)]
FRONT_RAD = [(42, 44), (30.7, 31.9), (16.5, 16.5), (17.5, 16.5), (32.4, 20), (28.2, 17.6)]
HIND_PATH = [(-228, 155.8, 434), (-202, 155.8, 245), (-224, 155.8, 119), (-208, 155.8, 64), (-182.8, 155.8, 20), (-138, 155.8, 20)]
HIND_RAD = [(42, 44), (30.7, 31.9), (16.5, 16.5), (17.5, 16.5), (32.4, 20), (28.2, 17.6)]
EAR_PATH = [(461.9, 60, 695.1), (535.8, 95.4, 705.7), (596.3, 124.3, 712.3)]
EAR_RAD = [(11.5, 34.2), (10, 36), (3.5, 10.8)]
ANTLER = [(463.4, 52, 755.5), (481.4, 96, 845.5), (487.4, 140, 935.5), (473.4, 172, 1005.5)]
TINE_A = [(482.4, 114, 877.5), (559.4, 140, 905.5)]
TINE_B = [(487.4, 136, 923.5), (541.4, 172, 969.5)]


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

    coat = bkit.pbr("RoedeerCoat", base=(0.520, 0.320, 0.160), rough=0.70)
    pale = bkit.pbr("RoedeerPale", base=(0.880, 0.840, 0.760), rough=0.74)
    dark = bkit.pbr("RoedeerDark", base=(0.140, 0.110, 0.090), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 307.7)

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
    _sweep("Neck", [(0, -288.8, 532), (0, -360, 575.3), (0, -428.8, 621.8), (0, -482, 661.9), (0, -516.8, 689.5)],
           [(120, 120), (107.6, 108.2), (90.1, 91.3), (73.3, 75.1), (62, 64)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -423.4, 689.5), (0, -493.4, 673.5), (0, -593.4, 631.5), (0, -673.4, 595.5), (0, -715.4, 573.5)],
           [(72, 74), (69.1, 71), (42, 46), (32, 36), (30.2, 34)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 30.0, segments=24, rings=12,
                  centre=(0.0, -727.4, 565.5), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 380, 644), (0, 418, 602), (0, 440.8, 546)],
           [(22, 22), (18, 18), (12, 12)], coat, n=2.4, steps=24)

    # ---- antlers: one main beam and two tines a side, mirrored
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Antler%s" % side, [(sy * y, -x, z) for (x, y, z) in ANTLER],
               [(17, 17), (13, 13), (9, 9), (4, 4)], pale, n=2.0, steps=16)
        _sweep("AntlerTine%sA" % side, [(sy * y, -x, z) for (x, y, z) in TINE_A],
               [(10, 10), (4, 4)], pale, n=2.0, steps=12)
        _sweep("AntlerTine%sB" % side, [(sy * y, -x, z) for (x, y, z) in TINE_B],
               [(9, 9), (4, 4)], pale, n=2.0, steps=12)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=17)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=760, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=380, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=455, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=324.3, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=144, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=117.3, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=1209.3, tol=1.2, how="bbox_y"),
]
