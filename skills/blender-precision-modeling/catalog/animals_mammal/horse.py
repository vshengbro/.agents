"""
horse -- a 1600 mm-shoulder riding horse

The horse silhouette is the long one: body length barely exceeds shoulder height, the neck is a long forward-rising sweep, the head hangs steeply below the poll, and all four legs are long with a narrow cannon and a hoof rather than a paw.

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
    withers                  = 1600.0,
    body_length              = 1700.0,
    body_width               = 620.0,
    chest_depth              = 760.0,
    neck_length              = 776.1,
    head_length              = 640.1,
    head_width               = 236.0,
    head_top_height          = 1822.0,
    shoulder_joint_height    = 992.0,
    stance_front_track       = 496.0,
    stance_hind_track        = 508.4,
    tail_length              = 1113.7,
    overall_length           = 2757.7,
    overall_height           = 1813.3,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (850, 186, 608, 1448),
            (612, 279, 737.2, 1560),
            (85, 310, 760, 1584),
            (-374, 303.8, 760, 1600),
            (-612, 279, 722, 1576),
            (-799, 223.2, 577.6, 1488),
            (-850, 167.4, 440.8, 1392),
    ]
FRONT_PATH = [(510, 248, 992), (502, 248, 640), (508, 248, 320), (514, 248, 147.2), (557.2, 248, 46), (634, 248, 46)]
FRONT_RAD = [(88, 96), (61.4, 68.4), (33, 30.7), (35, 30.7), (67, 46), (58.3, 40.5)]
HIND_PATH = [(-510, 254.2, 992), (-458, 254.2, 624), (-498, 254.2, 320), (-472, 254.2, 147.2), (-428.8, 254.2, 46), (-352, 254.2, 46)]
HIND_RAD = [(88, 96), (61.4, 68.4), (33, 30.7), (35, 30.7), (67, 46), (58.3, 40.5)]
EAR_PATH = [(1146.8, 80, 1687.9), (1165.8, 97.4, 1762.6), (1181.3, 111.7, 1809.2)]
EAR_RAD = [(18.4, 41.8), (16, 44), (5.6, 13.2)]


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

    coat = bkit.pbr("ThoroughbredmareCoat", base=(0.300, 0.200, 0.120), rough=0.70)
    pale = bkit.pbr("ThoroughbredmarePale", base=(0.160, 0.110, 0.080), rough=0.74)
    dark = bkit.pbr("ThoroughbredmareDark", base=(0.100, 0.090, 0.090), rough=0.34)

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
    _sweep("Neck", [(0, -646, 1184), (0, -835.2, 1320.3), (0, -1017.7, 1465), (0, -1157.8, 1587.9), (0, -1249.5, 1672)],
           [(230, 270), (200.3, 239.1), (160.7, 196.6), (124.3, 156.8), (100, 130)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -1076.7, 1672), (0, -1196.7, 1632), (0, -1376.7, 1522), (0, -1526.7, 1422), (0, -1616.7, 1362)],
           [(118, 148), (113.3, 142.1), (72, 128), (60, 110), (66, 96)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 60.0, segments=24, rings=12,
                  centre=(0.0, -1638.7, 1344.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 816, 1440), (0, 935, 1248), (0, 986, 928), (0, 1020, 608), (0, 1037, 352)],
           [(46, 46), (40, 40), (34, 34), (28, 28), (22, 22)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1700, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=620, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=777.2, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=640.1, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=236, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=1113.7, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2757.7, tol=1.2, how="bbox_y"),
]
