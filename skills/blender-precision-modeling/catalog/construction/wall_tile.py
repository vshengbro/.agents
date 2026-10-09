"""
wall_tile -- a pack of 9 glazed ceramic wall tiles, 200 x 100 x 9 mm.

The read on a tile is the GLAZE: a high-gloss face with a slight pillow to it,
a crisp bevelled edge, and a stack that shows the tiles are thin and identical.
A tile modelled as a plain box reads as a coaster.

Real 200 x 100 x 9 mm ceramic wall tile, the standard UK bathroom size, packed
9 to a stack with a 2 mm gap so the individual tiles stay legible. The pillow is
a real feature: the glaze domes 1.5 mm proud of the flat back, so the tile is
6 mm at the edge and 9 mm at the centre. The back is unglazed biscuit, which is
a different material from the face -- and `assign_faces_by` is how one solid
gets two surfaces without z-fighting.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    tile_length=200.0,
    tile_width=100.0,
    tile_thickness=9.0,
    edge_thickness=6.0,
    pillow=1.5,
    bevel=1.0,
    count=9,
    gap=2.0,
)

TL = SPEC["tile_length"]
TW = SPEC["tile_width"]
TT = SPEC["tile_thickness"]
TE = SPEC["edge_thickness"]
PIL = SPEC["pillow"]
N = SPEC["count"]
GAP = SPEC["gap"]

# the stack: N tiles at (TT + gap) pitch, standing on edge like a real pack
STACK_H = N * (TT + GAP) - GAP

CHECKS = [
    dict(name="tile_length", mm=200.0, tol=1.0, how="bbox_x", part="WallTile0"),
    dict(name="tile_width", mm=100.0, tol=1.0, how="bbox_y", part="WallTile0"),
    dict(name="tile_edge_thickness", mm=6.0, tol=1.0, how="bbox_z", part="WallTile0"),
    dict(name="tile_count", mm=94.0, tol=0.0, how="bbox_z", part=None),
    dict(name="stack_height", mm=94.0, tol=2.0, how="bbox_z", part=None),
    dict(name="stack_width", mm=200.0, tol=2.0, how="bbox_x", part=None),
]


def build():
    glaze = bkit.pbr("TileGlaze", base=(0.90, 0.90, 0.87), metal=0.0,
                     rough=0.08, coat=0.7)
    biscuit = bkit.pbr("TileBiscuit", base=(0.74, 0.70, 0.63), rough=0.80)

    # ---- one tile: a pillow-faced glazed slab ----------------------
    # The tile is TWO solids joined into one object: a bevelled slab at the edge
    # thickness, and a smaller pillow block standing PIL proud of it. So the tile
    # is 6 mm at the edge and 9 mm at the centre -- the difference between a tile
    # and a bevelled coaster. Joining (rather than leaving two objects) keeps it
    # one solid, so there is no interpenetration to z-fight.
    slab = bkit.rounded_box("WallTile0", TL, TW, TE, r=SPEC["bevel"],
                            segments=2, centre=(0.0, 0.0, 0.0), mat=glaze)
    inset = SPEC["bevel"] * 2.0
    pillow = bkit.rounded_box("WallTilePillow", TL - 2.0 * inset,
                              TW - 2.0 * inset, PIL, r=3.0, segments=2,
                              centre=(0.0, 0.0, TE / 2.0 + PIL / 2.0 - 2.0),
                              mat=glaze)
    tile = bkit.join([slab, pillow], "WallTile0")
    bkit.recalc(tile)

    # the back face is unglazed biscuit -- one solid, two materials
    bkit.assign_faces_by(tile, biscuit, lambda c, n: c.z * bkit.MM < -TE / 4.0)

    # ---- the pack: 9 tiles on the computed 11 mm pitch -------------
    # `duplicate` SETS an absolute location, so the source is placed first at
    # its own station and each copy is given the pitch offset explicitly.
    for i in range(N):
        z = i * (TT + GAP) + TT / 2.0
        if i == 0:
            bkit.move(tile, 0.0, 0.0, z)
        else:
            bkit.duplicate(tile, "WallTile%d" % i, offset_mm=(0.0, 0.0, z))

    return dict(spec=SPEC, parts=N, tiles=N)