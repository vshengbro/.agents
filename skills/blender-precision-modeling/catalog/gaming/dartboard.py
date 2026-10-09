"""
dartboard -- 300 mm board: 20 sectors, 5 scoring rings, real spider wires.

A dartboard is the most countable object in this domain, so it is modelled by
count rather than by eye. The scoring bands come straight off the standard
proportions measured as fractions of the board radius (double outer 1.00, treble
outer 0.583, outer bull 0.082, inner bull 0.038), so the ring boundaries are
CONSEQUENCES of one radius rather than five numbers typed side by side. The 20
sector dividers are one box swept 20 times by array_radial about the board's
face centre -- never hand-placed, or two of them land on the same spoke.

Each ring is a separate solid with its own colour, which is the only reason a
dartboard reads as a dartboard rather than as a brown disc: the bands are what
the eye counts, not the wires.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

R = 138.0                 # board radius (276 mm board)
BOARD_T = 18.0
FACE_T = 2.0

# standard dartboard band radii as a fraction of the outer radius
F_DOUBLE_OUT = 1.000
F_DOUBLE_IN = 0.935
F_TREBLE_OUT = 0.583
F_TREBLE_IN = 0.524
F_OUTER_BULL = 0.082
F_INNER_BULL = 0.038

R_DOUBLE_OUT = R * F_DOUBLE_OUT
R_DOUBLE_IN = R * F_DOUBLE_IN
R_TREBLE_OUT = R * F_TREBLE_OUT
R_TREBLE_IN = R * F_TREBLE_IN
R_OUTER_BULL = R * F_OUTER_BULL
R_INNER_BULL = R * F_INNER_BULL

SECTORS = 20
WIRE_W = 1.2
WIRE_T = 1.6
SECTOR_SPAN = 360.0 / SECTORS

SPEC = dict(board_diameter=2.0 * R,
            board_thickness=BOARD_T,
            sector_count=SECTORS,
            sector_span=SECTOR_SPAN,
            treble_outer_diameter=2.0 * R_TREBLE_OUT,
            inner_bull_diameter=2.0 * R_INNER_BULL,
            double_band_width=R_DOUBLE_OUT - R_DOUBLE_IN,
            overall_diameter=296.0)


def _band(name, r_out, r_in, z, mat, segments=160):
    """One scoring band: a flat annulus of real radial width.

    A band whose inner radius is zero (the inner bull) is lathed as a SOLID
    disc instead: closing the loop by returning along the axis would revolve a
    segment between two axis points into a ring of zero-area faces, which is
    the one non-manifold edge this model would otherwise have.
    """
    if r_in <= 0.0:
        return bkit.lathe(name, [(0.0, 0.0), (r_out, 0.0), (r_out, FACE_T),
                                 (0.0, FACE_T)],
                          segments=segments, centre=(0.0, 0.0, z), mat=mat)
    return bkit.lathe(name,
                      [(r_in, 0.0), (r_out, 0.0), (r_out, FACE_T), (r_in, FACE_T),
                       (r_in, 0.0)],
                      segments=segments, centre=(0.0, 0.0, z), cap_ends=False,
                      mat=mat)


def build():
    sisal = bkit.pbr("DartSisal", base=(0.52, 0.40, 0.24), metal=0.0, rough=0.88)
    black = bkit.pbr("DartBlack", base=(0.05, 0.05, 0.05), metal=0.0, rough=0.70)
    green = bkit.pbr("DartGreen", base=(0.05, 0.30, 0.14), metal=0.0, rough=0.60)
    red = bkit.pbr("DartRed", base=(0.55, 0.05, 0.05), metal=0.0, rough=0.60)
    wire = bkit.pbr("SpiderWire", base=(0.20, 0.20, 0.22), metal=0.85, rough=0.30)
    frame = bkit.pbr("DartFrame", base=(0.10, 0.10, 0.12), metal=0.0, rough=0.40)

    # ---- the sisal body -----------------------------------------------------
    body = bkit.lathe("Sisal",
                      [(0.0, 0.0), (R + 4.0, 0.0), (R + 4.0, BOARD_T),
                       (R, BOARD_T), (R, FACE_T), (0.0, FACE_T)],
                      segments=160, mat=sisal)

    # ---- the five scoring bands, bottom first so the stack reads outward ---
    bands = []
    bands.append(_band("SingleRing", R_DOUBLE_IN, R_TREBLE_OUT, FACE_T, black))
    bands.append(_band("TrebleRing", R_TREBLE_OUT, R_TREBLE_IN, FACE_T, red))
    bands.append(_band("DoubleRing", R_DOUBLE_OUT, R_DOUBLE_IN, FACE_T, red))
    bands.append(_band("BullRing", R_OUTER_BULL, R_INNER_BULL, FACE_T, green))
    bands.append(_band("InnerBull", R_INNER_BULL, 0.0, FACE_T, black))
    for b in bands:
        pass
    # lift the inner rings fractionally so they draw on top of the outer ones
    for i, b in enumerate(bands):
        bkit.move(b, 0.0, 0.0, FACE_T + 0.12 * (len(bands) - 1 - i))

    # ---- 20 sector dividers, swept about the face centre -------------------
    # ONE divider on the +X spoke, then array_radial. Hand-placing twenty of
    # them is how two dividers end up on the same spoke.
    spoke = bkit.rounded_box("Spokes", R + 4.0, WIRE_W, WIRE_T, r=0.3, segments=2,
                             centre=((R + 4.0) / 2.0, 0.0, FACE_T + 0.8), mat=wire)
    bkit.array_radial(spoke, SECTORS, centre=(0.0, 0.0, FACE_T + 0.8))

    # ---- two concentric spider wires ---------------------------------------
    for r in (R_OUTER_BULL, R_INNER_BULL):
        bkit.torus("BullWire", r, 0.5, seg_major=96, seg_minor=8,
                   centre=(0.0, 0.0, FACE_T + 0.8), mat=wire)

    # ---- surround: a turned trim ring, not a rope -------------------------
    # A rope surround would push the silhouette to 360 mm; the catalogue size
    # class for this item is small, whose band tops out at 300 mm.
    surround = bkit.lathe("Surround",
                          [(R + 2.0, -10.0), (148.0, -10.0), (148.0, 2.0),
                           (R + 2.0, 2.0), (R + 2.0, -10.0)],
                          segments=120, cap_ends=False, mat=frame)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    # the sisal body runs 4 mm proud of the scoring face on every side
    dict(name="board_diameter", mm=284.0, tol=0.3, how="diameter", part="Sisal"),
    dict(name="board_thickness", mm=18.0, tol=0.2, how="bbox_z", part="Sisal"),
    dict(name="treble_outer", mm=160.9, tol=0.2, how="diameter", part="TrebleRing"),
    dict(name="inner_bull", mm=10.5, tol=0.1, how="diameter", part="InnerBull"),
    dict(name="double_ring_outer", mm=276.0, tol=0.2, how="bbox_x", part="DoubleRing"),
    # 2 * 138 * 0.935: the single-scoring ring's outside
    dict(name="single_ring_outer", mm=258.1, tol=0.2, how="bbox_x",
         part="SingleRing"),
    dict(name="overall_diameter", mm=296.0, tol=0.3, how="diameter", part="Surround"),
    dict(name="overall_height", mm=28.0, tol=0.2, how="bbox_z", part=None)
]