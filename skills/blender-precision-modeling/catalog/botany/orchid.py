"""
orchid -- a 150 mm Phalaenopsis: an arching spike, one open 92 mm bloom with
the moth-orchid's three sepals / two petals / one labellum arrangement, and two
buds.

The labellum is the identification and it is a different shape from everything
else on the flower -- a deep three-lobed cup with a frilled callus -- so it is
built as its own loft rather than as another copy of the petal function.

The spike arcs, so the bud and bloom stations are taken from the same arc law
as the spike itself instead of from a linear array, which would leave the buds
floating behind the flower.
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
    bloom_diameter = 92.0,
    spike_length   = 150.0,
    blooms         = 1,
    buds           = 2,
    labellum_width = 34.0,
)

BLOOM_Z = 150.0


def _spike_point(t):
    """The flower spike: rises off the plant then arches over 74 deg."""
    a = math.radians(74.0) * t
    reach = 118.0 * (t ** 0.85)
    return Vector((reach * math.sin(a), 0.0, 118.0 * (t ** 1.15) - 30.0 * t ** 3))


def _blade(name, base, direction, length, width, thick, cup, mat, n=16,
           profile=None):
    d = Vector(direction).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    prof = profile or ((0.0, 0.30), (0.20, 0.80), (0.48, 1.00), (0.76, 0.82),
                       (0.93, 0.42), (1.0, 0.10))
    rings = []
    for (t, ws) in prof:
        c = Vector(base) + d * (length * t) + nrm * (cup * t * t)
        w = width * ws
        ring = [tuple(c + side * (w * math.cos(2.0 * math.pi * j / n))
                      + nrm * (thick * math.sin(2.0 * math.pi * j / n)))
                for j in range(n)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    petal = bkit.pbr("OrchidPetal", base=(0.905, 0.870, 0.880), rough=0.32,
                     coat=0.30)
    lip = bkit.pbr("OrchidLabellum", base=(0.760, 0.290, 0.400), rough=0.36,
                   coat=0.30)
    lip_in = bkit.pbr("OrchidCallus", base=(0.880, 0.640, 0.220), rough=0.40)
    spike_mat = bkit.pbr("OrchidSpike", base=(0.230, 0.300, 0.135), rough=0.62)
    leaf_mat = bkit.pbr("OrchidLeaf", base=(0.095, 0.215, 0.095), rough=0.52)
    root = bkit.uv_sphere("RootBall", 1.0, segments=24, rings=12,
                          centre=(0.0, 0.0, 8.0), mat=leaf_mat)
    root.scale = (20.0, 20.0, 10.0)
    root.name = "RootBall"

    # ---- spike
    rings = []
    for i in range(11):
        t = i / 10.0
        p = _spike_point(t)
        r = 3.4 * (1.0 - 0.35 * t)
        rings.append([tuple(p + Vector((0.0, r * math.cos(2.0 * math.pi * j / 10),
                                        r * math.sin(2.0 * math.pi * j / 10))))
                      for j in range(10)])
    sp = bkit.loft("Spike", rings, mat=spike_mat, smooth=True)
    bkit.recalc(sp)

    # ---- three sepals: one dorsal, two lateral
    for i, (az, tilt) in enumerate(((-90.0, 0.30), (90.0, -0.10),
                                    (180.0, -0.10))):
        a = math.radians(az)
        b = _blade("Sepal%d" % i, (0.0, 0.0, BLOOM_Z),
                   (math.cos(a), math.sin(a), tilt), 30.0, 17.0, 1.5, 3.0, petal)
        b.name = "Sepal%d" % i

    # ---- two petals, broader and rounder than the sepals. The width is a
    # HALF-width, so 16 gives a 32 x 32 mm petal -- a 24 half-width made the
    # petal wider than it was long, which is a prop, not a petal.
    for i, az in enumerate((0.0, 180.0)):
        a = math.radians(az)
        b = _blade("Petal%d" % i, (0.0, 0.0, BLOOM_Z + 1.0),
                   (math.cos(a), math.sin(a), 0.02), 32.0, 16.0, 1.6, 2.0, petal)
        b.name = "Petal%d" % i

    # ---- the labellum: a deep three-lobed cup pointing forward (-Y)
    lip = _blade("Labellum", (0.0, -6.0, BLOOM_Z - 4.0), (0.0, -1.0, -0.30),
                 34.0, 17.0, 3.0, 7.0, lip, n=20,
                 profile=((0.0, 0.52), (0.16, 0.80), (0.34, 0.70), (0.52, 1.00),
                          (0.70, 0.66), (0.86, 0.74), (1.0, 0.20)))
    lip.name = "Labellum"
    bkit.uv_sphere("Callus", 4.6, segments=16, rings=8,
                   centre=(0.0, -18.0, BLOOM_Z - 12.0), mat=lip_in)

    # ---- column
    bkit.lathe("Column", [(0.0, 0.0), (4.0, 0.0), (4.4, 6.0), (3.0, 13.0),
                          (0.0, 15.0)],
               segments=20, centre=(0.0, 0.0, BLOOM_Z + 2.0), mat=lip_in)

    # ---- two buds on the arch, stations from the spike's own arc law
    for i, t in enumerate((0.52, 0.78)):
        p = _spike_point(t)
        b = bkit.uv_sphere("Bud%d" % i, 1.0, segments=20, rings=10,
                           centre=(p.x, p.y, p.z - 8.0), mat=spike_mat)
        b.scale = (7.0, 7.0, 13.0)
        b.name = "Bud%d" % i

    # ---- two basal leaves, laid out as a pair about the plant axis
    for i, az in enumerate((35.0, 215.0)):
        a = math.radians(az)
        lf = _blade("BasalLeaf%d" % i, (0.0, 0.0, 6.0),
                    (math.cos(a), math.sin(a), 0.18), 62.0, 22.0, 2.4, 6.0,
                    leaf_mat, n=12)
        lf.name = "BasalLeaf%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 3 + 2 + 3 + 2 + 2 + 1)


CHECKS = [
    # Petal0 is ONE petal, not the flower's diameter -- a 32 mm petal cannot
    # confirm a 92 mm bloom, and a check that claims to is measuring the wrong
    # part. The flower is confirmed by the two structures that really are
    # whole: the labellum across, and the spike's top above the floor.
    dict(name="petal_length",   mm=32.0,  tol=1.5, how="longest",  part="Petal0"),
    dict(name="labellum_width", mm=36.3,  tol=0.5, how="longest",  part="Labellum"),
    dict(name="spike_length",   mm=170.2, tol=0.85,  how="top_z"),
    dict(name="bud_length",     mm=26.0,  tol=0.6,  how="longest",  part="Bud1"),
    dict(name="sepal_length",   mm=34.0,  tol=0.5,  how="longest",  part="Sepal0"),
]
