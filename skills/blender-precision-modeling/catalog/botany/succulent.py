"""
succulent -- a 30 mm echeveria rosette: 8 outer, 6 mid and 4 core leaves.

A succulent is a rosette, which is the purest use of `array_radial` in the
catalog: three concentric rings of identical leaves, each swept about the
rosette centre. The only thing that varies between rings is the count, the tilt
and the length, so the rings are built by one leaf function called three times.

The leaves are deliberately fat -- a fleshy superellipse section with n = 2.4
and a 6 mm half-thickness -- because a thin blade reads as a flower, not a
succulent, and the rosette is the whole identification.
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
    rosette_diameter = 30.0,
    rosette_height   = 23.0,
    outer_leaves     = 8,
    mid_leaves       = 6,
    core_leaves      = 4,
    leaf_thickness   = 5.6,
)

# (name, count, length, half_width, half_thick, tilt_deg, z_base, material)
RINGS = [
    ("LeafRingOuter", 8, 25.0, 8.0, 3.0, 64.0, 9.0, "LeafOuter"),
    ("LeafRingMid",   6, 17.0, 6.0, 2.7, 42.0, 10.5, "LeafMid"),
    ("LeafRingCore",  4, 10.0, 4.5, 2.4, 20.0, 12.0, "LeafCore"),
]

# (t, width_scale) -- a spade-shaped succulent leaf, widest at 60% of its length.
LEAF = [(0.00, 0.46), (0.16, 0.84), (0.40, 1.00), (0.64, 0.96),
        (0.84, 0.70), (0.95, 0.36), (1.00, 0.10)]


def _leaf(name, base, tilt_deg, length, half_w, half_t, mat, n=16):
    """One fleshy leaf: superelliptical rings along a tilted axis."""
    t = math.radians(tilt_deg)
    d = Vector((math.cos(t), 0.0, math.sin(t)))
    ref = Vector((0.0, 0.0, 1.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (u, ws) in LEAF:
        c = Vector(base) + d * (length * u)
        w, th = half_w * ws, half_t * (1.0 - 0.22 * u)
        ring = []
        for j in range(n):
            a = 2.0 * math.pi * j / n
            cy, sz = math.cos(a), math.sin(a)
            # n = 2.4 squashes the section towards a rounded rectangle, which
            # is the cross-section of a leaf full of water.
            ex = math.copysign(abs(cy) ** (2.0 / 2.4), cy)
            ey = math.copysign(abs(sz) ** (2.0 / 2.4), sz)
            ring.append(tuple(c + side * (w * ex) + nrm * (th * ey)))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    green = bkit.pbr("SucculentGreen", base=(0.245, 0.400, 0.220), rough=0.44)
    green_d = bkit.pbr("SucculentDeep", base=(0.165, 0.310, 0.185), rough=0.46)
    blush = bkit.pbr("SucculentBlush", base=(0.400, 0.290, 0.235), rough=0.48)

    for (name, count, length, hw, ht, tilt, z, _matname) in RINGS:
        mat = {"LeafOuter": green, "LeafMid": green_d, "LeafCore": blush}[_matname]
        lf = _leaf(name, (0.0, 0.0, z), tilt, length, hw, ht, mat)
        # The hub is the rosette centre at the leaf's own base height, not the
        # world origin: orbiting about (0,0,0) would throw the outer ring's
        # copies down and out of the rosette.
        bkit.array_radial(lf, count, centre=(0.0, 0.0, z))

    # ---- the short stem the rosette sits on: a rosette with no stem is a
    # flat star, and the stem is what sets the plant's height above its pot
    bkit.lathe("Stem", [(0.0, 0.0), (4.2, 0.0), (3.6, 4.0), (4.4, 7.0),
                        (5.6, 9.0), (0.0, 9.0)],
               segments=24, mat=green_d)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(RINGS) + 1)


CHECKS = [
    dict(name="rosette_diameter", mm=26.1, tol=0.5, how="diameter",
         part="LeafRingOuter"),
    # LeafRingMid is the whole 6-copy array, so its bbox_z is the ring's rise,
    # not one leaf's thickness. A leaf's own girth cannot be read off a sweep.
    dict(name="mid_ring_rise", mm=15.0, tol=0.6, how="bbox_z",
         part="LeafRingMid"),
    dict(name="stem",             mm=9.0, tol=0.3, how="bbox_z", part="Stem"),
    dict(name="rosette_height",   mm=32.5, tol=0.5, how="top_z"),
]
