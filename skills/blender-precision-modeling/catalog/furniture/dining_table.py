"""
dining_table -- 1800 x 900 mm six-seat dining table, 750 mm high.

750 mm is the number that makes it a dining table (a kitchen worktop is
900 mm, a bar is 1050 mm), and the 40 mm top plus a 110 mm apron under it is
what makes it read as furniture rather than as a board on trestles. The legs
taper 70 -> 95 mm upward, built as lofts so there is no seam line where a
stacked box would show one.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=1800.0,
    depth=900.0,
    height=750.0,
    top_thickness=40.0,
    apron_height=110.0,
    apron_thickness=45.0,
    leg_height=600.0,
    leg_bottom_section=70.0,
    leg_top_section=95.0,
    leg_inset=110.0,        # inboard of the top edge on each axis
)

L, D, H = SPEC["length"], SPEC["depth"], SPEC["height"]
TOP_T = SPEC["top_thickness"]
APRON_H = SPEC["apron_height"]
APRON_T = SPEC["apron_thickness"]
LEG_H = SPEC["leg_height"]
TOP_Z0 = H - TOP_T                            # 710
APRON_Z1 = TOP_Z0                            # 710
APRON_Z0 = APRON_Z1 - APRON_H                 # 600
LEG_X = L / 2.0 - SPEC["leg_inset"]           # 790
LEG_Y = D / 2.0 - SPEC["leg_inset"]           # 340
APRON_CZ = (APRON_Z0 + APRON_Z1) / 2.0        # 655

CHECKS = [
    dict(name="overall_length", mm=1800.0, tol=0.4, how="bbox_x"),
    dict(name="overall_height", mm=750.0, tol=0.3, how="bbox_z"),
    dict(name="overall_depth", mm=900.0, tol=0.4, how="bbox_y"),
    dict(name="top_thickness", mm=40.0, tol=0.3, how="bbox_z", part="TableTop"),
    dict(name="leg_top_section", mm=95.0, tol=0.3, how="bbox_x",
         part="LegFrontLeft"),
]


def _tapered_leg(name, x, y, mat):
    """Square leg swelling from 70 mm at the floor to 95 mm under the apron."""
    bot = bkit.rounded_rect_section(SPEC["leg_bottom_section"],
                                    SPEC["leg_bottom_section"], r=5.0,
                                    per_corner=3, centre=(x, y))
    top = bkit.rounded_rect_section(SPEC["leg_top_section"],
                                    SPEC["leg_top_section"], r=6.0,
                                    per_corner=3, centre=(x, y))
    sections = [[(px, py, 0.0) for (px, py) in bot],
                [(px, py, LEG_H) for (px, py) in top]]
    leg = bkit.loft(name, sections, closed_loop=True, cap_start=True,
                    cap_end=True, mat=mat)
    bkit.bevel(leg, width_mm=1.0, segments=2, angle_deg=35)
    return leg


def build():
    oak = bkit.pbr("DiningTableOak", base=(0.49, 0.32, 0.16), metal=0.0,
                   rough=0.36)
    oak_dark = bkit.pbr("DiningTableLeg", base=(0.40, 0.25, 0.12), metal=0.0,
                        rough=0.42)

    bkit.rounded_box("TableTop", L, D, TOP_T, r=10.0, segments=4,
                     centre=(0, 0, TOP_Z0 + TOP_T / 2.0), mat=oak)

    # Apron spans stop at the legs' inner faces, so each rail end lands on a leg
    # instead of stopping in mid-air beside one.
    inner_x = LEG_X - SPEC["leg_top_section"] / 2.0
    inner_y = LEG_Y - SPEC["leg_top_section"] / 2.0
    for (sy, tag) in ((-1, "Front"), (1, "Back")):
        bkit.rounded_box("Apron%s" % tag, 2 * inner_x, APRON_T, APRON_H, r=5.0,
                         segments=2, centre=(0, sy * (inner_y - APRON_T / 2.0),
                                             APRON_CZ),
                         mat=oak_dark)
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Apron%s" % tag, APRON_T, 2 * inner_y, APRON_H, r=5.0,
                         segments=2, centre=(sx * (inner_x - APRON_T / 2.0), 0,
                                             APRON_CZ),
                         mat=oak_dark)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            _tapered_leg("Leg%s%s" % (yn, xn), sx * LEG_X, sy * LEG_Y, oak_dark)

    return dict(spec=SPEC, parts=9)
