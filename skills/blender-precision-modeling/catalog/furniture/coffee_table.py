"""
coffee_table -- 1200 x 600 mm oak coffee table with a lower shelf, 420 mm high.

The whole read of a coffee table is its ratio: 1200 mm of top over 420 mm of
height is about 2.9:1, which is the difference between a coffee table and a
side table. The top overhangs the leg frame by 60 mm on every side so it
visibly floats, and the shelf at 120 mm stops the 380 mm of open leg from
reading as a flimsy stool.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    top_length=1200.0,
    top_depth=600.0,
    height=420.0,
    top_thickness=40.0,
    shelf_length=1020.0,
    shelf_depth=440.0,
    shelf_thickness=25.0,
    shelf_height=132.5,        # centre height of the lower shelf
    leg_top_section=52.0,      # legs taper 34 -> 52 over their length
    leg_bottom_section=34.0,
    rail_section=26.0,
)

TOP_Z0 = SPEC["height"] - SPEC["top_thickness"]     # 380: underside of the top
LEG_X = 540.0
LEG_Y = 240.0

CHECKS = [
    dict(name="overall_length", mm=1200.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=420.0, tol=0.3, how="bbox_z"),
    dict(name="top_depth", mm=600.0, tol=0.3, how="bbox_y", part="TableTop"),
    dict(name="top_thickness", mm=40.0, tol=0.3, how="bbox_z", part="TableTop"),
    dict(name="shelf_thickness", mm=25.0, tol=0.3, how="bbox_z", part="Shelf"),
    dict(name="leg_top_section", mm=52.0, tol=0.3, how="bbox_x", part="LegFrontLeft"),
]


def _tapered_leg(name, x, y, h, w_bottom, w_top, mat):
    """A square leg that swells upward, lofted from two 2D rings.

    A loft rather than two stacked boxes: a box on a box shows a seam line
    halfway down the leg, and a cone primitive would give a round leg. Two
    rounded-rect rings at different z give a real furniture taper, and loft()
    caps both ends so the leg is watertight on its own.
    """
    bot = bkit.rounded_rect_section(w_bottom, w_bottom, r=3.0, per_corner=3,
                                    centre=(x, y))
    top = bkit.rounded_rect_section(w_top, w_top, r=4.0, per_corner=3,
                                    centre=(x, y))
    sections = [[(px, py, 0.0) for (px, py) in bot],
                [(px, py, h) for (px, py) in top]]
    return bkit.loft(name, sections, closed_loop=True, cap_start=True,
                     cap_end=True, mat=mat)


def build():
    oak = bkit.pbr("TableOak", base=(0.47, 0.31, 0.16), metal=0.0, rough=0.40)
    oak_dark = bkit.pbr("TableOakDark", base=(0.38, 0.24, 0.12), metal=0.0,
                        rough=0.46)

    bkit.rounded_box("TableTop", SPEC["top_length"], SPEC["top_depth"],
                     SPEC["top_thickness"], r=9.0, segments=4,
                     centre=(0, 0, TOP_Z0 + SPEC["top_thickness"] / 2.0),
                     mat=oak)

    bkit.rounded_box("Shelf", SPEC["shelf_length"], SPEC["shelf_depth"],
                     SPEC["shelf_thickness"], r=6.0, segments=3,
                     centre=(0, 0, SPEC["shelf_height"]), mat=oak)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            _tapered_leg("Leg%s%s" % (yn, xn), sx * LEG_X, sy * LEG_Y, TOP_Z0,
                         SPEC["leg_bottom_section"], SPEC["leg_top_section"],
                         oak_dark)

    # ---- rails under the shelf, tying the leg frame together ---------------
    # Spans stop at the legs' inner faces so the rail ends land ON the leg
    # rather than floating in the gap beside it.
    r = SPEC["rail_section"]
    span_x = 2.0 * (LEG_X - SPEC["leg_bottom_section"] / 2.0)
    span_y = 2.0 * (LEG_Y - SPEC["leg_bottom_section"] / 2.0)
    rail_z = SPEC["shelf_height"] - SPEC["shelf_thickness"] / 2.0 - r / 2.0
    for (sy, tag) in ((-1, "Front"), (1, "Back")):
        bkit.rounded_box("Rail%s" % tag, span_x, r, r, r=r / 2.0, segments=2,
                         centre=(0, sy * (LEG_Y - r / 2.0), rail_z), mat=oak_dark)
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Rail%s" % tag, r, span_y, r, r=r / 2.0, segments=2,
                         centre=(sx * (LEG_X - r / 2.0), 0, rail_z), mat=oak_dark)

    return dict(spec=SPEC, parts=10)
