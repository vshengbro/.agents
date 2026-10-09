"""
flower_pot -- a 120 mm terracotta pot with a rolled rim, a foot, a drainage
saucer and a soil surface.

The pot is a single `lathe` over a real wall profile: the inside is part of the
same surface of revolution as the outside, so the wall has a true 6 mm thickness
and the pot is watertight as one solid. Building the inside as a second, nested
object instead would z-fight with the wall and double the non-manifold count --
the trap `authoring-a-model.md` calls out under "prefer one solid over many
shells".

The rim is a `torus` laid into the mouth because a rolled lip catches a
highlight that a sharp edge never will.
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
    rim_diameter = 120.0,
    height       = 106.0,
    wall         = 6.0,
    soil_depth   = 88.0,
    saucer_width = 132.0,
)

RIM_R = SPEC["rim_diameter"] / 2.0
H = SPEC["height"]
WALL = SPEC["wall"]
SOIL_Z = SPEC["soil_depth"]

# (radius, z) up the outside, over the rim, back down the inside, across the
# floor. One closed profile, so the pot is one solid with a real wall.
PROFILE = [
    (0.0, 0.0),
    (36.0, 0.0),
    (40.0, 5.0),
    (50.0, 52.0),
    (RIM_R, H - 8.0),
    (RIM_R, H - 1.0),
    (RIM_R - WALL, H),
    (RIM_R - WALL, H - 3.0),
    (48.0, 56.0),
    (38.0, 12.0),
    (30.0, 10.0),
    (0.0, 10.0),
]


def build():
    terracotta = bkit.pbr("Terracotta", base=(0.545, 0.250, 0.150), rough=0.66)
    terracotta_d = bkit.pbr("TerracottaShaded", base=(0.420, 0.180, 0.110),
                            rough=0.70)
    soil = bkit.preset("soil")

    pot = bkit.lathe("Pot", PROFILE, segments=56, mat=terracotta)
    bkit.assign_faces_by(pot, terracotta_d,
                         lambda c, n: c.z / bkit.MM < 26.0)

    # ---- rolled rim sitting in the mouth
    bkit.torus("Rim", RIM_R - WALL / 2.0, WALL * 0.85, seg_major=56,
               seg_minor=14, centre=(0.0, 0.0, H - 2.0), mat=terracotta)

    # ---- soil: a shallow dome, so it does not read as a flat lid
    soil_ob = bkit.lathe("Soil", [(0.0, SOIL_Z + 4.0), (26.0, SOIL_Z + 3.0),
                                  (44.0, SOIL_Z), (RIM_R - WALL - 1.0, SOIL_Z - 3.0)],
                         segments=48, mat=soil)
    # The profile descends, and lathe() does not orient normals, so without this
    # the soil solid reports negative_volume even though it renders fine.
    bkit.recalc(soil_ob)

    # ---- saucer
    bkit.lathe("Saucer", [(0.0, 0.0), (40.0, 0.0), (52.0, 3.0),
                          (66.0, 12.0), (66.0, 16.0), (60.0, 15.0),
                          (48.0, 6.0), (0.0, 4.0)],
               segments=48, mat=terracotta)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="rim_diameter", mm=124.2, tol=0.62, how="diameter", part="Rim"),
    dict(name="height",       mm=106.0, tol=1.0, how="bbox_z",   part="Pot"),
    dict(name="soil_depth",   mm=92.0,  tol=0.5, how="top_z",    part="Soil"),
    dict(name="saucer_width", mm=132.0, tol=1.0, how="diameter", part="Saucer"),
]
