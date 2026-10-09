"""
sheep -- a 580 mm-shoulder primitive short-tailed breed

Sheep read as a woolly barrel on four short legs: the fleece is a shell of overlapping spheres over a lofted body, which is cheaper and far more convincing than trying to loft a lumpy surface.

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
    withers                  = 574.2,
    body_length              = 560.0,
    body_width               = 330.0,
    chest_depth              = 379.9,
    neck_length              = 189.2,
    head_length              = 277.8,
    head_width               = 104.0,
    head_top_height          = 593.4,
    shoulder_joint_height    = 348.0,
    stance_front_track       = 277.2,
    stance_hind_track        = 283.8,
    tail_length              = 73.0,
    overall_length           = 1019.1,
    overall_height           = 592.4,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (280, 105.6, 311.5, 522),
            (190.4, 151.8, 372.3, 562.6),
            (28, 165, 379.9, 571.3),
            (-123.2, 160, 379.9, 574.2),
            (-201.6, 148.5, 364.7, 565.5),
            (-263.2, 122.1, 296.3, 533.6),
            (-280, 92.4, 227.9, 501.7),
    ]
FRONT_PATH = [(168, 138.6, 348), (166, 138.6, 191.4), (168, 138.6, 84.1), (172, 138.6, 60.8), (192.7, 138.6, 19), (229.5, 138.6, 19)]
FRONT_RAD = [(38, 38), (30.7, 30.7), (18.9, 17.7), (20, 17.7), (31.3, 19), (27.3, 16.7)]
HIND_PATH = [(-168, 141.9, 348), (-148, 141.9, 191.4), (-164, 141.9, 89.9), (-152, 141.9, 60.8), (-131.3, 141.9, 19), (-94.5, 141.9, 19)]
HIND_RAD = [(38, 38), (30.7, 30.7), (18.9, 17.7), (20, 17.7), (31.3, 19), (27.3, 16.7)]
EAR_PATH = [(337.6, 46, 543), (386, 76.4, 546.7), (425.6, 101.2, 549)]
EAR_RAD = [(10.3, 23.8), (9, 25), (3.1, 7.5)]


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

    coat = bkit.pbr("SoaysheepCoat", base=(0.760, 0.730, 0.680), rough=0.92)
    pale = bkit.pbr("SoaysheepPale", base=(0.520, 0.490, 0.450), rough=0.74)
    dark = bkit.pbr("SoaysheepDark", base=(0.100, 0.090, 0.090), rough=0.34)

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
    _sweep("Neck", [(0, -224, 452.4), (0, -276.6, 474.2), (0, -327.4, 499.5), (0, -366.4, 522.9), (0, -392, 539.4)],
           [(80, 84), (72.6, 76.1), (61.7, 64.7), (51.2, 53.6), (44, 46)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -309.4, 539.4), (0, -379.4, 525.4), (0, -469.4, 493.4), (0, -535.4, 467.4), (0, -567.4, 453.4)],
           [(52, 54), (49.9, 51.8), (32, 33), (25, 26), (22, 23)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 21.0, segments=24, rings=12,
                  centre=(0.0, -579.4, 451.4), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 280, 522), (0, 313.6, 498.8), (0, 336, 464)],
           [(13, 13), (11, 11), (8, 8)], coat, n=2.4, steps=24)

    # ---- fleece: a shell of overlapping spheres laid out on a computed
    # grid. Positions come from grid_positions(), never hand-placed, and
    # every blob overlaps the torso so the two read as one woolly mass.
    for i, (gx, gy) in enumerate(bkit.grid_positions(cols=6, rows=3,
                                         pitch_x=107.7, pitch_y=114.0)):
        r = 104.0 + gy * 0.30
        bkit.uv_sphere("Fleece%d" % (i + 1), r, segments=20, rings=10,
                      centre=(gy * 0.68, -(gx - 11.2), 399.2), mat=coat)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=29)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=560, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=330, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=383.9, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=277.8, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=104, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=73, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=1019.1, tol=1.2, how="bbox_y"),
]
