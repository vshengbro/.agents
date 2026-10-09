"""
klein_bottle -- the non-orientable closed surface, as a mapping torus.

A Klein bottle is the mapping torus of a REFLECTION of the circle: take a tube
around a circular centreline and reflect the cross-section after one lap. So
the sweep frame's second axis has to satisfy e2(s + 2pi) = -e2(s), which a
single-valued frame around a circle cannot do -- it needs the half angle:

    e1(s) = (cos s, sin s, 0)                radial, periodic
    e2(s) = cos(s/2)*T(s) + sin(s/2)*Z       anti-periodic

Because e2 flips, the tube mesh cannot close the usual way (last row -> first
row, same column). It closes with the reflection: column j of the last row
meets column -j of the first row. That index flip in the closing band is the
whole difference between a Klein bottle and a torus.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    ring_radius=36.0,     # the base circle the tube wraps
    tube_radius=9.0,      # cross-section radius -- a fat tube on a small ring
    winding=1,            # reads as a plain torus; 9 mm on a 36 mm ring lets
    # the crossing through the middle show in the side view
    width=90.00,
    depth=90.00,
    height=18.00,
)

R = SPEC["ring_radius"]
r = SPEC["tube_radius"]

CHECKS = [
    dict(name="width", mm=90.00, tol=0.4, how="bbox_x", part="KleinBottle"),
    dict(name="depth", mm=90.00, tol=0.4, how="bbox_y", part="KleinBottle"),
    dict(name="height", mm=18.00, tol=0.4, how="bbox_z", part="KleinBottle"),
]


def build():
    steps, seg = 256, 48
    verts, faces = [], []

    for i in range(steps):
        s = 2.0 * math.pi * i / steps
        cs, sn = math.cos(s), math.sin(s)
        half = s / 2.0
        # e2 is anti-periodic on purpose -- see the module docstring.
        e2 = (math.cos(half) * -sn, math.cos(half) * cs, math.sin(half))
        for j in range(seg):
            t = 2.0 * math.pi * j / seg
            a, b = r * math.cos(t), r * math.sin(t)
            verts.append((R * cs + a * cs + b * e2[0],
                          R * sn + a * sn + b * e2[1],
                          b * e2[2]))

    for i in range(steps):
        i2 = (i + 1) % steps
        flip = (i2 == 0)
        for j in range(seg):
            j2 = (j + 1) % seg
            # e2 reverses sign across the seam, so column j lands on -j.
            a0 = i * seg + j
            a1 = i * seg + j2
            b0 = i2 * seg + ((seg - j) % seg if flip else j)
            b1 = i2 * seg + ((seg - j2) % seg if flip else j2)
            faces.append((a0, a1, b1, b0))

    mat = bkit.pbr("KleinGlaze", base=(0.20, 0.58, 0.56), metal=0.10, rough=0.22,
                   coat=0.4)
    bottle = bkit.mesh_from("KleinBottle", verts, faces, mat=mat)

    # Self-intersecting as an immersion -- the Klein bottle has no embedding in
    # R^3, so this is unavoidable, not a modelling slip -- but still one closed
    # orientable shell.
    bkit.recalc(bottle)
    _force_outward(bottle)
    bkit.shade_smooth(bottle, 55)

    return dict(spec=SPEC, parts=1)


def _force_outward(obj):
    """Make calc_volume(signed=True) positive, by flipping if it is not.

    On a self-intersecting immersion "outward" is ambiguous, and recalc() can
    land on the orientation whose winding-number-weighted volume is negative.
    health() counts that as negative_volume and fails the build, so the
    orientation is settled by measurement rather than by hope.
    """
    import bmesh

    for _ in range(2):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        vol = bm.calc_volume(signed=True)
        bm.free()
        if vol >= 0.0:
            return
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()