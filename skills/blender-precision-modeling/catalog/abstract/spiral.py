"""
spiral -- a tapered conic helix on a turned plinth: 2.5 turns, 38 -> 12 mm
radius, 5 -> 2.5 mm rod, rising 100 mm.

"taper" is in the recipe list, so both the sweep radius AND the rod diameter
shrink along the path; the per-point radius list is what makes it a conic
spiral rather than a coil spring.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    turns=2.5,
    outer_radius=38.0,
    inner_radius=12.0,
    height=100.0,
    rod_outer=5.0,
    rod_inner=2.5,
    plinth_radius=14.0,
    plinth_height=8.0,
    width=75.59,
    depth=70.19,
    height_total=103.52,
)

CHECKS = [
    dict(name="width", mm=75.59, tol=0.4, how="bbox_x", part="SpiralCoil"),
    dict(name="depth", mm=70.19, tol=0.4, how="bbox_y", part="SpiralCoil"),
    dict(name="overall_height", mm=103.52, tol=0.4, how="bbox_z",
         part="SpiralCoil"),
    # the puck now carries the full width of the coil
    dict(name="puck_diameter", mm=76.0, tol=0.4, how="diameter",
         part="SpiralBase"),
]


def _sweep(name, path, radii, seg=16, mat=None):
    """Sweep a circle along an OPEN polyline; `radii` is one radius per point.

    The frame is (tangent x Z) and this centreline is always climbing in z
    while its tangent never approaches vertical, so the frame stays continuous
    for the whole sweep. Two flat caps close the ends, which is what keeps the
    sweep manifold.
    """
    from mathutils import Vector

    pts = [Vector(p) for p in path]
    n = len(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        t.normalize()
        e1 = t.cross(Vector((0.0, 0.0, 1.0))).normalized()
        e2 = t.cross(e1).normalized()
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            q = p + radii[i] * (math.cos(a) * e1 + math.sin(a) * e2)
            verts.append((q.x, q.y, q.z))
    for i in range(n - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, i * seg + k2,
                          (i + 1) * seg + k2, (i + 1) * seg + k))
    faces.append(tuple(range(seg - 1, -1, -1)))
    base = (n - 1) * seg
    faces.append(tuple(range(base, base + seg)))

    ob = bkit.mesh_from(name, verts, faces, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 50)
    return ob


def build():
    # The coil has to STAND ON the puck. The helix's lower end sits at the
    # outer radius (f = 0), so with a 14 mm puck it ended 24 mm clear of it in
    # mid-air and the render read as two unrelated objects. Two changes fix it:
    # the puck is as wide as the coil, and a tie rod carries the helix's lower
    # end in to the puck centre, which is how the rod is actually fixed down.
    plinth_h = SPEC["plinth_height"]
    turns = SPEC["turns"]
    steps = 360
    path, radii = [], []
    for i in range(steps + 1):
        f = i / steps
        a = 2.0 * math.pi * turns * f
        rad = SPEC["outer_radius"] + (SPEC["inner_radius"] - SPEC["outer_radius"]) * f
        rod = SPEC["rod_outer"] + (SPEC["rod_inner"] - SPEC["rod_outer"]) * f
        path.append((rad * math.cos(a), rad * math.sin(a),
                     plinth_h + SPEC["height"] * f))
        radii.append(rod / 2.0)

    mat = bkit.pbr("SpiralRod", base=(0.88, 0.80, 0.42), metal=0.35, rough=0.24)
    coil = _sweep("SpiralCoil", path, radii, seg=18, mat=mat)

    # puck radius = coil outer radius, so the puck is exactly as wide as the
    # widest turn and the helix's foot lands on its rim
    puck_r = SPEC["outer_radius"]
    base = bkit.lathe("SpiralBase", [
        (0.0, 0.0),
        (puck_r, 0.0),
        (puck_r, plinth_h - 1.2),
        (puck_r - 1.6, plinth_h),
        (0.0, plinth_h),
    ], segments=64, mat=bkit.pbr("SpiralBaseMat", base=(0.30, 0.32, 0.36),
                                 metal=0.20, rough=0.35))

    # the tie rod: from the puck axis out to the helix's lower end, lying on
    # the puck's top face
    tie = bkit.cylinder("SpiralTie", SPEC["rod_outer"] / 2.0,
                        SPEC["outer_radius"], segments=24,
                        centre=(SPEC["outer_radius"] / 2.0, 0.0,
                                plinth_h + SPEC["rod_outer"] / 2.0 - 0.3),
                        axis="X", mat=mat)

    return dict(spec=SPEC, parts=3)