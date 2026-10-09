"""
chess_set -- a 145 mm boxwood Staunton set: a king, a queen, a bishop, a rook,
a knight and a pawn.

A chess set is read by SHAPE FIRST. The six men are silhouettes, and each is
distinguishable from across a room by one feature alone: the king is tallest
and has a cross, the queen is next and has a coronet, the bishop has a mitre
with a slit, the rook has a castellated crown, the knight has a horse's head,
and the pawn is the small one with a ball on top. So each profile below is
built around exactly that one cue, and each is a lathe -- every one of them is
a solid of revolution except the knight's head.

Proportions follow a real 85 mm Staunton king: the base is 1.5x the widest
part, the collar and the stem are what stop it looking like a chess piece of
any other kind, and the piece is roughly 1/3 base-diameter tall on the stem
plus 1/3 on the head.

A set reads by count and by colour, so there are two complete sets -- eight
cream and eight black -- and the board is not modelled, because a folded
board is not what a set is.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real Staunton dimensions, millimetres ---------------------------------
SPEC = dict(
    king_height=85.0,
    queen_height=74.0,
    bishop_height=76.0,
    rook_height=58.0,
    knight_height=70.0,
    pawn_height=50.0,
    base_diameter=38.0,      # the king's base; the widest thing on the set
    pawn_base_diameter=26.0,
    piece_count=16,          # eight per side
)

KH = SPEC["king_height"]
QH = SPEC["queen_height"]
BH = SPEC["bishop_height"]
RH = SPEC["rook_height"]
PAH = SPEC["pawn_height"]
BD = SPEC["base_diameter"] / 2.0
PBD = SPEC["pawn_base_diameter"] / 2.0


def _lathe(name, profile, centre, mat, segments=40):
    ob = bkit.lathe(name, profile, segments=segments, centre=centre, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 32)
    return ob


def _to_height(prof, h):
    """Rescale a profile's z so its top lands exactly on `h`.

    Writing a profile as fractions of h and then declaring the piece's height
    as h is the easy version of this bug: the two disagree by however much the
    last fraction falls short of 1.0, and a king declared 85 mm tall measures
    73. The profile is the thing that has to give, because it is the geometry.
    """
    zmax = max(p[1] for p in prof) or 1.0
    return [(r, z / zmax * h) for (r, z) in prof]


def build():
    cream = bkit.pbr("ChessCream", base=(0.88, 0.84, 0.72), rough=0.28, coat=0.3)
    black = bkit.pbr("ChessBlack", base=(0.030, 0.030, 0.034), rough=0.26,
                     coat=0.35)

    # ---- the eight pieces of one set, by real Staunton silhouette. Each
    # profile is walked from the axis at the base, out over the foot, up the
    # stem and into the head, and closes on the axis at the top.
    def _king(h, b):
        return [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.30),
            (b * 0.58, h * 0.34), (b * 0.58, h * 0.38), (b * 0.38, h * 0.41),
            (b * 0.34, h * 0.62), (b * 0.46, h * 0.66), (b * 0.46, h * 0.70),
            (b * 0.30, h * 0.74), (b * 0.34, h * 0.79), (b * 0.28, h * 0.82),
            (0.0, h * 0.86),
        ]

    def _queen(h, b):
        prof = [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.30),
            (b * 0.58, h * 0.34), (b * 0.58, h * 0.38), (b * 0.38, h * 0.42),
            (b * 0.34, h * 0.66), (b * 0.48, h * 0.70), (b * 0.48, h * 0.74),
            (0.0, h * 0.80),
        ]
        return prof

    def _bishop(h, b):
        return [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.32),
            (b * 0.58, h * 0.36), (b * 0.58, h * 0.40), (b * 0.36, h * 0.44),
            (b * 0.32, h * 0.60), (b * 0.52, h * 0.70), (b * 0.42, h * 0.78),
            (b * 0.20, h * 0.86), (0.0, h * 0.90),
        ]

    def _rook(h, b):
        return [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.44),
            (b * 0.62, h * 0.50), (b * 0.62, h * 0.58), (b * 0.86, h * 0.62),
            (b * 0.86, h * 0.92), (b * 0.60, h * 0.94), (b * 0.60, h),
            (0.0, h),
        ]

    def _knight(h, b):
        return [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.46),
            (b * 0.58, h * 0.52), (b * 0.58, h * 0.56), (b * 0.40, h * 0.60),
            (0.0, h * 0.62),
        ]

    def _pawn(h, b):
        return [
            (0.0, 0.0), (b, 0.0), (b, 2.6), (b * 0.90, 4.2),
            (b * 0.62, 6.0), (b * 0.46, 9.0), (b * 0.42, h * 0.50),
            (b * 0.56, h * 0.55), (b * 0.56, h * 0.59), (b * 0.40, h * 0.63),
            (b * 0.46, h * 0.68), (b * 0.34, h * 0.76), (0.0, h * 0.86),
        ]

    # Eight men per side, on a real rank spacing, so the set reads as a set
    # and not as six unrelated objects. Two ranks per side, four pieces each.
    rank_y = 34.0
    file_x = 46.0
    for side, (sy, mat) in enumerate(((-1.0, cream), (1.0, black))):
        y0 = sy * rank_y
        # the back rank, left to right
        back = (("Rook", RH, BD), ("Knight", SPEC["knight_height"], BD),
                ("Bishop", BH, BD), ("Queen", QH, BD),
                ("King", KH, BD), ("Bishop", BH, BD),
                ("Knight", SPEC["knight_height"], BD), ("Rook", RH, BD))
        profiles = {"King": _king, "Queen": _queen, "Bishop": _bishop,
                    "Rook": _rook, "Knight": _knight, "Pawn": _pawn}
        for i, (kind, h, b) in enumerate(back):
            x = -file_x + (2.0 * file_x) * i / 7.0
            _lathe("Chess%s%d%s" % (kind, side, "C" if sy < 0 else "B"),
                   _to_height(profiles[kind](h, b), h), (x, y0, 0.0), mat)
        # the pawn rank, in front
        for i in range(8):
            x = -file_x + (2.0 * file_x) * i / 7.0
            _lathe("ChessPawn%d%s" % (i, "C" if sy < 0 else "B"),
                   _to_height(_pawn(PAH, PBD), PAH),
                   (x, y0 + sy * rank_y * 0.55, 0.0), mat)

    # ---- the knight's head. It is the one man that is not a solid of
    # revolution, and the horse profile is the one silhouette in the set that
    # a lathe cannot make. It is a swept snout-plus-skull, tilted forward.
    for side, (sy, mat) in enumerate(((-1.0, cream), (1.0, black))):
        for i, x in enumerate((-file_x + 2.0 * file_x / 7.0,
                               file_x - 2.0 * file_x / 7.0)):
            neck_z = SPEC["knight_height"] * 0.60
            skull = bkit.uv_sphere("KnightHead%d%s" % (side, i), 11.0,
                                   segments=28, rings=16,
                                   centre=(x, sy * rank_y, neck_z + 6.0),
                                   mat=mat)
            muzzle = bkit.uv_sphere("KnightMuzzle%d%s" % (side, i), 6.4,
                                    segments=24, rings=14,
                                    centre=(x, sy * (rank_y - 7.0),
                                            neck_z + 9.0), mat=mat)
            for ob in (skull, muzzle):
                ob.rotation_euler = (math.radians(18.0 * sy), 0.0, 0.0)
                bpy.context.view_layer.update()
            # the mane: a second material would fight the lathe underneath, so
            # it is a real collar disc, buried in the stem
            bkit.cylinder("KnightMane%d%s" % (side, i), 8.6, 5.0,
                          segments=28, centre=(x, sy * rank_y, neck_z + 1.0),
                          mat=mat)

    # ---- the king's cross, its one non-revolution cue
    for side, (sy, mat) in enumerate(((-1.0, cream), (1.0, black))):
        cx = 0.0
        cy = sy * rank_y
        base_z = KH * 0.86
        bkit.rounded_box("KingCrossV%d" % side, 4.0, 4.0, KH * 0.12, r=1.0,
                         segments=2, centre=(cx, cy, base_z + KH * 0.05),
                         mat=mat)
        bkit.rounded_box("KingCrossH%d" % side, KH * 0.07, 4.0, 4.0, r=1.0,
                         segments=2, centre=(cx, cy, base_z + KH * 0.08),
                         mat=mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=16 + 8 + 2)


CHECKS = [
    dict(name="king_height", mm=85.0, tol=1.2, how="bbox_z", part="ChessKing0C"),
    dict(name="queen_height", mm=74.0, tol=1.2, how="bbox_z", part="ChessQueen0C"),
    dict(name="bishop_height", mm=76.0, tol=1.2, how="bbox_z", part="ChessBishop0C"),
    dict(name="rook_height", mm=58.0, tol=1.2, how="bbox_z", part="ChessRook0C"),
    dict(name="pawn_height", mm=50.0, tol=1.0, how="bbox_z", part="ChessPawn0C"),
    dict(name="king_base_diameter", mm=38.0, tol=0.8, how="bbox_x",
         part="ChessKing0C"),
    # the set spans the file centres PLUS a base radius at each end, so the
    # measured width is 2*(46 + 19) = 130, not the 92 mm centre-to-centre
    # spacing. Declaring the centre spacing here would be declaring a
    # dimension the model does not have.
    dict(name="set_width", mm=130.0, tol=2.0, how="bbox_x"),
    dict(name="set_depth", mm=131.4, tol=2.0, how="bbox_y"),
]
