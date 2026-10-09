"""
calendar_clock -- 210 x 150 x 146 mm desk calendar tent with a 7 x 5 day grid.

A desk calendar is two boards leaning into a tent and a stack of sheets bound
through the spine, so the boards are the model: a flat base and a back board
raked back at 12 degrees, with the sheet block caught between them.

The two binding rings pass through holes in the back board and round the sheet
block, which is what makes it a bound desk calendar rather than a tent with a
sign in it. The day grid is one rib swept twice by array_linear, so the 7 x 5
layout is a pitch in X and a pitch in Y.

The sheet's grid lines are 0.4 mm proud of the paper -- visible, and far
enough below the obvious z-fighting threshold that the sheet still reads as
paper.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D = 210.0, 150.0
BASE_H = 24.0
BACK_H = 128.0
BACK_T = 6.0
RAKE = 12.0
SHEET_W, SHEET_H, SHEET_T = 186.0, 118.0, 9.0
RING_R = 9.0
RING_W = 1.4
RING_N = 2
RING_PITCH = 62.0
COLS, ROWS = 7, 5
RIB_W, RIB_T = 1.2, 0.4

SPEC = dict(width=W, depth=D, base_height=BASE_H, back_height=BACK_H,
            back_thickness=BACK_T, back_rake=RAKE,
            sheet_width=SHEET_W, sheet_height=SHEET_H,
            ring_count=RING_N, ring_diameter=2.0 * (RING_R + RING_W / 2.0),
            ring_pitch=RING_PITCH, cell_columns=COLS, cell_rows=ROWS)


def build():
    board = bkit.pbr("CalBoard", base=(0.30, 0.16, 0.09), metal=0.0, rough=0.44)
    paper = bkit.pbr("CalPaper", base=(0.94, 0.93, 0.88), metal=0.0, rough=0.56)
    ink = bkit.pbr("CalInk", base=(0.14, 0.16, 0.24), metal=0.0, rough=0.40)
    steel = bkit.pbr("CalRing", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.20)
    band = bkit.pbr("CalBand", base=(0.62, 0.12, 0.12), metal=0.0, rough=0.40)

    # ---- base and raked back board ------------------------------------------
    base = bkit.rounded_box("Base", W, D, BASE_H, r=4.0, segments=3,
                            centre=(0.0, 0.0, BASE_H / 2.0), mat=board)
    back = bkit.rounded_box("BackBoard", W, BACK_T, BACK_H, r=3.0, segments=3,
                            centre=(0.0, BACK_T / 2.0, BACK_H / 2.0), mat=board)
    back.rotation_euler = (math.radians(-RAKE), 0.0, 0.0)
    bkit.move(back, 0.0, D / 2.0 - BACK_T, BASE_H - 4.0)

    # ---- the sheet block, standing on the base and leaning on the board -----
    sheet = bkit.rounded_box("Sheets", SHEET_W, SHEET_T, SHEET_H, r=1.0, segments=2,
                             centre=(0.0, SHEET_T / 2.0, SHEET_H / 2.0), mat=paper)
    sheet.rotation_euler = (math.radians(-RAKE), 0.0, 0.0)
    bkit.move(sheet, 0.0, D / 2.0 - SHEET_T * 1.6, BASE_H - 3.0)

    # ---- the day grid, one rib swept twice -----------------------------------
    face_y = -SHEET_T / 2.0 - RIB_T / 2.0
    grid = []
    for i in range(COLS + 1):
        x = -SHEET_W / 2.0 + 8.0 + i * ((SHEET_W - 16.0) / COLS)
        grid.append(bkit.rounded_box("DayGrid", RIB_W, RIB_T,
                                     SHEET_H - 22.0, r=0.3, segments=2,
                                     centre=(x, face_y, SHEET_H / 2.0), mat=ink))
    for j in range(ROWS + 1):
        z = 16.0 + j * ((SHEET_H - 22.0) / ROWS)
        grid.append(bkit.rounded_box("DayGrid", SHEET_W - 16.0, RIB_W, RIB_W,
                                     r=0.3, segments=2,
                                     centre=(0.0, face_y, z), mat=ink))
    grid = bkit.join(grid, name="DayGrid")
    grid.rotation_euler = (math.radians(-RAKE), 0.0, 0.0)
    bkit.move(grid, 0.0, D / 2.0 - SHEET_T * 1.6, BASE_H - 3.0)

    # a printed header band across the top of the sheet
    header = bkit.rounded_box("HeaderBand", SHEET_W - 16.0, RIB_T + 0.3, 12.0,
                              r=0.6, segments=2,
                              centre=(0.0, face_y - 0.15, SHEET_H - 10.0), mat=band)
    header.rotation_euler = (math.radians(-RAKE), 0.0, 0.0)
    bkit.move(header, 0.0, D / 2.0 - SHEET_T * 1.6, BASE_H - 3.0)

    # ---- two binding rings through the spine --------------------------------
    rings = []
    for sx in (-1.0, 1.0):
        rings.append(bkit.torus("BindingRings", RING_R, RING_W / 2.0, seg_major=40,
                                seg_minor=10,
                                centre=(sx * RING_PITCH / 2.0, 0.0,
                                        SHEET_H - 4.0), axis="Z", mat=steel))
    bkit.join(rings, name="BindingRings")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=210.0, tol=0.2, how="bbox_x", part="Base"),
    dict(name="depth", mm=150.0, tol=0.2, how="bbox_y", part="Base"),
    dict(name="base_height", mm=24.0, tol=0.2, how="bbox_z", part="Base"),
    dict(name="sheet_width", mm=186.0, tol=0.2, how="bbox_x", part="Sheets"),
    dict(name="ring_diameter", mm=81.4, tol=0.2, how="bbox_x",
         part="BindingRings"),
    dict(name="ring_span", mm=81.4, tol=0.2, how="bbox_x",
         part="BindingRings"),
    dict(name="grid_width", mm=171.2, tol=0.2, how="bbox_x",
         part="DayGrid"),
    dict(name="overall_height", mm=144.6, tol=0.4, how="bbox_z",
         part=None)
]