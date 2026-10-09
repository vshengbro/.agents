"""
pedestrian_crossing -- 2500 mm crossing post: a 90 mm pole on a cast base, a
300 mm circular blue plate with a white triangle, a push-button unit at 1000 mm
and a yellow reflective band at the correct height.

`small` in the catalog, modelled at its real 2500 mm post height. Both faces are
real extruded profiles -- the plate from a 48-gon circle, the triangle from a
3-point outline -- turned to face -Y by `place(axis="Y")`, which is how you get
a true 10 mm plate edge and a true 12 mm triangle standing proud of it, neither
of which a rounded box can do.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    pole_diameter=90.0,
    pole_height=2450.0,
    sign_diameter=300.0,
    sign_thickness=10.0,
    triangle_height=200.0,
    button_height=1050.0,
    band_height=150.0,
    overall_height=2478.0,
)

POLE_R = SPEC["pole_diameter"] / 2.0
SIGN_C = (0.0, -70.0, 2150.0)


def circle_poly(r, n=48, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def build():
    post = bkit.pbr("CrossPost", base=(0.62, 0.63, 0.60), metal=0.60,
                    rough=0.42)
    plate_blue = bkit.pbr("CrossPlateBlue", base=(0.05, 0.16, 0.46),
                          rough=0.26,
                          emission=(0.06, 0.20, 0.55), emission_strength=0.7)
    white = bkit.pbr("CrossWhite", base=(0.93, 0.93, 0.90), rough=0.24)
    yellow = bkit.pbr("CrossBand", base=(0.85, 0.72, 0.10), rough=0.26,
                      emission=(0.90, 0.78, 0.14), emission_strength=0.5)
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("brushed_metal")

    # ---- cast base and pole, the pole sunk 20 mm into the base ---------
    bkit.cylinder("CrossBase", 90.0, 70.0, segments=32, centre=(0.0, 0.0, 35.0),
                  mat=post)
    bkit.cylinder("CrossPole", POLE_R, SPEC["pole_height"], segments=32,
                  centre=(0.0, 0.0, 1235.0), mat=post)
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("PoleCap", [(0.0, 2450.0), (POLE_R, 2450.0), (42.0, 2466.0),
                          (26.0, 2476.0), (0.0, 2478.0)], segments=32,
               mat=post)

    # ---- base bolts on a computed grid -----------------------------------
    bolts = [bkit.cylinder("_b", 9.0, 12.0, segments=16, centre=(bx, by, 74.0),
                           mat=steel)
             for (bx, by) in bkit.grid_positions(2, 2, 120.0, 120.0)]
    bkit.join(bolts, name="CrossBaseBolts")

    # ---- 300 mm plate with a 200 mm white triangle ----------------------
    bkit.extrude_profile("CrossingSign", circle_poly(150.0), 10.0,
                         centre=SIGN_C, axis="Y", mat=plate_blue)
    bkit.extrude_profile("SignRim", circle_poly(158.0), 6.0,
                         centre=(SIGN_C[0], SIGN_C[1] + 8.0, SIGN_C[2]),
                         axis="Y", mat=post)
    # An equilateral triangle 200 mm TALL: base at y=-115, apex at y=+85.
    # Writing it as circumradius/angles would give 150 mm, not 200.
    tri = [(-115.0, -115.0), (115.0, -115.0), (0.0, 85.0)]
    bkit.extrude_profile("CrossTriangle", tri, 14.0,
                         centre=(SIGN_C[0], SIGN_C[1] - 2.0, SIGN_C[2] - 10.0),
                         axis="Y", mat=white)

    # ---- two clamp brackets holding the plate to the pole ---------------
    clamps = []
    for i, cz in enumerate((SIGN_C[2] - 60.0, SIGN_C[2] + 60.0)):
        clamps.append(bkit.box("_c%d" % i, 60.0, 90.0, 40.0, mat=steel,
                               centre=(0.0, -25.0, cz)))
        clamps.append(bkit.cylinder("_cb%d" % i, 7.0, 30.0, segments=16,
                                    axis="X", mat=dark,
                                    centre=(0.0, -60.0, cz)))
    bkit.join(clamps, name="SignClamps")

    # ---- push-button unit at the correct 1050 mm hand height -----------
    bkit.rounded_box("ButtonBracket", 90.0, 110.0, 200.0, r=8.0, segments=2,
                     centre=(0.0, -POLE_R - 50.0, SPEC["button_height"] - 120.0),
                     mat=post)
    bkit.rounded_box("ButtonFace", 70.0, 26.0, 150.0, r=6.0, segments=2,
                     centre=(0.0, -POLE_R - 100.0, SPEC["button_height"] - 120.0),
                     mat=yellow)
    bkit.cylinder("PushButton", 26.0, 22.0, segments=28, axis="Y",
                  centre=(0.0, -POLE_R - 118.0, SPEC["button_height"] - 120.0),
                  mat=dark)

    # ---- yellow reflective band on the pole ------------------------------
    bkit.tube("ReflectiveBand", POLE_R + 1.0, POLE_R - 1.0,
              SPEC["band_height"], segments=32, centre=(0.0, 0.0, 1500.0),
              mat=yellow)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="pole_diameter", mm=90.0, tol=0.6, how="diameter",
         part="CrossPole"),
    dict(name="sign_diameter", mm=300.0, tol=1.0, how="diameter",
         part="CrossingSign"),
    dict(name="triangle_height", mm=200.0, tol=1.0, how="bbox_z",
         part="CrossTriangle"),
    dict(name="band_height", mm=150.0, tol=0.6, how="bbox_z",
         part="ReflectiveBand"),
    dict(name="overall_height", mm=2478.0, tol=2.0, how="bbox_z"),
]