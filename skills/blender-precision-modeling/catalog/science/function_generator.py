"""
function_generator -- 240 x 200 x 118 mm bench function generator: chassis on
four feet, a recessed 130 x 56 mm display, a six-key mode keypad, a 52 mm
main tuning dial with a pointer, two BNC outputs and a top cooling grille.

Same science-instrument grammar as `oscilloscope`, at bench-instrument scale:
the recess is cut proud-and-deep so the cutter crosses the panel instead of
touching it, and the six keys, two outputs and eighteen grille holes all come
from `grid_positions`, `lay_out` and `perforated_panel` rather than from
hand-placed coordinates.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    chassis_width=240.0,
    chassis_depth=200.0,
    chassis_height=118.0,
    screen_width=130.0,
    screen_height=56.0,
    keypad_buttons=6,
    dial_diameter=52.0,
    bnc_outputs=2,
    grille_holes=18,
)

CW, CD, CH = SPEC["chassis_width"], SPEC["chassis_depth"], SPEC["chassis_height"]
BODY_Z = 6.0 + CH / 2.0
FRONT = -CD / 2.0                    # -100


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("FgenShell", base=(0.82, 0.81, 0.79), rough=0.34)
    dark = bkit.pbr("FgenDark", base=(0.065, 0.065, 0.070), rough=0.42)
    knob_mat = bkit.pbr("FgenKnob", base=(0.14, 0.14, 0.15), rough=0.46)
    nickel = bkit.preset("brushed_metal")
    screen = bkit.pbr("FgenScreen", base=(0.05, 0.08, 0.07), rough=0.10,
                      emission=(0.30, 0.66, 0.48), emission_strength=1.0)

    # ---- chassis and feet -------------------------------------------------
    bkit.rounded_box("FgenChassis", CW, CD, CH, r=8.0, segments=3,
                     centre=(0.0, 0.0, BODY_Z), mat=shell)
    feet = [bkit.cylinder("_foot", 10.0, 8.0, segments=20,
                          centre=(fx, fy, 4.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, CW - 50.0, CD - 50.0)]
    bkit.join(feet, name="FgenFeet")

    # ---- recessed display --------------------------------------------------
    _recess("FgenScreen", bpy.data.objects["FgenChassis"], SPEC["screen_width"],
            SPEC["screen_height"], -46.0, 88.0, screen)

    # ---- six keys on one grid ---------------------------------------------
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(3, 2, 38.0, 24.0)):
        keys.append(bkit.rounded_box(
            "_key%d" % i, 28.0, 7.0, 15.0, r=2.5, segments=2, mat=knob_mat,
            centre=(-46.0 + kx, FRONT + 2.5, 34.0 + kz)))
    bkit.join(keys, name="FgenKeypad")

    # ---- 52 mm main dial with its pointer skirt --------------------------
    bkit.cylinder("FgenDial", SPEC["dial_diameter"] / 2.0, 18.0, segments=48,
                  axis="Y", centre=(58.0, FRONT + 8.0, 84.0), mat=knob_mat)
    bkit.box("DialPointer", 2.0, 3.0, 20.0, mat=shell,
             centre=(58.0, FRONT - 1.0, 96.0))

    # ---- two BNC outputs ---------------------------------------------------
    bnc = []
    for i, (bx, bw) in enumerate(bkit.lay_out([22.0] * SPEC["bnc_outputs"],
                                               gap=18.0)):
        bnc.append(bkit.cylinder("_b%d" % i, 11.0, 9.0, segments=28, axis="Y",
                                 mat=nickel,
                                 centre=(58.0 + bx, FRONT + 3.5, 30.0)))
        bnc.append(bkit.cylinder("_bp%d" % i, 4.5, 12.0, segments=20, axis="Y",
                                 mat=dark, centre=(58.0 + bx, FRONT + 3.0,
                                                   30.0)))
    bkit.join(bnc, name="FgenBncOutputs")

    # ---- top grille, 6 x 3 holes ------------------------------------------
    bkit.perforated_panel("FgenGrille", 6, 3, 18.0, 18.0, 6.0, 120.0, 60.0,
                          4.0, mat=dark)
    bkit.move(bpy.data.objects["FgenGrille"], 50.0, 0.0, BODY_Z + CH / 2.0)

    # ---- rear mains inlet and a mode switch -------------------------------
    bkit.rounded_box("MainsInlet", 34.0, 6.0, 26.0, r=2.0, segments=2,
                     centre=(-70.0, CD / 2.0 - 1.0, 50.0), mat=dark)
    bkit.rounded_box("PowerSwitch", 26.0, 6.0, 18.0, r=2.0, segments=2,
                     centre=(-70.0, CD / 2.0 - 1.0, 20.0), mat=knob_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="chassis_width", mm=240.0, tol=0.6, how="bbox_x",
         part="FgenChassis"),
    dict(name="chassis_depth", mm=200.0, tol=0.6, how="bbox_y",
         part="FgenChassis"),
    dict(name="chassis_height", mm=118.0, tol=0.6, how="bbox_z",
         part="FgenChassis"),
    dict(name="screen_width", mm=130.0, tol=0.6, how="bbox_x",
         part="FgenScreen"),
    dict(name="dial_diameter", mm=52.0, tol=0.6, how="diameter",
         part="FgenDial"),
]