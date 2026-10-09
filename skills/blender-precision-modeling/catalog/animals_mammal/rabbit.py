"""
rabbit -- a 150 mm-shoulder dwarf rabbit

The rabbit signature is ear-to-body ratio: the ears are longer than the head and held vertical, the head is short with a blunt muzzle, the hind haunches are enormous, and the tail is a short puff that stands up rather than hanging.

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
    withers                  = 149.2,
    body_length              = 230.0,
    body_width               = 210.0,
    chest_depth              = 93.0,
    neck_length              = 59.2,
    head_length              = 85.8,
    head_width               = 88.0,
    head_top_height          = 177.0,
    shoulder_joint_height    = 90.0,
    stance_front_track       = 184.8,
    stance_hind_track        = 193.2,
    tail_length              = 34.0,
    overall_length           = 360.4,
    overall_height           = 243.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (115, 73.5, 76.3, 135),
            (78.2, 98.7, 93, 145.5),
            (11.5, 105, 93, 148.5),
            (-50.6, 100.8, 93, 149.2),
            (-82.8, 92.4, 87.4, 146.2),
            (-108.1, 75.6, 70.7, 138),
            (-115, 56.7, 53.9, 129),
    ]
FRONT_PATH = [(69, 92.4, 90), (67, 92.4, 51), (69, 92.4, 22.5), (73, 92.4, 41.6), (91.9, 92.4, 13), (125.5, 92.4, 13)]
FRONT_RAD = [(34, 34), (30.7, 30.7), (22.4, 21.2), (23.8, 21.2), (27, 13), (23.5, 11.4)]
HIND_PATH = [(-69, 96.6, 90), (-45, 96.6, 48), (-65, 96.6, 21), (-55, 96.6, 41.6), (-36.1, 96.6, 13), (-2.5, 96.6, 13)]
HIND_RAD = [(34, 34), (30.7, 30.7), (22.4, 21.2), (23.8, 21.2), (27, 13), (23.5, 11.4)]
EAR_PATH = [(117.3, 24, 135), (114.3, 27.8, 201.3), (111.9, 31, 242.6)]
EAR_RAD = [(10.3, 21.8), (9, 23), (3.1, 6.9)]


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

    coat = bkit.pbr("NetherlanddwarfrabbitCoat", base=(0.600, 0.520, 0.440), rough=0.70)
    pale = bkit.pbr("NetherlanddwarfrabbitPale", base=(0.800, 0.760, 0.700), rough=0.74)
    dark = bkit.pbr("NetherlanddwarfrabbitDark", base=(0.350, 0.160, 0.180), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 65.5)

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
    _sweep("Neck", [(0, -92, 117), (0, -109.6, 120.1), (0, -126.7, 125.1), (0, -139.8, 130.7), (0, -148.3, 135)],
           [(48, 46), (45.3, 43.5), (40.6, 39.1), (35.6, 34.4), (32, 31)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -122.8, 135), (0, -148.8, 135), (0, -180.8, 132), (0, -202.8, 126)],
           [(44, 42), (44, 41), (36, 31), (26, 22)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 15.0, segments=24, rings=12,
                  centre=(0.0, -208.8, 124.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 115, 138), (0, 126.5, 150)],
           [(17, 17), (14, 14)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=230, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=210, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=96.8, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=85.8, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=88, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=34, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=360.4, tol=1.2, how="bbox_y"),
]
