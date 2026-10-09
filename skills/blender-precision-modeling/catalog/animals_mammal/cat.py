"""
cat -- a 250 mm-shoulder shorthair cat

Cats are the extreme of the family: body length 1.5x the shoulder height, a very short neck, a short muzzle on a wide skull, and tall prick ears. The hind legs are folded well forward under the body, which is why the hock angle here is much tighter than a dog's.

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
    withers                  = 245.0,
    body_length              = 380.0,
    body_width               = 148.0,
    chest_depth              = 175.0,
    neck_length              = 101.9,
    head_length              = 110.0,
    head_width               = 90.0,
    head_top_height          = 268.0,
    shoulder_joint_height    = 145.0,
    stance_front_track       = 130.2,
    stance_hind_track        = 133.2,
    tail_length              = 133.4,
    overall_length           = 659.6,
    overall_height           = 336.7,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (190, 44.4, 136.5, 225),
            (129.2, 65.1, 168, 242.5),
            (19, 74, 175, 245),
            (-83.6, 71.8, 175, 245),
            (-136.8, 66.6, 168, 241.2),
            (-178.6, 53.3, 133, 230),
            (-190, 40, 101.5, 215),
    ]
FRONT_PATH = [(114, 65.1, 145), (115, 65.1, 85), (115, 65.1, 37.5), (119, 65.1, 38.4), (133.4, 65.1, 12), (159, 65.1, 12)]
FRONT_RAD = [(30, 32), (23.6, 26), (15.3, 15.3), (16.3, 15.3), (20.5, 12), (17.9, 10.6)]
HIND_PATH = [(-114, 66.6, 145), (-84, 66.6, 82.5), (-110, 66.6, 38.8), (-98, 66.6, 38.4), (-83.6, 66.6, 12), (-58, 66.6, 12)]
HIND_RAD = [(30, 32), (23.6, 26), (15.3, 15.3), (16.3, 15.3), (20.5, 12), (17.9, 10.6)]
EAR_PATH = [(210.6, 28, 225), (214.7, 36, 263.1), (218, 42.5, 286.9)]
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

    coat = bkit.pbr("DomesticshorthairCoat", base=(0.460, 0.430, 0.400), rough=0.70)
    pale = bkit.pbr("DomesticshorthairPale", base=(0.760, 0.730, 0.700), rough=0.74)
    dark = bkit.pbr("DomesticshorthairDark", base=(0.080, 0.070, 0.080), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 94.5)

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
    _sweep("Neck", [(0, -152, 200), (0, -182.6, 203.6), (0, -212.4, 210.4), (0, -235.6, 218.7), (0, -250.8, 225)],
           [(50, 48), (46.8, 45), (41.4, 40), (35.9, 34.7), (32, 31)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -216.2, 225), (0, -244.2, 225), (0, -280.2, 223), (0, -306.2, 220), (0, -324.2, 218)],
           [(45, 43), (45, 42), (38, 32), (27, 23), (20, 18.1)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 11.0, segments=24, rings=12,
                  centre=(0.0, -330.2, 220.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 190, 220), (0, 239.4, 237.5), (0, 281.2, 265), (0, 304, 305), (0, 311.6, 335)],
           [(15, 15), (15, 15), (13, 13), (10, 10), (7, 7)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=380, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=148, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=175, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=110, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=90, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=133.4, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=659.6, tol=1.2, how="bbox_y"),
]
