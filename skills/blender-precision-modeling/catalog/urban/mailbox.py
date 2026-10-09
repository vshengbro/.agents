"""
mailbox -- 470 x 500 x 1140 mm US rural collection box on a pedestal: a lofted
dome-topped body, a barrel-vaulted door, a latch handle, a hinged flag on a
two-post arm and a base skirt.

The dome is a `loft` over rounded-rectangle sections that shrink and round off
as they rise, which is how a real mailbox body is formed and the only way to get
a barrel vault instead of a chamfered box. The flag is set to raised -- the
detail that makes a mailbox instantly readable from any camera angle.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    body_width=470.0,
    body_depth=500.0,
    body_height=520.0,
    vault_height=180.0,
    pedestal_height=440.0,
    overall_height=1020.0,
    flag_width=150.0,
)

BW, BD = SPEC["body_width"], SPEC["body_depth"]
PED_H = SPEC["pedestal_height"]
BASE_Y = 430.0                       # body base, sunk 20 mm into the pedestal cap


def build():
    body = bkit.pbr("MailboxBody", base=(0.16, 0.30, 0.18), metal=0.45,
                    rough=0.44)
    door_mat = bkit.pbr("MailboxDoor", base=(0.14, 0.26, 0.15), metal=0.45,
                        rough=0.40)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    # ---- pedestal and base skirt ------------------------------------------
    bkit.rounded_box("MailboxPedestal", 420.0, 450.0, PED_H, r=12.0,
                     segments=3, centre=(0.0, 0.0, PED_H / 2.0), mat=dark)
    bkit.rounded_box("PedestalCap", 470.0, 500.0, 60.0, r=10.0, segments=2,
                     centre=(0.0, 0.0, PED_H - 20.0), mat=steel)
    bolts = [bkit.cylinder("_bolt", 10.0, 14.0, segments=16,
                           centre=(bx, by, 8.0), mat=steel)
             for (bx, by) in bkit.grid_positions(2, 2, 340.0, 370.0)]
    bkit.join(bolts, name="PedestalBolts")

    # ---- body: straight sides, then a barrel vault ------------------------
    # Rounded-rect sections at rising heights, shrinking in y as the vault
    # rounds over. loft() takes the 2D rings the section helper returns.
    sections = []
    for (h, r) in ((0.0, 40.0), (300.0, 40.0), (440.0, 38.0), (500.0, 36.0)):
        sec = bkit.rounded_rect_section(BW, BD, r, per_corner=7)
        sections.append([(x, y, BASE_Y + h) for (x, y) in sec])
    for i in range(1, 7):
        a = (i / 7.0) * (3.14159265 / 2.0)
        sec = bkit.rounded_rect_section(BW, BD * math.cos(a), 36.0,
                                        per_corner=7)
        sections.append([(x, y, BASE_Y + 500.0 + BD * 0.5 * math.sin(a) * 0.36)
                         for (x, y) in sec])
    bkit.loft("MailboxBody", sections, mat=body)

    # ---- door: a slightly proud panel with a barrel-vault top ------------
    # Offset to BD/2 + 4 so the door overlaps the body wall by 11 mm rather
    # than meeting it flush along a whole 440 mm edge.
    door = []
    for (h, r) in ((0.0, 30.0), (300.0, 30.0)):
        sec = bkit.rounded_rect_section(BW - 30.0, 30.0, r, per_corner=6)
        door.append([(x, y - (BD / 2.0 + 4.0), BASE_Y + h) for (x, y) in sec])
    for i in range(1, 6):
        a = (i / 6.0) * (3.14159265 / 2.0)
        sec = bkit.rounded_rect_section(BW - 30.0, 30.0 * math.cos(a), 30.0,
                                        per_corner=6)
        door.append([(x, y - (BD / 2.0 + 4.0),
                      BASE_Y + 300.0 + 26.0 * math.sin(a)) for (x, y) in sec])
    bkit.loft("MailboxDoor", door, mat=door_mat)

    # ---- latch handle on the door -----------------------------------------
    bkit.box("DoorLatch", 26.0, 26.0, 90.0, mat=steel,
             centre=(0.0, -(BD / 2.0 + 12.0), BASE_Y + 150.0))
    bkit.cylinder("LatchBar", 9.0, 220.0, segments=20, axis="X", mat=steel,
                  centre=(0.0, -(BD / 2.0 + 20.0), BASE_Y + 150.0))
    bkit.box("LatchLever", 22.0, 22.0, 130.0, mat=steel,
             centre=(100.0, -(BD / 2.0 + 20.0), BASE_Y + 120.0))

    # ---- raised flag on a two-post arm -------------------------------------
    for side in (-1.0, 1.0):
        bkit.cylinder("FlagPost%.0f" % side, 9.0, 190.0, segments=16,
                      centre=(side * (SPEC["flag_width"] / 2.0), BD / 2.0 - 30.0,
                              BASE_Y + 300.0), mat=steel)
    bkit.rounded_box("MailboxFlag", SPEC["flag_width"], 14.0, 150.0, r=6.0,
                     segments=2,
                     centre=(0.0, BD / 2.0 - 30.0, BASE_Y + 440.0), mat=body)
    bkit.box("FlagHinge", SPEC["flag_width"] + 20.0, 22.0, 16.0, mat=steel,
             centre=(0.0, BD / 2.0 - 30.0, BASE_Y + 366.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="body_width", mm=470.0, tol=1.0, how="bbox_x",
         part="MailboxBody"),
    dict(name="body_depth", mm=500.0, tol=1.5, how="bbox_y",
         part="MailboxBody"),
    dict(name="pedestal_height", mm=440.0, tol=1.0, how="bbox_z",
         part="MailboxPedestal"),
    dict(name="overall_height", mm=1020.0, tol=8.0, how="bbox_z"),
    dict(name="flag_width", mm=150.0, tol=0.6, how="bbox_x",
         part="MailboxFlag"),
]