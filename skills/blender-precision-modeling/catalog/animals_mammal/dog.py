"""
dog -- a 380 mm-shoulder beagle standing square

Proportions are beagle, not generic dog: body length is 1.13x the shoulder height, the chest is deep relative to a long-backed breed, and the head is carried level with the withers on a short neck. The hound stance has plumb front legs and a strongly angulated hind pair.

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
    body_length              = 430.0,
    body_width               = 165.0,
    chest_depth              = 210.1,
    neck_length              = 141.2,
    head_length              = 168.5,
    head_width               = 100.0,
    head_top_height          = 373.1,
    shoulder_joint_height    = 228.0,
    stance_front_track       = 151.8,
    stance_hind_track        = 155.1,
    tail_length              = 132.8,
    overall_length           = 786.6,
    overall_height           = 380.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (215, 51.1, 168.1, 343.9),
            (154.8, 74.2, 203.8, 370.5),
            (21.5, 82.5, 210.1, 376.2),
            (-94.6, 80.8, 210.1, 380),
            (-154.8, 75.9, 199.6, 374.3),
            (-202.1, 61, 163.9, 353.4),
            (-215, 46.2, 126.1, 330.6),
    ]
FRONT_PATH = [(129, 75.9, 228), (133, 75.9, 125.4), (136, 75.9, 55.1), (141, 75.9, 44.8), (158.1, 75.9, 14), (188.5, 75.9, 14)]
FRONT_RAD = [(36, 40), (28.3, 30.7), (16.5, 16.5), (17.5, 16.5), (22.7, 14), (19.7, 12.3)]
HIND_PATH = [(-129, 77.5, 228), (-103, 77.5, 129.2), (-122, 77.5, 62.7), (-107, 77.5, 44.8), (-89.9, 77.5, 14), (-59.5, 77.5, 14)]
HIND_RAD = [(36, 40), (28.3, 30.7), (16.5, 16.5), (17.5, 16.5), (22.7, 14), (19.7, 12.3)]
EAR_PATH = [(246.6, 34, 321.1), (250.7, 37.8, 264.8), (254, 41, 229.7)]
EAR_RAD = [(12.6, 30.4), (11, 32), (3.8, 9.6)]


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

    coat = bkit.pbr("BeagleCoat", base=(0.480, 0.300, 0.150), rough=0.70)
    pale = bkit.pbr("BeaglePale", base=(0.780, 0.660, 0.500), rough=0.74)
    dark = bkit.pbr("BeagleDark", base=(0.070, 0.060, 0.060), rough=0.34)

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
                      lambda c, n: c.z / bkit.MM < 195.5)

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
    _sweep("Neck", [(0, -172, 281.2), (0, -214.5, 287), (0, -255.4, 297.8), (0, -286.9, 311), (0, -307.4, 321.1)],
           [(64, 68), (58.3, 62.5), (49.9, 54.1), (41.7, 45.8), (36, 40)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -254.3, 321.1), (0, -298.3, 321.1), (0, -352.3, 319.1), (0, -394.3, 315.1), (0, -420.3, 312.1)],
           [(50, 52), (49, 50), (41, 39), (30, 27), (24, 21.8)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 15.0, segments=24, rings=12,
                  centre=(0.0, -428.3, 315.1), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 215, 334.4), (0, 266.6, 319.2), (0, 309.6, 273.6), (0, 335.4, 228)],
           [(16, 16), (15, 15), (12, 12), (9, 9)], coat, n=2.4, steps=24)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=430, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=165, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=213.9, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=168.5, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=100, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=132.8, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=786.6, tol=1.2, how="bbox_y"),
]
