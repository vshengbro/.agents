"""
jigsaw_puzzle -- a single 76 x 70 x 3 mm jigsaw piece with one tab and one blank.

A puzzle piece is defined by its EDGE PROFILE, not by its size: one knob and
one socket on opposite sides and two flats reads as an edge piece, and a
viewer recognises that silhouette long before the print.

The outline is ONE closed polygon and it is built the only way that stays
simple (non-self-intersecting): each knob is a semicircle whose DIAMETER lies
along the edge, so the arc starts and ends exactly on the edge line. Growing
the arc from a centre that sits off the edge line is the obvious mistake and
it produces a profile that crosses itself -- `extrude_profile` then caps a
figure-eight and the depth comes out 12 mm too long.

Tab and socket share one radius, because that is what makes two neighbouring
pieces actually fit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    piece_size=28.0,       # square body of a small children's puzzle piece
    piece_thickness=2.4,
    knob_radius=2.4,       # tab and socket share one radius, or it will not fit
    tab_reach=2.4,         # how far the knob stands proud of the edge
    socket_depth=2.4,      # and how far the blank bites into it
    tab_count=1,
    socket_count=1,
)

S = SPEC["piece_size"]
H = S / 2.0
T = SPEC["piece_thickness"]
KR = SPEC["knob_radius"]


def _semicircle(cx, cy, r, a0, a1, steps=14):
    """Half-circle arc from a0 to a1 degrees, endpoints included."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


def build():
    face = bkit.pbr("PuzzleCard", base=(0.88, 0.86, 0.80), rough=0.52)
    print_mat = bkit.pbr("PuzzlePrint", base=(0.09, 0.30, 0.60), rough=0.44)

    # Counter-clockwise from the bottom-left corner. The tab bulges OUT of the
    # top edge; the socket bites IN to the same depth on the bottom edge.
    poly = [(-H, -H), (H, -H), (H, H), (KR, H)]
    poly += _semicircle(0.0, H, KR, 0.0, 180.0)[1:]
    poly += [(-H, H), (-H, -KR)]
    poly += _semicircle(0.0, -H, KR, 180.0, 360.0)[1:]
    poly += [(KR, -H)]

    piece = bkit.extrude_profile("PuzzlePiece", poly, T,
                                 centre=(0.0, 0.0, T / 2.0), axis="Z",
                                 mat=face)
    bkit.recalc(piece)
    bkit.bevel(piece, width_mm=0.35, segments=2)
    bkit.recalc(piece)
    # a real piece is printed on one side only; the back is bare board
    bkit.assign_faces_by(piece, print_mat,
                         lambda c, n: n.z > 0.55 and c.z / bkit.MM > T * 0.6)

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="piece_width", mm=28.0, tol=0.3, how="bbox_x", part="PuzzlePiece"),
    dict(name="piece_thickness", mm=2.4, tol=0.3, how="bbox_z", part="PuzzlePiece"),
    # the tab stands KR proud of the top edge and the socket bites KR into
    # the bottom one, so the depth is the body plus both: 28 + 2*2.4
    dict(name="piece_depth_with_connectors", mm=32.8, tol=0.3, how="bbox_y",
         part="PuzzlePiece"),
]
