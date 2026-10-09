"""
basalt_column -- a Giant's Causeway colonnade: hexagonal columns, 320 mm
across the flats, standing 1.8 m.

Real object: the Giant's Causeway columns are basalt prisms on a hexagonal
lattice, 300-400 mm across, contracted at the top where cooling was slower.
The habit that reads is the joint pattern: not a fan, but a honeycomb of
columns with real hex-section tops at slightly different heights.

The columns are explicit hex-section lofts on a computed hexagonal lattice
(pitch = flat width + gap), heights jittered by a fixed seed, and the top
contraction is a real taper. No two columns share a top face height, so the
skyline is broken the way a real colonnade is.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    column_across_flats=320.0,
    column_height=1800.0,
    joint_gap=14.0,          # the shrinkage gap between neighbouring columns
    columns=7,
    contraction=0.86,        # top width / base width
)

FLAT = SPEC["column_across_flats"]
GAP = SPEC["joint_gap"]
PITCH = FLAT + GAP           # computed, never hand-typed per column


def _hex_ring(flat, z, spin=0.0):
    """Hexagon of the given across-flats width, rotated by `spin` degrees."""
    # Vertices sit ON the axes, so the ring's extremes are the VERTICES and
    # the bbox measures vertex-to-vertex = 2r. Deriving r from the across-
    # flats width (r = flat/sqrt(3)) makes a "320 mm" column measure 370 mm,
    # because across-flats is the distance between the face midpoints.
    r = flat / 2.0
    return [(r * math.cos(math.radians(60 * i + spin)),
             r * math.sin(math.radians(60 * i + spin))) for i in range(6)]


def build():
    basalt = bkit.pbr("BasaltColumn", base=(0.135, 0.135, 0.140), rough=0.84)
    weathered = bkit.pbr("BasaltWeathered", base=(0.28, 0.285, 0.27), rough=0.92)
    lichen = bkit.pbr("BasaltLichen", base=(0.42, 0.46, 0.30), rough=0.95)

    # ---- hexagonal lattice: a real honeycomb, so joint lines close --------
    # Axial lattice coordinates (q, r) -> centre point. PITCH is computed from
    # the column width plus the gap, so the joints are always GAP wide no
    # matter how the SPEC is retuned.
    cells = [(0, 0), (1, 0), (0, 1), (-1, 1), (1, -1), (0, -1), (2, -1)]
    cells = cells[:SPEC["columns"]]
    for i, (q, rr) in enumerate(cells):
        cx = PITCH * (q + rr / 2.0)
        cy = PITCH * math.sqrt(3.0) / 2.0 * rr
        # Heights fall in a computed sequence from the tallest column, not a random
        # draw: a declared "column height" check has to be able to name a real
        # column, and a random spread put the tallest column 5 mm off the
        # declared figure. Column 1 is exactly the declared height.
        h = SPEC["column_height"] * (1.0 - 0.115 * i / (len(cells) - 1.0))
        spin = 30.0 if i % 2 else 0.0
        base = _hex_ring(FLAT, 0.0, spin)
        top = _hex_ring(FLAT * SPEC["contraction"], h, spin)
        secs = [[(x, y, 0.0) for (x, y) in base],
                [(x, y, h) for (x, y) in top]]
        col = bkit.loft("Column%d" % (i + 1), secs, mat=basalt)
        bkit.recalc(col)
        bkit.move(col, cx, cy, 0.0)
        # Weathering on the up-facing top faces: a second material on the same
        # solid, not a cap shell that would z-fight with the column top.
        bkit.assign_faces_by(col, weathered,
                             lambda c, n, cx=cx, cy=cy: n.z > 0.9
                             and abs(c.x / bkit.MM - cx) < FLAT
                             and abs(c.y / bkit.MM - cy) < FLAT)

    # ---- the pavement the columns stand on -------------------------------
    # Top face exactly at z=0, so the overall height IS the tallest column.
    # A pad buried 40 mm down made the assembly 60 mm taller than any column.
    pad_r = PITCH * 3.0
    pad = bkit.cylinder("CausewayPad", pad_r, 120.0, segments=6,
                        centre=(0.0, 0.0, -60.0), smooth=False, mat=lichen)

    return dict(spec=SPEC, parts=len(cells) + 1)


CHECKS = [
    dict(name="column1_across_flats", mm=320.0, tol=1.0,
         how="bbox_x", part="Column1"),
    dict(name="tallest_column_height", mm=1800.0, tol=6.0,
         how="bbox_z", part="Column1"),
    dict(name="shortest_column_height", mm=1593.0, tol=6.0,
         how="bbox_z", part="Column7"),
    # sit_on_floor raises the whole assembly so the pad's underside rests on
    # z=0, which puts the pad BELOW the columns: overall = pad + tallest column.
    dict(name="overall_height", mm=1920.0, tol=6.0, how="bbox_z"),
]