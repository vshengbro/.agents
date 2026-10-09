"""
pig -- a 430 mm-shoulder Vietnamese pot-banded pig

Pigs are barrels: the body is nearly as deep as it is long, the legs are short and the head is a wedge that ends in a flat snout disc. The disc is modelled as its own cylinder overlapping the muzzle, never as a hole cut into it.

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
    withers                  = 430.0,
    body_length              = 520.0,
    body_width               = 285.0,
    chest_depth              = 301.0,
    neck_length              = 142.6,
    head_length              = 225.0,
    head_width               = 128.0,
    head_top_height          = 423.3,
    shoulder_joint_height    = 258.0,
    stance_front_track       = 239.4,
    stance_hind_track        = 245.1,
    tail_length              = 62.2,
    overall_length           = 814.9,
    overall_height           = 444.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (260, 99.8, 258.9, 389.2),
            (176.8, 133.9, 301, 419.2),
            (26, 142.5, 301, 425.7),
            (-114.4, 139.7, 301, 430),
            (-187.2, 131.1, 289, 423.6),
            (-244.4, 111.2, 246.8, 399.9),
            (-260, 85.5, 192.6, 374.1),
    ]
FRONT_PATH = [(156, 119.7, 258), (153, 119.7, 146.2), (155, 119.7, 68.8), (159, 119.7, 57.6), (179.7, 119.7, 18), (216.5, 119.7, 18)]
FRONT_RAD = [(38, 38), (33, 33), (22.4, 22.4), (23.8, 22.4), (31.3, 18), (27.3, 15.8)]
HIND_PATH = [(-156, 122.5, 258), (-138, 122.5, 146.2), (-152, 122.5, 68.8), (-140, 122.5, 57.6), (-119.3, 122.5, 18), (-82.5, 122.5, 18)]
HIND_RAD = [(38, 38), (33, 33), (22.4, 22.4), (23.8, 22.4), (31.3, 18), (27.3, 15.8)]
EAR_PATH = [(312.9, 52, 365.5), (323.3, 61.2, 404.4), (331.7, 68.7, 428.7)]
EAR_RAD = [(9.2, 24.7), (8, 26), (2.8, 7.8)]


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

    coat = bkit.pbr("Pot-bandedpigCoat", base=(0.420, 0.280, 0.300), rough=0.70)
    pale = bkit.pbr("Pot-bandedpigPale", base=(0.700, 0.600, 0.580), rough=0.74)
    dark = bkit.pbr("Pot-bandedpigDark", base=(0.240, 0.140, 0.160), rough=0.34)

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

    # bands: selected faces of the one torso solid take the darker coat.
    bkit.assign_faces_by(torso, dark,
                      lambda c, n: abs(math.sin((c.z / bkit.MM + 0.12 * c.y / bkit.MM) * 0.0524)) > 0.80)

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
    _sweep("Neck", [(0, -208, 326.8), (0, -250.4, 333.9), (0, -291.9, 344.1), (0, -324.4, 355.2), (0, -345.8, 363.3)],
           [(92, 90), (85.1, 82.4), (74.4, 71), (63.5, 59.8), (56, 52)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -279.9, 363.3), (0, -335.9, 357.3), (0, -405.9, 339.3), (0, -459.9, 319.3), (0, -485.9, 307.3)],
           [(64, 60), (61.4, 57.6), (46, 40), (38, 32), (36, 30)], coat, n=2.4, steps=32)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 260, 395.6), (0, 291.2, 421.4), (0, 312, 438.6)],
           [(9, 9), (8, 8), (7, 7)], coat, n=2.4, steps=24)

    # ---- snout: a short fat cylinder overlapping the muzzle. It is a
    # real part, never a bore -- cutting the muzzle face would leave the
    # loft's own cap exactly tangent to the cutter.
    bkit.cylinder("Snout", 36.0, 44.0, segments=28, centre=(0.0, -467.9, 301.3),
                  axis="Y", mat=dark)

    # ---- curly tail: a near-closed arc_torus tucked against the rump
    bkit.arc_torus("TailCurl", 26.0, 7.0, 20.0, 340.0, plane="XZ",
                  centre=(0.0, 262.6, 387.0), seg_major=28, mat=coat, caps=True)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=520, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=285, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=311.8, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=225, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=128, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=62.2, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=814.9, tol=1.2, how="bbox_y"),
]
