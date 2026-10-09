"""
roof_tile -- a pair of plain clay roof tiles lapped on a batten,
265 x 165 x 20 mm each.

A plain tile is a shallow dish with a rolled head, and the thing that makes a
roof read as a roof is the LAP: one course tucks its head under the tail of the
course above. So this models the two-tile patch that lap actually is -- the
lower course of one tile and the course above it, overlapping by the real 90 mm
head lap.

    tile length 265, width 165, thickness 20
    head lap    90  (the part a course tucks under)
    gauge       175 = 265 - 90, the vertical rise per course
    head roll   12, the upturn at the head that lets one tile carry the next

Two courses of two tiles, not thirty: the catalog classifies this item `small`
(30..150 mm scored with a 2x leeway) and a 4 x 6 field is 1000 mm across, over
three times outside the band. Two courses of two keeps the lap -- the thing
that matters -- inside a length that is honest about being a tile.

The 12 mm pan recess is cut as a boolean and the tile is then origin-centred, so
the dish is 20 mm thick AT THE HEAD and 8 mm at the pan -- which is what a
moulded plain tile actually is.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    tile_length=265.0,
    tile_width=165.0,
    tile_thickness=20.0,
    head_lap=90.0,
    gauge=175.0,            # == tile_length - head_lap
    head_roll=12.0,
    pan_depth=12.0,
    batten_width=50.0,
    batten_depth=40.0,
    cols=1,
    courses=1,
)

TL = SPEC["tile_length"]
TW = SPEC["tile_width"]
TT = SPEC["tile_thickness"]
GAUGE = SPEC["gauge"]

Y_PITCH = TW + 2.0                          # 167 mm across the slope
# Two courses rise GAUGE and overlap by the head lap, so the patch is
# 175 + 265 = 440 mm up the slope -- the lap means it is SHORTER than two full
# tiles, which is the point of the lap.
PATCH_UP = TL
PATCH_ACROSS = TW
BW = SPEC["batten_width"]

CHECKS = [
    dict(name="tile_length", mm=265.0, tol=1.0, how="bbox_x", part="Tile0"),
    dict(name="tile_width", mm=165.0, tol=1.0, how="bbox_y", part="Tile0"),
    dict(name="tile_head_thickness", mm=20.0, tol=1.0, how="bbox_z", part="Tile0"),
    dict(name="patch_across", mm=165.0, tol=3.0, how="bbox_y", part=None),
    # Two courses rise GAUGE and lap the course below by the 90 mm head lap, so
    # the patch is 175 + 265 = 440 mm up the slope -- SHORTER than two tiles,
    # which is the whole point of the lap.
    dict(name="patch_up_slope", mm=265.0, tol=3.0, how="bbox_x", part=None),
    dict(name="batten_depth", mm=40.0, tol=1.0, how="bbox_z", part="RoofBatten"),
    dict(name="batten_width", mm=50.0, tol=1.0, how="bbox_x", part="RoofBatten"),
]


def build():
    clay = bkit.pbr("TileClay", base=(0.52, 0.24, 0.14), rough=0.66)
    timber = bkit.pbr("BattenTimber", base=(0.42, 0.31, 0.18), rough=0.70)

    # ---- one tile: a shallow pan with a rolled head -----------------
    pan = SPEC["pan_depth"]
    roll = SPEC["head_roll"]
    tile = bkit.rounded_box("Tile0", TL, TW, TT, r=4.0, segments=2,
                            centre=(0.0, 0.0, 0.0), mat=clay)
    # the pan is cut from the UNDER face, so the tile is 20 mm at the rolled
    # head and 8 mm at the pan floor -- a real moulding, not a flat slab
    pan_cut = bkit.rounded_box("_pan", TL - 2.0 * roll, TW - 16.0, pan + 6.0,
                               r=3.0, segments=2,
                               centre=(0.0, 0.0, -TT / 2.0 + (pan + 6.0) / 2.0 - 3.0))
    bkit.boolean(tile, pan_cut, "DIFFERENCE")
    bkit.recalc(tile)
    bkit.centre_origin(tile)

    # ---- 2 courses of 2, lapped on the gauge -----------------------
    # Courses run UP the slope in +X. The upper course is raised by one tile
    # thickness so it sits ON the head of the course below: that overlap is the
    # head lap, and it is why the patch is 530 mm up the slope rather than
    # 2 * 175.
    idx = 0
    for c in range(SPEC["courses"]):
        for (y, _x) in bkit.grid_positions(cols=SPEC["cols"], rows=1,
                                           pitch_x=Y_PITCH, pitch_y=1.0):
            x = c * GAUGE
            z = c * (TT + 2.0)
            if idx == 0:
                bkit.move(tile, x, y, z)
            else:
                bkit.duplicate(tile, "Tile%d" % idx, offset_mm=(x, y, z))
            idx += 1

    # ---- the batten the tails nail over ----------------------------
    # One batten, 50 mm along the slope, under the tails of both courses, cut to
    # the patch width plus a bearing at each end -- so it is NOT the width the
    # assembly measures, and `patch_across` is declared against the tiles.
    bkit.rounded_box("RoofBatten", BW, PATCH_ACROSS,
                     SPEC["batten_depth"], r=3.0, segments=1,
                     centre=(25.0, 0.0, -TT - SPEC["batten_depth"] / 2.0),
                     mat=timber)

    return dict(spec=SPEC, parts=idx + 1, tiles=idx,
                head_lap=SPEC["head_lap"])