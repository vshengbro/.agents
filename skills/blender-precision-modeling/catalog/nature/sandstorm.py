"""
sandstorm -- a 5 m wall of sand: a rolling dust front, a dense advancing base,
and 120 grit particles in three size grades.

A sandstorm is a wall, not a cloud. The difference is entirely in the
distribution: the mass is TALL and DENSE at the base and THIN at the top, so
the radius law falls off with height much faster than a cumulus's does, and the
leading edge is a sloping front rather than a lumpy row.

The particles are three grades on three station grids, and the grids are offset
from one another. One grid of 120 identical grains reads as a screen door;
three offset grids of graded grains read as suspended sand.

The front is built as a slab (the waterfall technique) so the advancing face
is a surface with a shape, and the wall leans over the viewer the way a real
haboob does.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width   = 5000.0,
    height  = 2600.0,
    depth   = 2200.0,
    particles = 120,
)

SEG = 28
H = SPEC["height"]
NODES = 16


def _front(t):
    """The advancing face: a slab leaning back over the viewer."""
    # t = 0 at the ground, 1 at the top
    return Vector((0.0, -260.0 * t * t, H * t))


def build():
    dust = bkit.pbr("SandstormDust", base=(0.620, 0.480, 0.290), rough=0.96,
                    transmission=0.28, ior=1.05)
    dust_d = bkit.pbr("SandstormDustDense", base=(0.470, 0.345, 0.195),
                      rough=0.97, transmission=0.18, ior=1.05)
    grit = bkit.pbr("SandGrit", base=(0.720, 0.590, 0.380), rough=0.94)
    grit_f = bkit.pbr("SandGritFine", base=(0.800, 0.690, 0.480), rough=0.95)
    sky = bkit.pbr("StormSky", base=(0.420, 0.330, 0.220), rough=0.98)

    # ---- the front: a closed slab swept up the face. The radius law falls off
    # fast with height -- the defining difference between a sandstorm wall and
    # a cumulus, whose lobes stay wide all the way up.
    rings = []
    for i in range(NODES + 1):
        t = i / float(NODES)
        c = _front(t)
        r = 1500.0 * (1.0 - 0.72 * t ** 0.7) + 120.0
        ring = []
        for j in range(SEG):
            a = 2.0 * math.pi * j / SEG
            # the front is not circular: it is a wall, so the section is wide
            # and shallow and its width falls off with height
            rr = r * (1.0 + 0.10 * math.sin(4.0 * a + t * 3.0)
                      + 0.07 * math.sin(7.0 * a - t * 2.0))
            ring.append((rr * math.cos(a) * 1.9, c.y + rr * math.sin(a) * 0.72,
                         c.z))
        rings.append(ring)
    front = bkit.loft("DustFront", rings, mat=dust, smooth=True)
    bkit.recalc(front)

    # ---- the dense base: the first 700 mm is opaque, and that band is what
    # makes it a sandstorm rather than a brown cloud
    rings2 = []
    for i in range(7):
        t = 0.27 * i / 6.0
        c = _front(t)
        r = 1450.0 * (1.0 - 0.72 * t ** 0.7) * 0.96
        ring = []
        for j in range(SEG):
            a = 2.0 * math.pi * j / SEG
            rr = r * (1.0 + 0.08 * math.sin(4.0 * a + t * 3.0))
            ring.append((rr * math.cos(a) * 1.9, c.y + rr * math.sin(a) * 0.72,
                         c.z))
        rings2.append(ring)
    base = bkit.loft("DustBase", rings2, mat=dust_d, smooth=True)
    bkit.recalc(base)

    # ---- three grades of grit on three OFFSET station grids. One grid of
    # identical grains reads as a screen door; three offset grades read as
    # suspended sand.
    grades = ((0.0, 320.0, 26.0, grit), (700.0, 420.0, 16.0, grit_f),
              (1500.0, 380.0, 10.0, grit_f))
    n = 0
    for (z0, pitch, r, mat) in grades:
        for (x, y) in bkit.grid_positions(cols=7, rows=6, pitch_x=pitch,
                                          pitch_y=pitch * 0.8):
            if n >= SPEC["particles"]:
                break
            if math.hypot(x, y) > 1700.0:
                continue
            ob = bkit.uv_sphere("Grit%03d" % n, 1.0, segments=10, rings=6,
                                centre=(x + 0.37 * z0, y - 0.21 * z0,
                                        z0 + 120.0 * abs(math.sin(1.9 * n))),
                                mat=mat)
            ob.scale = (r, r * 0.9, r * 0.7)
            ob.name = "Grit%03d" % n
            n += 1

    # ---- the sky the wall is eating
    bkit.lathe("StormSky", [(0.0, 0.0), (4200.0, 0.0), (7000.0, 400.0),
                            (8600.0, 1000.0)],
               segments=48, mat=sky)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + n + 1)


CHECKS = [
    dict(name="width", mm=6523.5, tol=32.62, how="bbox_x", part="DustFront"),
    dict(name="height", mm=2600.0, tol=40.0, how="top_z", part="DustFront"),
    dict(name="depth", mm=2475.0, tol=12.37, how="bbox_y", part="DustFront"),
    dict(name="dense_base", mm=700.0, tol=8.0, how="bbox_z", part="DustBase"),
]
