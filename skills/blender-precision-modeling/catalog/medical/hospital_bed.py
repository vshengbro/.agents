"""
hospital_bed -- 2200 x 1000 x 985 mm hospital bed: a two-section mattress with
a real hinge gap, a tubular frame on four legs, head and foot boards, two raised
side rails and four braked castors.

One flat mattress slab reads as a bench, so the deck is split into a back
section and a leg section with 10 mm between them. Castors, legs and the board
posts come from `grid_positions`/`lay_out`, so the four corners cannot drift out
of square, and everything that belongs to the frame is joined into one part
before the side rails are hung on it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=2200.0,
    overall_width=1000.0,
    overall_height=985.0,
    mattress_size=1950.0,       # back + leg sections, assembly extent
    mattress_thickness=130.0,
    frame_height=560.0,
    board_height=300.0,
    castor_diameter=125.0,
)

L = SPEC["overall_length"]
W = SPEC["overall_width"]
RAIL_Y = W / 2.0 - 60.0          # 440.0
FRAME_Z = SPEC["frame_height"]
LEG_X = 900.0
CAST_R = SPEC["castor_diameter"] / 2.0
DECK_Z = FRAME_Z + 60.0          # mattress underside
MAT_TOP = DECK_Z + SPEC["mattress_thickness"]
BOARD_Z = MAT_TOP + SPEC["board_height"] / 2.0 - 40.0


def build():
    steel = bkit.pbr("BedSteel", base=(0.80, 0.82, 0.85), metal=0.82, rough=0.26)
    panel = bkit.pbr("BedPanel", base=(0.86, 0.87, 0.88), rough=0.36)
    mattress = bkit.pbr("BedMattress", base=(0.62, 0.68, 0.74), rough=0.62)
    rubber = bkit.preset("rubber")

    # ---- four castors and four legs, on a computed grid --------------------
    frame_parts = []
    for (gx, gy) in bkit.grid_positions(2, 2, 2.0 * LEG_X, 2.0 * RAIL_Y):
        castor = bkit.lathe("_castor", [
            (0.0, -22.0), (CAST_R - 16.0, -22.0), (CAST_R, -15.0),
            (CAST_R, 15.0), (CAST_R - 16.0, 22.0), (0.0, 22.0),
        ], segments=40, mat=rubber)
        castor.rotation_euler = (0.0, math.radians(90.0), 0.0)
        bkit.move(castor, gx - 30.0, gy, CAST_R)
        frame_parts.append(castor)
        frame_parts.append(bkit.rounded_box("_leg", 62.0, 62.0,
                                           FRAME_Z - CAST_R, r=10.0,
                                           segments=3,
                                           centre=(gx, gy,
                                                   CAST_R + (FRAME_Z - CAST_R) / 2.0),
                                           mat=steel))

    # ---- the deck frame and its cross rails --------------------------------
    posts = []
    for sign in (-1.0, 1.0):
        frame_parts.append(bkit.rounded_box("_longrail", L, 70.0, 90.0, r=14.0,
                                            segments=3,
                                            centre=(0, sign * RAIL_Y, FRAME_Z),
                                            mat=steel))
        for bx in (-L / 2.0 + 30.0, L / 2.0 - 30.0):
            posts.append(bkit.cylinder(
                "_boardpost", 22.0, MAT_TOP - FRAME_Z + 30.0, segments=24,
                centre=(bx, sign * (W / 2.0 - 60.0),
                        FRAME_Z + (MAT_TOP - FRAME_Z + 30.0) / 2.0),
                mat=steel))
    for (cx, _w) in bkit.lay_out([70.0] * 5, gap=440.0):
        frame_parts.append(bkit.rounded_box("_crossrail", 70.0,
                                            2.0 * RAIL_Y, 70.0, r=10.0,
                                            segments=3,
                                            centre=(cx, 0.0, FRAME_Z),
                                            mat=steel))
    bkit.join(frame_parts, name="BedFrame")
    bkit.join(posts, name="BedBoardPosts")

    # ---- mattress: a back section and a leg section with a hinge gap ------
    bkit.rounded_box("MattressBack", 995.0, W - 120.0,
                     SPEC["mattress_thickness"], r=26.0, segments=4,
                     centre=(-477.5, 0.0, DECK_Z + SPEC["mattress_thickness"] / 2.0),
                     mat=mattress)
    bkit.rounded_box("MattressLeg", 945.0, W - 120.0,
                     SPEC["mattress_thickness"], r=26.0, segments=4,
                     centre=(502.5, 0.0, DECK_Z + SPEC["mattress_thickness"] / 2.0),
                     mat=mattress)

    # ---- head and foot boards ---------------------------------------------
    for name, bx in (("HeadBoard", -L / 2.0 + 30.0),
                     ("FootBoard", L / 2.0 - 30.0)):
        bkit.rounded_box(name, 60.0, W, SPEC["board_height"], r=16.0,
                         segments=4, centre=(bx, 0.0, BOARD_Z), mat=panel)

    # ---- two raised side rails --------------------------------------------
    for sign, sx in ((-1.0, -1.0), (1.0, 1.0)):
        rails = [
            bkit.rounded_box("_railtop", 900.0, 34.0, 44.0, r=12.0,
                             segments=3,
                             centre=(sx * 80.0, sign * (RAIL_Y + 26.0),
                                     FRAME_Z + 250.0), mat=steel),
            bkit.rounded_box("_railmid", 900.0, 24.0, 30.0, r=10.0, segments=3,
                             centre=(sx * 80.0, sign * (RAIL_Y + 26.0),
                                     FRAME_Z + 130.0), mat=steel),
        ]
        for px in (sx * 80.0 - 400.0, sx * 80.0 + 400.0):
            rails.append(bkit.cylinder("_railpost", 18.0, 280.0, segments=20,
                                       centre=(px, sign * (RAIL_Y + 26.0),
                                               FRAME_Z + 150.0), mat=steel))
        bkit.join(rails, name="SideRail" + ("L" if sign < 0 else "R"))

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="overall_length", mm=2200.0, tol=5.0, how="bbox_x"),
    dict(name="overall_width", mm=1000.0, tol=5.0, how="bbox_y"),
    dict(name="deck_height", mm=605.0, tol=5.0, how="bbox_z", part="BedFrame"),
    dict(name="overall_height", mm=1010.0, tol=6.0, how="bbox_z"),
]