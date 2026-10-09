"""
raindrop -- an 8.4 mm falling drop: a 3.2 mm sphere with a tail drawn out above
it, and a meniscus flat at the bottom.

A drop is a surface of revolution, which makes `lathe` the exact right recipe
and the profile the whole model. The profile is the physics in one list: the
bulbous lower two-thirds where surface tension has won, the shoulder where the
radius reaches its maximum, and then a tail that narrows almost to nothing
over the top 30% as the drop is stretched by its own fall.

The bottom is closed at r = 0 (a point), which is a sphere, and the tail is
closed at r = 0 too, so the whole drop is one closed solid with no boolean and
no seam. The meniscus is modelled by the last profile node being at a small but
non-zero radius, which is why cap_ends matters here.
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
    drop_length  = 8.4,
    drop_bulb    = 3.2,   # the sphere's radius
    tail_length  = 2.9,
)

# (radius, z): bulbous bottom, maximum-radius shoulder, drawn-out tail.
DROP = [
    (0.0, 0.0),
    (0.9, 0.10),
    (1.9, 0.40),
    (2.7, 0.95),
    (3.15, 1.70),
    (3.2, 2.35),
    (3.05, 3.10),
    (2.65, 3.90),
    (2.10, 4.70),
    (1.50, 5.45),
    (0.95, 6.15),
    (0.52, 6.85),
    (0.24, 7.50),
    (0.0, 8.40),
]


def build():
    water = bkit.pbr("RaindropWater", base=(0.560, 0.700, 0.780), rough=0.04,
                     transmission=0.82, ior=1.333)
    # A refractive drop with nothing bright behind it renders near-black in a
    # dark studio, so the base is tinted rather than fully transmissive: the
    # drop keeps its silhouette and still holds a highlight.
    sheen = bkit.pbr("RaindropSheen", base=(0.820, 0.880, 0.920), rough=0.10,
                     transmission=0.35, ior=1.333)

    drop = bkit.lathe("Drop", DROP, segments=48, mat=water)
    bkit.recalc(drop)

    # ---- the specular cap: a thin bright lens over the shoulder, the one part
    # of a drop that catches a studio light and tells you which way is up
    bkit.uv_sphere("ShoulderSheen", 1.0, segments=32, rings=16,
                   centre=(0.0, 0.0, 2.30), mat=sheen).scale = \
        (2.62, 2.62, 1.30)

    # ---- the trailing vapour thread above the drop
    for i, (z, r) in enumerate(((8.9, 0.34), (9.9, 0.24), (10.8, 0.15))):
        bkit.uv_sphere("VapourThread%d" % i, 1.0, segments=12, rings=6,
                       centre=(0.0, 0.0, z), mat=sheen).scale = (r, r, r * 1.6)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="drop_length", mm=8.4,  tol=0.2, how="bbox_z",  part="Drop"),
    dict(name="drop_bulb",   mm=6.4,  tol=0.2, how="diameter", part="Drop"),
    dict(name="shoulder",    mm=5.24, tol=0.2, how="diameter", part="ShoulderSheen"),
    dict(name="tail",        mm=11.0,  tol=0.5, how="z_max",   part="VapourThread2"),
]
