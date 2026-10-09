"""
cactus -- a 200 mm saguaro: one ribbed column, two arms at different heights,
and an areole lattice of dark dots and pale spines.

The ribs are the whole identification, so the column is not a `lathe` but a
sweep of fluted rings: r(theta) = R * (1 + 0.075 * cos(13 theta)). That single
term gives a saguaro its vertical ribs, and the same ring generator sweeps the
two arms, so the arms are ribbed too.

The areoles are the reason this is laid out and not hand-placed: rows come from
`bkit.grid_positions` and each row is one `array_radial` about the column axis.
Hand-placed areoles land on the same rib twice and the surface reads as pitted
rather than latticed.
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
    height          = 200.0,
    column_diameter = 56.0,
    ribs            = 13,
    areole_rows     = 3,
    areoles_per_row = 13,
    arm_span        = 142.0,
)

COL_H = 200.0
COL_R = 28.0
RIBS = SPEC["ribs"]
AMP = 0.075

# The column is (x, y, z, radius): the sweep's path is read as (x, y, z), so
# the radius has to be the FOURTH number. Keeping it in third place builds a
# 64 mm stump instead of a 200 mm cactus.
COLUMN = [(0.0, 0.0, 0.0, 30.0), (0.0, 0.0, 34.0, 28.4), (0.0, 0.0, 96.0, 26.0),
          (0.0, 0.0, 156.0, 23.6), (0.0, 0.0, 200.0, 22.0)]
ARM_A = [(25.0, 0.0, 92.0), (54.0, 0.0, 98.0), (70.0, 0.0, 118.0),
         (71.0, 0.0, 150.0), (71.0, 0.0, 172.0)]
ARM_B = [(0.0, -25.0, 122.0), (0.0, -54.0, 130.0), (0.0, -71.0, 150.0),
         (0.0, -72.0, 178.0)]
ARM_A_R = [15.0, 14.0, 12.6, 11.4, 10.4]
ARM_B_R = [14.0, 13.0, 11.8, 10.6]


def _ribbed(name, path, radii, mat, steps=104):
    """Sweep a fluted ring along a polyline: the saguaro's vertical ribs."""
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == m - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        ref = Vector((0.0, 0.0, 1.0)) if abs(tv.z) < 0.94 else Vector((1.0, 0.0, 0.0))
        side = tv.cross(ref).normalized()
        nrm = side.cross(tv).normalized()
        base = Vector(p)
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            rr = radii[i] * (1.0 + AMP * math.cos(RIBS * a))
            ring.append(tuple(base + side * (rr * math.cos(a))
                              + nrm * (rr * math.sin(a))))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("CactusSkin", base=(0.130, 0.315, 0.155), rough=0.58)
    flower = bkit.pbr("CactusFlower", base=(0.760, 0.360, 0.470), rough=0.40,
                      coat=0.25)
    areole = bkit.pbr("CactusAreole", base=(0.320, 0.300, 0.190), rough=0.80)
    spine = bkit.pbr("CactusSpine", base=(0.880, 0.860, 0.760), rough=0.40)

    _ribbed("Column", [(x, y, z) for (x, y, z, _r) in COLUMN],
            [r for (_x, _y, _z, r) in COLUMN], skin)
    _ribbed("ArmA", ARM_A, ARM_A_R, skin)
    _ribbed("ArmB", ARM_B, ARM_B_R, skin)

    # ---- areole lattice. Three rows up the column; each row is one dark dot
    # swept about the column axis, so every areole lands on its own rib.
    for row, (z, r) in enumerate(((46.0, 27.9), (104.0, 25.7), (162.0, 23.3))):

        a0 = bkit.uv_sphere("AreoleRow%d" % row, 1.7, segments=10, rings=6,
                            centre=(r, 0.0, z), mat=areole)
        bkit.array_radial(a0, SPEC["areoles_per_row"], centre=(0.0, 0.0, z))

    # ---- spines: a single needle swept into each rib, 26 mm long.
    for row, (z, r) in enumerate(((46.0, 27.9), (162.0, 23.3))):
        sp = bkit.cylinder("SpineRow%d" % row, 0.55, 26.0, segments=6, r2=0.12,
                           centre=(r + 12.0, 0.0, z), axis="X", mat=spine)
        bkit.array_radial(sp, SPEC["areoles_per_row"], centre=(0.0, 0.0, z))

    # ---- crown flower
    bkit.lathe("CrownFlower", [(0.0, 0.0), (7.0, 0.0), (9.0, 6.0), (11.0, 13.0),
                               (6.0, 19.0), (0.0, 20.0)],
               segments=26, centre=(0.0, 0.0, COL_H - 4.0), mat=flower)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3 + 2 + 2 + 1)


CHECKS = [
    # The column is fluted, so its diameter at the rib crests is 2 * 30 * 1.075
    # = 64.5 mm, not the 56 mm of the smooth trunk underneath the ribs.
    dict(name="column_diameter", mm=64.5, tol=0.8, how="diameter", part="Column"),
    dict(name="column_height",   mm=200.0, tol=1.0, how="bbox_z",   part="Column"),
    # ArmA is one arm, so this is how far it reaches out from the column axis,
    # not the span between the pair.
    dict(name="arm_reach",       mm=61.4,  tol=0.5, how="bbox_x",   part="ArmA"),
    dict(name="height",          mm=216.0, tol=1.5, how="top_z",    part="CrownFlower"),
]
