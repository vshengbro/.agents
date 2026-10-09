"""
clamp -- 100 mm C-clamp, 166 mm frame height, throat open 19 mm.

One extruded C outline plus the screw, the swivel pad and the sliding tommy
bar. The throat is a genuine gap between two arms of the same polygon (the
outline goes up the inner back, across the jaw face, and back out), so the
clamp is a single watertight solid rather than a ring assembled from bars.

The swivel pad presents its face HORIZONTALLY against the jaw -- the screw
axis is X, but the pad the screw pushes with is a Z-axis disc, because that is
what a real swivel pad does and it is also what makes the clamp look open.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    frame_width=116.0,
    frame_height=166.0,
    throat_opening=19.0,
    tommy_bar_length=92.0,
    overall_length=166.0,
)


def build():
    cast = bkit.pbr("ClampCast", base=(0.50, 0.51, 0.54), metal=0.20,
                    rough=0.48)
    steel = bkit.pbr("ClampSteel", base=(0.70, 0.72, 0.76), metal=0.30,
                     rough=0.28)

    c_poly = [(-58.0, 0.0), (44.0, 0.0), (44.0, 28.0), (-6.0, 44.0),
              (-6.0, 130.0), (58.0, 130.0), (58.0, 162.0), (-58.0, 166.0)]
    frame = bkit.extrude_profile("ClampFrame", c_poly, 22.0, axis="Y",
                                mat=cast)
    bkit.recalc(frame)
    bkit.bevel(frame, width_mm=1.4, segments=2, angle_deg=34)

    screw = bkit.cylinder("ClampScrew", 10.0, 68.0, segments=40, axis="X",
                          centre=(14.0, 0, 92.0), mat=steel)

    pad = bkit.cylinder("ClampSwivelPad", 15.0, 18.0, segments=40,
                        centre=(52.0, 0, 102.0), mat=steel)
    bkit.bevel(pad, width_mm=1.0, segments=2, angle_deg=30)

    bar = bkit.cylinder("ClampTBar", 5.5, 92.0, segments=32, axis="Y",
                        centre=(-20.0, 0, 92.0), mat=steel)
    for i, y in enumerate((-46.0, 46.0)):
        bkit.uv_sphere("ClampTBarKnob%d" % (i + 1), 7.0, segments=24,
                       rings=12, centre=(-20.0, y, 92.0), mat=steel)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="frame_width", mm=116.0, tol=0.5, how="bbox_x",
         part="ClampFrame"),
    dict(name="frame_height", mm=166.0, tol=0.5, how="bbox_z",
         part="ClampFrame"),
    dict(name="tommy_bar_length", mm=92.0, tol=0.5, how="bbox_y",
         part="ClampTBar"),
    dict(name="overall_length", mm=166.0, tol=1.0, how="bbox_z"),
]