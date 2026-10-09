"""
tape_measure -- 8 m tape measure, 72 mm case with the blade drawn out.

The case is stood on its flat face and the blade is drawn out horizontally
along -Y rather than dropping through the bottom. That is the only orientation
where sit_on_floor seats the model AND the blade stays visible: a blade
exiting downward would be pressed into the studio floor.

The yellow case gets a dark rubber band one millimetre proud of the shell,
so it reads as an overmould rather than a second co-planar shell.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

CASE = 72.0
CASE_H = 36.0

SPEC = dict(
    overall_length=102.5,
    case_width=CASE,
    case_depth=CASE,
    case_height=CASE_H,
    blade_width=24.0,
)


def build():
    shell = bkit.preset("yellow_paint")
    rubber = bkit.preset("rubber")
    blade_mat = bkit.pbr("TapeBlade", base=(0.80, 0.62, 0.10), rough=0.30)
    steel = bkit.pbr("TapeSteel", base=(0.70, 0.72, 0.76), metal=0.30,
                     rough=0.26)

    case = bkit.rounded_box("TapeCase", CASE, CASE, CASE_H, r=13.0,
                            segments=5, centre=(0, 0, CASE_H / 2.0),
                            mat=shell)
    band = bkit.rounded_box("TapeCaseBand", CASE + 1.5, CASE + 1.5, 15.0,
                            r=6.0, segments=4, centre=(0, 0, CASE_H / 2.0),
                            mat=rubber)

    blade = bkit.rounded_box("TapeBladeStrip", 24.0, 26.0, 0.8, r=0.35,
                             segments=2, centre=(0, -44.0, 8.0),
                             mat=blade_mat)
    hook = bkit.rounded_box("TapeHook", 24.0, 4.0, 12.0, r=1.0, segments=2,
                            centre=(0, -58.0, 8.0), mat=steel)
    clip = bkit.rounded_box("TapeBeltClip", 30.0, 7.0, 44.0, r=2.5,
                            segments=3, centre=(0, 39.0, 20.0), mat=steel)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="case_width", mm=72.0, tol=0.5, how="bbox_x", part="TapeCase"),
    dict(name="case_height", mm=36.0, tol=0.5, how="bbox_z", part="TapeCase"),
    dict(name="blade_width", mm=24.0, tol=0.4, how="bbox_x",
         part="TapeBladeStrip"),
    dict(name="overall_length", mm=102.5, tol=1.5, how="bbox_y"),
]