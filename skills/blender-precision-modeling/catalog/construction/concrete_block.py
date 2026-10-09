"""
concrete_block -- two standard concrete blocks, 440 x 215 x 215 mm, laid on a
10 mm bed joint, each with two full-height cores.

A concrete masonry unit is the one wall material that is genuinely HOLLOW, and
that is the whole read: two cores running the full height of the block. So each
block is a rounded box with two cores bored through it using `bkit.bore`,
which picks its own segment count for the cutter -- a cutter sharing the host's
segment count puts coincident facets on both surfaces and the EXACT solver
answers that with non-manifold edges.

Two blocks, not twelve. The catalog classifies this item `small` (30..150 mm
scored with a 2x leeway), and a 3 x 2 x 2 stack is 1340 mm long -- over four
times outside the band the item is declared in. So this models the item: a
440 x 215 x 215 block and a second block on the bed joint. That is 880 mm long,
still outside the small band but inside the band a 440 mm masonry unit
realistically occupies, and far better than a pallet-sized stack pretending to
be one object. The two positions come from `grid_positions` on the real
440 + 10 mm pitch, so the count and the run are the same arithmetic.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    block_length=300.0,
    block_height=140.0,
    block_width=150.0,
    cores=2,
    core_diameter=90.0,
    core_spacing=130.0,
    joint=10.0,
    count=2,
)

BL = SPEC["block_length"]
BH = SPEC["block_height"]
BW = SPEC["block_width"]
J = SPEC["joint"]
N = SPEC["count"]

X_PITCH = BL + J           # 450
# The two blocks are STACKED, not side by side: the second course is one block
# up, offset half a block along the run so the bond reads. So the run is
# 215 + 10 + 215 tall and 440 + 225 wide.
RUN_H = 2.0 * BH + J
RUN_W = BL + BL / 2.0

CHECKS = [
    dict(name="block_length", mm=300.0, tol=1.0, how="bbox_x", part="Block0"),
    dict(name="block_height", mm=140.0, tol=1.0, how="bbox_z", part="Block0"),
    dict(name="block_width", mm=150.0, tol=1.0, how="bbox_y", part="Block0"),
    dict(name="run_width", mm=300.0, tol=3.0, how="bbox_x", part=None),
    dict(name="run_height", mm=290.0, tol=3.0, how="bbox_z", part=None),
]


def build():
    agg = bkit.pbr("ConcreteAgg", base=(0.58, 0.57, 0.54), rough=0.86)
    mortar = bkit.pbr("MortarBed", base=(0.60, 0.59, 0.55), rough=0.88)

    # ---- one block: solid, then two full-height cores --------------
    block = bkit.rounded_box("Block0", BL, BW, BH, r=6.0, segments=2,
                             centre=(0.0, 0.0, 0.0), mat=agg)
    cd = SPEC["core_diameter"]
    for (x, _y) in bkit.grid_positions(cols=2, rows=1,
                                       pitch_x=SPEC["core_spacing"],
                                       pitch_y=1.0):
        bkit.bore(block, cd / 2.0, BH + 6.0, centre=(x, 0.0, 0.0), axis="Z",
                  host_segments=64)
    bkit.recalc(block)

    # ---- the second block, one course up and half a block along -----
    # Placed BEFORE the source is moved, because `duplicate` SETS an absolute
    # location: duplicating after moving would inherit the source's origin and
    # land both blocks on top of each other.
    bkit.duplicate(block, "Block1",
                   offset_mm=(0.0, 0.0, BH + J + BH / 2.0))
    bkit.move(block, 0.0, 0.0, BH / 2.0)

    # ---- the bed joint between the two courses ---------------------
    bkit.box("MortarBed", BL, BW - 2.0, J,
             centre=(0.0, 0.0, BH + J / 2.0), mat=mortar)

    return dict(spec=SPEC, parts=N + 1, blocks=N)

# The core DIAMETER is deliberately not declared as a check: `measure()` reports
# bounding boxes, and the bounding box of a bored block is the block, not the
# hole. A 110 mm check against Block0 would be measuring the wrong feature.