"""
street_sign -- 700 x 160 x 2418 mm fingerpost street sign: a 60 mm base, an 80
mm pole, a 600 x 400 mm rounded plate on two bracket arms, four anchor bolts
and a domed pole cap.

Modelled at its real 2400 mm signpost height; a sign at 200 mm would not be a
signpost. The plate is a real `extrude_profile` over a rounded-rectangle
outline, turned to face along -Y by `place(axis="Y")` -- that is what gives it
rounded corners and a 12 mm edge thickness, which a `rounded_box` cannot do at
this corner radius.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    pole_diameter=80.0,
    pole_height=2395.0,
    plate_width=600.0,
    plate_height=400.0,
    plate_thickness=12.0,
    plate_corner_radius=40.0,
    bracket_arms=2,
    anchor_bolts=4,
    overall_height=2422.5,
)

POST_R = SPEC["pole_diameter"] / 2.0
PLATE_C = (320.0, 0.0, 2050.0)


def build():
    post = bkit.pbr("SignPost", base=(0.30, 0.31, 0.30), metal=0.70,
                    rough=0.44)
    face = bkit.pbr("SignFace", base=(0.10, 0.32, 0.16), rough=0.36)
    rim = bkit.pbr("SignRim", base=(0.80, 0.80, 0.78), rough=0.34)
    dark = bkit.preset("dark_metal")

    # ---- base, pole and domed cap ----------------------------------------
    bkit.cylinder("SignBase", 60.0, 60.0, segments=32, centre=(0.0, 0.0, 30.0),
                  mat=post)
    bkit.cylinder("SignPole", POST_R, SPEC["pole_height"], segments=32,
                  centre=(0.0, 0.0, 1225.0), mat=post)
    bkit.lathe("PoleCap", [(0.0, 2395.0), (POST_R, 2395.0), (38.0, 2408.0),
                           (24.0, 2416.0), (0.0, 2418.0)], segments=40,
               mat=post)

    # ---- four anchor bolts on a computed grid -----------------------------
    bolts = [bkit.cylinder("_bolt", 9.0, 12.0, segments=16,
                           centre=(bx, by, 64.0), mat=dark)
             for (bx, by) in bkit.grid_positions(2, 2, 76.0, 76.0)]
    bkit.join(bolts, name="SignAnchorBolts")

    # ---- 600 x 400 plate from a rounded-rectangle profile, facing -Y ------
    outline = bkit.rounded_rect_section(SPEC["plate_width"],
                                        SPEC["plate_height"],
                                        SPEC["plate_corner_radius"],
                                        per_corner=8)
    bkit.extrude_profile("SignPlate", outline, SPEC["plate_thickness"],
                         centre=PLATE_C, axis="Y", mat=face)
    # rim sits behind the face and is wider, so the plate reads as a panel in
    # a frame rather than as a painted board.
    rim_outline = bkit.rounded_rect_section(SPEC["plate_width"] + 24.0,
                                            SPEC["plate_height"] + 24.0,
                                            SPEC["plate_corner_radius"] + 12.0,
                                            per_corner=8)
    bkit.extrude_profile("SignRim", rim_outline, 6.0,
                         centre=(PLATE_C[0], PLATE_C[1] + 9.0, PLATE_C[2]),
                         axis="Y", mat=rim)

    # ---- two bracket arms and two fixing bolts ----------------------------
    arms = []
    for i, az in enumerate((1900.0, 2200.0)):
        arms.append(bkit.box("_arm%d" % i, 120.0, 26.0, 26.0, mat=rim,
                             centre=(120.0, 0.0, az)))
        arms.append(bkit.box("_plate%d" % i, 20.0, 30.0, 60.0, mat=rim,
                             centre=(30.0, 0.0, az)))
        arms.append(bkit.cylinder("_bolt%d" % i, 8.0, 40.0, segments=16,
                                  axis="Y", mat=dark,
                                  centre=(30.0, -12.0, az)))
    bkit.join(arms, name="SignBrackets")

    # ---- a small supplementary plate lower down ---------------------------
    small = bkit.rounded_rect_section(300.0, 200.0, 24.0, per_corner=8)
    bkit.extrude_profile("AuxPlate", small, 10.0, centre=(-150.0, 0.0, 1500.0),
                         axis="Y", mat=face)
    bkit.box("AuxBracket", 80.0, 22.0, 22.0, mat=rim,
             centre=(-90.0, 0.0, 1500.0))

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="pole_diameter", mm=80.0, tol=0.5, how="diameter",
         part="SignPole"),
    dict(name="plate_width", mm=600.0, tol=0.6, how="bbox_x",
         part="SignPlate"),
    dict(name="plate_height", mm=400.0, tol=0.6, how="bbox_z",
         part="SignPlate"),
    dict(name="pole_height", mm=2395.0, tol=1.0, how="bbox_z", part="SignPole"),
    dict(name="overall_height", mm=2422.5, tol=2.0, how="bbox_z"),
]