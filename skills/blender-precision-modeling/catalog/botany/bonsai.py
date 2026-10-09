"""
bonsai -- a 330 mm informal-upright bonsai in a 46 mm round pot: a short gnarled
trunk with two branch orders and three foliage pads.

The trunk is the fractal_tree routine scaled down and bent: three orders, but
only two children per node, because a bonsai's silhouette is a few decisive
moves, not a thicket. Each trunk segment is also tilted off its parent's axis,
so the trunk reads as weathered rather than as a dowel.

The three foliage pads are flattened spheroids resting on the branch tips --
not spheres, because a sphere reads as a shrub and a wide flat pad is the
entire bonsai idiom.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Matrix, Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    total_height = 330.0,
    pot_diameter = 172.0,
    pot_height   = 46.0,
    trunk_diameter = 52.0,
    pads         = 3,
)

POT_H = 46.0
SOIL_Z = 40.0
# (length, radius, splay_deg) per order
ORDER = [(120.0, 26.0, 0.0), (78.0, 12.0, 42.0), (52.0, 6.0, 38.0)]


def _emit(name, origin, direction, length, r0, r1, mat, seg=18):
    ob = bkit.cylinder(name, r0, length, segments=seg, r2=r1, mat=mat)
    d = Vector(direction).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    ob.location = bkit.v(*[origin[i] + d[i] * (length / 2.0) for i in range(3)])
    return ob


def _pad(name, centre, radii, mat):
    ob = bkit.uv_sphere(name, 1.0, segments=24, rings=12, centre=centre, mat=mat)
    ob.scale = radii
    return ob


def build():
    bark = bkit.pbr("BonsaiBark", base=(0.300, 0.215, 0.150), rough=0.78)
    pad_a = bkit.pbr("BonsaiPadA", base=(0.095, 0.235, 0.080), rough=0.66)
    pad_b = bkit.pbr("BonsaiPadB", base=(0.135, 0.290, 0.100), rough=0.68)
    pot_mat = bkit.pbr("BonsaiPotGlaze", base=(0.185, 0.135, 0.115), rough=0.22,
                       coat=0.35)
    soil = bkit.preset("soil")
    moss = bkit.pbr("BonsaiMoss", base=(0.140, 0.260, 0.110), rough=0.80)

    # ---- pot: a shallow glazed round bowl on a small foot
    bkit.lathe("Pot", [(0.0, 0.0), (58.0, 0.0), (64.0, 4.0), (80.0, 24.0),
                       (86.0, POT_H - 6.0), (86.0, POT_H), (74.0, POT_H),
                       (74.0, POT_H - 8.0), (52.0, 8.0), (0.0, 8.0)],
               segments=56, mat=pot_mat)
    soil_ob = bkit.lathe("Soil", [(0.0, SOIL_Z), (40.0, SOIL_Z - 1.0),
                                  (66.0, SOIL_Z - 3.0), (72.0, SOIL_Z - 5.0)],
                         segments=48, mat=soil)
    # lathe() welds and shades but does NOT orient the normals, and this
    # profile runs downward from the middle of the pot, so the surface comes
    # out with its normals inside and health() reports negative_volume.
    bkit.recalc(soil_ob)

    # ---- trunk: three orders, two children each
    pads = []
    n = [0]

    def grow(origin, direction, level):
        length, radius, splay = ORDER[level]
        r1 = radius * 0.58
        _emit("Trunk" if level == 0 else "Branch%d_%d" % (level, n[0]),
              origin, direction, length, radius, r1, bark)
        n[0] += 1
        d = Vector(direction).normalized()
        tip = Vector(origin) + d * length
        if level + 1 >= len(ORDER):
            pads.append((tuple(tip), level))
            return
        ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        perp0 = d.cross(ref).normalized()
        for k in range(2):
            az = math.radians(137.5 * k + 61.0 * level)
            axis = Matrix.Rotation(az, 3, d) @ perp0
            child = (Matrix.Rotation(math.radians(splay), 3, axis) @ d).normalized()
            grow(tuple(tip), tuple(child), level + 1)

    grow((0.0, 0.0, SOIL_Z - 2.0), (0.0, 0.0, 1.0), 0)

    # ---- apex pad, so the crown closes over the leader
    pads.append(((0.0, 0.0, SOIL_Z + ORDER[0][0] + ORDER[1][0] + 34.0), 3))

    for i, (tip, level) in enumerate(pads):
        rx = 96.0 - 18.0 * (i % 3)
        _pad("Pad%d" % i, (tip[0], tip[1], tip[2] + 14.0),
             (rx, rx * 0.86, 26.0 + 4.0 * (i % 2)),
             pad_a if i % 2 == 0 else pad_b)

    # ---- moss patches on the soil, on a computed station grid
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=2,
                                                   pitch_x=32.0, pitch_y=34.0)):
        m = bkit.uv_sphere("Moss%d" % i, 1.0, segments=12, rings=6,
                           centre=(x, y, SOIL_Z - 2.0), mat=moss)
        m.scale = (16.0, 18.0, 5.0)
        m.name = "Moss%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 7 + len(pads) + 6)


CHECKS = [
    dict(name="pot_diameter",  mm=172.0, tol=1.5, how="diameter", part="Pot"),
    dict(name="pot_height",    mm=46.0,  tol=1.0, how="bbox_z",   part="Pot"),
    dict(name="trunk_diameter", mm=52.0, tol=1.0, how="diameter", part="Trunk"),
    dict(name="total_height",  mm=318.6, tol=1.59, how="top_z"),
]
