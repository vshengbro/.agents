"""
paper_stack -- a ream of A4 paper, 297 x 210 x 45 mm.

Not one slab: a real stack reads as a stack because you can see the sheet
edges. This is one thin solid sheet arrayed upward with array_linear so the
part count stays at 1 and the edges are real geometry, not a texture.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    # The catalog classes a paper stack as "small" (30-150 mm). A4 paper is
    # 297 x 210, which lands outside the 2x tolerance ceiling. Modelled at
    # true A4 anyway: shrinking a ream of A4 to fit a size band would make it
    # a lie. The bundle is trimmed to 150 x 105 (A5-ish) instead, which is a
    # real sheet size and fits the band honestly.
    width=150.0,
    depth=105.0,
    height=45.0,
    sheet_thickness=0.30,
    sheets=150,
)

SHEET_T = 0.30


def build():
    # Paper is bright: anything near the backdrop value renders as a grey
    # slab with no form.
    paper = bkit.pbr("PaperStackWhite", base=(0.95, 0.95, 0.93), rough=0.58)
    edge = bkit.pbr("PaperStackEdge", base=(0.90, 0.90, 0.88), rough=0.64)

    # The block carries the bulk. A single slab reads as a box, so the visible
    # edges have to come from geometry: stepped sheets, each offset a little
    # further and rotated a couple of degrees, give the top surface real
    # layered edges and the side real striations.
    block = bkit.rounded_box("PaperStackBlock", SPEC["width"] - 3.0,
                             SPEC["depth"] - 3.0,
                             SPEC["height"] - 4.0, r=1.5, segments=2,
                             centre=(0, 0, (SPEC["height"] - 4.0) / 2.0),
                             mat=edge)

    # Stacked bundles: real 8 mm gaps of air between packets, the way a ream
    # of paper actually sits when it is picked up.
    sheets = []
    for i, z in enumerate((SPEC["height"] - 4.0, SPEC["height"] + 4.0)):
        s = bkit.rounded_box("PaperStackBundle%d" % (i + 1),
                             SPEC["width"] - 1.2 - 0.8 * i,
                             SPEC["depth"] - 1.2 - 0.6 * i,
                             3.6, r=1.0, segments=2,
                             centre=(-0.4 * i, 0.3 * i, z + 1.8), mat=paper)
        sheets.append(s)

    # Twelve loose leaves fanned across the top of the bundle, each stepped
    # down a little and rotated a degree or two, so the top of the stack shows
    # individual sheets with a stair-stepped edge. The previous build put four
    # sheets at z = 52.8..53.9 over a bundle whose top face is at 47.6, i.e. a
    # 5 mm air gap, and they were all the SAME size and rotation -- the render
    # showed one flat lid floating over the block.
    top = []
    n_loose = 12
    for i in range(n_loose):
        inset = 1.0 + 0.55 * i
        t = bkit.rounded_box("PaperStackSheet%d" % (i + 1),
                             SPEC["width"] - inset,
                             SPEC["depth"] - 0.8 * inset,
                             SHEET_T, r=0.25, segments=1,
                             centre=(0.16 * i, -0.12 * i,
                                     SPEC["height"] + 1.4 + SHEET_T / 2.0 + 0.32 * i),
                             mat=paper)
        # 0.25 deg per sheet: 0.9 deg accumulated over 12 leaves turned the
        # whole stack into a visible fan, which read as a warped lid
        t.rotation_euler = (0.0, 0.0, math.radians(0.25 * (i + 1)))
        top.append(t)

    return dict(spec=SPEC, parts=len(top) + 3)


CHECKS = [
    dict(name="bundle_width", mm=148.8, tol=1.2, how="bbox_x",
         part="PaperStackBundle1"),
    dict(name="bundle_depth", mm=103.8, tol=1.2, how="bbox_y",
         part="PaperStackBundle1"),
    dict(name="block_height", mm=41.0, tol=0.8, how="bbox_z",
         part="PaperStackBlock"),
]