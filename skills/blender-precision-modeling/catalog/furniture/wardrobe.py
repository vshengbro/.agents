"""
wardrobe -- 1200 x 600 mm two-door wardrobe, 2100 mm high.

The proportion rule for a wardrobe is 2 x 600: 1200 mm of width against
2100 mm of height, with the door split on the centre line and a 3 mm reveal
between the leaves. Everything else follows from that -- the two fixed shelves
are computed from a 931 mm gap so the hanging space above and below is
symmetric, and the doors are inset flush with the carcass sides so the 600 mm
depth stays the depth of the case and not the depth of the case plus a proud
door.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=1200.0,
    depth=600.0,
    height=2100.0,
    plinth_height=100.0,
    side_thickness=25.0,
    board_thickness=25.0,
    back_thickness=15.0,
    divider_thickness=22.0,
    door_count=2,
    door_width=573.5,        # two leaves plus a 3 mm reveal = 1150 clear
    door_thickness=22.0,
    door_gap=3.0,
    door_height=1980.0,
    fixed_shelf_count=2,
    fixed_shelf_thickness=22.0,
    fixed_shelf_gap=931.0,
    handle_length=320.0,
    handle_diameter=20.0,
    handle_protrusion=21.0,    # stands 21 mm proud of the 600 mm carcass
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
PLINTH_H = SPEC["plinth_height"]
SIDE_T = SPEC["side_thickness"]
BOARD_T = SPEC["board_thickness"]
BACK_T = SPEC["back_thickness"]
DIV_T = SPEC["divider_thickness"]
INNER_W = W - 2 * SIDE_T                    # 1150
CARC_Z0 = PLINTH_H                          # 100
CARC_Z1 = H - BOARD_T                       # 2075
DOOR_T = SPEC["door_thickness"]
DOOR_Y = -D / 2.0 + DOOR_T / 2.0            # -289: leaf flush with the front
SHELF_T = SPEC["fixed_shelf_thickness"]
SHELF_CLEAR_D = D - BACK_T - 10.0           # 575 usable depth
SHELF_MID = (CARC_Z0 + BOARD_T + CARC_Z1) / 2.0

CHECKS = [
    dict(name="overall_width", mm=1200.0, tol=0.4, how="bbox_x"),
    dict(name="overall_height", mm=2100.0, tol=0.4, how="bbox_z"),
    # 600 mm is the carcass depth and belongs to the side panel; the bar pulls
    # stand 21 mm proud of the doors, so an assembly bbox_y would read 621.
    dict(name="carcass_depth", mm=600.0, tol=0.4, how="bbox_y", part="SideLeft"),
    dict(name="door_width", mm=573.5, tol=0.3, how="bbox_x", part="DoorLeft"),
    dict(name="door_thickness", mm=22.0, tol=0.3, how="bbox_y", part="DoorLeft"),
    dict(name="side_thickness", mm=25.0, tol=0.3, how="bbox_x", part="SideLeft"),
]


def build():
    wood = bkit.pbr("WardrobeOak", base=(0.48, 0.32, 0.17), metal=0.0, rough=0.38)
    wood_dk = bkit.pbr("WardrobeInterior", base=(0.37, 0.24, 0.12), metal=0.0,
                       rough=0.52)
    chrome = bkit.preset("polished_metal")

    bkit.rounded_box("Plinth", INNER_W, D - 40.0, PLINTH_H, r=4.0, segments=2,
                     centre=(0, 0, PLINTH_H / 2.0), mat=wood_dk)

    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Side%s" % tag, SIDE_T, D, H - PLINTH_H, r=4.0,
                         segments=2,
                         centre=(sx * (W / 2.0 - SIDE_T / 2.0), 0,
                                 (PLINTH_H + H) / 2.0),
                         mat=wood)

    bkit.rounded_box("Top", INNER_W, D, BOARD_T, r=4.0, segments=2,
                     centre=(0, 0, H - BOARD_T / 2.0), mat=wood)
    bkit.rounded_box("Bottom", INNER_W, D, BOARD_T, r=4.0, segments=2,
                     centre=(0, 0, CARC_Z0 + BOARD_T / 2.0), mat=wood)
    bkit.rounded_box("Back", INNER_W, BACK_T, CARC_Z1 - (CARC_Z0 + BOARD_T),
                     r=2.0, segments=2,
                     centre=(0, D / 2.0 - BACK_T / 2.0,
                             (CARC_Z0 + BOARD_T + CARC_Z1) / 2.0),
                     mat=wood_dk)
    bkit.rounded_box("Divider", DIV_T, D - BACK_T - 10.0,
                     CARC_Z1 - (CARC_Z0 + BOARD_T), r=3.0, segments=2,
                     centre=(0, -5.0, (CARC_Z0 + BOARD_T + CARC_Z1) / 2.0),
                     mat=wood_dk)

    # ---- fixed shelves: even gap, symmetric hanging space -----------------
    for i, (dz, _w) in enumerate(
            bkit.lay_out([SHELF_T] * SPEC["fixed_shelf_count"],
                         gap=SPEC["fixed_shelf_gap"])):
        bkit.rounded_box("Shelf%d" % (i + 1), INNER_W - 6.0, SHELF_CLEAR_D, SHELF_T,
                         r=3.0, segments=2, centre=(0, -5.0, SHELF_MID + dz),
                         mat=wood_dk)

    # ---- doors: 2 x 573.5 mm leaves with a 3 mm reveal -------------------
    for i, (dx, _w) in enumerate(
            bkit.lay_out([SPEC["door_width"]] * SPEC["door_count"],
                         gap=SPEC["door_gap"])):
        tag = "Left" if i == 0 else "Right"
        bkit.rounded_box("Door%s" % tag, SPEC["door_width"], DOOR_T,
                         SPEC["door_height"], r=4.0, segments=2,
                         centre=(dx, DOOR_Y, PLINTH_H + SPEC["door_height"] / 2.0),
                         mat=wood)
        # handles meet on the centre line, 30 mm in from the meeting edges
        bkit.cylinder("Handle%s" % tag, SPEC["handle_diameter"] / 2.0,
                      SPEC["handle_length"], segments=24,
                      centre=(dx + (60.0 if i == 0 else -60.0), DOOR_Y - 22.0,
                              PLINTH_H + 1000.0),
                      mat=chrome)

    return dict(spec=SPEC, parts=14)
