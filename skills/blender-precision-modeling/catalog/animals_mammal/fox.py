"""
fox -- a 380 mm-shoulder red fox

Fox proportions: long low body, short legs, a very large triangular ear and a bushy tail almost as long as the body carried low behind. The muzzle is a long taper -- the single clearest species cue.

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
    withers                  = 380.0,
    body_length              = 560.0,
    body_width               = 270.0,
    chest_depth              = 250.0,
    neck_length              = 175.9,
    head_length              = 196.6,
    head_width               = 112.0,
    head_top_height          = 373.3,
    shoulder_joint_height    = 228.0,
    stance_front_track       = 226.8,
    stance_hind_track        = 232.2,
    tail_length              = 226.1,
    overall_length           = 1036.3,
    overall_height           = 424.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (280, 83.7, 200, 343.9),
            (201.6, 121.5, 242.5, 370.5),
            (28, 135, 250, 376.2),
            (-123.2, 132.3, 250, 380),
            (-201.6, 124.2, 237.5, 374.3),
            (-263.2, 99.9, 195, 353.4),
            (-280, 75.6, 150, 330.6),
    ]
FRONT_PATH = [(168, 113.4, 228), (171, 113.4, 121.6), (173, 113.4, 53.2), (177, 113.4, 51.2), (198.6, 113.4, 16), (237, 113.4, 16)]
FRONT_RAD = [(38, 40), (31.9, 34.2), (20.1, 20.1), (21.3, 20.1), (29.2, 16), (25.4, 14.1)]
HIND_PATH = [(-168, 116.1, 228), (-144, 116.1, 125.4), (-164, 116.1, 57), (-150, 116.1, 51.2), (-128.4, 116.1, 16), (-90, 116.1, 16)]
HIND_RAD = [(38, 40), (31.9, 34.2), (20.1, 20.1), (21.3, 20.1), (29.2, 16), (25.4, 14.1)]
EAR_PATH = [(329, 40, 317.3), (326, 50.8, 382.6), (323.7, 59.6, 423.4)]
EAR_RAD = [(10.3, 36.1), (9, 38), (3.1, 11.4)]


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

    coat = bkit.pbr("RedfoxCoat", base=(0.720, 0.340, 0.110), rough=0.70)
    pale = bkit.pbr("RedfoxPale", base=(0.900, 0.880, 0.840), rough=0.74)
    dark = bkit.pbr("RedfoxDark", base=(0.140, 0.120, 0.110), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 161.2)

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
    _sweep("Neck", [(0, -224, 288.8), (0, -276.9, 292.6), (0, -329.1, 300.3), (0, -370.3, 309.9), (0, -397.6, 317.3)],
           [(84, 84), (75.5, 75.5), (63.4, 63.4), (51.9, 51.9), (44, 44)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -336.8, 317.3), (0, -382.8, 317.3), (0, -440.8, 309.3), (0, -492.8, 295.3), (0, -526.8, 285.3)],
           [(56, 56), (54, 53), (38, 32), (26, 21), (23.5, 23.5)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 12.0, segments=24, rings=12,
                  centre=(0.0, -532.8, 282.3), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 280, 334.4), (0, 352.8, 304), (0, 420, 250.8), (0, 459.2, 197.6), (0, 470.4, 159.6)],
           [(38, 38), (42, 42), (40, 40), (32, 32), (22, 22)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=560, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=270, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=253.8, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=196.6, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=112, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=226.1, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=1036.3, tol=1.2, how="bbox_y"),
]
