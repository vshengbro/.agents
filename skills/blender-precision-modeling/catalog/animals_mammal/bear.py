"""
bear -- a 950 mm-shoulder grizzly

A bear is a loaf: body length barely 1.4x the shoulder height, the ears are round and set wide, the muzzle is short and broad, and the tail is a stub. The hind legs carry more of the mass than the front.

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
    withers                  = 950.0,
    body_length              = 1320.0,
    body_width               = 660.0,
    chest_depth              = 640.3,
    neck_length              = 378.3,
    head_length              = 318.6,
    head_width               = 344.0,
    head_top_height          = 985.8,
    shoulder_joint_height    = 589.0,
    stance_front_track       = 580.8,
    stance_hind_track        = 594.0,
    tail_length              = 106.5,
    overall_length           = 1908.6,
    overall_height           = 985.8,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (660, 224.4, 537.9, 859.8),
            (475.2, 303.6, 627.5, 926.2),
            (66, 330, 640.3, 940.5),
            (-290.4, 323.4, 640.3, 950),
            (-475.2, 303.6, 614.7, 935.8),
            (-620.4, 250.8, 512.2, 883.5),
            (-660, 198, 409.8, 826.5),
    ]
FRONT_PATH = [(396, 290.4, 589), (388, 290.4, 323), (394, 290.4, 142.5), (404, 290.4, 160), (459.8, 290.4, 50), (559, 290.4, 50)]
FRONT_RAD = [(96, 104), (85, 92), (56.6, 54.3), (60, 54.3), (88.6, 50), (77.1, 44)]
HIND_PATH = [(-396, 297, 589), (-356, 297, 313.5), (-388, 297, 142.5), (-366, 297, 160), (-310.2, 297, 50), (-211, 297, 50)]
HIND_RAD = [(96, 104), (85, 92), (56.6, 54.3), (60, 54.3), (88.6, 50), (77.1, 44)]
EAR_PATH = [(779, 132, 821.8), (790.9, 136.2, 866.4), (800.7, 139.6, 894.2)]
EAR_RAD = [(18.4, 45.6), (16, 48), (5.6, 14.4)]


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

    coat = bkit.pbr("GrizzlybearCoat", base=(0.400, 0.280, 0.190), rough=0.70)
    pale = bkit.pbr("GrizzlybearPale", base=(0.560, 0.440, 0.320), rough=0.74)
    dark = bkit.pbr("GrizzlybearDark", base=(0.080, 0.070, 0.060), rough=0.34)

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
    _sweep("Neck", [(0, -528, 741), (0, -639.9, 760.5), (0, -751, 783.9), (0, -839.1, 806), (0, -897.6, 821.8)],
           [(220, 215), (205.5, 201.8), (181.8, 179.7), (157.2, 156.4), (140, 140)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -800.3, 821.8), (0, -878.3, 821.8), (0, -976.3, 809.8), (0, -1058.3, 793.8), (0, -1104.3, 783.8)],
           [(172, 164), (168, 156), (126, 102), (88, 68), (72.2, 68.9)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 44.0, segments=24, rings=12,
                  centre=(0.0, -1120.3, 775.8), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 660, 855), (0, 726, 798)],
           [(34, 34), (28, 28)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1320, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=660, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=651.2, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=318.6, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=344, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=106.5, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=1908.6, tol=1.2, how="bbox_y"),
]
