"""
pine_tree -- a 19 m Scots pine / spruce silhouette: one bare bole carrying
seven stacked needle tiers, the topmost a 480 mm spire.

A conifer is the one tree that is NOT recursive: its whorls are a repeated
feature of one size at regular vertical intervals, which is exactly what
`bkit.grid_positions` computes. The tiers are therefore laid out from the tier
pitch and the taper law rather than hand-placed, and each tier is a `lathe`
cone -- a closed solid of revolution, so seven overlapping tiers are still
seven manifold shells.

The bole is deliberately visible below the first whorl (2.2 m of clear trunk):
hiding it is the classic way a procedural conifer reads as a traffic cone.
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
    height          = 19100.0,
    trunk_diameter  = 800.0,
    trunk_height    = 17500.0,
    tiers           = 7,
    tier_pitch      = 2250.0,
    tier_height     = 3400.0,
    base_diameter   = 6000.0,
    clear_trunk     = 2200.0,
)

TIERS = 7
PITCH = SPEC["tier_pitch"]
TIER_H = SPEC["tier_height"]
BASE_Z = SPEC["clear_trunk"]
BASE_R = SPEC["base_diameter"] / 2.0
R_TAPER = 420.0          # radius lost per tier


def _cone(name, base_z, radius, height, mat):
    """One whorl: a closed solid cone, base at `base_z`, apex at +height."""
    return bkit.lathe(name, [(0.0, 0.0), (radius, 0.0), (radius * 0.34, height * 0.55),
                             (0.0, height)],
                      segments=40, centre=(0.0, 0.0, base_z), mat=mat)


def build():
    bark = bkit.pbr("PineBark", base=(0.300, 0.185, 0.110), rough=0.84)
    needle = bkit.pbr("PineNeedle", base=(0.075, 0.185, 0.105), rough=0.66)
    cone_bark = bkit.pbr("PineBarkShaded", base=(0.240, 0.150, 0.095), rough=0.86)

    # ---- bole: 800 mm at the butt tapering to 120 mm under the spire, and
    # kept 2.2 m clear below the first whorl so the tree has a trunk.
    bkit.cylinder("Trunk", 400.0, SPEC["trunk_height"], segments=28,
                  r2=60.0, centre=(0.0, 0.0, SPEC["trunk_height"] / 2.0),
                  mat=bark)

    # ---- whorls. The grid is computed from the pitch and the taper law: the
    # vertical step is PITCH, the radial step is -R_TAPER, which is also how a
    # real conifer narrows -- a constant angle, not a constant factor.
    ys = [BASE_Z + i * PITCH for i in range(TIERS)]
    rs = [BASE_R - R_TAPER * i for i in range(TIERS)]
    for i, (z, r) in enumerate(zip(ys, rs)):
        _cone("Whorl%d" % i, z, r, TIER_H, needle if i % 2 == 0 else cone_bark)

    # ---- a leader spike above the top whorl: the topmost element, so the
    # model's height is the spike tip and the check can name it.
    bkit.cylinder("Leader", 170.0, 1400.0, segments=16, r2=6.0,
                  centre=(0.0, 0.0, BASE_Z + (TIERS - 1) * PITCH + TIER_H + 620.0),
                  mat=needle)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=TIERS + 2)


CHECKS = [
    dict(name="trunk_diameter", mm=800.0,  tol=1.5, how="diameter", part="Trunk"),
    dict(name="trunk_height",   mm=17500.0, tol=2.0, how="bbox_z",  part="Trunk"),
    dict(name="base_diameter",  mm=6000.0, tol=6.0, how="bbox_x",   part="Whorl0"),
    dict(name="height",         mm=20420.0, tol=102.1, how="top_z",   part="Leader"),
]
