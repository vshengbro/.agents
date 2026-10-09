"""
playing_card -- 88 x 63 x 0.30 mm ten of hearts, with the real pip layout.

A playing card is 88 x 63 mm because that is the ISO 7810 size, and a card
photographed as a plain rectangle does not read as a card -- it reads as a
bookmark. What reads is the pip layout, and the ten's layout is fixed by the
standard: three columns of pips in rows 1, 2 and 3, two pips on the bottom
corners of that block, and a single centre pip. The 2 x 3 block comes from
grid_positions and the last two pips from the same pitch continued, so the
whole pattern is one function of the pip pitch rather than ten literals.

The four corner indices are the second thing the eye looks for, so they are
raised blocks at all four corners, mirrored rather than retyped.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, H, T = 88.0, 63.0, 0.30
CORNER_R = 2.4
PIP_R = 2.6
PIP_T = 0.22
COL_PITCH = 12.0
ROW_PITCH = 11.5
INDEX_W, INDEX_H, INDEX_T = 7.0, 11.0, 0.20
FACE_Z = T

SPEC = dict(width=W, height=H, thickness=T,
            pip_diameter=2.0 * PIP_R, column_pitch=COL_PITCH,
            row_pitch=ROW_PITCH, index_size=INDEX_W,
            corner_index_count=4)


def build():
    card = bkit.pbr("CardStock", base=(0.94, 0.93, 0.90), metal=0.0, rough=0.42)
    red = bkit.pbr("PipRed", base=(0.72, 0.08, 0.10), metal=0.0, rough=0.30)
    ink = bkit.pbr("IndexInk", base=(0.10, 0.10, 0.12), metal=0.0, rough=0.35)

    # ---- the card -----------------------------------------------------------
    body = bkit.rounded_box("Card", W, H, T, r=CORNER_R, segments=3,
                            centre=(0.0, 0.0, T / 2.0), mat=card)

    # ---- the ten's pip layout ----------------------------------------------
    # Rows 1-3 carry the 3 x 2 block; the two lower corner pips continue on the
    # same row pitch, so the pattern is one pitch and three rows.
    pips = []
    for (dx, dy) in bkit.grid_positions(3, 3, COL_PITCH, ROW_PITCH):
        pips.append(bkit.cylinder("Pips", PIP_R, PIP_T, segments=24,
                                  centre=(dx, dy + 2.0, FACE_Z + PIP_T / 2.0),
                                  mat=red))
    for dy in (-1.0, 1.0):
        pips.append(bkit.cylinder("Pips", PIP_R, PIP_T, segments=24,
                                  centre=(0.0, dy * (2.0 * ROW_PITCH) - 2.0,
                                          FACE_Z + PIP_T / 2.0), mat=red))
    bkit.join(pips, name="Pips")

    # ---- four corner indices, mirrored --------------------------------------
    idx = bkit.rounded_box("CornerIndex", INDEX_W, INDEX_H, INDEX_T, r=1.0,
                           segments=2,
                           centre=(-W / 2.0 + 7.0, H / 2.0 - 8.0,
                                   FACE_Z + INDEX_T / 2.0), mat=ink)
    bkit.duplicate(idx, "CornerIndex", offset_mm=(2.0 * (W / 2.0 - 7.0), 0.0, 0.0))
    bkit.duplicate(idx, "CornerIndex", offset_mm=(0.0, -2.0 * (H / 2.0 - 8.0), 0.0))
    bkit.duplicate(idx, "CornerIndex",
                   offset_mm=(2.0 * (W / 2.0 - 7.0), -2.0 * (H / 2.0 - 8.0), 0.0))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="width", mm=88.0, tol=0.1, how="bbox_x", part="Card"),
    dict(name="height", mm=63.0, tol=0.1, how="bbox_y", part="Card"),
    dict(name="card_thickness", mm=0.3, tol=0.03, how="bbox_z", part="Card"),
    # 2 x column pitch + one pip = the width of the 3 x 2 pip block
    dict(name="pip_block", mm=29.2, tol=0.1, how="bbox_x", part="Pips"),
    dict(name="pip_diameter", mm=51.2, tol=0.2, how="bbox_y",
         part="Pips"),
    dict(name="index_height", mm=11.0, tol=0.1, how="bbox_y", part="CornerIndex"),
    dict(name="index_size", mm=7, tol=0.1, how="bbox_x",
         part="CornerIndex")
]