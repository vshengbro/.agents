"""
monkey -- a 125 mm-shoulder pygmy marmoset

The world's smallest monkey: head-body 125 mm and a long tail almost as long again, held out behind for balance. Small round head, no neck to speak of, and grasping limbs set well forward of the body.

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
    withers                  = 123.8,
    body_length              = 125.0,
    body_width               = 100.0,
    chest_depth              = 80.0,
    neck_length              = 35.4,
    head_length              = 54.0,
    head_width               = 54.0,
    head_top_height          = 138.5,
    shoulder_joint_height    = 75.0,
    stance_front_track       = 88.0,
    stance_hind_track        = 90.0,
    tail_length              = 68.1,
    overall_length           = 262.6,
    overall_height           = 138.7,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (62.5, 33, 65.6, 112.5),
            (42.5, 46, 78.4, 121.2),
            (6.2, 50, 80, 123.8),
            (-27.5, 48, 80, 123.8),
            (-45, 43, 75.2, 121.9),
            (-58.8, 34, 57.6, 115),
            (-62.5, 25, 43.2, 107.5),
    ]
FRONT_PATH = [(37.5, 44, 75), (41.5, 44, 40), (43.5, 44, 17.5), (46.5, 44, 25.6), (56.9, 44, 8), (75.2, 44, 8)]
FRONT_RAD = [(18, 18), (15.3, 15.3), (10.6, 10.6), (11.3, 10.6), (14, 8), (12.2, 7)]
HIND_PATH = [(-37.5, 45, 75), (-25.5, 45, 40), (-35.5, 45, 17.5), (-28.5, 45, 25.6), (-18.1, 45, 8), (0.2, 45, 8)]
HIND_RAD = [(18, 18), (15.3, 15.3), (10.6, 10.6), (11.3, 10.6), (14, 8), (12.2, 7)]
EAR_PATH = [(62.4, 22, 112.5), (66.5, 24.1, 127.7), (69.8, 25.8, 137.1)]
EAR_RAD = [(6.9, 15.2), (6, 16), (2.1, 4.8)]


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

    coat = bkit.pbr("PygmymarmosetCoat", base=(0.580, 0.470, 0.360), rough=0.70)
    pale = bkit.pbr("PygmymarmosetPale", base=(0.820, 0.740, 0.600), rough=0.74)
    dark = bkit.pbr("PygmymarmosetDark", base=(0.120, 0.100, 0.090), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 54.0)

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
    _sweep("Neck", [(0, -50, 100), (0, -60.2, 103), (0, -70.2, 106.6), (0, -78, 110), (0, -83.1, 112.5)],
           [(30, 30), (28.9, 28.9), (26.6, 26.6), (24, 24), (22, 22)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -65.8, 112.5), (0, -81.8, 112.5), (0, -103.8, 114.5), (0, -119.8, 114.5)],
           [(27, 26), (27, 26), (22, 20), (15, 13)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 9.0, segments=24, rings=12,
                  centre=(0.0, -123.8, 114.5), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 62.5, 115), (0, 90, 117.5), (0, 112.5, 115), (0, 127.5, 107.5)],
           [(9, 9), (8, 8), (7, 7), (5, 5)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=125, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=100, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=80.9, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=54, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=54, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=68.1, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=262.6, tol=1.2, how="bbox_y"),
]
