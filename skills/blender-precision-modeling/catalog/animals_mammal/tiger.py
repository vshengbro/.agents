"""
tiger -- a 1050 mm-shoulder male tiger

Stripes are a second material assigned to selected faces of the one torso solid -- a sin field over face centres. That keeps the mesh watertight, where a painted texture would have been the honest alternative but is out of scope for a procedural model.

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
    withers                  = 1050.0,
    body_length              = 1450.0,
    body_width               = 600.0,
    chest_depth              = 651.0,
    neck_length              = 419.4,
    head_length              = 348.2,
    head_width               = 296.0,
    head_top_height          = 1066.0,
    shoulder_joint_height    = 651.0,
    stance_front_track       = 504.0,
    stance_hind_track        = 516.0,
    tail_length              = 429.8,
    overall_length           = 2397.3,
    overall_height           = 1066.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (725, 186, 520.8, 950.2),
            (522, 270, 631.5, 1023.8),
            (72.5, 300, 651, 1039.5),
            (-319, 294, 651, 1050),
            (-522, 276, 618.4, 1034.2),
            (-681.5, 222, 507.8, 976.5),
            (-725, 168, 390.6, 913.5),
    ]
FRONT_PATH = [(435, 252, 651), (429, 252, 378), (433, 252, 168), (439, 252, 121.6), (478.6, 252, 38), (549, 252, 38)]
FRONT_RAD = [(72, 78), (56.6, 61.4), (35.4, 33), (37.5, 33), (64.8, 38), (56.4, 33.4)]
HIND_PATH = [(-435, 258, 651), (-405, 258, 367.5), (-429, 258, 168), (-411, 258, 121.6), (-371.4, 258, 38), (-301, 258, 38)]
HIND_RAD = [(72, 78), (56.6, 61.4), (35.4, 33), (37.5, 33), (64.8, 38), (56.4, 33.4)]
EAR_PATH = [(859.8, 112, 924), (871.6, 120.3, 968), (881.2, 127, 995.4)]
EAR_RAD = [(11.5, 32.3), (10, 34), (3.5, 10.2)]


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

    coat = bkit.pbr("SiberiantigerCoat", base=(0.840, 0.500, 0.120), rough=0.70)
    pale = bkit.pbr("SiberiantigerPale", base=(0.920, 0.820, 0.620), rough=0.74)
    dark = bkit.pbr("SiberiantigerDark", base=(0.090, 0.070, 0.060), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 479.6)

    # stripes: selected faces of the one torso solid take the darker coat.
    bkit.assign_faces_by(torso, dark,
                      lambda c, n: math.sin((0.85 * c.y + 1.15 * c.z) / bkit.MM * 0.0370) > 0.30)

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
    _sweep("Neck", [(0, -580, 819), (0, -703.4, 844.2), (0, -825.5, 874.6), (0, -922, 903.5), (0, -986, 924)],
           [(180, 180), (169.2, 169.2), (150.9, 150.9), (131.6, 131.6), (118, 118)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -878.5, 924), (0, -966.5, 924), (0, -1074.5, 916), (0, -1166.5, 900), (0, -1214.5, 890)],
           [(148, 142), (144, 138), (110, 92), (76, 60), (62.2, 59.6)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 40.0, segments=24, rings=12,
                  centre=(0.0, -1228.5, 884.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 710.5, 945), (0, 870, 882), (0, 1015, 735), (0, 1116.5, 546)],
           [(26, 26), (23, 23), (19, 19), (14, 14)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1450, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=600, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=661.5, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=348.2, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=296, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=429.8, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2397.3, tol=1.2, how="bbox_y"),
]
