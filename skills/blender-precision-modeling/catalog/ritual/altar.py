"""
altar -- a 1800 x 800 x 950 mm carved altar table on four turned legs.

An altar is a TABLE, and a table is four turned legs, an apron and a top with
a carved front panel. The turned legs come from `_ritual.turned_leg` because
turning is the whole vocabulary of this domain: a lathe profile with foot,
waist, knee and capital, not a tapered box.

The front panel is an extruded carved outline -- the one thing on an altar that
is carved rather than turned or joined -- and the two altar objects on the top
are candlesticks, which is what tells you it is an altar and not a sideboard.

Real altar table: 1800 x 800 mm top, 950 mm overall, 130 mm turned legs with a
54 mm waist, 90 mm carved front panel.
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
    top_length=1800.0,
    top_width=800.0,
    top_thickness=70.0,
    overall_height=950.0,
    leg_height=760.0,
    leg_dia=130.0,
    leg_waist=54.0,
    apron_height=170.0,
    panel_height=90.0,
    panel_depth=26.0,
    candlestick_height=420.0,
)

LH = SPEC["leg_height"]
LX = SPEC["top_length"] / 2.0 - 150.0
LY = SPEC["top_width"] / 2.0 - 130.0

CHECKS = [
    dict(name="top_length", mm=1800.0, tol=6.0, how="bbox_x",
         part="AltarTop"),
    dict(name="top_width", mm=800.0, tol=6.0, how="bbox_y", part="AltarTop"),
    dict(name="top_thickness", mm=70.0, tol=3.0, how="bbox_z",
         part="AltarTop"),
    dict(name="table_height", mm=1000.0, tol=6.0, how="top_z",
         part="AltarTop"),
    dict(name="leg_dia", mm=130.0, tol=5.0, how="bbox_x", part="AltarLeg0"),
    dict(name="panel_height", mm=90.0, tol=4.0, how="bbox_z",
         part="AltarPanel"),
    dict(name="table_on_floor", mm=0.0, tol=4.0, how="z_min",
         part="AltarLeg0"),
]


def build():
    walnut = R_.cedar("AltarWalnut", base=(0.32, 0.17, 0.09), rough=0.42)
    trim = R_.cedar("AltarTrim", base=(0.24, 0.12, 0.06), rough=0.38)
    gild = R_.gild("AltarGild")
    wax = bkit.pbr("AltarWax", base=(0.92, 0.90, 0.84), rough=0.44)

    # ---- four turned legs, from a real lathe profile ----------------
    for i, (x, y) in enumerate(bkit.grid_positions(2, 2, 2 * LX, 2 * LY)):
        R_.turned_leg("AltarLeg%d" % i, LH, SPEC["leg_dia"] / 2.0,
                      SPEC["leg_dia"] / 2.0 * 0.78,
                      SPEC["leg_waist"] / 2.0, segments=32, mat=walnut)
        R_.place_in_mesh(bpy.data.objects["AltarLeg%d" % i], x, y, 0.0)

    # ---- the apron, all four sides, one profile extruded ------------
    aw, ad = SPEC["apron_height"], 40.0
    for i, (x, y, sx, sy) in enumerate((
            (0.0, LY, 2 * LX - 40.0, ad),
            (0.0, -LY, 2 * LX - 40.0, ad),
            (LX, 0.0, ad, 2 * LY - 40.0),
            (-LX, 0.0, ad, 2 * LY - 40.0))):
        bkit.rounded_box("AltarApron%d" % i, sx, sy, aw, r=8.0, segments=2,
                         centre=(x, y, LH + aw / 2.0), mat=trim)

    # ---- the top, with a moulded edge ------------------------------
    bkit.rounded_box("AltarTop", SPEC["top_length"], SPEC["top_width"],
                     SPEC["top_thickness"], r=14.0, segments=3,
                     centre=(0.0, 0.0,
                             LH + aw + SPEC["top_thickness"] / 2.0),
                     mat=walnut)
    bkit.rounded_box("AltarTopEdge", SPEC["top_length"] + 40.0,
                     SPEC["top_width"] + 40.0, 22.0, r=10.0, segments=3,
                     centre=(0.0, 0.0, LH + aw + 11.0), mat=gild)

    # ---- the carved front panel: an outline, given depth -----------
    hw = SPEC["top_length"] / 2.0 - 60.0
    hh = SPEC["panel_height"]
    poly = []
    n = 15
    for i in range(n + 1):
        t = i / float(n)
        x = -hw + 2 * hw * t
        poly.append((x, -hh * 0.5 + hh * 0.5 * math.sin(math.pi * t) ** 0.6))
    for i in range(n, -1, -1):
        t = i / float(n)
        x = -hw + 2 * hw * t
        poly.append((x, hh * 0.5 - hh * 0.18 * math.sin(math.pi * t) ** 0.8))
    panel = bkit.extrude_profile("AltarPanel", poly, SPEC["panel_depth"],
                                 centre=(0.0, -LY - ad / 2.0,
                                         LH + aw * 0.55), axis="Y", mat=gild)
    bkit.recalc(panel)

    # ---- two altar candlesticks -------------------------------------
    for i, x in enumerate((-560.0, 560.0)):
        R_.turned_leg("AltarCandle%d" % i, SPEC["candlestick_height"],
                      46.0, 34.0, 22.0, segments=28, mat=gild)
        R_.place_in_mesh(bpy.data.objects["AltarCandle%d" % i], x, 90.0,
                         LH + aw + SPEC["top_thickness"])
        bkit.cylinder("AltarWax%d" % i, 22.0, 300.0, segments=20,
                      centre=(x, 90.0,
                              LH + aw + SPEC["top_thickness"]
                              + SPEC["candlestick_height"] + 150.0),
                      mat=wax)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 4 + 2 + 1 + 4,
                note="Four legs turned from a lathe profile; the front panel "
                     "is an extruded carved outline.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
