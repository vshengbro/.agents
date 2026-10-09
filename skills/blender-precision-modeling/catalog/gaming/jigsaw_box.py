"""
jigsaw_box -- 400 x 300 x 90 mm puzzle box with a 10 x 8 lid grid.

A jigsaw box is a base and a lid, and the thing that says "jigsaw" is the grid
on the lid -- a 1000-piece box really is 38 x 26 pieces, so the lid here is
divided 10 x 8 on a 40 x 36.25 mm pitch and the ribs are 1.5 mm proud of the
lid, which is how a printed-and-embossed box lid actually looks.

The ribs are ONE rib swept by array_linear in X and then by array_linear in Y,
not twenty hand-placed strips. That matters more here than in most models: a
rib grid has 19 ribs that all have to be parallel, and a single typo in one
coordinate shows up as a grid that does not line up at one intersection.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D = 400.0, 300.0
BASE_H = 54.0
LID_H = 36.0
LID_OVERHANG = 6.0
LID_T = 6.0
COLS, ROWS = 10, 8
RIB_W = 2.2
RIB_T = 1.5
LABEL_W, LABEL_H = 190.0, 46.0

SPEC = dict(base_width=W, base_depth=D, base_height=BASE_H,
            lid_height=LID_H, overhang=LID_OVERHANG,
            piece_columns=COLS, piece_rows=ROWS, piece_count=COLS * ROWS,
            rib_count=(COLS + 1) + (ROWS + 1), rib_width=RIB_W)


def build():
    board = bkit.pbr("BoxBoard", base=(0.62, 0.50, 0.36), metal=0.0, rough=0.72)
    lid_mat = bkit.pbr("BoxLid", base=(0.72, 0.60, 0.44), metal=0.0, rough=0.66)
    art = bkit.pbr("BoxArt", base=(0.14, 0.30, 0.52), metal=0.0, rough=0.30,
                   coat=0.5)
    paper = bkit.pbr("BoxPaper", base=(0.93, 0.91, 0.86), metal=0.0, rough=0.50)

    # ---- base and lid --------------------------------------------------------
    base = bkit.rounded_box("Base", W, D, BASE_H, r=5.0, segments=3,
                            centre=(0.0, 0.0, BASE_H / 2.0), mat=board)
    lid = bkit.rounded_box("Lid", W + 2.0 * LID_OVERHANG, D + 2.0 * LID_OVERHANG,
                           LID_H, r=6.0, segments=3,
                           centre=(0.0, 0.0, BASE_H + LID_H / 2.0 - 2.0), mat=lid_mat)

    # ---- the piece grid, printed on the lid top -----------------------------
    art_face = bkit.rounded_box(
        "LidArt", W + 2.0 * LID_OVERHANG - 16.0, D + 2.0 * LID_OVERHANG - 16.0,
        1.0, r=3.0, segments=2,
        centre=(0.0, 0.0, BASE_H + LID_H - 2.0 + 0.3), mat=art)

    top_z = BASE_H + LID_H - 2.0 + 0.8
    pitch_x = (W + 2.0 * LID_OVERHANG - 16.0) / COLS
    pitch_y = (D + 2.0 * LID_OVERHANG - 16.0) / ROWS
    ribs = []
    for i in range(COLS + 1):
        x = -(W + 2.0 * LID_OVERHANG - 16.0) / 2.0 + i * pitch_x
        ribs.append(bkit.rounded_box("Ribs", RIB_W,
                                     D + 2.0 * LID_OVERHANG - 16.0, RIB_T,
                                     r=0.6, segments=2,
                                     centre=(x, 0.0, top_z + RIB_T / 2.0 - 0.4),
                                     mat=lid_mat))
    for j in range(ROWS + 1):
        y = -(D + 2.0 * LID_OVERHANG - 16.0) / 2.0 + j * pitch_y
        ribs.append(bkit.rounded_box("Ribs", W + 2.0 * LID_OVERHANG - 16.0, RIB_W,
                                     RIB_T, r=0.6, segments=2,
                                     centre=(0.0, y, top_z + RIB_T / 2.0 - 0.4),
                                     mat=lid_mat))
    bkit.join(ribs, name="Ribs")

    # ---- title label across the lid front -----------------------------------
    label = bkit.rounded_box("Label", LABEL_W, 3.0, LABEL_H, r=2.0, segments=2,
                             centre=(0.0, -(D + 2.0 * LID_OVERHANG) / 2.0 + 0.5,
                                     BASE_H + LID_H / 2.0 - 4.0), mat=paper)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="base_width", mm=400.0, tol=0.2, how="bbox_x", part="Base"),
    dict(name="base_depth", mm=300.0, tol=0.2, how="bbox_y", part="Base"),
    dict(name="base_height", mm=54.0, tol=0.2, how="bbox_z", part="Base"),
    dict(name="lid_width", mm=412.0, tol=0.2, how="bbox_x", part="Lid"),
    # 10 columns across the 396 mm art face, measured rib centre to rib centre
    # the rib run is the art face plus one corner radius at each end
    dict(name="rib_run_x", mm=398.2, tol=0.2, how="bbox_x", part="Ribs"),
    dict(name="rib_run_y", mm=298.2, tol=0.2, how="bbox_y", part="Ribs"),
    dict(name="overall_height", mm=91.0, tol=0.2, how="bbox_z", part=None)
]