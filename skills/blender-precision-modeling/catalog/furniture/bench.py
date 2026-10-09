"""
bench -- park bench with armrests, 1500 mm long, seat 450 mm, back 850 mm.

A slatted bench is entirely a spacing problem: five 90 mm seat slats with 25 mm
gaps make exactly 550 mm of depth, and three 90 mm back slats with 20 mm gaps
make exactly 310 mm of back. Both banks come out of bkit.lay_out from those
real widths, which is the only way the slats stay parallel and evenly spaced
across 1500 mm.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=1500.0,
    depth=550.0,
    overall_height=850.0,
    seat_height=450.0,
    seat_slat_count=5,
    slat_width=90.0,
    slat_thickness=40.0,
    slat_gap=25.0,
    back_slat_count=3,
    back_slat_height=90.0,
    back_slat_gap=20.0,
    frame_section=70.0,
    armrest_height=690.0,
    armrest_length=500.0,
)

L, D, H = SPEC["length"], SPEC["depth"], SPEC["overall_height"]
SEAT_TOP = SPEC["seat_height"]                # 450
SLAT_W = SPEC["slat_width"]                   # 90
SLAT_T = SPEC["slat_thickness"]               # 40
FRAME = SPEC["frame_section"]                 # 70
FRAME_X = 650.0                               # frame centreline
FRAME_Y = 220.0
SEAT_CZ = SEAT_TOP - SLAT_T / 2.0             # 430
# Back bank: lay_out puts three 90 mm slats at centres -110, 0, +110, so the
# stack is 310 mm tall and BACK_MID has to be 695 for its top edge to land on
# the 850 mm posts with a 10 mm cap showing above.
BACK_SLAT_H = SPEC["back_slat_height"]
BACK_MID = 695.0                              # centre of the 310 mm back bank

CHECKS = [
    dict(name="overall_length", mm=1500.0, tol=0.4, how="bbox_x"),
    dict(name="overall_depth", mm=550.0, tol=0.4, how="bbox_y"),
    dict(name="overall_height", mm=850.0, tol=0.4, how="bbox_z"),
    dict(name="slat_width", mm=90.0, tol=0.3, how="bbox_y", part="SeatSlat0"),
    dict(name="slat_thickness", mm=40.0, tol=0.3, how="bbox_z", part="SeatSlat0"),
    dict(name="back_slat_height", mm=90.0, tol=0.3, how="bbox_z",
         part="BackSlat0"),
]


def build():
    timber = bkit.pbr("BenchTeak", base=(0.52, 0.35, 0.19), metal=0.0, rough=0.44)
    cast = bkit.pbr("BenchCastIron", base=(0.13, 0.13, 0.14), metal=0.55,
                    rough=0.50)

    # ---- frame: rear posts run to 850, front legs stop at the seat --------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("PostRear%s" % tag, FRAME, FRAME, H, r=6.0, segments=3,
                         centre=(sx * FRAME_X, FRAME_Y, H / 2.0), mat=cast)
        bkit.rounded_box("LegFront%s" % tag, FRAME, FRAME, SEAT_TOP, r=6.0,
                         segments=3,
                         centre=(sx * FRAME_X, -FRAME_Y, SEAT_TOP / 2.0),
                         mat=cast)
        # cross rail carries the seat slats
        bkit.rounded_box("SeatRail%s" % tag, 30.0, 480.0, SLAT_T, r=4.0,
                         segments=2,
                         centre=(sx * FRAME_X, 0, SEAT_TOP - SLAT_T - SLAT_T / 2.0),
                         mat=cast)
        # armrest: post off the front leg, then the rest itself
        bkit.rounded_box("ArmPost%s" % tag, 55.0, 55.0, 200.0, r=6.0, segments=2,
                         centre=(sx * FRAME_X, -FRAME_Y, SEAT_TOP + 100.0),
                         mat=cast)
        bkit.rounded_box("ArmRest%s" % tag, 90.0, SPEC["armrest_length"], 40.0,
                         r=14.0, segments=3,
                         centre=(sx * FRAME_X, 0,
                                 SPEC["armrest_height"] - 20.0),
                         mat=timber)

    # ---- seat slats: 5 x 90 mm with 25 mm gaps = exactly 550 mm deep ------
    for i, (dy, _w) in enumerate(
            bkit.lay_out([SLAT_W] * SPEC["seat_slat_count"], gap=SPEC["slat_gap"])):
        bkit.rounded_box("SeatSlat%d" % i, L, SLAT_W, SLAT_T, r=9.0, segments=3,
                         centre=(0, dy, SEAT_CZ), mat=timber)

    # ---- back slats: 3 x 90 mm with 20 mm gaps, 310 mm of back -----------
    for i, (dz, _h) in enumerate(
            bkit.lay_out([BACK_SLAT_H] * SPEC["back_slat_count"],
                         gap=SPEC["back_slat_gap"])):
        bkit.rounded_box("BackSlat%d" % i, L, 40.0, BACK_SLAT_H, r=9.0,
                         segments=3, centre=(0, FRAME_Y, BACK_MID + dz),
                         mat=timber)

    return dict(spec=SPEC, parts=15)
