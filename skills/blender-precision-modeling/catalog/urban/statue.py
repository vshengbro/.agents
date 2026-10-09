"""
statue -- 900 x 900 x 2460 mm monument statue: a chamfered plinth, a panelled
pedestal with a bronze plaque, a moulded cap and base, and a robed standing
figure with arms and a head.

`large`, and 2460 mm is the real installed height. The figure is one `lathe`
over a hand-written robe profile -- the flare from shoulder to hem is what makes
a solid of revolution read as a robed figure rather than as a chess piece -- with
the arms and head added so the silhouette is not perfectly rotationally
symmetric.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    plinth_width=900.0,
    pedestal_width=700.0,
    pedestal_height=1100.0,
    figure_diameter=420.0,
    figure_height=990.0,
    plaque_width=420.0,
    overall_height=2460.0,
)

Z_FIGURE = 1430.0                    # figure starts on the moulded base


def build():
    stone = bkit.pbr("StatueStone", base=(0.72, 0.70, 0.66), rough=0.62)
    stone2 = bkit.pbr("StatueStoneWorn", base=(0.66, 0.64, 0.60), rough=0.70)
    bronze = bkit.pbr("StatueBronze", base=(0.42, 0.30, 0.12), metal=0.85,
                      rough=0.38)
    figure_mat = bkit.pbr("StatueFigure", base=(0.70, 0.68, 0.64), rough=0.56)

    # ---- plinth, pedestal and moulded cap ------------------------------
    bkit.rounded_box("StatuePlinth", SPEC["plinth_width"], SPEC["plinth_width"],
                     180.0, r=8.0, segments=2, centre=(0.0, 0.0, 90.0),
                     mat=stone)
    bkit.rounded_box("StatuePedestal", SPEC["pedestal_width"],
                     SPEC["pedestal_width"], SPEC["pedestal_height"], r=10.0,
                     segments=3, centre=(0.0, 0.0, 730.0), mat=stone)
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("PedestalPanel" + tag, 18.0, 400.0, 760.0, r=5.0,
                         segments=2, mat=stone2,
                         centre=(side * (SPEC["pedestal_width"] / 2.0
                                         - 2.0), 0.0, 700.0))
    bkit.rounded_box("StatueCap", 760.0, 760.0, 90.0, r=8.0, segments=2,
                     centre=(0.0, 0.0, 1325.0), mat=stone)
    bkit.rounded_box("StatueBase", 820.0, 820.0, 60.0, r=10.0, segments=2,
                     centre=(0.0, 0.0, 1400.0), mat=stone2)

    # ---- bronze dedication plaque on the pedestal front ----------------
    bkit.rounded_box("StatuePlaque", SPEC["plaque_width"], 14.0, 260.0,
                     r=4.0, segments=2,
                     centre=(0.0, -SPEC["pedestal_width"] / 2.0 - 4.0, 700.0),
                     mat=bronze)

    # ---- robed figure: one lathe over the robe silhouette ----------------
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("FigureRobe", [
        (0.0, Z_FIGURE), (200.0, Z_FIGURE), (210.0, 1500.0),
        (205.0, 1650.0), (185.0, 1800.0), (170.0, 1930.0),
        (162.0, 2040.0), (150.0, 2150.0), (120.0, 2250.0),
        (86.0, 2330.0), (66.0, 2400.0), (0.0, 2420.0),
    ], segments=48, mat=figure_mat)

    # ---- arms breaking the rotational symmetry, and the head ------------
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("FigureArm" + tag, 70.0, 70.0, 430.0, r=30.0,
                         segments=3, mat=figure_mat,
                         centre=(side * 155.0, -30.0, 2050.0))
    bkit.cylinder("FigureNeck", 46.0, 70.0, segments=28, centre=(0.0, 0.0, 2430.0),
                  mat=figure_mat)
    bkit.uv_sphere("FigureHead", 78.0, segments=32, rings=20,
                   centre=(0.0, 0.0, 2510.0), mat=figure_mat)

    # ---- weathering: two weep holes and a worn top surface --------------
    bkit.rounded_box("PlinthWear", 620.0, 620.0, 8.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 176.0), mat=stone2)
    weeps = [bkit.cylinder("_w", 12.0, 60.0, segments=16, axis="Y",
                           centre=(wx, -SPEC["pedestal_width"] / 2.0, 180.0),
                           mat=stone2)
             for wx in (-200.0, 200.0)]
    bkit.join(weeps, name="WeepHoles")

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="plinth_width", mm=900.0, tol=1.0, how="bbox_x",
         part="StatuePlinth"),
    dict(name="pedestal_width", mm=700.0, tol=1.0, how="bbox_x",
         part="StatuePedestal"),
    dict(name="pedestal_height", mm=1100.0, tol=1.0, how="bbox_z",
         part="StatuePedestal"),
    dict(name="figure_diameter", mm=420.0, tol=2.0, how="diameter",
         part="FigureRobe"),
    dict(name="overall_height", mm=2588.0, tol=3.0, how="bbox_z"),
]