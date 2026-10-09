"""
street_lamp -- 4.5 m column luminaire: cast base, tapered column, a swan-neck
outreach arm and a hanging lantern.

The identifying geometry is the SILHOUETTE: a very long slim column, then a
quarter-circle neck that carries the lantern out over the road. The neck is a
real arc_torus quarter-turn, not a diagonal strut -- a straight brace reads as
a floodlight mast, not a street lamp.

Authored standing on the ground at z = 0 (run_model calls sit_on_floor, and a
column built hanging below the origin would be pushed through the backdrop).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    column_height=4200.0,     # to the underside of the swan neck
    column_base_diameter=190.0,
    column_top_diameter=110.0,
    base_diameter=420.0,
    base_height=140.0,
    neck_radius=900.0,
    neck_tube_diameter=70.0,
    lantern_diameter=340.0,
    lantern_height=230.0,
    overall_height=5300.0,
)

NECK_R = SPEC["neck_radius"]


def build():
    alu = bkit.preset("anodized")
    dark = bkit.preset("dark_metal")
    glass = bkit.pbr("LanternGlass", base=(0.88, 0.90, 0.88), rough=0.12,
                     emission=(1.0, 0.94, 0.78), emission_strength=4.0)

    base_h = SPEC["base_height"]
    col_h = SPEC["column_height"]
    top_z = base_h + col_h

    # ---- cast base with its access door ---------------------------------
    base = bkit.lathe("StreetLampBase", [
        (0.0, 0.0),
        (196.0, 0.0),
        (210.0, 6.0),
        (210.0, 96.0),
        (198.0, 118.0),
        (150.0, 134.0),
        (110.0, base_h),
        (95.0, base_h),
        (0.0, base_h),
    ], segments=72, mat=dark)

    # ---- tapered column --------------------------------------------------
    column = bkit.cylinder("StreetLampColumn",
                           SPEC["column_base_diameter"] / 2.0, col_h,
                           r2=SPEC["column_top_diameter"] / 2.0,
                           segments=48, centre=(0.0, 0.0, base_h + col_h / 2.0),
                           mat=alu)

    # ---- swan neck: a quarter circle springing from the column top -----
    # Centre the arc at (NECK_R, 0, top_z) with radius NECK_R and it passes
    # through BOTH ends the lamp needs: a = 180 lands on the column axis at
    # z = top_z, and a = 90 lands at (NECK_R, 0, top_z + NECK_R) with a
    # horizontal tangent, which is where the lantern hangs. Centring it on
    # the axis instead (the obvious reading) puts the arm edge-on as a spike
    # above the column with the lantern nowhere near it.
    neck = bkit.arc_torus("StreetLampNeck", NECK_R,
                          SPEC["neck_tube_diameter"] / 2.0,
                          90.0, 180.0, centre=(NECK_R, 0.0, top_z),
                          plane="XZ", seg_major=56, mat=alu, caps=True)

    # ---- lantern housing hanging from the neck end ----------------------
    lant_r = SPEC["lantern_diameter"] / 2.0
    lant_h = SPEC["lantern_height"]
    arm_end_z = top_z + NECK_R
    lant_top = arm_end_z - 20.0            # bracket overlaps the arm end
    lantern = bkit.lathe("StreetLampLantern", [
        (0.0, 0.0),                        # hanger spigot into the arm end
        (54.0, 0.0),
        (58.0, 34.0),
        (58.0, 76.0),
        (lant_r, 100.0),                   # shoulder out to the lantern body
        (lant_r, lant_h - 34.0),
        (lant_r - 30.0, lant_h),
        (0.0, lant_h),
    ], segments=72, centre=(NECK_R, 0.0, lant_top), mat=alu)

    # the glass band is a second material on the lantern, not a second shell
    bkit.assign_faces_by(
        lantern, glass,
        lambda c, n: (c.z / bkit.MM) < lant_top + lant_h - 46.0
        and (c.x - NECK_R) ** 2 + c.y ** 2 > 40.0 ** 2)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="column_height", mm=4200.0, tol=1.0, how="bbox_z", part="StreetLampColumn"),
    dict(name="column_base_diameter", mm=190.0, tol=0.6, how="diameter", part="StreetLampColumn"),
    dict(name="base_diameter", mm=420.0, tol=0.6, how="diameter", part="StreetLampBase"),
    dict(name="base_height", mm=140.0, tol=0.5, how="bbox_z", part="StreetLampBase"),
    dict(name="lantern_diameter", mm=340.0, tol=0.6, how="diameter", part="StreetLampLantern"),
]