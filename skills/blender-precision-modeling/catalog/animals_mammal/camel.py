"""
camel -- a 1800 mm-shoulder dromedary

The camel is the extreme of the family: 1800 mm at the shoulder, a single hump on the spine, a long S-curved neck, and long legs on small padded feet. The hump is a scaled sphere blended over the withers rather than a fifth torso section.

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
    withers                  = 1800.0,
    body_length              = 1800.0,
    body_width               = 700.0,
    chest_depth              = 819.0,
    neck_length              = 1078.9,
    head_length              = 305.3,
    head_width               = 208.0,
    head_top_height          = 2422.0,
    shoulder_joint_height    = 1134.0,
    stance_front_track       = 532.0,
    stance_hind_track        = 546.0,
    tail_length              = 833.9,
    overall_length           = 2476.9,
    overall_height           = 2440.1,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (900, 224, 655.2, 1629),
            (612, 322, 794.4, 1746),
            (90, 350, 819, 1782),
            (-396, 343, 819, 1800),
            (-648, 308, 769.9, 1773),
            (-846, 245, 606.1, 1674),
            (-900, 175, 442.3, 1557),
    ]
FRONT_PATH = [(540, 266, 1134), (534, 266, 720), (538, 266, 360), (544, 266, 162), (598, 266, 44), (694, 266, 44)]
FRONT_RAD = [(88, 98), (70.8, 75.5), (42.5, 40.1), (45, 40.1), (79.9, 44), (69.6, 38.7)]
HIND_PATH = [(-540, 273, 1134), (-504, 273, 702), (-532, 273, 360), (-512, 273, 162), (-458, 273, 44), (-362, 273, 44)]
HIND_RAD = [(88, 98), (70.8, 75.5), (42.5, 40.1), (45, 40.1), (79.9, 44), (69.6, 38.7)]
EAR_PATH = [(1088.4, 68, 2332.5), (1100, 76.3, 2377.8), (1109.4, 83.1, 2406.1)]
EAR_RAD = [(13.8, 24.7), (12, 26), (4.2, 7.8)]


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

    coat = bkit.pbr("DromedarycamelCoat", base=(0.680, 0.500, 0.300), rough=0.70)
    pale = bkit.pbr("DromedarycamelPale", base=(0.780, 0.620, 0.400), rough=0.74)
    dark = bkit.pbr("DromedarycamelDark", base=(0.200, 0.140, 0.100), rough=0.34)

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
    _sweep("Neck", [(0, -684, 1368), (0, -823.8, 1660.2), (0, -972.9, 1947.5), (0, -1100.5, 2173), (0, -1188, 2322)],
           [(160, 160), (142.6, 143.2), (118.4, 119.7), (95.5, 97.2), (80, 82)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -1101, 2322), (0, -1181, 2348), (0, -1297, 2372), (0, -1373, 2376)],
           [(104, 100), (100, 94), (68, 58), (52, 45)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 38.0, segments=24, rings=12,
                  centre=(0.0, -1385.0, 2372.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 900, 1620), (0, 1008, 1260), (0, 1044, 792)],
           [(18, 18), (14, 14), (10, 10)], coat, n=2.4, steps=24)

    # ---- the hump: one scaled sphere on the spine, which is how a
    # dromedary carries the fat -- not a fifth torso section
    hump = bkit.uv_sphere("Hump", 100.0, segments=32, rings=16,
                       centre=(0.0, 108, 1784), mat=coat)
    hump.scale = (1.15, 2.30, 1.60)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1800, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=700, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=848.4, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=305.3, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=208, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=833.9, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2476.9, tol=1.2, how="bbox_y"),
]
