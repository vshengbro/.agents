"""
clipboard -- A4 clipboard, 232 x 330 x 8 mm.

Medium size class. The board is thin, so the parts that read are the spring
clip across the top and the paper stack under it. Both are real solids with
thickness; the clip is two bars and a wire loop, which is what a bulldog clip
actually is.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=232.0,
    height=330.0,
    board_thickness=4.0,
    clip_width=96.0,
    clip_height=26.0,
)

W = SPEC["width"]
H = SPEC["height"]
BT = SPEC["board_thickness"]


def build():
    board = bkit.pbr("ClipboardBoard", base=(0.30, 0.22, 0.13), rough=0.55)
    metal = bkit.preset("brushed_metal")
    paper = bkit.pbr("ClipboardPaper", base=(0.94, 0.94, 0.91), rough=0.70)

    base = bkit.rounded_box("ClipboardBoard2", W, H, BT, r=6.0, segments=4,
                            centre=(0, 0, BT / 2.0), mat=board)

    # ---- paper on the board ----------------------------------------------
    sheet = bkit.rounded_box("ClipboardPaper", W - 40.0, H - 46.0, 1.6,
                             r=1.0,
                             centre=(0, -8.0, BT + 0.8), mat=paper)

    # ---- spring clip: two bars plus the wire loop -------------------------
    clip_y = H / 2.0 - 26.0
    jaw = bkit.rounded_box("ClipboardClipJaw", SPEC["clip_width"], 14.0, 3.0,
                           r=1.0, centre=(0, clip_y + 6.0, BT + 1.5),
                           mat=metal)
    top = bkit.rounded_box("ClipboardClipTop", SPEC["clip_width"],
                           SPEC["clip_height"], 4.0, r=1.5,
                           centre=(0, clip_y + 1.0, BT + 5.0), mat=metal)
    wire = bkit.arc_torus("ClipboardClipWire", 7.0, 1.3, 200.0, -20.0,
                          plane="YZ",
                          centre=(0, clip_y + 1.0, BT + 5.0),
                          seg_major=26, seg_minor=12, mat=metal, caps=True)
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="width", mm=232.0, tol=0.8, how="bbox_x", part="ClipboardBoard2"),
    dict(name="height", mm=330.0, tol=0.8, how="bbox_y", part="ClipboardBoard2"),
    dict(name="board_thickness", mm=4.0, tol=0.5, how="bbox_z",
         part="ClipboardBoard2"),
]