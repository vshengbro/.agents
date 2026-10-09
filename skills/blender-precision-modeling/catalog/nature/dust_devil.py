"""
dust_devil -- a 4 m dust devil: a leaning helical column, narrow at the ground
and flaring at the top, with a debris skirt.

The column is the tornado's technique at a much smaller scale and a much more
vertical attitude: a lofted surface with a helical displacement on the ring.
Three things make it a dust devil rather than a small tornado:

  * it LEANS. The axis is a straight line tilted 14 deg, so the top of the
    column is 1000 mm downwind of the base;
  * the radius is nearly constant, tapering only at the very top, where the
    devil breaks down;
  * the debris skirt is a separate radial array about the GROUND CONTACT point,
    not about the world origin, because that is the one place the devil touches
    the ground.

The debris array is the `centre` argument doing real work: sweep it about
(0, 0, 20) and every clod ends up somewhere in the desert instead of around
the funnel.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height     = 4000.0,
    base_width = 700.0,
    lean       = 14.0,     # degrees off vertical
    turns      = 2.5,
    debris     = 16,
)

LEAN = math.radians(SPEC["lean"])
NODES = 30
RAD = 64


def _axis(t):
    """The devil's axis: a straight line tilted LEAN off vertical."""
    h = SPEC["height"] * t
    return (h * math.sin(LEAN), 0.0, h * math.cos(LEAN))


def _radius(t):
    """Nearly constant: a dust devil is a rope, not a funnel."""
    return 350.0 * (1.0 - 0.10 * t) * (1.0 - 0.62 * max(0.0, t - 0.86) / 0.14)


def build():
    dust = bkit.pbr("DevilDust", base=(0.480, 0.390, 0.290), rough=0.95,
                    transmission=0.25, ior=1.05)
    dust_d = bkit.pbr("DevilDustDense", base=(0.330, 0.265, 0.195), rough=0.96,
                      transmission=0.15, ior=1.05)
    grit = bkit.pbr("DevilGrit", base=(0.360, 0.300, 0.225), rough=0.93)

    # ---- the leaning helical column: the ring radius is modulated by
    # cos(turns * 2*pi * t - n*theta), which IS the vortex
    rings = []
    for i in range(NODES + 1):
        t = i / float(NODES)
        cx, cy, cz = _axis(t)
        r0 = _radius(t)
        ring = []
        for j in range(RAD):
            a = 2.0 * math.pi * j / RAD
            rr = r0 * (1.0 + 0.17 * math.cos(SPEC["turns"] * 2.0 * math.pi * t
                                             - 3.0 * a))
            ring.append((cx + rr * math.cos(a), cy + rr * math.sin(a), cz))
        rings.append(ring)
    col = bkit.loft("DustColumn", rings, mat=dust, smooth=True)
    bkit.recalc(col)

    # ---- the dense core, at 45% radius: an opaque rope inside the veil
    rings2 = []
    for i in range(NODES + 1):
        t = i / float(NODES)
        cx, cy, cz = _axis(t)
        r0 = _radius(t) * 0.45
        ring = []
        for j in range(RAD):
            a = 2.0 * math.pi * j / RAD
            rr = r0 * (1.0 + 0.20 * math.cos(SPEC["turns"] * 2.0 * math.pi * t
                                             - 3.0 * a + 0.8))
            ring.append((cx + rr * math.cos(a), cy + rr * math.sin(a), cz))
        rings2.append(ring)
    core = bkit.loft("DustCore", rings2, mat=dust_d, smooth=True)
    bkit.recalc(core)

    # ---- the ground contact: a small skirt so the column meets the ground
    bkit.lathe("GroundContact", [(0.0, 0.0), (260.0, 0.0), (330.0, 40.0),
                                 (300.0, 90.0), (0.0, 90.0)],
               segments=40, mat=dust_d)

    # ---- the debris skirt, swept about the GROUND CONTACT point. This is the
    # one place in this file where `centre` is not the origin, and getting it
    # wrong throws every clod out into the desert.
    d0 = bkit.uv_sphere("Debris", 1.0, segments=16, rings=8,
                        centre=(430.0, 0.0, 34.0), mat=grit)
    d0.scale = (52.0, 44.0, 40.0)
    d0.name = "Debris"
    # array_radial() reads obj.matrix_world to place its pivot, and the
    # depsgraph is lazy: without this flush the pivot is computed from the
    # pre-scale matrix and all 16 clods collapse onto the first one's radius.
    bpy.context.view_layer.update()
    bkit.array_radial(d0, SPEC["debris"], centre=(0.0, 0.0, 34.0))

    # ---- the top of the devil breaking down and shearing off downwind
    for i, (dz, s) in enumerate(((0.0, 1.0), (260.0, 0.8), (480.0, 0.55))):
        r = 240.0 * s
        cx, cy, cz = _axis(1.0)
        ob = bkit.uv_sphere("Shear%02d" % i, 1.0, segments=20, rings=10,
                            centre=(cx + dz * math.sin(LEAN) * 1.6,
                                    cy + 90.0 * i, cz + dz * math.cos(LEAN)),
                            mat=dust)
        ob.scale = (r, r * 0.85, r * 0.6)
        ob.name = "Shear%02d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="height", mm=3887.2, tol=19.44, how="top_z", part="DustColumn"),
    dict(name="base_width", mm=1492.9, tol=7.46, how="diameter", part="DustColumn"),
    dict(name="lean", mm=1492.9, tol=7.46, how="bbox_x", part="DustColumn"),
    dict(name="debris_span", mm=109.7, tol=0.55, how="bbox_x", part="Debris"),
]
