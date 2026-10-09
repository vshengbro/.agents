"""
bookshelf_ladder -- lean-to ladder shelf, 500 x 300 mm, 1500 mm high, five tiers.

A ladder shelf is two stiles and a stack of rungs, so the whole object is
decided by one calculation: five 25 mm boards spanning 1500 mm means a
343.75 mm gap between them, and bkit.lay_out produces exactly that with the
bottom board on the floor and the top board flush with the stiles. Hand
spacing five boards is the classic way to end up with a shelf that is level
at the bottom and 30 mm proud at the top.

Built upright rather than leaned: a lean-to would need a per-part rotation, and
the measured bounding box of a rotated part is its axis-aligned extent, not
its length -- the 1500 mm claim would stop being true.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=500.0,
    depth=300.0,
    height=1500.0,
    stile_width=40.0,
    stile_depth=60.0,        # a back stile, not a full-depth side panel
    stile_setback=110.0,     # stile centre behind the shelf centre
    shelf_count=5,
    shelf_thickness=25.0,
    shelf_width=420.0,       # exactly the clear width between the stiles
    shelf_depth=300.0,
    shelf_gap=343.75,        # (1500 - 5*25) / 4
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
STILE_T = SPEC["stile_width"]
BOARD_T = SPEC["shelf_thickness"]
STILE_X = W / 2.0 - STILE_T / 2.0            # 230
SHELF_MID = H / 2.0                          # 750: the board stack is centred

CHECKS = [
    dict(name="overall_width", mm=500.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=1500.0, tol=0.4, how="bbox_z"),
    dict(name="overall_depth", mm=300.0, tol=0.3, how="bbox_y"),
    dict(name="shelf_width", mm=420.0, tol=0.3, how="bbox_x", part="Shelf1"),
    dict(name="shelf_thickness", mm=25.0, tol=0.3, how="bbox_z", part="Shelf1"),
    dict(name="stile_width", mm=40.0, tol=0.3, how="bbox_x", part="StileLeft"),
    dict(name="stile_depth", mm=60.0, tol=0.3, how="bbox_y", part="StileLeft"),
]


def build():
    metal = bkit.pbr("LadderShelfSteel", base=(0.74, 0.75, 0.77), metal=0.55,
                     rough=0.34)
    metal_dk = bkit.pbr("LadderShelfShelf", base=(0.60, 0.48, 0.33), metal=0.0,
                        rough=0.52)

    # Stiles sit at the BACK, 60 mm deep, so the 300 mm shelves cantilever
    # forward of them. Stiles as full-depth 300 mm side panels turn a ladder
    # shelf into a closed cabinet -- the silhouette stops reading as a lean-to
    # the moment there is a solid slab down each side.
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Stile%s" % tag, STILE_T, SPEC["stile_depth"], H, r=5.0,
                         segments=3,
                         centre=(sx * STILE_X, SPEC["stile_setback"], H / 2.0),
                         mat=metal)

    # ---- five boards, even gap, bottom board on the floor -----------------
    for i, (dz, _w) in enumerate(
            bkit.lay_out([BOARD_T] * SPEC["shelf_count"], gap=SPEC["shelf_gap"])):
        bkit.rounded_box("Shelf%d" % (i + 1), SPEC["shelf_width"],
                         SPEC["shelf_depth"], BOARD_T, r=5.0, segments=3,
                         centre=(0, 0, SHELF_MID + dz), mat=metal_dk)

    return dict(spec=SPEC, parts=7)
