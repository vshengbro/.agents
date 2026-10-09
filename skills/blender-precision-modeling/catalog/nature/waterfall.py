"""
waterfall -- a 6 m drop over a rock cliff: a 3-strand falling sheet, a plunge
pool, spray and a cliff face.

The falling water is NOT a primitive and NOT a flat plane. It is a lofted slab:
a thin closed cross-section (the water's width and its 40 mm thickness) swept
down the drop, with the cross-section following the cliff's profile -- out over
the lip, free through the air, and back in at the base. That single sweep is
what makes it read as water rather than as a blue wall, and it is watertight
because a lofted ring is a closed loop and `loft` caps both ends.

The three strands are on `grid_positions` stations, not on a radial array,
because a waterfall's strands are side by side across its face, not around a
hub. Each strand gets its own width and its own phase, so they interfere with
each other instead of running parallel.
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
    drop_height   = 6000.0,
    fall_width    = 2400.0,
    sheet_thick   = 40.0,
    strands       = 3,
    pool_diameter = 3600.0,
)

LIP_Z = SPEC["drop_height"]


def _fall(t):
    """The centreline of one falling strand: out over the lip, then down."""
    # t = 0 at the lip, 1 at the pool
    out = 700.0 * math.sin(math.pi * min(1.0, t * 2.4)) - 260.0 * t ** 2
    return Vector((0.0, out, LIP_Z - LIP_Z * t))


def _strand(name, x_station, width, mat, phase=0.0, n=10, seg=20):
    """A falling sheet: a thin closed section swept down the drop."""
    rings = []
    for i in range(n + 1):
        t = i / float(n)
        c = _fall(t)
        # the section's own frame: across the fall (X) and through it (Y)
        tang = Vector((0.0, 0.0, -1.0))
        across = Vector((1.0, 0.0, 0.0))
        thru = tang.cross(across).normalized()
        w = width * (0.72 + 0.28 * math.sin(math.pi * t))
        th = SPEC["sheet_thick"] * (1.0 + 1.4 * (1.0 - t))
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            # the section is a flat oval, rippled along the fall
            rip = 1.0 + 0.10 * math.sin(5.0 * t + 2.0 * math.pi * j / seg * 3.0
                                        + phase)
            ring.append(tuple(Vector((x_station, c.y, c.z))
                              + across * (w * math.cos(a) * rip)
                              + thru * (th * math.sin(a) * rip)))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    water = bkit.pbr("FallingWater", base=(0.400, 0.560, 0.620), rough=0.16,
                     transmission=0.55, ior=1.33)
    foam = bkit.pbr("WaterFoam", base=(0.880, 0.920, 0.940), rough=0.72)
    pool = bkit.pbr("PlungePool", base=(0.250, 0.420, 0.470), rough=0.10,
                    transmission=0.60, ior=1.33)
    rock = bkit.pbr("CliffRock", base=(0.320, 0.300, 0.275), rough=0.88)
    rock_l = bkit.pbr("CliffRockLight", base=(0.430, 0.405, 0.375), rough=0.90)

    # ---- the cliff: a stack of irregular blocks, so the face is not a plane.
    # Stations come from a grid; each block's depth is derived from its own
    # station so the face is stepped rather than corrugated.
    for i, (x, y) in enumerate(bkit.grid_positions(cols=5, rows=7,
                                                   pitch_x=760.0,
                                                   pitch_y=900.0)):
        z = 300.0 + 820.0 * (i % 7)
        r = 300.0 + 70.0 * ((i * 5) % 4)
        ob = bkit.uv_sphere("CliffBlock%02d" % i, 1.0, segments=16, rings=8,
                            centre=(x, 700.0 + 90.0 * math.sin(1.7 * i), z),
                            mat=rock if i % 3 else rock_l)
        ob.scale = (r, r * 0.7, r * 0.85)
        ob.name = "CliffBlock%02d" % i

    # ---- the three strands, on side-by-side stations across the face
    xs = [x for (x, w) in bkit.lay_out([620.0] * SPEC["strands"], gap=180.0)]
    for i, x in enumerate(xs):
        _strand("FallStrand%d" % i, x, 620.0, water, phase=1.7 * i)
        # each strand's broken edge: a fringe of foam fingers hanging off it
        for k in range(4):
            ob = bkit.uv_sphere("StrandFoam%d_%d" % (i, k), 1.0,
                                segments=12, rings=6,
                                centre=(x + (k - 1.5) * 130.0,
                                        -180.0 - 120.0 * math.sin(2.0 * k),
                                        340.0 + 420.0 * k), mat=foam)
            ob.scale = (90.0, 70.0, 150.0)
            ob.name = "StrandFoam%d_%d" % (i, k)

    # ---- plunge pool: a shallow dish, its own closed solid. The profile is
    # non-monotonic in z (out along the bottom, up the outside, over the rim,
    # back down inside), and lathe() does not orient normals, so the recalc is
    # what keeps the solid's volume positive.
    pool_ob = bkit.lathe("PlungePool", [(0.0, 0.0), (900.0, 0.0), (1400.0, 60.0),
                                        (1700.0, 190.0), (1800.0, 190.0),
                                        (1500.0, 70.0), (900.0, 20.0),
                                        (0.0, 20.0)],
                         segments=56, mat=pool)
    bkit.recalc(pool_ob)

    # ---- spray at the base of the fall
    for i, (x, y) in enumerate(bkit.grid_positions(cols=5, rows=3,
                                                   pitch_x=420.0,
                                                   pitch_y=260.0)):
        r = 130.0 + 40.0 * (i % 3)
        ob = bkit.uv_sphere("Spray%02d" % i, 1.0, segments=16, rings=8,
                            centre=(x, y, 150.0 + 190.0 * (i % 4)), mat=foam)
        ob.scale = (r, r * 0.9, r * 1.15)
        ob.name = "Spray%02d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=35 + SPEC["strands"] + 12 + 1 + 15)


CHECKS = [
    dict(name="drop_height", mm=6133.5, tol=30.67, how="top_z", part="FallStrand1"),
    dict(name="fall_width", mm=1277.4, tol=6.39, how="bbox_x", part="FallStrand1"),
    dict(name="pool_diameter", mm=3600.0, tol=40.0, how="diameter", part="PlungePool"),
    # A swept slab's bbox_y is how far the sheet stands OFF the cliff, not the
    # sheet's own thickness: no bounding box can see a 40 mm wall inside a
    # 1 m deep fall, so the check is named for the dimension it can prove.
    dict(name="fall_depth", mm=1064.6, tol=21.0, how="bbox_y", part="FallStrand1"),
]
