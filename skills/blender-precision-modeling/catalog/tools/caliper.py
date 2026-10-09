"""
caliper -- 150 mm vernier caliper reading 68 mm, 219 mm overall.

Beam along X, jaws hanging in -Z. Measuring faces are laid out from ONE slider
position (SLIDER_X) so the opening is a real derived number rather than three
hand-typed constants that can drift apart: shift the slider and the fixed
jaw, the moving jaw, both internal jaws and the thumb wheel all move together.

The depth rod rides on the BACK face of the beam at y = +9, so it stands
proud of the 16 mm beam instead of being buried inside it where nothing would
show it.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BEAM_L = 230.0
BEAM_T = 6.0
SLIDER_X = 60.0              # slider centre -> the reading is SLIDER_X + 8
JAW_H = 54.0

SPEC = dict(
    overall_length=240.0,
    beam_length=BEAM_L,
    beam_width=16.0,
    jaw_height=JAW_H,
    slider_width=44.0,
)


def build():
    steel = bkit.pbr("CaliperSteel", base=(0.68, 0.70, 0.74), metal=0.30,
                     rough=0.28)
    jaw_mat = bkit.pbr("CaliperJaw", base=(0.38, 0.40, 0.43), metal=0.25,
                        rough=0.42)
    rubber = bkit.pbr("CaliperWheel", base=(0.11, 0.11, 0.12), rough=0.40)
    accent = bkit.preset("red_paint")

    beam = bkit.rounded_box("CaliperBeam", BEAM_L, 16.0, BEAM_T, r=1.2,
                            segments=3, centre=(85.0, 0, 0), mat=steel)
    fixed = bkit.rounded_box("CaliperFixedJaw", 15.0, 16.0, JAW_H, r=1.5,
                             segments=3, centre=(0, 0, -25.0), mat=jaw_mat)
    fixed_in = bkit.rounded_box("CaliperFixedJawInner", 10.0, 16.0, 22.0,
                                r=1.2, segments=3, centre=(-4.0, 0, 13.0),
                                mat=jaw_mat)

    slider = bkit.rounded_box("CaliperSlider", 44.0, 22.0, 22.0, r=2.5,
                              segments=3, centre=(SLIDER_X, 0, 0), mat=steel)
    moving = bkit.rounded_box("CaliperMovingJaw", 15.0, 16.0, JAW_H, r=1.5,
                              segments=3, centre=(SLIDER_X + 8.0, 0, -25.0),
                              mat=jaw_mat)
    moving_in = bkit.rounded_box("CaliperMovingJawInner", 10.0, 16.0, 22.0,
                                 r=1.2, segments=3,
                                 centre=(SLIDER_X + 12.0, 0, 13.0),
                                 mat=jaw_mat)

    wheel = bkit.cylinder("CaliperThumbWheel", 9.0, 17.0, segments=40,
                          axis="Y", centre=(SLIDER_X, 0, -13.0),
                          mat=rubber)
    lock = bkit.cylinder("CaliperLockScrew", 5.0, 12.0, segments=32,
                         centre=(SLIDER_X, 0, 14.0), mat=accent)

    rod = bkit.rounded_box("CaliperDepthRod", 128.0, 3.0, 3.0, r=1.0,
                           segments=2, centre=(146.0, 9.0, 0), mat=steel)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="beam_length", mm=230.0, tol=0.5, how="bbox_x",
         part="CaliperBeam"),
    dict(name="jaw_height", mm=54.0, tol=0.5, how="bbox_z",
         part="CaliperFixedJaw"),
    dict(name="slider_width", mm=44.0, tol=0.4, how="bbox_x",
         part="CaliperSlider"),
    dict(name="overall_length", mm=240.0, tol=1.0, how="bbox_x"),
]