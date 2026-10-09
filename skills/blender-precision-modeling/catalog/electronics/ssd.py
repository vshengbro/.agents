"""
ssd -- M.2 2280 solid-state drive, 80 x 22 x 3.5 mm.

The count is what makes this read as an M.2 module and not a green brick: 28
gold edge fingers in two rows of 14, one key notch 6.5 mm from the connector
end, the controller and NAND packages, and the mounting hole at the far end.
Fingers come from `lay_out`, so the 1.2 mm pad / 0.2 mm gap rhythm is the
single source of truth for both rows.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=80.0,
    width=22.0,
    height=3.3,
    pins=14,
    package_height=1.8,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
PINS = SPEC["pins"]


def build():
    pcb = bkit.pbr("SsdPcb", base=(0.07, 0.24, 0.14), rough=0.42)
    gold = bkit.preset("gold")
    chip = bkit.pbr("SsdChip", base=(0.14, 0.14, 0.15), rough=0.30)
    resist = bkit.pbr("SsdResistor", base=(0.72, 0.70, 0.62), rough=0.40)

    board = bkit.rounded_box("SsdBoard", L, W, 1.6, r=0.8, segments=3,
                             centre=(0, 0, 0.8), mat=pcb)

    # ---- M.2 key notch: 2 mm of board removed from one long edge ---------
    notch = bkit.rounded_box("_notch", 4.0, 2.6, 3.0, r=0.3,
                             centre=(-L / 2.0 + 13.5, W / 2.0 - 0.8, 0.8))
    bkit.boolean(board, notch, "DIFFERENCE")

    # ---- free-board mounting hole at the far end -------------------------
    bkit.bore(board, radius=1.6, depth=4.0, centre=(L / 2.0 - 4.5, 0.0, 0.8),
              host_segments=24)

    # ---- 2 x 14 gold edge fingers, one computed pitch --------------------
    # Inset 11 mm from the connector end: an M.2's fingers sit ON the board
    # edge, and starting the row nearer than this overhangs the PCB and
    # inflates the assembly bounding box.
    pads = []
    for row, y in enumerate((W / 2.0 - 3.6, -W / 2.0 + 3.6)):
        for i, (x, w) in enumerate(bkit.lay_out([1.2] * PINS, gap=0.2)):
            pads.append(bkit.rounded_box(
                "_p%d_%d" % (row, i), w, 4.0, 0.45, r=0.12,
                centre=(-L / 2.0 + 11.0 + x, y, 1.82), mat=gold))
    bkit.join(pads, name="SsdContacts")

    # ---- controller + NAND packages, sunk 0.1 mm into the solder mask ----
    # Sunk rather than butted: a package bottom coplanar with the board top
    # z-fights, and the 0.1 mm overlap keeps the two surfaces distinct. The
    # controller is the tallest part, so it sets the module's 3.3 mm height.
    ctl = bkit.rounded_box("SsdController", 12.0, 12.0, SPEC["package_height"],
                           r=0.4, segments=2, centre=(-3.0, 0.0, 2.4),
                           mat=chip)
    nand = bkit.rounded_box("SsdNand", 13.0, 11.0, SPEC["package_height"] - 0.2,
                            r=0.4, segments=2, centre=(16.0, 0.0, 2.2),
                            mat=chip)

    # ---- SMD passives: three rows on one computed grid --------------------
    smd = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=4, rows=2,
                                                   pitch_x=2.2, pitch_y=2.4)):
        smd.append(bkit.box("_r%d" % i, 1.0, 1.2, 0.4,
                            centre=(24.0 + x, y, 1.9), mat=resist))
    bkit.join(smd, name="SmdPassives")

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="length", mm=80.0, tol=0.4, how="bbox_x", part="SsdBoard"),
    dict(name="width", mm=22.0, tol=0.4, how="bbox_y", part="SsdBoard"),
    dict(name="height", mm=3.3, tol=0.4, how="bbox_z"),
]
