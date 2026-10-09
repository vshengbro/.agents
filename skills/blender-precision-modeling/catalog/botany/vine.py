"""
vine -- a 2 m climbing vine spiralling a trellis stake, 22 leaves on the helix.

A helix is not a radial array, so the stem is swept directly along a parametric
helix: radius 46 mm, one turn per 330 mm of rise. The leaf stations come off the
same law at every half-turn, alternating side, which is what makes the vine
read as a vine rather than as a corkscrew with decoration stuck on it.

The support is part of the model on purpose -- a vine is only recognisable in
relation to something it is climbing, and the stake is also what gives the
model a vertical datum for the leaf layout.
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
    height        = 2000.0,
    helix_diameter = 92.0,
    turns         = 6.0,
    leaves        = 22,
    leaf_length   = 96.0,
)

STAKE_H = 2000.0
R_H = SPEC["helix_diameter"] / 2.0
PITCH = 330.0
TURNS = SPEC["turns"]
LEAF_N = SPEC["leaves"]


def _helix(t):
    """Point and unit tangent on the helix at parameter t in [0, 1]."""
    a = 2.0 * math.pi * TURNS * t
    p = Vector((R_H * math.cos(a), R_H * math.sin(a), PITCH * TURNS * t))
    d = Vector((-math.sin(a), math.cos(a), PITCH / (2.0 * math.pi)))
    return p, d.normalized()


def _stem(name, mat):
    rings = []
    steps = 20
    n = 150
    for i in range(n + 1):
        p, d = _helix(i / float(n))
        ref = Vector((0.0, 0.0, 1.0))
        side = d.cross(ref).normalized()
        nrm = side.cross(d).normalized()
        r = 7.0 * (1.0 - 0.45 * (i / float(n)))
        rings.append([tuple(p + side * (r * math.cos(2.0 * math.pi * j / steps))
                            + nrm * (r * math.sin(2.0 * math.pi * j / steps)))
                      for j in range(steps)])
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def _leaf(name, base, direction, length, width, mat, n=12):
    d = Vector(direction).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (t, ws) in ((0.0, 0.24), (0.20, 0.80), (0.48, 1.00), (0.74, 0.84),
                    (0.92, 0.42), (1.0, 0.08)):
        c = Vector(base) + d * (length * t) + nrm * (-length * 0.30 * t * t)
        w = width * ws
        ring = [tuple(c + side * (w * math.cos(2.0 * math.pi * j / n))
                      + nrm * (1.1 * math.sin(2.0 * math.pi * j / n)))
                for j in range(n)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    wood = bkit.pbr("VineStem", base=(0.185, 0.225, 0.105), rough=0.70)
    leaf = bkit.pbr("VineLeaf", base=(0.110, 0.290, 0.085), rough=0.56)
    stake = bkit.pbr("TrellisStake", base=(0.330, 0.255, 0.175), rough=0.80)

    bkit.cylinder("Stake", 9.0, STAKE_H, segments=16, r2=7.0,
                  centre=(0.0, 0.0, STAKE_H / 2.0), mat=stake)
    _stem("Stem", wood)

    # ---- leaf stations: one every half turn, alternating side, taken from
    # the same helix law the stem was swept along.
    for i in range(LEAF_N):
        t = 0.06 + 0.92 * (i / float(LEAF_N - 1))
        p, d = _helix(t)
        sign = 1.0 if i % 2 == 0 else -1.0
        out = Vector((p.x, p.y, 0.0)).normalized()
        direction = (out * (0.72 * sign) + Vector((0.0, 0.0, 0.42))
                     + d * 0.30).normalized()
        lf = _leaf("Leaf%02d" % i, tuple(p), tuple(direction),
                   SPEC["leaf_length"] * (0.72 + 0.28 * (1.0 - t)),
                   52.0 * (0.8 + 0.2 * (1.0 - t)), leaf)
        lf.name = "Leaf%02d" % i

    # ---- three tendrils at the growing tip
    for k in range(3):
        t = 0.99
        p, _d = _helix(t)
        a = math.radians(120.0 * k + 30.0)
        tn = _leaf("Tendril%d" % k, tuple(p),
                   (math.cos(a), math.sin(a), 0.72), 54.0, 7.0, leaf, n=8)
        tn.name = "Tendril%d" % k

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + LEAF_N + 3)


CHECKS = [
    dict(name="helix_diameter", mm=105.3,  tol=0.53, how="diameter", part="Stem"),
    dict(name="height",         mm=2000.0, tol=8.0, how="top_z"),
    dict(name="leaf_length",    mm=93.4,  tol=0.5, how="longest",  part="Leaf10"),
    dict(name="stake_height",   mm=2000.0, tol=1.0, how="bbox_z",   part="Stake"),
]
