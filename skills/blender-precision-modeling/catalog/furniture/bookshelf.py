"""
bookshelf -- 900 x 300 mm open bookcase, 2000 mm high, five shelves.

A 2000 mm bookcase is 80% usable bay: the structural top and bottom boards take
50 mm and the three adjustable shelves take 75 mm, leaving four bays. Those
bays are what the eye measures, so the three shelves are placed with
bkit.lay_out at a fixed 462.5 mm gap -- the first bay is 25 mm deeper because
the shelves have thickness, which is true of every real bookcase and looks
wrong only if you space the boards by their centres instead of by their gaps.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=900.0,
    depth=300.0,
    height=2000.0,
    side_thickness=25.0,
    board_thickness=25.0,
    shelf_count=3,           # adjustable shelves between top and bottom
    shelf_gap=462.5,         # clear air between boards
    back_thickness=12.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
SIDE_T = SPEC["side_thickness"]
BOARD_T = SPEC["board_thickness"]
BACK_T = SPEC["back_thickness"]
INNER_W = W - 2 * SIDE_T                    # 850
BAY_Z0 = BOARD_T                            # 25: top of the bottom board
BAY_Z1 = H - BOARD_T                        # 1975: underside of the top board
# The three shelves straddle the usable bay; 1012.5 is the middle of 25..2000
# measured to the shelf *bottoms*, so the stack is symmetric top to bottom.
SHELF_MID = (BAY_Z0 + BAY_Z1 + BOARD_T) / 2.0

CHECKS = [
    dict(name="overall_width", mm=900.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=2000.0, tol=0.4, how="bbox_z"),
    dict(name="overall_depth", mm=300.0, tol=0.3, how="bbox_y"),
    dict(name="side_thickness", mm=25.0, tol=0.3, how="bbox_x", part="SideLeft"),
    dict(name="board_thickness", mm=25.0, tol=0.3, how="bbox_z", part="Shelf1"),
]


def build():
    board = bkit.pbr("ShelfBirch", base=(0.62, 0.47, 0.28), metal=0.0, rough=0.44)
    board_dk = bkit.pbr("ShelfBack", base=(0.46, 0.34, 0.20), metal=0.0,
                        rough=0.55)

    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Side%s" % tag, SIDE_T, D, H, r=4.0, segments=2,
                         centre=(sx * (W / 2.0 - SIDE_T / 2.0), 0, H / 2.0),
                         mat=board)

    for (nm, zc) in (("Bottom", BAY_Z0 + BOARD_T / 2.0),
                     ("Top", H - BOARD_T / 2.0)):
        bkit.rounded_box("Board%s" % nm, INNER_W, D, BOARD_T, r=4.0, segments=2,
                         centre=(0, 0, zc), mat=board)

    # ---- adjustable shelves: real thickness + real gap, computed ----------
    for i, (dz, _w) in enumerate(
            bkit.lay_out([BOARD_T] * SPEC["shelf_count"],
                         gap=SPEC["shelf_gap"])):
        bkit.rounded_box("Shelf%d" % (i + 1), INNER_W, D - 6.0, BOARD_T, r=4.0,
                         segments=2, centre=(0, -3.0, SHELF_MID + dz), mat=board)

    bkit.rounded_box("Back", INNER_W, BACK_T, H - 2 * BOARD_T, r=2.0,
                     segments=2,
                     centre=(0, D / 2.0 - BACK_T / 2.0, H / 2.0), mat=board_dk)

    return dict(spec=SPEC, parts=8)
