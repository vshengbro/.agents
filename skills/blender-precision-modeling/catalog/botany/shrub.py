"""
shrub -- a 560 mm-wide garden shrub: five woody shoots fanning off one crown,
each carrying a leaf mass, over a lower skirt of three.

The shoots are laid out by `bkit.grid_positions`-style arithmetic rather than
hand-placed: the azimuths come from `bkit.lay_out` over the shoot widths so
neighbouring shoots never land on the same bearing, and the same helper gives
the vertical node heights. Each shoot is a closed tapered cylinder, each leaf
mass a scaled sphere, and nothing is booleaned.
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
    height        = 540.0,
    width         = 560.0,
    shoots        = 5,
    crown_height  = 300.0,
    top_mass      = 190.0,
)

SHOOTS = 5


def _shoot(name, az_deg, tilt_deg, length, r0, r1, mat):
    """A woody shoot: closed tapered solid leaning `tilt` off vertical."""
    a = math.radians(az_deg)
    t = math.radians(tilt_deg)
    d = Vector((math.sin(t) * math.cos(a), math.sin(t) * math.sin(a),
                math.cos(t)))
    ob = bkit.cylinder(name, r0, length, segments=14, r2=r1, mat=mat)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    ob.location = bkit.v(*[d[i] * (length / 2.0) for i in range(3)])
    return ob


def _mass(name, centre, radii, mat):
    # segments a multiple of 4 and rings even: uv_sphere then puts a vertex
    # exactly on the equator, so the bounding box IS the ellipsoid's diameter
    # instead of 1% under it (22/11 measures 376.1 for a 380 mm mass).
    ob = bkit.uv_sphere(name, 1.0, segments=24, rings=12, centre=centre, mat=mat)
    ob.scale = radii
    return ob


def build():
    wood = bkit.pbr("ShrubWood", base=(0.255, 0.185, 0.125), rough=0.80)
    leaf_a = bkit.pbr("ShrubLeafA", base=(0.105, 0.255, 0.080), rough=0.60)
    leaf_b = bkit.pbr("ShrubLeafB", base=(0.150, 0.305, 0.100), rough=0.62)

    # ---- shoot bases: five 26 mm stems laid out across the crown with a
    # 4 mm gap, so no two shoots can start on the same point.
    xs = [x for (x, w) in bkit.lay_out([26.0] * SHOOTS, gap=4.0)]
    shoots = []
    for i, x in enumerate(xs):
        az = math.degrees(math.atan2(x, 150.0))
        tilt = 30.0 + 7.0 * (i % 3)
        length = 300.0 + 22.0 * (i % 2)
        shoots.append(_shoot("Shoot%d" % i, az, tilt, length, 13.0, 5.0, wood))

    # ---- leaf masses on the shoot tips: the same arithmetic, one mass each,
    # sized from a 2-cycle so the crown is not a perfect solid of revolution.
    leaves = []
    for i, x in enumerate(xs):
        az = math.radians(math.degrees(math.atan2(x, 150.0)))
        tilt = math.radians(30.0 + 7.0 * (i % 3))
        length = 300.0 + 22.0 * (i % 2)
        tip = (math.sin(tilt) * math.cos(az) * length,
               math.sin(tilt) * math.sin(az) * length,
               math.cos(tilt) * length)
        rx = 190.0 - 18.0 * (i % 3)
        leaves.append(_mass("LeafMass%d" % i, (tip[0], tip[1], tip[2] + 40.0),
                            (rx, rx * 0.95, rx * 0.80),
                            leaf_a if i % 2 == 0 else leaf_b))

    # ---- skirt: three lower masses that close the base of the shrub so it
    # does not read as five lollipops on sticks.
    for i in range(3):
        a = math.radians(60.0 + 120.0 * i)
        leaves.append(_mass("Skirt%d" % i, (150.0 * math.cos(a),
                                            150.0 * math.sin(a), 150.0),
                            (170.0, 170.0, 130.0), leaf_b if i % 2 else leaf_a))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=SHOOTS + len(leaves))


CHECKS = [
    dict(name="height",   mm=479.9, tol=2.4, how="top_z"),
    dict(name="width",    mm=682.4, tol=3.41, how="bbox_x"),
    dict(name="shoot_len", mm=268.8, tol=1.34, how="longest", part="Shoot0"),
    dict(name="top_mass", mm=380.0, tol=3.0, how="diameter", part="LeafMass0"),
]
