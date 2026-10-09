"""
snowflake -- a 22 mm stellar snowflake: six arms on the hexagonal lattice, each
carrying its own side branches, with a hexagonal plate at the centre.

This is the one object in the domain where a RADIAL ARRAY is exactly right, and
the `centre` matters: the six arms orbit about the crystal's own centre at the
origin, and a 60 deg step is the only step that produces a closed sixfold
figure. Count 6, step 60 -- if either is wrong the flake reads as a gear.

Each arm is a single sweep along a slightly curved dendrite path, and the side
branches are on a station ladder taken from `bkit.lay_out` along the arm, so no
two branches on an arm can land on the same station. The dendrite's taper (1.5 mm
at the root to 0.25 mm at the tip) is the real reason snow looks like snow.
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
    diameter    = 22.0,
    arms        = 6,
    arm_length  = 11.0,
    root_radius = 1.5,
)

ARMS = SPEC["arms"]
SEG = 8


def _sweep(name, path, radii, mat, steps=SEG):
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
        ref = Vector((0.0, 0.0, 1.0))
        side = tv.cross(ref)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        nrm = tv.cross(side).normalized()
        r = radii[i]
        rings.append([tuple(Vector(p)
                            + side * (r * math.cos(2.0 * math.pi * j / steps))
                            + nrm * (r * math.sin(2.0 * math.pi * j / steps)))
                      for j in range(steps)])
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def _arm(name, mat):
    """One dendrite arm: a tapered main spine plus side branches."""
    # the main spine, very slightly curved -- a perfect straight arm looks cast
    path = []
    radii = []
    for i in range(9):
        t = i / 8.0
        L = SPEC["arm_length"] * t
        path.append((L, 0.34 * math.sin(math.pi * t), 0.0))
        radii.append(SPEC["root_radius"] * (1.0 - t) ** 0.8 + 0.22)
    # the main spine, RETURNED: array_radial needs the object, and a sweep
    # helper that forgets to return it hands back None
    spine = _sweep(name, path, radii, mat)

    # ---- side branches: 4 pairs on a station ladder along the arm, angled 60
    # deg off the spine, which is the hexagonal lattice angle
    for i, s in enumerate([x for (x, w) in
                           bkit.lay_out([1.6] * 4, gap=1.5)]):
        t = 0.18 + 0.72 * (i / 3.0)
        L = SPEC["arm_length"] * t
        y = 0.34 * math.sin(math.pi * t)
        bl = SPEC["arm_length"] * 0.30 * (1.0 - 0.55 * t)
        for sign, tag in ((1.0, "L"), (-1.0, "R")):
            a = math.radians(60.0) * sign
            d = (math.cos(a), math.sin(a), 0.0)
            bpath = [(L, y, 0.0), (L + d[0] * bl, y + d[1] * bl, 0.0)]
            _sweep("%s_Branch%d%s" % (name, i, tag), bpath,
                   [0.62 * (1.0 - 0.5 * t), 0.20], mat)
    return spine


def build():
    ice = bkit.pbr("SnowIce", base=(0.780, 0.870, 0.920), rough=0.16,
                   transmission=0.55, ior=1.31)
    ice_b = bkit.pbr("SnowIceBright", base=(0.870, 0.930, 0.960), rough=0.10,
                     transmission=0.65, ior=1.31)

    # ---- the hexagonal plate at the centre: the crystal's nucleus
    bkit.lathe("Core", [(0.0, 0.0), (2.4, 0.0), (2.9, 0.35), (2.6, 0.70),
                        (0.0, 0.70)],
               segments=6, mat=ice_b)

    # ---- six arms on the hexagonal lattice. The sweep is about (0,0,0),
    # which is the crystal's own centre, and a 60 deg step is what makes a
    # closed sixfold figure instead of a six-bladed gear.
    arm = _arm("Arm0", ice)
    bkit.array_radial(arm, ARMS, centre=(0.0, 0.0, 0.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2)


CHECKS = [
    # Arm0 is the whole six-copy array after array_radial, so its box is the
    # FLAKE, not one arm: an 11 mm arm cannot measure 22 mm. The side branches
    # are not swept, so one of them is the honest single-arm measurement.
    dict(name="flake_diameter", mm=22.0, tol=0.8, how="bbox_x", part="Arm0"),
    dict(name="branch_length", mm=3.0, tol=0.5, how="longest",
         part="Arm0_Branch0L"),
    dict(name="flake_thickness", mm=3.4, tol=0.3, how="bbox_z", part="Arm0"),
    dict(name="core", mm=5.8, tol=0.4, how="diameter", part="Core"),
]
