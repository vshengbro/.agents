"""
salt_crystal -- a halite cube: 18 mm edge, 2.1 g, cut from a rock-salt mine.

Habit, not shape, is the point. Halite grows as an exact cube because its
lattice is cubic, so this model is a true `box` with a 0.6 mm edge break --
any prism that isn't six square faces with 90 deg corners reads as calcite or
quartz, not salt. The dissolve rounding is what makes it read as a mined
crystal rather than a game asset: one corner is slumped more than the rest.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    edge=18.0,            # cube edge
    edge_break=0.6,       # chamfer on every edge, as mined
    slumped_edge=11.4,    # the one rounded-off corner
)

E = SPEC["edge"]
BEV = SPEC["edge_break"]


def build():
    rock_salt = bkit.pbr("Halite", base=(0.90, 0.86, 0.78), rough=0.13,
                         transmission=0.42, ior=1.54)
    brine = bkit.pbr("HaliteBrine", base=(0.84, 0.80, 0.72), rough=0.09,
                     transmission=0.56, ior=1.54)

    # ---- the cube ---------------------------------------------------------
    # `box` + `bevel`, not `rounded_box`: rounded_box fillets all 12 edges
    # equally, which gives a soap bar. A 0.6 mm break on a 6-degree angle
    # limit keeps the faces dead flat and only softens the arrises.
    cube = bkit.box("SaltCube", E, E, E, centre=(0.0, 0.0, E / 2.0), mat=rock_salt)
    bkit.bevel(cube, BEV, segments=2, angle_deg=20.0)

    # ---- the slumped corner ----------------------------------------------
    # A second, smaller cube buried 4 mm into the top corner: overlapping
    # solids read as a rounded, partly dissolved corner. A boolean here would
    # be an intersection of two nearly-parallel faces -- the classic recipe
    # for a non-manifold result.
    s = SPEC["slumped_edge"]
    lump = bkit.rounded_box("SaltLump", s, s, s * 0.8, r=3.4,
                            centre=(E / 2.0 - s / 2.0 + 1.2,
                                    -E / 2.0 + s / 2.0 - 1.2,
                                    E - s * 0.32), mat=brine)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="edge_x", mm=18.0, tol=0.25, how="bbox_x", part="SaltCube"),
    dict(name="edge_y", mm=18.0, tol=0.25, how="bbox_y", part="SaltCube"),
    dict(name="edge_z", mm=18.0, tol=0.25, how="bbox_z", part="SaltCube"),
    dict(name="overall_height", mm=18.0, tol=1.6, how="bbox_z"),
]