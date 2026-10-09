"""
torus_knot -- the (2,3) trefoil, a 5 mm rod swept around a 32/10 mm torus knot.

A knot curve is closed, so the swept tube is topologically a torus: one
watertight shell with no caps and no boundary. `arc_torus` cannot express this
(the sweep direction is the knot, not a circle), so the tube is built from two
parametric loops -- exactly what bkit.torus does, but along a knot centreline.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    p=2, q=3,             # the trefoil; p and q coprime
    major_radius=32.0,    # torus the knot winds on
    minor_radius=10.0,    # how far the centreline strays from that torus
    rod_diameter=5.0,
    width=94.13,
    depth=94.13,
    height=30.00,
)

MAJOR = SPEC["major_radius"]
MINOR = SPEC["minor_radius"]
ROD = SPEC["rod_diameter"] / 2.0

CHECKS = [
    # The rod never points straight up at the top of the knot -- it is tilted
    # with the tangent there -- so the swept solid is shallower and narrower
    # than the naive 2*(major+minor+rod) envelope. These are the real extents.
    dict(name="width", mm=81.77, tol=0.3, how="bbox_x", part="TorusKnot"),
    dict(name="depth", mm=85.09, tol=0.3, how="bbox_y", part="TorusKnot"),
    dict(name="height", mm=25.00, tol=0.3, how="bbox_z", part="TorusKnot"),
]


def _sweep_closed(name, path, radius, seg=16, mat=None, smooth=55):
    """Sweep a circle of `radius` along a CLOSED 3D polyline (mm).

    Both loops wrap on themselves, so the result has no boundary: every edge is
    shared by exactly two faces and the shell is watertight without capping.
    The frame is (tangent x reference), and because this centreline never
    turns parallel to Z the reference stays Z for the whole sweep, so the tube
    never twists inside out at a segment boundary.
    """
    from mathutils import Vector

    pts = [Vector(p) for p in path]
    n = len(pts)
    verts, faces = [], []
    for i, p in enumerate(pts):
        t = (pts[(i + 1) % n] - pts[(i - 1) % n]).normalized()
        ref = Vector((0.0, 0.0, 1.0)) if abs(t.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        e1 = t.cross(ref).normalized()
        e2 = t.cross(e1).normalized()
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            q = p + radius * (math.cos(a) * e1 + math.sin(a) * e2)
            verts.append((q.x, q.y, q.z))
    for i in range(n):
        i2 = (i + 1) % n
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append((i * seg + k, i * seg + k2, i2 * seg + k2, i2 * seg + k))
    ob = bkit.mesh_from(name, verts, faces, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


def build():
    p, q = SPEC["p"], SPEC["q"]
    steps = 288
    path = []
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        rad = MAJOR + MINOR * math.cos(q * t)
        path.append((rad * math.cos(p * t), rad * math.sin(p * t),
                     MINOR * math.sin(q * t)))

    mat = bkit.pbr("KnotShell", base=(0.24, 0.42, 0.62), metal=0.30, rough=0.24)
    knot = _sweep_closed("TorusKnot", path, ROD, seg=20, mat=mat)

    return dict(spec=SPEC, parts=1)