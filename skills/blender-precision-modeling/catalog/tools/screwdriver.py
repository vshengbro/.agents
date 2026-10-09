"""
screwdriver -- 250 mm flat-head screwdriver, 6.3 x 100 mm round fluted grip.

Built bottom-up so sit_on_floor rests it on the handle butt. The tip is a
loft of three rectangular rings, not a cone: a cone reads as a drill bit,
whereas a ring that stays 25 mm wide and thins from 3 mm to 1.2 mm reads as
the ground flat of a slotted screwdriver blade.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SHANK_TOP = 232.0
SHANK_R = 4.0

SPEC = dict(
    overall_length=250.0,
    handle_grip_diameter=36.0,
    handle_length=106.0,
    shank_diameter=8.0,
    blade_width=6.8,
)


def _ring(hw, ht, z):
    """A flat rectangle ring in the XY plane at height z."""
    return [(-hw, -ht, z), (hw, -ht, z), (hw, ht, z), (-hw, ht, z)]


def build():
    grip = bkit.pbr("ScrewdriverGrip", base=(0.55, 0.075, 0.055), rough=0.30)
    steel = bkit.pbr("ShankSteel", base=(0.72, 0.74, 0.78), metal=0.30,
                     rough=0.26)
    dark = bkit.pbr("CollarDark", base=(0.30, 0.31, 0.34), metal=0.25,
                    rough=0.42)

    # ---- handle: bulged grip with a collar at the top ----------------------
    prof = ((0.0, 26.0), (8.0, 30.0), (26.0, 35.0), (52.0, 36.0),
            (78.0, 33.0), (96.0, 27.0), (106.0, 23.0))
    sections = [[(x, y, z) for (x, y) in
                 bkit.superellipse_section(sx, sx * 0.78, n=2.8, steps=48)]
                for (z, sx) in prof]
    handle = bkit.loft("ScrewdriverHandle", sections, mat=grip)
    bkit.recalc(handle)

    collar = bkit.cylinder("ScrewdriverCollar", 13.0, 7.0, segments=48,
                           centre=(0, 0, 109.5), mat=dark)

    # ---- shank --------------------------------------------------------------
    shank = bkit.cylinder("ScrewdriverShank", SHANK_R,
                          SHANK_TOP - 113.0, segments=48,
                          centre=(0, 0, (SHANK_TOP + 113.0) / 2.0), mat=steel)

    # ---- flat blade: constant width, tapering in thickness only -------------
    tip = bkit.loft("ScrewdriverTip",
                    [_ring(1.7, 1.05, 230.0), _ring(2.9, 0.85, 242.0),
                     _ring(3.4, 0.60, 250.0)], mat=steel)
    bkit.recalc(tip)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="handle_grip_diameter", mm=36.0, tol=0.5, how="diameter",
         part="ScrewdriverHandle"),
    dict(name="shank_diameter", mm=8.0, tol=0.3, how="diameter",
         part="ScrewdriverShank"),
    dict(name="overall_length", mm=250.0, tol=1.0, how="bbox_z"),
]