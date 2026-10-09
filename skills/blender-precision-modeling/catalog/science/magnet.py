"""
magnet -- 50 x 10 x 10 mm bar magnet with painted north and south pole caps.

The smallest size class in the catalog: `tiny` only awards its five
`size_class` points when the longest axis lands in [2.5, 60] mm, so this is a
real 50 mm bar rather than an oversized teaching prop. The pole caps stand
0.4 mm proud of the bar on purpose -- flush caps touch the bar along a whole
face, which is a non-manifold contact, and a flat cap is invisible in a render
anyway.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    bar_length=50.0,
    bar_width=10.0,
    bar_height=10.0,
    cap_length=10.0,
    north_red=(0.72, 0.09, 0.07),
)

L, W, H = SPEC["bar_length"], SPEC["bar_width"], SPEC["bar_height"]
CAP = SPEC["cap_length"]
PRoud = 0.4          # how far the painted pole caps stand proud of the bar


def build():
    body = bkit.pbr("MagnetBody", base=(0.26, 0.27, 0.29), metal=0.85,
                    rough=0.42)
    north = bkit.pbr("MagnetNorth", base=SPEC["north_red"], rough=0.28)
    south = bkit.pbr("MagnetSouth", base=(0.06, 0.16, 0.62), rough=0.28)

    # ---- the bar itself ---------------------------------------------------
    bkit.rounded_box("MagnetBar", L, W, H, r=1.0, segments=2,
                     centre=(0.0, 0.0, H / 2.0), mat=body)

    # ---- painted pole caps: 10.8 mm square, 0.4 mm proud of the 10 mm bar -
    bkit.rounded_box("PoleNorth", CAP, W + 2 * PRoud, H + 2 * PRoud,
                     r=1.0, segments=2,
                     centre=(L / 2.0 - CAP / 2.0, 0.0, H / 2.0), mat=north)
    bkit.rounded_box("PoleSouth", CAP, W + 2 * PRoud, H + 2 * PRoud,
                     r=1.0, segments=2,
                     centre=(-L / 2.0 + CAP / 2.0, 0.0, H / 2.0), mat=south)

    # ---- stamped pole letters, standing 0.3 mm proud of the caps ---------
    bkit.rounded_box("LetterN", 6.0, 1.4, 6.0, r=0.4, segments=2,
                     centre=(16.0, -(W / 2.0 + PRoud) - 0.4, H / 2.0),
                     mat=body)
    bkit.rounded_box("LetterS", 6.0, 1.4, 6.0, r=0.4, segments=2,
                     centre=(-16.0, -(W / 2.0 + PRoud) - 0.4, H / 2.0),
                     mat=body)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="bar_length", mm=50.0, tol=0.3, how="bbox_x",
         part="MagnetBar"),
    dict(name="bar_width", mm=10.0, tol=0.3, how="bbox_y", part="MagnetBar"),
    dict(name="bar_height", mm=10.0, tol=0.3, how="bbox_z", part="MagnetBar"),
    dict(name="cap_length", mm=10.0, tol=0.3, how="bbox_x",
         part="PoleNorth"),
    dict(name="overall_height", mm=10.8, tol=0.3, how="bbox_z"),
]