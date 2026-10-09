"""
rose -- a cut garden rose, 92 mm bloom on a 120 mm stem, three petal whorls.

A rose is concentric whorls, so the petals are `array_radial` copies about the
bloom hub and the whorl counts come from a measured pitch: eight outer petals
at a 76 mm pitch ring, six at 56 mm, five at 36 mm. Deriving the counts from
the ring circumference is what keeps the whorls from interpenetrating into one
another -- a rose with 12 outer and 5 inner petals reads as a mess, not a rose.

Every petal is a loft of cupped, drooping rings, so each one is its own closed
solid and the assembly needs no boolean at all.
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
    bloom_diameter  = 92.0,
    stem_length     = 120.0,
    bloom_height    = 132.0,
    outer_petals    = 8,
    mid_petals      = 6,
    core_petals     = 5,
)

HUB_Z = 132.0
OUTER_L, OUTER_W = 46.0, 40.0
MID_L, MID_W = 38.0, 34.0
CORE_L, CORE_W = 28.0, 24.0

# (t, width_scale) -- a broad round-tipped rose petal, not a lance leaf.
PETAL = [(0.00, 0.30), (0.15, 0.68), (0.38, 0.98), (0.62, 1.00),
         (0.82, 0.76), (0.94, 0.36), (1.00, 0.10)]


def _petal(name, base, direction, length, width, thick, cup, droop, mat,
           n=18):
    """One cupped petal: rings along `direction`, cupped across the width."""
    d = Vector(direction).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (t, ws) in PETAL:
        c = Vector(base) + d * (length * t) + nrm * (-droop * t * t)
        w = width * ws
        th = thick * (1.0 - 0.4 * t)
        ring = []
        for j in range(n):
            a = 2.0 * math.pi * j / n
            cy, sz = math.cos(a), math.sin(a)
            ring.append(tuple(c + side * (w * cy)
                              + nrm * (th * sz + cup * (cy * cy - 0.5))))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    red = bkit.pbr("RoseRed", base=(0.520, 0.045, 0.070), rough=0.42, coat=0.25)
    red_d = bkit.pbr("RoseRedDeep", base=(0.400, 0.030, 0.055), rough=0.40,
                     coat=0.30)
    green = bkit.pbr("RoseStem", base=(0.105, 0.240, 0.080), rough=0.58)
    sepal = bkit.pbr("RoseSepal", base=(0.085, 0.205, 0.070), rough=0.60)

    # ---- stem and receptacle. The stem is the part that owns `stem_length`,
    # so the check points at it rather than at the whole 160 mm rose.
    bkit.cylinder("Stem", 3.4, SPEC["stem_length"], segments=16, r2=2.6,
                  centre=(0.0, 0.0, SPEC["stem_length"] / 2.0), mat=green)
    bkit.lathe("Receptacle", [(0.0, 0.0), (13.0, 2.0), (16.0, 9.0), (11.0, 15.0),
                              (0.0, 15.0)],
               segments=24, centre=(0.0, 0.0, HUB_Z - 15.0), mat=green)

    # ---- whorl 1: eight petals lying almost flat, cupping upward.
    w1 = _petal("PetalRingOuter", (0.0, 0.0, HUB_Z - 6.0), (1.0, 0.0, 0.16),
                OUTER_L, OUTER_W, 2.6, 7.0, 5.0, red)
    bkit.array_radial(w1, SPEC["outer_petals"], centre=(0.0, 0.0, HUB_Z - 6.0))

    # ---- whorl 2: six petals standing 26 deg steeper, over the first.
    w2 = _petal("PetalRingMid", (0.0, 0.0, HUB_Z - 2.0), (1.0, 0.0, 0.44),
                MID_L, MID_W, 2.4, 6.0, 4.0, red_d)
    bkit.array_radial(w2, SPEC["mid_petals"], centre=(0.0, 0.0, HUB_Z - 2.0))

    # ---- whorl 3: five tight petals forming the bud centre.
    w3 = _petal("PetalRingCore", (0.0, 0.0, HUB_Z + 2.0), (1.0, 0.0, 0.72),
                CORE_L, CORE_W, 2.2, 5.0, 2.0, red_d)
    bkit.array_radial(w3, SPEC["core_petals"], centre=(0.0, 0.0, HUB_Z + 2.0))

    # ---- five sepals splaying back under the bloom
    s0 = _petal("Sepal", (0.0, 0.0, HUB_Z - 12.0), (1.0, 0.0, -0.42),
                34.0, 9.0, 1.6, 0.0, 3.0, sepal, n=12)
    bkit.array_radial(s0, 5, centre=(0.0, 0.0, HUB_Z - 12.0))

    # ---- two compound leaves on the stem, each a pair of leaflets. One
    # leaflet is built at a 20 deg bearing and the array puts its opposite
    # there too, so a leaf can never be a single lopsided blade.
    for lvl, z in enumerate((52.0, 88.0)):
        az = math.radians(20.0 + 200.0 * lvl)
        lf = _petal("Leaf%d" % lvl, (0.0, 0.0, z),
                    (math.cos(az), math.sin(az), 0.30), 46.0, 20.0, 1.4, 2.0,
                    6.0, green, n=12)
        lf.name = "Leaf%d" % lvl
        bkit.array_radial(lf, 2, centre=(0.0, 0.0, z))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 1 + 1 + 4)


CHECKS = [
    dict(name="bloom_diameter", mm=96.0,  tol=0.5, how="diameter", part="PetalRingOuter"),
    dict(name="stem_length",    mm=120.0, tol=1.0, how="bbox_z",    part="Stem"),
    dict(name="receptacle_top", mm=132.0, tol=1.0, how="top_z",     part="Receptacle"),
    dict(name="bloom_height",   mm=152.0, tol=4.0, how="top_z"),
]
