"""
clevis_pin -- 8 x 60 mm clevis pin with a headed end and a circlip groove.

A clevis pin is a hardened shaft with three features that all have to be real:
a head to stop the clevis flying apart, a cross hole for a split pin or a grease
nipple, and a circlip groove near the free end. Two of those are cut from the
turned profile (head, chamfer, groove) and one is a boolean, which is why the
part is one revolved solid rather than stacked cylinders.

Dimensions follow the DIN 1444 / ISO 2341 practice: d = 8 gives a 14 mm head,
1.2 d of head length and a 2.2 mm deep snap-ring groove set 4 mm from the end.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SHANK_D = 8.0           # d
LENGTH = 60.0           # l, overall
HEAD_D = 14.0           # 1.75 d
HEAD_L = 7.5            # 0.94 d
GROOVE_D = 5.8          # snap-ring groove diameter
GROOVE_W = 1.6
GROOVE_FROM_END = 4.0
CROSS_HOLE_D = 3.6      # split-pin / grease hole

SPEC = dict(shank_diameter=SHANK_D,
            length=LENGTH,
            head_diameter=HEAD_D,
            head_length=HEAD_L,
            groove_diameter=GROOVE_D,
            cross_hole_diameter=CROSS_HOLE_D)


def build():
    steel = bkit.pbr("PinSteel", base=(0.80, 0.81, 0.84), metal=0.76,
                     rough=0.20)
    hr = HEAD_D / 2.0
    sr = SHANK_D / 2.0
    gr = GROOVE_D / 2.0
    g0 = LENGTH - GROOVE_FROM_END - GROOVE_W
    g1 = LENGTH - GROOVE_FROM_END

    profile = [
        (0.0, 0.0), (hr - 1.0, 0.0), (hr, 1.0),          # head, chamfered end
        (hr, HEAD_L - 1.0), (sr + 1.4, HEAD_L),
        (sr, HEAD_L + 1.6),                                # under-head chamfer
        (sr, g0), (gr, g0 + GROOVE_W / 2.0), (sr, g1),    # circlip groove
        (sr, LENGTH - 1.0), (sr - 1.0, LENGTH), (0.0, LENGTH),
    ]
    pin = bkit.lathe("ClevisPin", profile, segments=72, mat=steel)

    hole = bkit.cylinder("CrossHole", CROSS_HOLE_D / 2.0, SHANK_D * 2.0,
                         segments=24, centre=(0, 0, HEAD_L + 4.0), axis="Y",
                         mat=None)
    bkit.boolean(pin, hole, "DIFFERENCE")

    # lie the pin on its side: the turned axis becomes X, so the head diameter
    # shows on both transverse axes and the length on X
    pin.rotation_euler = (0.0, math.radians(90.0), 0.0)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="pin_length", mm=60.0, tol=0.05, how="bbox_x", part=None),
    dict(name="head_diameter", mm=14.0, tol=0.05, how="bbox_y", part="ClevisPin"),
    # the head is the widest feature on both transverse axes
    dict(name="head_diameter_flank", mm=14.0, tol=0.05, how="bbox_z",
         part="ClevisPin"),
]