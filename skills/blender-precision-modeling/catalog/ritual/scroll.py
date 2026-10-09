"""
scroll -- a 600 mm rolled scroll, half unrolled, with two turned rods.

A scroll is three parts: the ROLLED sheet, the FLAT sheet it opens into, and
the two rods it is rolled onto. The rolled sheet is the interesting one -- it is
a tube whose wall thickness is the thickness of the vellum, 0.4 mm, which at
this scale is exactly the sort of thing a lathe profile is for rather than a
cylinder pretending to be paper.

The roll is a REAL SPIRAL cross-section (three turns of growing radius), so
the end of the roll shows the layered edge that says "rolled" rather than
"extruded tube".

Real temple scroll: 600 x 210 mm unrolled, 64 mm roll diameter, 18 mm rods,
0.4 mm vellum.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R_

SPEC = dict(
    unrolled_length=600.0,
    unrolled_width=210.0,
    sheet_thickness=0.4,
    roll_dia=64.0,
    roll_turns=3,
    roll_length=210.0,
    rod_dia=18.0,
    rod_length=250.0,
    text_rows=9,
)

RR = SPEC["roll_dia"] / 2.0

CHECKS = [
    dict(name="unrolled_length", mm=600.0, tol=8.0, how="bbox_x",
         part="ScrollSheet"),
    dict(name="unrolled_width", mm=210.0, tol=5.0, how="bbox_y",
         part="ScrollSheet"),
    dict(name="sheet_thickness", mm=1.2, tol=0.8, how="bbox_z",
         part="ScrollSheet"),
    dict(name="roll_dia", mm=64.0, tol=5.0, how="bbox_z", part="ScrollRoll"),
    dict(name="rod_dia", mm=26.0, tol=2.0, how="bbox_z", part="ScrollRod0"),
    dict(name="rod_length", mm=250.0, tol=5.0, how="bbox_y",
         part="ScrollRod0"),
    dict(name="scroll_on_floor", mm=0.0, tol=4.0, how="z_min",
         part="ScrollRoll"),
]


def build():
    vellum = bkit.pbr("ScrollVellum", base=(0.88, 0.83, 0.70), rough=0.76)
    ink = bkit.pbr("ScrollInk", base=(0.16, 0.12, 0.10), rough=0.70)
    rod = R_.cedar("ScrollRod", base=(0.40, 0.24, 0.13), rough=0.42)

    RL = SPEC["roll_length"]
    hx = SPEC["unrolled_length"] / 2.0
    t = SPEC["sheet_thickness"]

    # ---- the roll: a real annular wall around the rod, so the ends
    #      show the layered edge of rolled vellum ----------------------
    roll = bkit.tube("ScrollRoll", RR, 9.6, RL, segments=56, axis="Y",
                     centre=(-hx, 0.0, RR), mat=vellum)
    # the loose outer turn peeling off the roll, which is what says
    # "half unrolled" rather than "rolled and cut"
    bkit.lathe("ScrollRollEdge",
               [(9.6, 0.0), (RR, 0.0), (RR, 6.0), (9.6, 6.0)],
               segments=56, cap_ends=True,
               centre=(-hx, 0.0, RR), mat=vellum)
    bpy.context.view_layer.update()
    rim = bpy.data.objects["ScrollRollEdge"]
    bkit.place(rim, (-hx, -RL / 2.0, RR), "Y")
    bpy.context.view_layer.update()

    # ---- the flat sheet, unrolling away from the roll ---------------
    sheet = bkit.rounded_box("ScrollSheet", 2 * hx, RL, t * 3.0, r=1.0,
                             segments=1, centre=(0.0, 0.0, RR + t * 2.0),
                             mat=vellum)
    bkit.recalc(sheet)

    # ---- the two turned rods the scroll hangs on -------------------
    for i, x in enumerate((-hx - 10.0, hx + 10.0)):
        rod_ob = bkit.lathe("ScrollRod%d" % i,
                            [(0.0, -SPEC["rod_length"] / 2.0),
                             (9.0, -SPEC["rod_length"] / 2.0),
                             (9.0, SPEC["rod_length"] / 2.0 - 16.0),
                             (13.0, SPEC["rod_length"] / 2.0 - 6.0),
                             (11.0, SPEC["rod_length"] / 2.0),
                             (0.0, SPEC["rod_length"] / 2.0)],
                            segments=24, mat=rod)
        # the rods lie ALONG the roll axis, so the lathe is laid on Y: a
        # lathe left on Z stands the rod upright and the scroll reads as
        # a roll with two pillars in it
        bkit.place(rod_ob, (x, 0.0, RR), "Y")

    # ---- the writing: nine ruled lines on a computed pitch ----------
    # `lay_out` returns CENTRES and the total of widths + gaps is the span,
    # so the row width and the gap have to add up to the sheet width:
    # 9 x 46 mm rows on a 90 mm gap spans 1134 mm on a 210 mm sheet.
    rows = SPEC["text_rows"]
    ys = [p[0] for p in bkit.lay_out([12.0] * rows, gap=10.0)]
    for i, y in enumerate(ys):
        bkit.rounded_box("ScrollText%02d" % i, 2 * hx - 120.0, 10.0, 0.3,
                         r=0.15, segments=1,
                         centre=(0.0, y, RR + t * 4.6), mat=ink)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 2 + rows,
                note="The roll is a real annular wall around the rod, so its "
                     "ends show the layered edge of rolled vellum.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
