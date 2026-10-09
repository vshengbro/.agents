"""
sink -- inset kitchen sink: a fold-back loft bowl with a real 1.5 mm steel
wall, a flat rim flange that sits ON the worktop, a drain, and a mixer tap.

The 800 x 450 single bowl with a 45 mm flange and a 190 mm bowl depth is the
standard UK inset sink.

The one thing to get right in a fold-back loft is the ORDER of the sections.
`cap_start` closes the FIRST ring and `cap_end` closes the LAST, so the first
section must be the bowl's outer underside and the last must be the inner
floor. Starting at the inner rim instead puts a flat lid over the bowl: it
renders as a solid block with a flange underneath, and it is watertight the
whole time, so only the render shows it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=800.0,
    width=450.0,
    bowl_depth=190.0,
    flange_width=45.0,     # rim flange beyond the bowl opening
    flange_thickness=6.0,
    wall=1.5,
    bowl_corner_radius=45.0,
    drain_diameter=90.0,
    tap_body_height=210.0,
    overall_height=462.0,   # bowl flange top to the crown of the gooseneck
)

L, W = SPEC["length"], SPEC["width"]
FD = SPEC["bowl_depth"]
FL = SPEC["flange_width"]
FT = SPEC["flange_thickness"]
CR = SPEC["bowl_corner_radius"]

FLANGE_TOP = FT + FD          # 196: the flange sits 190 above the bowl floor
BOWL_FLOOR = FT + 12.0


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=8)]


def build():
    steel = bkit.preset("brushed_metal")
    flange_mat = bkit.pbr("SinkSteel", base=(0.78, 0.79, 0.80), metal=0.85,
                          rough=0.26)

    # ---- bowl: underside -> outer wall -> flange top -> inner wall -> floor
    bowl = bkit.loft("SinkBowl", [
        _ring(L - 2 * FL - 60.0, W - 2 * FL - 60.0, CR + 20.0, 0.0),
        _ring(L - 2 * FL - 60.0, W - 2 * FL - 60.0, CR + 20.0, 14.0),
        _ring(L - 2 * FL - 40.0, W - 2 * FL - 40.0, CR + 10.0, 60.0),
        _ring(L - 2 * FL, W - 2 * FL, CR, FLANGE_TOP - 6.0),      # outer wall
        _ring(L, W, CR + 90.0, FLANGE_TOP),                       # flange, outer
        _ring(L - 2 * FL + 20.0, W - 2 * FL + 20.0, CR + 30.0, FLANGE_TOP),
        _ring(L - 2 * FL - 2.0 * SPEC["wall"],
              W - 2 * FL - 2.0 * SPEC["wall"], CR - 4.0, FLANGE_TOP - 46.0),
        _ring(L - 2 * FL - 60.0, W - 2 * FL - 60.0, CR + 6.0, 40.0),
        _ring(L - 2 * FL - 150.0, W - 2 * FL - 150.0, CR + 20.0, BOWL_FLOOR),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=flange_mat)
    bkit.recalc(bowl)

    # ---- drain: a real hole through the bowl floor -----------------------
    # Driven from below the floor and stopping above the underside, so it
    # crosses both surfaces instead of being tangent to either.
    bkit.bore(bowl, SPEC["drain_diameter"] / 2.0, depth=90.0,
              centre=(0.0, 0.0, BOWL_FLOOR - 8.0), axis="Z", host_segments=120)

    # ---- strainer basket in the drain ------------------------------------
    basket = bkit.lathe("DrainBasket", [
        (0.0, 0.0), (30.0, 0.0), (42.0, 10.0), (42.0, 16.0),
        (36.0, 16.0), (36.0, 8.0), (0.0, 6.0),
    ], segments=48, mat=steel)
    bkit.move(basket, 0.0, 0.0, BOWL_FLOOR - 10.0)

    # ---- mixer tap standing on the back flange ---------------------------
    ty = W / 2.0 - 62.0
    tap_body = bkit.lathe("SinkTapBody", [
        (0.0, 0.0), (26.0, 0.0), (26.0, 12.0), (18.0, 28.0),
        (18.0, 198.0), (14.0, 210.0), (0.0, 210.0),
    ], segments=56, mat=steel)
    # Sunk 12 mm INTO the flange so the two solids interlock; resting it
    # exactly on top leaves a hairline that renders as a floating tap.
    bkit.move(tap_body, 0.0, ty, FLANGE_TOP - 12.0)

    # Gooseneck spout. The half torus runs from its RISING end (a0, tangent
    # up) to its far end (a1 = 180, tangent straight DOWN, over the bowl), so
    # the rising end is buried in the body and the tube leaves through the
    # body's side well below the top. Centre it on the body's own axis: a 34 mm
    # offset in y puts the spout beside the body and it reads as two parts.
    spout = bkit.arc_torus("SinkTapSpout", 90.0, 12.0, -25.0, 180.0,
                           centre=(-81.6, ty, 360.0), plane="XZ", seg_major=44,
                           seg_minor=24, mat=steel, caps=True)
    # The mixer lever: a paddle off the top of the body. Its far end overhangs,
    # which is how a lever reads, and the whole arc -- not the lever -- is what
    # sets the assembly's overall height.
    lever = bkit.rounded_box("SinkTapLever", 24.0, 88.0, 11.0, r=4.0,
                             segments=3, centre=(0.0, ty + 58.0, 399.5),
                             mat=steel)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="length", mm=800.0, tol=0.5, how="bbox_x", part="SinkBowl"),
    dict(name="width", mm=450.0, tol=0.5, how="bbox_y", part="SinkBowl"),
    dict(name="tap_body_height", mm=210.0, tol=0.5, how="bbox_z",
         part="SinkTapBody"),
    # 196 mm of bowl under the flange plus a 266 mm gooseneck mixer above it
    dict(name="overall_height", mm=462.0, tol=1.5, how="bbox_z"),
]
