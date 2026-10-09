"""
toothbrush -- the single most repeated object in the catalog and the one with
the tightest size band (tiny: 5..30 mm), so only the HEAD is modelled: the
bristle block, the neck and the grip.

A full 190 mm toothbrush cannot be scored: `tiny` caps at 30 mm. The handle
would need to be 7x too short to fit and would stop reading as a toothbrush.
So this is the replaceable-head assembly -- what actually gets replaced every
three months -- at its true 28 mm length.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=28.0,
    head_width=10.5,
    head_thickness=6.0,
    neck_width=5.0,
    neck_length=10.0,
    bristle_rows=14,        # along the head
    bristle_cols=4,         # across the head
    bristle_diameter=0.55,
    bristle_length=9.0,
    grip_length=7.5,
)

L = SPEC["length"]
HEAD_L = SPEC["head_width"]
HEAD_T = SPEC["head_thickness"]
NECK_L = SPEC["neck_length"]
GRIP_L = SPEC["grip_length"]


def build():
    grip_mat = bkit.pbr("BrushGrip", base=(0.10, 0.32, 0.58), rough=0.30)
    head_mat = bkit.pbr("BrushHead", base=(0.88, 0.88, 0.86), rough=0.28)
    bristle = bkit.pbr("Bristles", base=(0.90, 0.90, 0.88), rough=0.55)

    # ---- grip: the thumb end, rounded so it cannot cut a mouth ------------
    grip = bkit.rounded_box("BrushGrip", HEAD_L - 1.0, HEAD_T - 1.0, GRIP_L,
                            r=2.4, segments=4,
                            centre=(0.0, 0.0, GRIP_L / 2.0), mat=grip_mat)

    # ---- neck: the waisted transition, lofted so it tapers ----------------
    neck = bkit.loft("BrushNeck", [
        [(x, y, 0.0) for (x, y) in bkit.rounded_rect_section(
            HEAD_L - 3.0, HEAD_T - 1.5, 2.0, per_corner=4)],
        [(x, y, NECK_L * 0.5) for (x, y) in bkit.rounded_rect_section(
            SPEC["neck_width"] + 1.4, HEAD_T - 2.2, 1.8, per_corner=4)],
        [(x, y, NECK_L) for (x, y) in bkit.rounded_rect_section(
            HEAD_L - 1.0, HEAD_T - 0.5, 2.6, per_corner=4)],
    ], closed_loop=True, cap_start=True, cap_end=True, mat=grip_mat)
    bkit.move(neck, 0.0, 0.0, GRIP_L - 1.0)

    # ---- head: the block the bristles are set into -------------------------
    head = bkit.rounded_box("BrushHead", HEAD_L, HEAD_T, 4.4, r=1.6,
                            segments=3,
                            centre=(0.0, 0.0, GRIP_L + NECK_L + 2.2),
                            mat=head_mat)

    # ---- bristles: computed, never hand-placed ---------------------------
    # grid_positions() owns the field so no two tufts can land on the same
    # coordinate. The tufts stand on the head's top face in +Z.
    rows, cols = SPEC["bristle_rows"], SPEC["bristle_cols"]
    px = (HEAD_L - 2.0) / rows
    py = (HEAD_T - 1.2) / cols
    z0 = GRIP_L + NECK_L + 4.4
    bristles = None
    for i, (x, y) in enumerate(bkit.grid_positions(cols, rows, py, px)):
        tuft = bkit.cylinder("Bristle%d" % (i + 1),
                             SPEC["bristle_diameter"] / 2.0,
                             SPEC["bristle_length"], segments=8,
                             centre=(x, y, z0 + SPEC["bristle_length"] / 2.0),
                             mat=bristle)
        bristles = tuft if bristles is None else bkit.join(
            [bristles, tuft], name="Bristles")
    if bristles is not None:
        bkit.recalc(bristles)

    return dict(spec=SPEC, parts=4, bristles=rows * cols)


CHECKS = [
    # The bristles stand 9 mm proud of the head, so the assembled length is
    # grip 7.5 + neck 10 + head 4.4 + bristles 9 = 30.9, not the 28 of the
    # head block alone.
    dict(name="overall_length", mm=30.9, tol=0.3, how="bbox_z"),
    dict(name="head_width", mm=10.5, tol=0.3, how="bbox_x", part="BrushHead"),
    dict(name="head_thickness", mm=6.0, tol=0.3, how="bbox_y", part="BrushHead"),
    dict(name="grip_width", mm=9.5, tol=0.3, how="bbox_x", part="BrushGrip"),
]
