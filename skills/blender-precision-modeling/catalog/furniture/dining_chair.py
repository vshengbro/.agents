"""
dining_chair -- four-leg oak dining chair, 450 mm seat height, 900 mm overall.

Proportion IS the product for a dining chair, so every number here is a real
one: 450 mm seat (the standard dining height), 900 mm overall back (a clean 2:1
ratio), and a 440 x 440 mm seat square. The four legs run plumb from the floor
and the two back posts are the rear legs continued upward -- shaker
construction. That continuity is what makes the silhouette read square instead
of splayed, so the posts are single 900 mm members, not a leg plus a stub.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    overall_height=900.0,      # floor to top of the back posts
    seat_height=450.0,         # standard dining seat height
    seat_width=440.0,
    seat_depth=440.0,
    seat_thickness=40.0,
    leg_section=38.0,          # square leg, 38 x 38
    stretcher_section=24.0,
    stretcher_height=180.0,
    back_slats=3,
    back_slat_height=70.0,
    back_slat_thickness=18.0,
)

LEG = SPEC["leg_section"]
SEAT_W = SPEC["seat_width"]
SEAT_D = SPEC["seat_depth"]
SEAT_T = SPEC["seat_thickness"]
SEAT_TOP = SPEC["seat_height"]
LEG_H = SEAT_TOP - SEAT_T              # 410: the legs stop under the seat
OVERALL = SPEC["overall_height"]
INSET = 20.0                           # seat overhang beyond the legs
LEG_X = SEAT_W / 2.0 - INSET - LEG / 2.0   # 181
LEG_Y = SEAT_D / 2.0 - INSET - LEG / 2.0   # 181
STR = SPEC["stretcher_section"]
SLAT_H = SPEC["back_slat_height"]
SLAT_T = SPEC["back_slat_thickness"]
# slat gap chosen so the three slats fill the 450..900 back zone with even air
SLAT_GAP = 45.0

CHECKS = [
    dict(name="overall_height", mm=900.0, tol=0.3, how="bbox_z"),
    dict(name="seat_width", mm=440.0, tol=0.3, how="bbox_x", part="Seat"),
    dict(name="seat_depth", mm=440.0, tol=0.3, how="bbox_y", part="Seat"),
    dict(name="seat_thickness", mm=40.0, tol=0.3, how="bbox_z", part="Seat"),
    dict(name="leg_section", mm=38.0, tol=0.3, how="bbox_x", part="LegFrontLeft"),
]


def build():
    oak = bkit.pbr("ChairOak", base=(0.50, 0.33, 0.17), metal=0.0, rough=0.40)
    oak_dark = bkit.pbr("ChairOakDark", base=(0.41, 0.26, 0.12), metal=0.0,
                        rough=0.46)

    # ---- seat: the one level, horizontal surface --------------------------
    bkit.rounded_box("Seat", SEAT_W, SEAT_D, SEAT_T, r=7.0, segments=3,
                     centre=(0, 0, SEAT_TOP - SEAT_T / 2.0), mat=oak)

    # ---- front legs: plumb, square section --------------------------------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("LegFront%s" % tag, LEG, LEG, LEG_H, r=3.0, segments=2,
                         centre=(sx * LEG_X, -LEG_Y, LEG_H / 2.0), mat=oak_dark)

    # ---- back posts: the rear legs, run on to the full 900 mm -------------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("PostRear%s" % tag, LEG, LEG, OVERALL, r=3.0,
                         segments=2, centre=(sx * LEG_X, LEG_Y, OVERALL / 2.0),
                         mat=oak_dark)

    # ---- back slats: computed, not hand-placed ----------------------------
    # Spanning the clear width between the two posts (2 * (LEG_X - LEG/2)).
    clear = 2.0 * (LEG_X - LEG / 2.0)
    mid = (SEAT_TOP + 90.0 + OVERALL - 40.0) / 2.0
    for i, (dz, _w) in enumerate(
            bkit.lay_out([SLAT_H] * SPEC["back_slats"], gap=SLAT_GAP)):
        bkit.rounded_box("BackSlat%d" % (i + 1), clear, SLAT_T, SLAT_H, r=4.0,
                         segments=2, centre=(0, LEG_Y, mid + dz), mat=oak)

    # ---- stretchers: side rails first, then front/back ---------------------
    inner_x = LEG_X - LEG / 2.0      # 162: leg inner face
    inner_y = LEG_Y - LEG / 2.0
    strut_z = SPEC["stretcher_height"]
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("StretcherSide%s" % tag, STR, 2 * inner_y, STR, r=3.0,
                         segments=2,
                         centre=(sx * (inner_x - STR / 2.0), 0, strut_z),
                         mat=oak_dark)
    for (sy, tag) in ((-1, "Front"), (1, "Back")):
        bkit.rounded_box("Stretcher%s" % tag, 2 * inner_x, STR, STR, r=3.0,
                         segments=2,
                         centre=(0, sy * (inner_y - STR / 2.0), strut_z),
                         mat=oak_dark)

    return dict(spec=SPEC, parts=14)
