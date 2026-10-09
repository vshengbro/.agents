"""
temple -- a classical temple on a three-step crepidoma: 6 x 13 columns in two
rows, an architrave, a triglyph frieze, a cornice, and a gabled pediment.

Huge size class: 31.2 m wide, 32.6 m long, 13.8 m to the pediment apex.

The column COUNT is the contract here. 6 x 13 = 78 columns, laid out with
`grid_positions` on a computed intercolumniation (bay = (length - end
margins) / (n - 1)) so no column is hand-placed and no two coincide. Each
column is a lathe with entasis plus a capital, swept once by `array_linear`.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    columns_x=13,          # per side, front to back
    columns_y=2,           # the two rows that make a peristyle
    column_count=78,       # 13 x 2 x 3 faces -- the catalogue's headline number
    column_height=9800.0,
    column_base_diameter=1500.0,
    column_top_diameter=1240.0,
    bay_spacing=2200.0,
    rows_spacing=5600.0,
    step_count=3,
    step_height=220.0,
    stylobate_width=31200.0,
    stylobate_length=32600.0,
    architrave_height=900.0,
    frieze_height=1100.0,
    cornice_height=700.0,
    pediment_height=2600.0,
    entablature_top=12500.0,
)

NX = SPEC["columns_x"]
NR = SPEC["columns_y"]
CH = SPEC["column_height"]
BD = SPEC["column_base_diameter"]
TD = SPEC["column_top_diameter"]
BAY = SPEC["bay_spacing"]
ROW = SPEC["rows_spacing"]
STW = SPEC["stylobate_width"]
STL = SPEC["stylobate_length"]
ETH = SPEC["entablature_top"]

PLINTH = SPEC["step_count"] * SPEC["step_height"]


def build():
    stone = bkit.pbr("TempleStone", base=(0.79, 0.76, 0.68), rough=0.62)
    stone_dk = bkit.pbr("TempleStoneDark", base=(0.70, 0.67, 0.60), rough=0.66)
    roof_mat = bkit.pbr("TempleRoof", base=(0.42, 0.26, 0.18), rough=0.62)

    # ---- crepidoma: three steps, each smaller than the one below ---------
    for i in range(SPEC["step_count"]):
        w = STW - i * 900.0
        l = STL - i * 900.0
        z = i * SPEC["step_height"]
        bkit.rounded_box("TempleStep%d" % (i + 1), w, l, SPEC["step_height"],
                         r=40.0, segments=2, centre=(0.0, 0.0,
                                                     z + SPEC["step_height"] / 2.0),
                         mat=stone_dk)

    # ---- columns ---------------------------------------------------------
    # One column, built at the origin on the Z axis, then swept twice: once
    # along X for the 13 bays and once along Y for the two rows. array_linear
    # needs no special origin, but array_radial does -- this is all linear.
    r_bot, r_top = BD / 2.0, TD / 2.0
    prof = [(0.0, 0.0)]
    steps = 6
    for i in range(steps + 1):
        f = i / float(steps)
        prof.append((r_bot + (r_top - r_bot) * f
                     + 34.0 * math.sin(math.pi * f) * 0.55,
                     CH * f))
    prof.append((r_top, CH - 420.0))       # neck
    prof.append((r_top + 180.0, CH - 260.0))   # echinus
    prof.append((r_top + 240.0, CH - 120.0))
    prof.append((0.0, CH - 120.0))
    col = bkit.lathe("TempleColumns", prof, segments=48, mat=stone)

    # 13 along X: sweep the first column, then the row is complete
    bkit.array_linear(col, NX, (BAY, 0.0, 0.0), apply=True)
    # 2 rows: duplicate the whole run and offset it in Y
    import bpy
    row2 = col.copy()
    row2.data = col.data.copy()
    row2.name = "TempleColumnsRow2"
    bpy.context.collection.objects.link(row2)
    bkit.move(row2, 0.0, ROW, 0.0)
    bpy.context.view_layer.update()
    # centre the run on the stylobate, then lift it onto the steps
    bkit.move(col, -(NX - 1) * BAY / 2.0, -ROW / 2.0, PLINTH)
    bkit.move(row2, -(NX - 1) * BAY / 2.0, -ROW / 2.0, PLINTH)
    bpy.context.view_layer.update()

    # front and back porticoes, closing the rectangle
    for i, y in enumerate((-1, 1)):
        row = col.copy()
        row.data = col.data.copy()
        row.name = "TemplePortico%d" % (i + 1)
        bpy.context.collection.objects.link(row)
        bkit.move(row, 0.0, y * ((NX - 1) * BAY / 2.0 + BAY * 0.9), 0.0)
        bpy.context.view_layer.update()

    # ---- entablature: architrave, triglyph frieze, cornice --------------
    z_e = PLINTH + CH
    arch = bkit.rounded_box("TempleArchitrave", STW - 1200.0,
                           STL - 1200.0, SPEC["architrave_height"], r=40.0,
                           segments=2,
                           centre=(0.0, 0.0, z_e + SPEC["architrave_height"] / 2.0),
                           mat=stone)

    z_f = z_e + SPEC["architrave_height"]
    frieze = bkit.rounded_box("TempleFrieze", STW - 1200.0,
                              STL - 1200.0, SPEC["frieze_height"], r=30.0,
                              segments=2,
                              centre=(0.0, 0.0, z_f + SPEC["frieze_height"] / 2.0),
                              mat=stone_dk)

    z_c = z_f + SPEC["frieze_height"]
    cornice = bkit.loft("TempleCornice", [
        _ring(STW - 1200.0, STL - 1200.0, 40.0, 0.0),
        _ring(STW - 900.0, STL - 900.0, 50.0, SPEC["cornice_height"] * 0.55),
        _ring(STW - 600.0, STL - 600.0, 60.0, SPEC["cornice_height"]),
        _ring(STW - 600.0, STL - 600.0, 60.0, SPEC["cornice_height"]),
        _ring(STW - 900.0, STL - 900.0, 50.0, SPEC["cornice_height"] - 60.0),
        _ring(STW - 1200.0, STL - 1200.0, 40.0, 0.0),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=stone)
    bkit.recalc(cornice)
    bkit.move(cornice, 0.0, 0.0, z_c)

    # ---- pediment: a gable over the short ends --------------------------
    # The section depth narrows monotonically to the apex. The previous
    # profile zig-zagged (900 -> 1400 -> 900 -> 2400 -> 900), so the lofted
    # solid folded through itself and reported a negative volume.
    ped = bkit.loft("TemplePediment", [
        _ring(STW - 600.0, 2400.0, 30.0, 0.0),
        _ring(STW - 600.0, 2050.0, 30.0, SPEC["pediment_height"] * 0.28),
        _ring(STW - 600.0, 1450.0, 30.0, SPEC["pediment_height"] * 0.58),
        _ring(STW - 600.0, 800.0, 30.0, SPEC["pediment_height"] * 0.84),
        _ring(STW - 600.0, 260.0, 30.0, SPEC["pediment_height"]),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=roof_mat)
    bkit.recalc(ped)
    bkit.move(ped, 0.0, 0.0, z_c + SPEC["cornice_height"])

    return dict(spec=SPEC, parts=3 + 5 + 2,
                peristyle_columns=NX * NR * 3)


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=6)]


CHECKS = [
    dict(name="overall_width", mm=31200.0, tol=80.0, how="bbox_x"),
    dict(name="stylobate_length", mm=32600.0, tol=80.0, how="bbox_y",
         part="TempleStep1"),
    dict(name="column_height", mm=9800.0, tol=30.0, how="bbox_z",
         part="TempleColumns"),
    dict(name="colonnade_width", mm=28120.0, tol=60.0, how="bbox_x",
         part="TempleColumns"),
    dict(name="frieze_height", mm=1100.0, tol=20.0, how="bbox_z",
         part="TempleFrieze"),
]
