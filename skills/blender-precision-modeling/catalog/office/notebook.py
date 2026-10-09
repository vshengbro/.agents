"""
notebook -- A5 hardback notebook, 148 x 210 mm, 19 mm tall.

The cover is not a solid slab around the pages -- it is a U section (bottom
plate + spine) extruded across the width, which is what a real hardback looks
like from the edge and lets the page block stand 1.2 mm proud of the boards.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=148.0,
    height=210.0,
    total_height=19.0,
    page_block_height=16.0,
    board_thickness=1.8,
)

T = SPEC["board_thickness"]
W = SPEC["width"]
H = SPEC["total_height"]


def build():
    board = bkit.pbr("NotebookBoard", base=(0.09, 0.16, 0.36), rough=0.40)
    paper = bkit.pbr("NotebookPaper", base=(0.93, 0.92, 0.88), rough=0.80)
    endband = bkit.pbr("NotebookBands", base=(0.20, 0.45, 0.72), rough=0.55)

    # ---- cover: U section in the XZ plane, extruded across the width -------
    # Authored with the axis="Y" rotation, so poly x -> world x and poly
    # y -> world z.
    cover_poly = [
        (-W / 2.0, 0.0),
        (W / 2.0, 0.0),
        (W / 2.0, T),
        (-W / 2.0 + T, T),
        (-W / 2.0 + T, H),
        (-W / 2.0, H),
    ]
    cover = bkit.extrude_profile("NotebookCover", cover_poly,
                                 SPEC["height"], axis="Y", mat=board)
    bkit.recalc(cover)

    # Page block overlaps the spine so the two solids never share a face.
    pages = bkit.rounded_box("NotebookPages",
                             W - T - 1.0, SPEC["height"] - 3.0,
                             SPEC["page_block_height"], r=1.5,
                             centre=(-T / 2.0 - 0.5, 0.0,
                                     T + SPEC["page_block_height"] / 2.0),
                             mat=paper)

    # Elastic closure band wrapping the front board. It sits flush with the
    # boards rather than proud of them, so the declared total height stays the
    # measured one.
    band = bkit.rounded_box("NotebookBand", 6.0, SPEC["height"] - 1.0,
                            H - 0.4, r=0.8,
                            centre=(W / 2.0 - 16.0, 0.0, H / 2.0 - 0.2),
                            mat=endband)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="width", mm=148.0, tol=0.5, how="bbox_x", part="NotebookCover"),
    dict(name="height", mm=210.0, tol=0.5, how="bbox_y"),
    dict(name="total_height", mm=19.0, tol=0.4, how="bbox_z"),
    dict(name="page_block_height", mm=16.0, tol=0.4, how="bbox_z",
         part="NotebookPages"),
]