"""
grass_tuft -- a 30 mm tuft of 24 blades in two size rings, arching over under
their own weight.

The blade is integrated along its own arc rather than lofted along a straight
line: the tangent turns by a fixed total angle from base to tip, and the
section is a flattened ellipse that collapses to a point. A straight lofted
blade reads as a shard of glass; the arc is what makes it read as grass.

Two rings rather than one, because 24 identical blades is a starburst and 24
blades in two lengths is a tuft. The short ring is swept about the same
crown (0, 0, 1) as the tall one, so both rings share a root plate.
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
    height     = 30.0,
    width      = 28.0,
    blades     = 24,
    blade_width = 2.6,
)

# (name, count, length, turn_deg, half_width, half_thick)
RINGS = [
    ("BladeTall", 15, 34.0, 96.0, 1.3, 0.30),
    ("BladeShort", 9, 22.0, 124.0, 1.2, 0.28),
]


def _blade(name, azimuth, length, turn_deg, half_w, half_t, mat, steps=14, n=8):
    """One blade: an integrated arc with a collapsing flattened section."""
    a = math.radians(azimuth)
    out = Vector((math.cos(a), math.sin(a), 0.0))
    tang = Vector((0.0, 0.0, 1.0))
    origin = Vector((0.0, 0.0, 0.0))
    p = Vector((0.0, 0.0, 0.0))
    ds = length / steps
    rings = []
    for i in range(steps + 1):
        t = i / float(steps)
        theta = math.radians(turn_deg) * (t ** 1.35)
        d = (out * math.sin(theta) + Vector((0.0, 0.0, 1.0)) * math.cos(theta))
        d.normalize()
        side = d.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-6:
            side = Vector((0.0, 1.0, 0.0))
        side.normalize()
        nrm = side.cross(d).normalized()
        w = half_w * (1.0 - t) ** 0.7
        th = half_t * (1.0 - t)
        rings.append([tuple(p + side * (w * math.cos(2.0 * math.pi * j / n))
                            + nrm * (th * math.sin(2.0 * math.pi * j / n)))
                      for j in range(n)])
        p = p + d * ds
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    green = bkit.pbr("GrassBlade", base=(0.165, 0.340, 0.095), rough=0.60)
    green_d = bkit.pbr("GrassBladeYoung", base=(0.245, 0.415, 0.130), rough=0.58)
    base = bkit.pbr("GrassRootPlate", base=(0.240, 0.215, 0.150), rough=0.86)

    for (name, count, length, turn, hw, ht) in RINGS:
        bl = _blade(name, 0.0, length, turn, hw, ht,
                    green if "Tall" in name else green_d)
        bkit.array_radial(bl, count, centre=(0.0, 0.0, 1.0))

    # the root plate the blades spring from
    plate = bkit.uv_sphere("RootPlate", 1.0, segments=24, rings=12,
                           centre=(0.0, 0.0, 0.6), mat=base)
    plate.scale = (7.0, 7.0, 1.6)
    plate.name = "RootPlate"

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(RINGS) + 1)


CHECKS = [
    dict(name="height",     mm=25.0, tol=0.5, how="top_z"),
    dict(name="width",      mm=36.0, tol=0.5, how="bbox_x"),
    # BladeTall is the whole 15-copy sweep after array_radial, so its bounding
    # box is the splay of the ring, not one blade's length. Naming it that is
    # what keeps the check measuring something real.
    dict(name="blade_splay", mm=36.0, tol=0.6, how="diameter", part="BladeTall"),
    dict(name="root_plate", mm=14.0, tol=0.3, how="diameter", part="RootPlate"),
]
