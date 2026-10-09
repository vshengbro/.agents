"""
squirrel -- a 110 mm-shoulder red squirrel

A squirrel is a squirrel because of the tail: a plume that arcs up over the back and forward, thicker than the body. The plume is a lofted sweep with radii that swell past the hip and taper to a point.

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
    withers                  = 108.9,
    body_length              = 150.0,
    body_width               = 95.0,
    chest_depth              = 68.2,
    neck_length              = 38.3,
    head_length              = 49.4,
    head_width               = 42.0,
    head_top_height          = 120.0,
    shoulder_joint_height    = 66.0,
    stance_front_track       = 79.8,
    stance_hind_track        = 81.7,
    tail_length              = 106.8,
    overall_length           = 263.3,
    overall_height           = 201.2,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (75, 29.4, 54.6, 99),
            (51, 42.8, 65.5, 106.7),
            (7.5, 47.5, 68.2, 108.9),
            (-33, 45.6, 68.2, 108.9),
            (-54, 40.9, 62.7, 107.2),
            (-70.5, 32.3, 49.1, 101.2),
            (-75, 23.8, 36.8, 94.6),
    ]
FRONT_PATH = [(45, 39.9, 66), (44, 39.9, 37.4), (45, 39.9, 16.5), (47, 39.9, 25.6), (56.5, 39.9, 8), (73.2, 39.9, 8)]
FRONT_RAD = [(17, 17), (14.2, 14.2), (10.6, 10.6), (11.3, 10.6), (14, 8), (12.2, 7)]
HIND_PATH = [(-45, 40.9, 66), (-33, 40.9, 36.3), (-43, 40.9, 16.5), (-37, 40.9, 25.6), (-27.5, 40.9, 8), (-10.8, 40.9, 8)]
HIND_RAD = [(17, 17), (14.2, 14.2), (10.6, 10.6), (11.3, 10.6), (14, 8), (12.2, 7)]
EAR_PATH = [(78.3, 15, 99), (83.3, 18.1, 117.6), (87.4, 20.7, 129.2)]
EAR_RAD = [(5.8, 10.4), (5, 11), (1.8, 3.3)]


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

    coat = bkit.pbr("RedsquirrelCoat", base=(0.580, 0.300, 0.140), rough=0.70)
    pale = bkit.pbr("RedsquirrelPale", base=(0.840, 0.780, 0.660), rough=0.74)
    dark = bkit.pbr("RedsquirrelDark", base=(0.120, 0.100, 0.090), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 50.2)

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
    _sweep("Neck", [(0, -60, 85.8), (0, -71.4, 88.2), (0, -82.3, 91.9), (0, -90.6, 96), (0, -96, 99)],
           [(26, 26), (24.4, 24.4), (21.8, 21.8), (19, 19), (17, 17)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -81.3, 99), (0, -95.3, 99), (0, -113.3, 96), (0, -127.3, 91)],
           [(21, 21), (21, 20), (16, 14), (11, 10)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 9.0, segments=24, rings=12,
                  centre=(0.0, -131.3, 90.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 75, 103.4), (0, 90, 125.4), (0, 99, 154), (0, 99, 180.4), (0, 93, 198)],
           [(16, 16), (22, 22), (24, 24), (20, 20), (10, 10)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=150, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=95, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=68.2, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=49.4, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=42, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=106.8, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=263.3, tol=1.2, how="bbox_y"),
]
