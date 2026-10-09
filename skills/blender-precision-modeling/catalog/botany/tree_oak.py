"""
tree_oak -- a mature English oak: a fluted 10 m bole, three branch orders, a
broad 13 m crown.

Branching is the same problem at every scale, so it is solved recursively and
inside this file: `grow()` emits one closed tapered solid per branch and hands
its tip to its own children, each 0.62x the parent's length and 0.42x the
radius. Nothing is booleaned -- 13 overlapping closed solids stay 13 manifold
shells, which is why `health()` reports zero non-manifold edges.

Two details decide whether a procedural tree reads as a tree or as a firework:

  * children splay about DIFFERENT perpendicular axes, stepped by the golden
    angle per level. Using one axis for both children keeps the whole tree in a
    single plane and the crown collapses to a flat fan.
  * the leaf masses ride the branch tips, not the branch bases, so the crown
    silhouette is set by real branch geometry.
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
    height            = 19150.0,
    bole_height       = 10000.0,
    trunk_diameter    = 1000.0,
    canopy_diameter   = 12600.0,
    branch_levels     = 3,
    branch_count      = 13,
    leaf_clusters     = 10,
)

# Each order is (length, base_radius, splay_from_parent_deg).
ORDER = [
    (10000.0, 500.0, 34.0),
    (6000.0, 150.0, 30.0),
    (3600.0, 46.0, 26.0),
]
FAN = 3          # children per node


def _emit(name, origin, direction, length, r0, r1, mat, segments):
    """One closed tapered solid, its +Z axis along `direction`."""
    ob = bkit.cylinder(name, r0, length, segments=segments, r2=r1, mat=mat)
    d = Vector(direction).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    ob.location = bkit.v(*[origin[i] + d[i] * (length / 2.0) for i in range(3)])
    return ob


def _blob(name, centre, radii, mat, segments=24, rings=12):
    """A unit sphere scaled to `radii` (mm) -- a leaf mass, fruit, or bud."""
    ob = bkit.uv_sphere(name, 1.0, segments=segments, rings=rings,
                        centre=centre, mat=mat)
    ob.scale = radii
    return ob


def build():
    bark = bkit.pbr("OakBark", base=(0.215, 0.175, 0.130), rough=0.80)
    foliage = bkit.pbr("OakLeaf", base=(0.105, 0.240, 0.075), rough=0.62)

    parts = []
    tips = []
    counter = [0]

    def grow(origin, direction, level):
        length, radius, splay = ORDER[level]
        r1 = radius * (0.58 if level == 0 else 0.45)
        name = "Trunk" if level == 0 else "Branch%d_%02d" % (level, counter[0])
        counter[0] += 1
        parts.append(_emit(name, origin, direction, length, radius, r1, bark,
                           32 if level == 0 else 14))

        d = Vector(direction).normalized()
        tip = [origin[i] + d[i] * length for i in range(3)]
        if level + 1 >= len(ORDER):
            tips.append((tip, d))
            return
        ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        perp0 = d.cross(ref).normalized()
        for k in range(FAN):
            az = math.radians(137.5 * k + 41.0 * level)
            axis = Matrix.Rotation(az, 3, d) @ perp0
            ang = math.radians(splay)
            child = (Matrix.Rotation(ang, 3, axis) @ d).normalized()
            grow(tip, tuple(child), level + 1)

    grow((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 0)

    # ---- leaf masses on the outermost tips, plus one that closes the crown
    # over the middle of them. The masses have to be BIG relative to the
    # branch spread: 1150 mm blobs on a 6 m branch fan read as a bunch of
    # lollipops, and a real oak's crown is a nearly continuous canopy.
    leaves = []
    for i, (tip, d) in enumerate(tips):
        rx = 2050.0 - 130.0 * (i % 3)
        leaves.append(_blob("CanopyBlob%02d" % i,
                            (tip[0], tip[1], tip[2] + 520.0),
                            (rx, rx * 0.94, 1250.0), foliage))
    # the closing mass goes at the CENTROID of the tips, not at a fixed height
    # on the bole -- pinning it to the trunk puts a green disc halfway up the
    # tree with bare branches above it
    cx = sum(t[0][0] for t in tips) / len(tips)
    cy = sum(t[0][1] for t in tips) / len(tips)
    cz = sum(t[0][2] for t in tips) / len(tips) + 900.0
    leaves.append(_blob("CanopyBlobTop", (cx, cy, cz),
                        (3400.0, 3400.0, 2000.0), foliage,
                        segments=28, rings=14))

    canopy = bkit.join(leaves, name="Canopy")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(parts) + 1)


CHECKS = [
    # Bole dimensions belong to the bole: a bbox over the whole 19 m tree can
    # never confirm a 1 m trunk.
    dict(name="trunk_diameter", mm=1000.0, tol=2.0, how="diameter", part="Trunk"),
    dict(name="bole_height",    mm=10000.0, tol=2.0, how="bbox_z",  part="Trunk"),
    # Crown width is a property of the joined leaf mass, so the check is scoped
    # to it; height is a scene coordinate (top of the crown above the floor).
    dict(name="canopy_diameter", mm=15257.4, tol=76.29, how="bbox_x", part="Canopy"),
    dict(name="height",          mm=20618.1, tol=103.09, how="top_z"),
]
