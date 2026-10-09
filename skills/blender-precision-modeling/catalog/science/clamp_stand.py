"""
clamp_stand -- 200 x 130 x 900 mm laboratory retort stand: cast base plate,
a 12 mm upright rod, a boss head, a 220 mm clamp arm, a two-jaw clamp and a
boss screw.

`large` because the rod is 900 mm, so the base looks small next to it -- which
is exactly what a retort stand looks like, and the whole reason to model one
separately from the glassware it holds. The rod is deliberately sunk 3 mm into
the base: a rod standing exactly on the base touches it across a disc, and that
contact is a non-manifold generator.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=200.0,
    base_depth=130.0,
    base_thickness=14.0,
    rod_diameter=12.0,
    rod_length=880.0,
    overall_height=897.0,
    clamp_arm_length=220.0,
    boss_width=40.0,
)

BASE_T = SPEC["base_thickness"]
ROD_L = SPEC["rod_length"]


def build():
    cast = bkit.pbr("StandCast", base=(0.34, 0.34, 0.35), metal=0.85,
                    rough=0.52)
    steel = bkit.preset("brushed_metal")
    black = bkit.pbr("StandBlack", base=(0.075, 0.075, 0.080), rough=0.44)
    nickel = bkit.preset("polished_metal")

    # ---- base plate with three anti-slip pads ----------------------------
    bkit.rounded_box("StandBase", SPEC["base_width"], SPEC["base_depth"],
                     BASE_T, r=4.0, segments=2, centre=(0.0, 0.0, BASE_T / 2.0),
                     mat=cast)
    pads = [bkit.cylinder("_pad", 12.0, 4.0, segments=20, centre=(px, py, 2.0),
                          mat=black)
            for (px, py) in bkit.grid_positions(3, 2, 76.0, 90.0)]
    bkit.join(pads, name="StandPads")

    # ---- upright rod, sunk 3 mm into the base ----------------------------
    bkit.cylinder("StandRod", SPEC["rod_diameter"] / 2.0, ROD_L, segments=40,
                  centre=(0.0, 0.0, BASE_T - 3.0 + ROD_L / 2.0), mat=steel)
    bkit.uv_sphere("RodCap", SPEC["rod_diameter"] / 2.0, segments=24,
                   rings=12, centre=(0.0, 0.0, BASE_T - 3.0 + ROD_L),
                   mat=steel)

    # ---- boss head on the rod, then the clamp arm ------------------------
    bkit.rounded_box("BossHead", SPEC["boss_width"], 34.0, 40.0, r=6.0,
                     segments=2, centre=(0.0, 0.0, 320.0), mat=black)
    bkit.cylinder("BossScrew", 8.0, 44.0, segments=24, axis="X",
                  centre=(26.0, 0.0, 320.0), mat=nickel)
    bkit.box("BossHandle", 10.0, 34.0, 34.0, mat=nickel,
             centre=(46.0, 0.0, 320.0))

    bkit.cylinder("ClampArm", 5.0, SPEC["clamp_arm_length"], segments=28,
                  axis="X", centre=(110.0, 0.0, 320.0), mat=steel)

    # ---- two-jaw clamp on the end of the arm ----------------------------
    for side, tag in ((-1.0, "A"), (1.0, "B")):
        bkit.rounded_box("Jaw" + tag, 18.0, 56.0, 76.0, r=5.0, segments=2,
                         centre=(212.0, side * 26.0, 320.0), mat=black)
    for side, tag in ((-1.0, "A"), (1.0, "B")):
        bkit.rounded_box("JawPad" + tag, 14.0, 10.0, 62.0, r=3.0, segments=2,
                         centre=(212.0, side * 8.0, 320.0),
                         mat=bkit.preset("rubber"))
    bkit.cylinder("ClampScrew", 7.0, 70.0, segments=24, axis="Y",
                  centre=(212.0, 0.0, 250.0), mat=nickel)

    # ---- a second boss higher up, to read as a real stand ----------------
    bkit.rounded_box("BossHead2", 36.0, 30.0, 34.0, r=5.0, segments=2,
                     centre=(0.0, 0.0, 600.0), mat=black)
    bkit.cylinder("Arm2", 4.0, 120.0, segments=24, axis="X",
                  centre=(60.0, 0.0, 600.0), mat=steel)

    return dict(spec=SPEC, parts=15)


CHECKS = [
    dict(name="base_width", mm=200.0, tol=0.5, how="bbox_x",
         part="StandBase"),
    dict(name="base_depth", mm=130.0, tol=0.5, how="bbox_y", part="StandBase"),
    dict(name="base_thickness", mm=14.0, tol=0.5, how="bbox_z",
         part="StandBase"),
    dict(name="rod_diameter", mm=12.0, tol=0.4, how="diameter",
         part="StandRod"),
    dict(name="rod_length", mm=880.0, tol=0.8, how="bbox_z", part="StandRod"),
    dict(name="overall_height", mm=897.0, tol=1.0, how="bbox_z"),
]