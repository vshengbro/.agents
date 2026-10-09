"""
fractal_tree -- a self-similar branching structure, 4 levels, 15 branches.

Every branch is a real closed tapered solid, and each one is a separate named
part so `health()` can point at the offender if a level ever collides. Branch
geometry comes from `cylinder(r2=...)`, the truncated-cone case of the
primitive: it is already a watertight solid, so 15 overlapping solids stay
15 manifold shells rather than one tangled boolean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Matrix

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    levels=5,
    trunk_length=70.0,
    trunk_radius=11.0,
    length_ratio=0.72,     # each level is 0.72x its parent
    radius_ratio=0.62,
    branch_angle=22.0,     # degrees away from the parent axis
    # measured from the built geometry. These moved from 185.82 / 69.28 because
    # the flared root cone (base_radius 22 mm) was deleted and a fifth level
    # added, so the trunk now starts at z = 0 and the crown sits higher.
    height=196.04,
    width=73.07,
)

DEPTH = SPEC["levels"]

CHECKS = [
    # The tree is an assembly of 31 solids, so the envelope is measured over the
    # whole scene and the trunk's own diameter is checked on the Trunk part --
    # a bbox of one branch can never confirm the other thirty.
    dict(name="height", mm=SPEC["height"], tol=0.6, how="bbox_z"),
    dict(name="width", mm=SPEC["width"], tol=0.6, how="bbox_x"),
    dict(name="trunk_diameter", mm=22.0, tol=0.15, how="diameter", part="Trunk"),
]


def _rotate(direction, axis, degrees):
    """Rotate a unit direction `degrees` about `axis` (both as tuples)."""
    from mathutils import Matrix, Vector
    d = Vector(direction)
    return tuple(Matrix.Rotation(math.radians(degrees), 3, Vector(axis)) @ d)


def build():
    mat = bkit.pbr("Bark", base=(0.32, 0.20, 0.11), metal=0.0, rough=0.62)

    branches = []

    def grow(origin, direction, length, radius, level):
        """Emit one tapered branch and recurse into its two children."""
        tip = [origin[i] + direction[i] * length for i in range(3)]

        ob = bkit.cylinder("Trunk" if level == 0 else "Branch_%d_%d" % (level, len(branches)),
                           radius, length, segments=24 if level == 0 else 12,
                           r2=radius * SPEC["radius_ratio"], mat=mat)
        # Orient the cylinder's +Z axis along `direction` and centre it on the
        # branch mid-point. bkit.place() only does X/Y/Z, so this is the one
        # place a model has to reach for a quaternion.
        from mathutils import Vector
        d = Vector(direction).normalized()
        ob.rotation_mode = "QUATERNION"
        ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
        mid = [origin[i] + d[i] * (length / 2.0) for i in range(3)]
        ob.location = bkit.v(mid)
        branches.append(ob)

        if level + 1 >= DEPTH:
            return
        # Two children per node, splayed about DIFFERENT perpendicular axes:
        # if both use the same axis the whole tree stays in one plane and
        # bbox_y collapses to the root flare. Stepping the azimuth by 137.5 deg
        # (the golden angle) per child spreads successive levels in 3D.
        from mathutils import Vector
        axis = Vector(direction).normalized()
        ref = Vector((0.0, 0.0, 1.0)) if abs(axis.z) < 0.9 else Vector((1.0, 0.0, 0.0))
        perp0 = axis.cross(ref).normalized()
        for idx, sign in enumerate((-1.0, 1.0)):
            az = math.radians(137.5 * (idx + level))
            perp = Matrix.Rotation(az, 3, axis) @ perp0
            child = _rotate(tuple(axis), tuple(perp), sign * SPEC["branch_angle"])
            grow(tip, child, length * SPEC["length_ratio"],
                 radius * SPEC["radius_ratio"], level + 1)

    # No flared root cone. A conical foot under the trunk made the tree read as
    # a lamp base standing on the floor, and the trunk then appeared to start
    # above it with a visible seam. The trunk itself now meets the ground: its
    # own taper (11 -> 6.8 mm) is the flare.
    grow((0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
         SPEC["trunk_length"], SPEC["trunk_radius"], 0)

    # matrix_world is lazy: run_model seats the model by reading bbox(), so the
    # dependencies have to be flushed or the branches are measured at the origin.
    bpy.context.view_layer.update()

    return dict(spec=SPEC, parts=len(branches) + 1)