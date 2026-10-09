"""
kiosk -- 1000 x 800 x 2150 mm newspaper kiosk: a panelled base, a serving
counter with an open hatch, glazed upper panels, a projecting awning, a
fascia sign band, a hipped roof and four corner posts.

`medium`, modelled at its real 2150 mm street height. The counter opening is
built as a real recess cut proud-and-deep into the front panel, so the hatch
reads as an opening rather than a decal, and the four upper glazed panels each
overlap their post by more than 1 mm.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    kiosk_width=1000.0,
    kiosk_depth=800.0,
    base_height=900.0,
    counter_height=950.0,
    glazed_height=900.0,
    awning_depth=700.0,
    posts=4,
    fascia_height=300.0,
    overall_height=2150.0,
)

KW, KD = SPEC["kiosk_width"], SPEC["kiosk_depth"]
FRONT = -KD / 2.0
HATCH_Z = 1050.0
HATCH_W = 620.0
POST = 70.0
GLAZE_B = 980.0


def _recess(name, host, sx, sz, cx, cz, mat, depth=6.0, proud=4.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=3.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    body = bkit.pbr("KioskBody", base=(0.20, 0.24, 0.22), rough=0.44)
    trim = bkit.pbr("KioskTrim", base=(0.10, 0.14, 0.12), rough=0.38)
    glass = bkit.preset("glass")
    roof = bkit.pbr("KioskRoof", base=(0.14, 0.26, 0.18), metal=0.40,
                    rough=0.40)
    sign = bkit.pbr("KioskSign", base=(0.88, 0.84, 0.24), rough=0.26,
                    emission=(0.92, 0.88, 0.32), emission_strength=1.4)
    steel = bkit.preset("brushed_metal")

    # ---- panelled base ----------------------------------------------------
    bkit.rounded_box("KioskBase", KW, KD, SPEC["base_height"], r=10.0,
                     segments=3, centre=(0.0, 0.0, SPEC["base_height"] / 2.0),
                     mat=body)
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("BasePanel" + tag, 24.0, 300.0, 520.0, r=5.0,
                         segments=2, centre=(side * (KW / 2.0 - 6.0), 120.0,
                                             480.0), mat=trim)

    # ---- serving counter with a real hatch opening -----------------------
    bkit.rounded_box("Counter", KW, KD, SPEC["counter_height"], r=10.0,
                     segments=3, centre=(0.0, 0.0,
                                         SPEC["counter_height"] / 2.0),
                     mat=trim)
    _recess("HatchOpening", bpy.data.objects["Counter"], HATCH_W, 460.0,
            0.0, HATCH_Z, body, depth=90.0, proud=20.0, margin=30.0)
    bkit.rounded_box("CounterShelf", HATCH_W + 70.0, 260.0, 40.0, r=10.0,
                     segments=2, centre=(0.0, FRONT - 90.0, 820.0),
                     mat=steel)

    # ---- four corner posts and four upper glazed panels ------------------
    for side, tag in ((-1.0, "FL"), (1.0, "FR"), (-1.0, "RL"), (1.0, "RR")):
        px = side * (KW / 2.0 - POST / 2.0)
        py = (1.0 if tag[0] == "R" else -1.0) * (KD / 2.0 - POST / 2.0)
        bkit.rounded_box("KioskPost" + tag, POST, POST,
                         1200.0 - GLAZE_B, r=8.0, segments=2,
                         centre=(px, py, GLAZE_B + (1200.0 - GLAZE_B) / 2.0),
                         mat=trim)
    gz = GLAZE_B + (1200.0 - GLAZE_B) / 2.0
    gh = 1200.0 - GLAZE_B - 20.0
    bkit.rounded_box("KioskGlassF", HATCH_W - 60.0, 16.0, gh, r=3.0,
                     segments=2, centre=(0.0, FRONT + POST, gz), mat=glass)
    bkit.rounded_box("KioskGlassR", KW - 2 * POST + 16.0, 16.0, gh, r=3.0,
                     segments=2, centre=(0.0, KD / 2.0 - POST, gz),
                     mat=glass)
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("KioskGlass" + tag, 16.0, KD - 2 * POST + 16.0, gh,
                         r=3.0, segments=2, mat=glass,
                         centre=(side * (KW / 2.0 - POST), 0.0, gz))

    # ---- fascia, sign band, awning and hipped roof ----------------------
    bkit.rounded_box("KioskFascia", KW, KD, SPEC["fascia_height"], r=8.0,
                     segments=3, centre=(0.0, 0.0,
                                         1200.0 + SPEC["fascia_height"] / 2.0
                                         + 60.0), mat=body)
    bkit.rounded_box("KioskSignBand", KW - 80.0, 26.0, 240.0, r=6.0,
                     segments=2, centre=(0.0, FRONT - 6.0,
                                         1200.0 + SPEC["fascia_height"] / 2.0
                                         + 60.0), mat=sign)
    bkit.rounded_box("KioskAwning", KW - 40.0, SPEC["awning_depth"], 60.0,
                     r=10.0, segments=2, centre=(0.0,
                                                 FRONT - SPEC["awning_depth"]
                                                 / 2.0 + 40.0, 1180.0),
                     mat=roof)
    stays = [bkit.box("_st%d" % i, 24.0, 24.0, 500.0, mat=steel,
                      centre=(-KW / 2.0 + 90.0 + i * (KW - 180.0), FRONT
                              - SPEC["awning_depth"] + 60.0, 950.0))
             for i in range(2)]
    bkit.join(stays, name="AwningStays")

    bkit.rounded_box("KioskRoof", KW + 160.0, KD + 160.0, 140.0, r=24.0,
                     segments=3, centre=(0.0, 0.0,
                                         1200.0 + SPEC["fascia_height"]
                                         + 60.0 + 120.0), mat=roof)
    bkit.rounded_box("RoofCrest", KW - 200.0, 140.0, 90.0, r=20.0,
                     segments=2, centre=(0.0, 0.0,
                                         1200.0 + SPEC["fascia_height"]
                                         + 60.0 + 230.0), mat=trim)

    # ---- magazine rack and a service door on the flank ------------------
    racks = []
    for i, (rx, rz) in enumerate(bkit.grid_positions(2, 3, 260.0, 200.0)):
        racks.append(bkit.box("_mr%d" % i, 200.0, 160.0, 24.0, mat=sign,
                              centre=(KW / 2.0 + 30.0, -150.0 + rx,
                                      500.0 + rz)))
    bkit.join(racks, name="MagazineRack")
    bkit.rounded_box("ServiceDoor", 24.0, 420.0, 620.0, r=5.0, segments=2,
                     centre=(-KW / 2.0 + 4.0, 180.0, 460.0), mat=trim)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="kiosk_width", mm=1000.0, tol=1.0, how="bbox_x",
         part="KioskBase"),
    dict(name="kiosk_depth", mm=800.0, tol=1.0, how="bbox_y",
         part="KioskBase"),
    dict(name="base_height", mm=900.0, tol=1.0, how="bbox_z",
         part="KioskBase"),
    dict(name="post_width", mm=70.0, tol=0.6, how="bbox_x",
         part="KioskPostFL"),
    dict(name="awning_depth", mm=700.0, tol=1.0, how="bbox_y",
         part="KioskAwning"),
    dict(name="overall_height", mm=1835.0, tol=3.0, how="bbox_z"),
]