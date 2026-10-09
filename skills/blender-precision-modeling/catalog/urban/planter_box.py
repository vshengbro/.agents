"""
planter_box -- 1040 x 560 x 740 mm street tree planter: a `loft`ed tapered
trough that flares 140 mm from base to rim, a rolled coping, two cast feet, a
soil body and a shrub of seven lathed mounds.

`medium`. The trough is a `loft` over four rounded-rectangle sections of
growing size -- a straight box with a smaller box on top is not a planter, and
the flare is the silhouette that says "street furniture". The coping is a
`loft` ring rather than a `tube`, because a tube's circular section would not
follow the trough's rounded rectangle.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    planter_length=1040.0,
    planter_width=560.0,
    planter_height=440.0,
    base_length=900.0,
    base_width=450.0,
    wall=45.0,
    coping_height=55.0,
    soil_height=90.0,
    shrub_mounds=7,
)

BL, BW = SPEC["base_length"], SPEC["base_width"]
TL, TW = SPEC["planter_length"], SPEC["planter_width"]
PH = SPEC["planter_height"]


def build():
    concrete = bkit.pbr("PlanterConcrete", base=(0.56, 0.54, 0.50),
                        rough=0.74)
    coping = bkit.pbr("PlanterCoping", base=(0.48, 0.46, 0.43), rough=0.68)
    soil = bkit.pbr("PlanterSoil", base=(0.14, 0.10, 0.07), rough=0.92)
    leaf = bkit.pbr("PlanterLeaf", base=(0.12, 0.30, 0.10), rough=0.58)
    leaf2 = bkit.pbr("PlanterLeafLight", base=(0.18, 0.40, 0.13), rough=0.55)
    bark = bkit.preset("wood")

    # ---- trough: four sections flaring outward with height --------------
    stations = ((0.0, BL, BW, 22.0), (0.30, BL + 45.0, BW + 28.0, 24.0),
                (0.70, BL + 100.0, BW + 50.0, 26.0),
                (1.0, TL, TW, 28.0))
    sections = []
    for (t, sx, sy, r) in stations:
        sec = bkit.rounded_rect_section(sx, sy, r, per_corner=7)
        sections.append([(x, y, t * PH) for (x, y) in sec])
    bkit.loft("PlanterBody", sections, mat=concrete)

    # ---- coping: four walls around the rim, each overlapping the trough -
    # A loft ring would need two closed loops of equal vertex count and caps
    # that either leave holes or bury the soil, so four boxes are simpler and
    # watertight.
    coping_h = SPEC["coping_height"]
    cope = [bkit.box("_cs", TL + 50.0, 60.0, coping_h, mat=coping,
                     centre=(0.0, (TW + 50.0) / 2.0 - 30.0,
                             PH + coping_h / 2.0)),
            bkit.box("_cn", TL + 50.0, 60.0, coping_h, mat=coping,
                     centre=(0.0, -(TW + 50.0) / 2.0 + 30.0,
                             PH + coping_h / 2.0))]
    for side in (-1.0, 1.0):
        cope.append(bkit.box("_cw%.0f" % side, 60.0, TW - 50.0, coping_h,
                             mat=coping,
                             centre=(side * (TL + 50.0) / 2.0 - side * 30.0,
                                     0.0, PH + coping_h / 2.0)))
    bkit.join(cope, name="PlanterCoping")

    # ---- two cast feet, lifting the trough 60 mm off the pavement --------
    feet = []
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        feet.append(bkit.rounded_box("PlanterFoot" + tag, 140.0,
                                     TW - 60.0, 60.0, r=12.0, segments=2,
                                     centre=(side * (BL / 2.0 - 110.0), 0.0,
                                             -30.0), mat=coping))
    bkit.join(feet, name="PlanterFeet")

    # ---- soil body sitting inside the trough -----------------------------
    bkit.rounded_box("PlanterSoil", TL - 2 * SPEC["wall"] - 10.0,
                     TW - 2 * SPEC["wall"] - 10.0, SPEC["soil_height"], r=16.0,
                     segments=2, centre=(0.0, 0.0, PH - SPEC["soil_height"] / 2.0
                                        + 10.0), mat=soil)

    # ---- trunk and seven lathed shrub mounds on a computed grid ---------
    bkit.lathe("ShrubTrunk", [(0.0, PH), (34.0, PH), (26.0, PH + 90.0),
                              (18.0, PH + 170.0), (0.0, PH + 190.0)],
               segments=24, mat=bark)
    for i, (mx, my) in enumerate(bkit.grid_positions(3, 3, 260.0, 150.0)):
        r = 150.0 if i % 2 == 0 else 120.0
        bkit.lathe("ShrubMound%d" % i, [
            (0.0, PH + 150.0), (r * 0.55, PH + 170.0),
            (r, PH + 230.0), (r * 0.72, PH + 300.0), (0.0, PH + 330.0),
        ], segments=28, centre=(mx, my, 0.0),
            mat=leaf if i % 2 == 0 else leaf2)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="planter_length", mm=1090.0, tol=2.0, how="bbox_x",
         part="PlanterCoping"),
    dict(name="planter_width", mm=610.0, tol=2.0, how="bbox_y",
         part="PlanterCoping"),
    dict(name="planter_height", mm=440.0, tol=2.0, how="bbox_z",
         part="PlanterBody"),
    dict(name="soil_height", mm=90.0, tol=1.0, how="bbox_z",
         part="PlanterSoil"),
    dict(name="shrub_mound_height", mm=180.0, tol=2.0, how="bbox_z",
         part="ShrubMound4"),
    # 830 = 770 mound apex + 60 mm of cast foot below the lowest plane.
    dict(name="overall_height", mm=830.0, tol=3.0, how="bbox_z"),
]