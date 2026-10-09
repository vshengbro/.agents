"""
fume_hood -- 1500 x 840 x 2390 mm laboratory fume cupboard: base cabinet,
worktop, a raised glass sash with its rails and pull, two side uprights, a
service header with two taps, a rear baffle, a sink and a roof exhaust collar.

Large is the inverse of the science instruments: no display, no keypad, no
recesses. What sells a fume hood is the street furniture of a laboratory --
correct 1500 mm cabinet width, a 200 mm worktop overhang, a real sash you can
see through, and perforated return grilles with an actual hole count rather
than a texture.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    cabinet_width=1500.0,
    cabinet_depth=800.0,
    cabinet_height=880.0,
    worktop_depth=840.0,
    sash_width=1400.0,
    sash_height=500.0,
    header_height=300.0,
    exhaust_collar_diameter=320.0,
    overall_height=2390.0,
)

CW, CD, CH = (SPEC["cabinet_width"], SPEC["cabinet_depth"],
              SPEC["cabinet_height"])
FRONT = -CD / 2.0                    # -400
SASH_Y = FRONT + 14.0                # sash plane, just inside the opening
SASH_Z = 1250.0
HEADER_Z = 2070.0


def build():
    shell = bkit.pbr("HoodShell", base=(0.84, 0.84, 0.82), rough=0.36)
    liner = bkit.pbr("HoodLiner", base=(0.76, 0.77, 0.78), rough=0.30)
    dark = bkit.pbr("HoodDark", base=(0.075, 0.075, 0.080), rough=0.44)
    steel = bkit.preset("brushed_metal")
    glass = bkit.preset("glass")

    # ---- base cabinet, overlapping the worktop by 1 mm --------------------
    bkit.rounded_box("HoodCabinet", CW, CD, CH, r=6.0, segments=2,
                     centre=(0.0, 0.0, CH / 2.0), mat=shell)
    bkit.rounded_box("Worktop", CW + 40.0, SPEC["worktop_depth"], 42.0,
                     r=6.0, segments=2, centre=(0.0, 0.0, 900.0), mat=dark)

    # ---- lower plinth, recessed so the cabinet appears to float -----------
    bkit.rounded_box("HoodPlinth", CW - 60.0, CD - 60.0, 100.0, r=4.0,
                     segments=2, centre=(0.0, 0.0, 50.0), mat=dark)

    # ---- raised sash: glass, side rails and a full-width pull ------------
    bkit.rounded_box("SashGlass", SPEC["sash_width"], 12.0,
                     SPEC["sash_height"], r=3.0, segments=2,
                     centre=(0.0, SASH_Y, SASH_Z), mat=glass)
    sash_frame = []
    for i, sx in enumerate((-SPEC["sash_width"] / 2.0 + 20.0,
                            SPEC["sash_width"] / 2.0 - 20.0)):
        sash_frame.append(bkit.box("_sr%d" % i, 8.0, 18.0,
                                   SPEC["sash_height"] + 16.0, mat=steel,
                                   centre=(sx, SASH_Y, SASH_Z)))
    sash_frame.append(bkit.box("_sb", SPEC["sash_width"] - 24.0, 18.0, 8.0,
                               mat=steel,
                               centre=(0.0, SASH_Y,
                                       SASH_Z + SPEC["sash_height"] / 2.0)))
    bkit.join(sash_frame, name="SashFrame")
    bkit.cylinder("SashPull", 12.0, SPEC["sash_width"] - 60.0, segments=28,
                  axis="X", centre=(0.0, SASH_Y - 40.0, SASH_Z
                                    - SPEC["sash_height"] / 2.0), mat=steel)
    for side in (-1.0, 1.0):
        bkit.box("SashPullArm%.0f" % side, 12.0, 50.0, 12.0, mat=steel,
                 centre=(side * (SPEC["sash_width"] / 2.0 - 30.0),
                         SASH_Y - 20.0, SASH_Z - SPEC["sash_height"] / 2.0))

    # ---- side uprights carrying the header --------------------------------
    for side in (-1.0, 1.0):
        bkit.rounded_box("Upright%.0f" % side, 40.0, CD, 1000.0, r=5.0,
                         segments=2,
                         centre=(side * (CW / 2.0 - 20.0), 0.0, 1370.0),
                         mat=shell)

    # ---- service header with two taps -------------------------------------
    bkit.rounded_box("HoodHeader", CW, CD, SPEC["header_height"], r=6.0,
                     segments=2, centre=(0.0, 0.0, HEADER_Z), mat=shell)
    taps = []
    for i, (tx, ty) in enumerate(bkit.grid_positions(2, 1, 340.0, 0.0)):
        taps.append(bkit.cylinder("_tap%d" % i, 18.0, 90.0, segments=24,
                                  axis="Z", mat=steel,
                                  centre=(tx, FRONT + 90.0, 1890.0)))
        taps.append(bkit.cylinder("_tapn%d" % i, 12.0, 60.0, segments=20,
                                  axis="Y", mat=steel,
                                  centre=(tx, FRONT + 55.0, 1830.0)))
        taps.append(bkit.cylinder("_taph%d" % i, 6.0, 70.0, segments=16,
                                  axis="Y", mat=steel,
                                  centre=(tx, FRONT + 30.0, 1830.0)))
    bkit.join(taps, name="ServiceTaps")

    # ---- roof exhaust collar, overlapping the header by 10 mm ------------
    bkit.cylinder("ExhaustCollar", SPEC["exhaust_collar_diameter"] / 2.0, 180.0,
                  segments=48, r2=150.0, centre=(0.0, 120.0, 2300.0),
                  mat=steel)

    # ---- rear baffle and a sink bowl in the worktop ----------------------
    bkit.rounded_box("RearBaffle", CW - 80.0, 20.0, 700.0, r=4.0, segments=2,
                     centre=(0.0, CD / 2.0 - 20.0, 1560.0), mat=liner)
    bkit.rounded_box("SinkRim", 400.0, 360.0, 12.0, r=8.0, segments=2,
                     centre=(-380.0, 60.0, 918.0), mat=steel)

    # ---- lower return grille: 24 x 2 real holes --------------------------
    bkit.perforated_panel("ReturnGrille", 24, 2, 22.0, 40.0, 9.0, 540.0, 90.0,
                          5.0, mat=dark)
    bkit.move(bpy.data.objects["ReturnGrille"], 0.0, FRONT + 3.0, 240.0)
    bkit.rounded_box("GrilleFrame", 570.0, 12.0, 120.0, r=4.0, segments=2,
                     centre=(0.0, FRONT + 2.0, 240.0), mat=steel)

    # ---- interior light strip under the header ---------------------------
    bkit.rounded_box("LightStrip", CW - 300.0, 60.0, 30.0, r=6.0, segments=2,
                     centre=(0.0, 40.0, 1900.0),
                     mat=bkit.pbr("HoodLight", base=(0.9, 0.92, 0.95),
                                  rough=0.2,
                                  emission=(0.95, 0.97, 1.0),
                                  emission_strength=2.5))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=17)


CHECKS = [
    dict(name="cabinet_width", mm=1500.0, tol=1.0, how="bbox_x",
         part="HoodCabinet"),
    dict(name="cabinet_depth", mm=800.0, tol=1.0, how="bbox_y",
         part="HoodCabinet"),
    dict(name="worktop_depth", mm=840.0, tol=1.0, how="bbox_y", part="Worktop"),
    dict(name="sash_width", mm=1400.0, tol=1.0, how="bbox_x",
         part="SashGlass"),
    dict(name="exhaust_collar_diameter", mm=320.0, tol=1.0, how="diameter",
         part="ExhaustCollar"),
    dict(name="overall_height", mm=2390.0, tol=3.0, how="bbox_z"),
]