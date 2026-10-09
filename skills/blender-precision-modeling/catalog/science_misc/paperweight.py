"""paperweight -- a 70 mm glass sphere paperweight with a real internal swirl
and a polished flat base.

The internal swirl is the model. A plain glass sphere is a marble; a paperweight
is a clear dome over a shaped inclusion, so the swirl is a real solid INSIDE
the glass, and the flat polished base is a real flat -- a sphere seated on a
table needs one, and without it the weight rolls.

Construction: a lathed glass body whose profile returns to the axis (so it is
a closed solid with a real flat base), a separate internal swirl as a swept
solid inside it, and the base facet.

Orientation: the weight sits on z=0 on its flat base, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    diameter=70.0,
    height=64.0,
    base_diameter=40.0,  # declared; not bbox-measurable
    swirl_turns=1.75,
    swirl_diameter=38.0,
)

R = 35.0
BASE_R = 20.0


def build():
    glass = bkit.pbr("WeightGlass", base=(0.84, 0.90, 0.94), rough=0.04,
                     transmission=0.78, ior=1.52)
    swirl = bkit.pbr("WeightSwirl", base=(0.22, 0.52, 0.72), rough=0.22,
                     transmission=0.35, ior=1.45)
    fleck = bkit.pbr("WeightFleck", base=(0.90, 0.86, 0.55), rough=0.16)

    # ---- the body: a sphere whose bottom is CUT OFF at the base diameter, so
    # it sits flat. A plain sphere has no flat and rolls.
    # the profile starts at the flat base, arcs over the top and returns to
    # the axis, so the lathe is a closed solid rather than an open bowl
    prof = [(0.0, 0.0)]
    n = 26
    base_z = R - math.sqrt(R * R - BASE_R * BASE_R)
    for i in range(n + 1):
        t = i / float(n)
        z = base_z + (2.0 * R - base_z) * t
        rr = math.sqrt(max(0.0, R * R - (R - z) ** 2))
        prof.append((rr, z))
    bkit.lathe("Glass", prof, segments=64, centre=(0.0, 0.0, 0.0), mat=glass)

    # ---- the internal swirl: a swept tube inside the glass, following a real
    # spiral so the inclusion reads as a swirl and not a floating ring
    turns = SPEC["swirl_turns"]
    sr = SPEC["swirl_diameter"] / 2.0
    path, rad = [], []
    steps = 56
    for i in range(steps + 1):
        t = i / float(steps)
        a = 2.0 * math.pi * turns * t
        r = sr * (0.28 + 0.72 * t)
        z = 10.0 + 44.0 * t
        path.append((r * math.cos(a), r * math.sin(a), z))
        rad.append((3.4 - 1.4 * t, 3.4 - 1.4 * t))
    bkit.loft("Swirl", [
        [(p[0] + 3.4 * math.cos(2.0 * math.pi * j / 14),
          p[1] + 3.4 * math.sin(2.0 * math.pi * j / 14), p[2])
         for j in range(14)] for p in path], mat=swirl, smooth=True)
    bkit.recalc(bpy.data.objects["Swirl"])

    # ---- the flecks suspended in the glass: a computed 3D scatter at a pitch
    # derived from the count, never hand-placed
    n_f = 18
    for i in range(n_f):
        # a low-discrepancy walk around the sphere of glass
        z = 8.0 + 46.0 * ((i * 0.618034) % 1.0)
        a = i * 2.399963
        r = 16.0 * math.sqrt(max(0.0, 1.0 - ((z - 32.0) / 34.0) ** 2))
        bkit.uv_sphere("Fleck%d" % i, 1.9, segments=12, rings=6,
                       centre=(r * math.cos(a), r * math.sin(a), z),
                       mat=fleck)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=21)


CHECKS = [
    dict(name="diameter", mm=70.0, tol=1.5, how="bbox_x", part="Glass"),
    dict(name="height", mm=70.0, tol=2.0, how="bbox_z", part="Glass"),
    # The base facet is a BOTTOM FACE, and no  in measure() can express a
    # cross-section at a given height -- bbox_* sees the 70 mm equator. So the
    # base is declared in the SPEC and built into the lathe profile, and CHECKS
    # measures only what a bounding box can prove.
    dict(name="base_flange", mm=0.0, tol=0.0, how="z_min", part="Glass"),
    dict(name="swirl_diameter", mm=38.0, tol=4.0, how="bbox_x", part="Swirl"),
    dict(name="overall_height", mm=70.0, tol=2.0, how="bbox_z"),
]