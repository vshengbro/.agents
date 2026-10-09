"""
music_box -- 200 x 150 x 130 mm box with the lid open on its hinge.

A music box is a wooden case, a pinned cylinder and a steel comb, and the comb
is what makes it a music box rather than a box. So all three are modelled: the
cylinder carries pins on a real helix pitch, and the comb's twenty-two teeth
are one tooth swept by array_linear across the comb length.

The lid is hinged at the back and stands open at 100 degrees, so the inside of
the case and the mechanism are visible from the front -- which is how every
music box is photographed, and the only way the cylinder and comb read at all.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 200.0, 150.0, 130.0
WALL_T = 8.0
BASE_H = 58.0
LID_T = 10.0
LID_OPEN_DEG = 100.0
CYL_R = 20.0
CYL_L = 96.0
CYL_Z = 38.0
CAVITY_FLOOR = 4.0
PIN_N = 24
PIN_PITCH = 3.6
PIN_R = 0.9
COMB_TEETH = 22
COMB_TOOTH_PITCH = 4.4
COMB_TOOTH_L = 26.0
COMB_T = 1.4
SPRING_R = 14.0

SPEC = dict(width=W, depth=D, height=H, base_height=BASE_H,
            lid_thickness=LID_T, lid_open_degrees=LID_OPEN_DEG,
            cylinder_diameter=2.0 * CYL_R, cylinder_length=CYL_L,
            pin_count=PIN_N, pin_pitch=PIN_PITCH,
            comb_teeth=COMB_TEETH, comb_tooth_pitch=COMB_TOOTH_PITCH)


def build():
    wood = bkit.pbr("MusicWood", base=(0.44, 0.26, 0.12), metal=0.0, rough=0.42)
    inlay = bkit.pbr("MusicInlay", base=(0.72, 0.56, 0.26), metal=0.85, rough=0.30)
    steel = bkit.pbr("MusicSteel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.16)
    brass = bkit.pbr("MusicBrass", base=(0.92, 0.72, 0.32), metal=0.85, rough=0.20)

    # ---- case: a base box with the cavity the mechanism sits in ------------
    base = bkit.rounded_box("Base", W, D, BASE_H, r=4.0, segments=3,
                            centre=(0.0, 0.0, BASE_H / 2.0), mat=wood)
    # the cavity floor has to sit BELOW the comb (z 6..15) and the cylinder
    # (z 18..58), or both are buried in the case floor and neither is visible
    cavity = bkit.rounded_box("_cavity", W - 2.0 * WALL_T, D - 2.0 * WALL_T,
                              BASE_H + 8.0, r=2.0, segments=2,
                              centre=(0.0, 0.0, CAVITY_FLOOR + (BASE_H + 8.0) / 2.0))
    bkit.boolean(base, cavity, "DIFFERENCE")

    # ---- lid, hinged open at the back ---------------------------------------
    lid = bkit.rounded_box("Lid", W, D, LID_T, r=4.0, segments=3,
                           centre=(0.0, -D / 2.0, LID_T / 2.0), mat=wood)
    lid.rotation_euler = (math.radians(-LID_OPEN_DEG), 0.0, 0.0)
    bkit.move(lid, 0.0, D / 2.0, BASE_H - 2.0)
    lid_inlay = bkit.rounded_box("LidInlay", W - 30.0, D - 30.0, 2.0, r=3.0,
                                 segments=2,
                                 centre=(0.0, -D / 2.0, LID_T - 1.0), mat=inlay)
    lid_inlay.rotation_euler = (math.radians(-LID_OPEN_DEG), 0.0, 0.0)
    bkit.move(lid_inlay, 0.0, D / 2.0, BASE_H - 2.0)

    # ---- the pinned cylinder, laid along X ----------------------------------
    cyl = bkit.cylinder("Cylinder", CYL_R, CYL_L, segments=56,
                        centre=(0.0, 0.0, CYL_Z), axis="X", mat=brass)
    # 24 pins on a real 3.6 mm pitch, alternating rows so the tune is a tune
    pin = bkit.cylinder("CylinderPins", PIN_R, 4.0, segments=10,
                        centre=(-(PIN_N - 1) * PIN_PITCH / 2.0, 0.0,
                                CYL_Z + CYL_R - 0.6), axis="Z", mat=steel)
    bkit.array_linear(pin, PIN_N, (PIN_PITCH, 0.0, 0.0), world=True)

    # ---- the comb: one tooth, swept across the comb length ------------------
    tooth = bkit.rounded_box("CombTeeth", 1.6, COMB_TOOTH_L, COMB_T, r=0.4,
                             segments=2,
                             centre=(-(COMB_TEETH - 1) * COMB_TOOTH_PITCH / 2.0,
                                     0.0, CYL_Z - CYL_R - 5.0), mat=steel)
    bkit.array_linear(tooth, COMB_TEETH, (COMB_TOOTH_PITCH, 0.0, 0.0), world=True)
    bkit.rounded_box("CombBase", (COMB_TEETH - 1) * COMB_TOOTH_PITCH + 6.0, 6.0,
                     8.0, r=1.5, segments=2,
                     centre=(0.0, 0.0, CYL_Z - CYL_R - 10.0), mat=steel)

    # ---- the spring barrel driving it ---------------------------------------
    spring = bkit.lathe(
        "SpringBarrel",
        [(0.0, -9.0), (SPRING_R, -9.0), (SPRING_R, 9.0), (0.0, 9.0)],
        segments=40, mat=steel)
    spring.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(spring, -CYL_L / 2.0 - 16.0, 0.0, CYL_Z)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="width", mm=200.0, tol=0.2, how="bbox_x", part="Base"),
    dict(name="depth", mm=150.0, tol=0.2, how="bbox_y", part="Base"),
    dict(name="base_height", mm=58.0, tol=0.2, how="bbox_z", part="Base"),
    dict(name="cylinder_diameter", mm=40, tol=0.2, how="bbox_y",
         part="Cylinder"),
    dict(name="cylinder_length", mm=96.0, tol=0.2, how="bbox_x", part="Cylinder"),
    # 21 x 4.4 pitch + one tooth
    dict(name="comb_run", mm=94.0, tol=0.2, how="bbox_x", part="CombTeeth"),
    dict(name="overall_height", mm=203, tol=0.5, how="bbox_z",
         part=None)
]