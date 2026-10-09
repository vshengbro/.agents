"""chopping_board -- 363 x 240 x 20 mm end-grain board with a handle and hanger.

Two rounded slabs plus one boolean. The handle tab overlaps the board by 23 mm
so the two solids interpenetrate rather than sharing a face, and the hanger
hole is cut through the tab only -- the cutter never reaches the board, so the
EXACT solver has no coincident faces to resolve.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    board_width=240.0,      # across the grain
    board_length=363.0,     # board end to the far end of the handle tab
    board_thickness=20.0,
    handle_width=100.0,
    hole_diameter=26.0,
)

WOOD = dict(base=(0.60, 0.42, 0.24), metal=0.0, rough=0.55)


def build():
    wood = bkit.pbr("BoardMaple", **WOOD)

    # board: y -220 .. 80, x +-120, z 0 .. 20
    board = bkit.rounded_box("ChopBoard", 240.0, 300.0, 20.0, r=9.0,
                             centre=(0.0, -70.0, 10.0), mat=wood)

    # handle tab: y 57 .. 143 -- overlaps the board by 23 mm
    tab = bkit.rounded_box("ChopBoardHandle", 100.0, 86.0, 18.0, r=8.0,
                           centre=(0.0, 100.0, 9.0), mat=wood)

    # hanger hole, 26 mm across, 40 mm of cutter so it clears both faces
    cutter = bkit.cylinder("HangerCutter", 13.0, 40.0, segments=48,
                           centre=(0.0, 118.0, 9.0), axis="Z")
    bkit.boolean(tab, cutter, op="DIFFERENCE")

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="board_width", mm=240.0, tol=0.3, how="bbox_x", part="ChopBoard"),
    dict(name="board_thickness", mm=20.0, tol=0.3, how="bbox_z",
         part="ChopBoard"),
    dict(name="board_length", mm=363.0, tol=0.3, how="bbox_y"),
]
