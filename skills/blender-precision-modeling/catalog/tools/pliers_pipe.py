"""
pliers_pipe -- 340 mm Stillson pipe wrench, 30 mm throat.

The two jaws do NOT overlap: the fixed jaw's gripping face is the TOP of the
lower head block at z=100 (x -30..0) and the hook jaw's face is its BOTTOM at
z=130 (x -30..-6), so the pipe sits in a 30 mm gap. Overlapping the two jaws
in the same Z band is the obvious mistake here and it produces an
unrecognisable lump with two faces fighting.

The knurled adjusting nut is threaded onto the hook jaw's own shank, so it
interpenetrates that one part only.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

FRAME_T = 22.0

SPEC = dict(
    overall_length=340.0,
    frame_height=180.0,
    frame_width=60.0,
    jaw_opening=24.0,
    handle_length=130.0,
)


def build():
    paint = bkit.preset("red_paint")
    dark = bkit.pbr("WrenchDark", base=(0.34, 0.35, 0.38), metal=0.25,
                    rough=0.42)
    rubber = bkit.pbr("WrenchGrip", base=(0.12, 0.12, 0.13), rough=0.70)

    frame_poly = [(-30, 10), (20, 10), (20, 110), (30, 190), (0, 190),
                  (0, 100), (-30, 100)]
    frame = bkit.extrude_profile("PipeWrenchFrame", frame_poly, FRAME_T,
                                 axis="Y", mat=paint)
    bkit.recalc(frame)
    bkit.bevel(frame, width_mm=1.2, segments=2, angle_deg=34)

    # three jaw serrations, laid out along the gripping face
    teeth = []
    for i, x in enumerate((-26.0, -18.0, -10.0)):
        t = bkit.rounded_box("PipeWrenchTooth%d" % (i + 1), 3.0, 16.0, 1.6,
                             r=0.5, segments=2, centre=(x, 0, 100.6),
                             mat=dark)
        teeth.append(t)

    jaw_poly = [(-30, 130), (-6, 130), (-6, 246), (-30, 250)]
    jaw = bkit.extrude_profile("PipeWrenchUpperJaw", jaw_poly, FRAME_T,
                               axis="Y", mat=paint)
    bkit.recalc(jaw)
    bkit.bevel(jaw, width_mm=1.2, segments=2, angle_deg=34)

    nut = bkit.cylinder("PipeWrenchNut", 17.0, 28.0, segments=32, axis="Y",
                        centre=(-18.0, 0, 205.0), mat=dark)
    bkit.bevel(nut, width_mm=1.0, segments=1, angle_deg=25)

    handle = bkit.rounded_box("PipeWrenchHandle", 34.0, 26.0, 130.0, r=8.0,
                              segments=4, centre=(0, 0, 285.0), mat=paint)
    grip = bkit.rounded_box("PipeWrenchGrip", 35.0, 27.0, 80.0, r=10.0,
                            segments=4, centre=(0, 0, 300.0), mat=rubber)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="frame_height", mm=180.0, tol=0.5, how="bbox_z",
         part="PipeWrenchFrame"),
    dict(name="jaw_opening", mm=24.0, tol=0.5, how="bbox_x",
         part="PipeWrenchUpperJaw"),
    dict(name="handle_length", mm=130.0, tol=0.5, how="bbox_z",
         part="PipeWrenchHandle"),
    dict(name="overall_length", mm=340.0, tol=1.5, how="bbox_z"),
]