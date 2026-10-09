"""
tulip -- a 108 mm Darwin tulip: a smooth lathed cup with six outer tepals
splayed 34 deg off vertical.

A tulip is the easiest flower in the catalog to get right, because its cup is a
surface of revolution: `lathe` builds the closed body in one call, and the six
tepals are a radial array about the cup axis. The tepal pitch is derived from
the cup's own mouth radius (36 mm) so the array is the geometry's decision, not
a typed-in constant.

The tulip's own silhouette is the S-curve of its outer wall -- widest at 62% of
the flower height and drawn back in above it -- so the profile is given real
nodes rather than a straight taper.
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
    flower_height  = 78.0,
    flower_width   = 84.0,
    stem_length    = 62.0,
    tepals         = 6,
    overall_height = 140.0,
)

FLOWER_Z = 62.0                 # where the bloom sits on the stem
# (radius, height above the flower base) -- the tulip's drawn-in waist.
CUP = [
    (0.0, 0.0),
    (13.0, 0.0),
    (19.0, 6.0),
    (26.0, 20.0),
    (33.0, 36.0),
    (38.0, 50.0),
    (36.0, 62.0),
    (28.0, 72.0),
    (16.0, 77.0),
    (0.0, 78.0),
]

# (t, width_scale) -- a rounded obovate tepal.
TEPAL = [(0.00, 0.34), (0.18, 0.72), (0.44, 0.98), (0.70, 1.00),
         (0.88, 0.74), (1.00, 0.12)]


def _tepal(name, base, direction, length, width, thick, curl, mat, n=16):
    d = Vector(direction).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (t, ws) in TEPAL:
        c = Vector(base) + d * (length * t) + nrm * (curl * t * t)
        w = width * ws
        th = thick * (1.0 - 0.35 * t)
        ring = []
        for j in range(n):
            a = 2.0 * math.pi * j / n
            cy, sz = math.cos(a), math.sin(a)
            ring.append(tuple(c + side * (w * cy) + nrm * (th * sz)))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    petal = bkit.pbr("TulipPetal", base=(0.610, 0.075, 0.135), rough=0.36,
                     coat=0.30)
    petal_in = bkit.pbr("TulipPetalInner", base=(0.680, 0.140, 0.180),
                        rough=0.34, coat=0.35)
    stalk = bkit.pbr("TulipStalk", base=(0.140, 0.310, 0.095), rough=0.56)
    leaf = bkit.pbr("TulipLeaf", base=(0.115, 0.280, 0.090), rough=0.55)

    # ---- stem: a gentle S so the bloom is not stacked on a post
    stem = bkit.loft("Stem", [[(0.0, y, z) for (x, y) in
                               bkit.superellipse_section(2.0 * r, 2.0 * r, n=2.2,
                                                        steps=18)]
                              for (z, y, r) in ((0.0, 0.0, 4.4),
                                                (22.0, 1.6, 3.8),
                                                (44.0, 2.2, 3.4),
                                                (FLOWER_Z, 1.4, 3.2))],
                    mat=stalk, smooth=True)
    bkit.recalc(stem)

    # ---- the cup: one closed solid of revolution, the flower's own width
    cup = bkit.lathe("FlowerCup", CUP, segments=40,
                     centre=(0.0, 0.0, FLOWER_Z), mat=petal_in)
    bkit.assign_faces_by(cup, petal,
                         lambda c, n: c.z / bkit.MM > FLOWER_Z + 50.0)

    # ---- six tepals splayed off the cup mouth. The mouth radius (36 mm) sets
    # the splay; 34 deg is the real Darwin-hybrid opening angle.
    t0 = _tepal("Tepal", (0.0, 0.0, FLOWER_Z + 46.0),
                (math.sin(math.radians(34.0)), 0.0,
                 math.cos(math.radians(34.0))),
                34.0, 25.0, 2.2, -7.0, petal)
    bkit.array_radial(t0, SPEC["tepals"], centre=(0.0, 0.0, FLOWER_Z + 46.0))

    # ---- two strap leaves on the stem
    for i, (z, az) in enumerate(((20.0, 40.0), (38.0, 220.0))):
        a = math.radians(az)
        lf = _tepal("Leaf%d" % i, (0.0, 0.0, z),
                    (math.cos(a), math.sin(a), 0.55), 62.0, 12.0, 1.6, 12.0,
                    leaf, n=12)
        lf.name = "Leaf%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="flower_width",  mm=76.0,  tol=1.0, how="diameter", part="FlowerCup"),
    dict(name="flower_height", mm=78.0,  tol=1.0, how="bbox_z",    part="FlowerCup"),
    dict(name="stem_length",   mm=62.0,  tol=1.0, how="bbox_z",    part="Stem"),
    dict(name="bloom_height",  mm=140.0, tol=2.0,  how="top_z", part="FlowerCup"),
]
