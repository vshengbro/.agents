"""
bathtub -- 1700 mm acrylic bath: a fold-back loft with a real 8 mm wall, a
rolled rim, a flat floor that slopes to the waste, and a moulded end.

A bath is the clearest large hollow vessel in the catalog. Two numbers do the
work: the rim is rolled (a 35 mm radius, not a square corner), and the inner
floor is FLATTER than the bowl -- a bath floor slopes only enough to drain, so
the inner wall meets it in a fillet rather than a cone.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1700.0,
    width=750.0,
    height=560.0,          # floor to rim
    wall=8.0,              # acrylic
    rim_width=60.0,
    bowl_depth=420.0,      # rim down to the floor of the well
    floor_flat_length=1100.0,   # flat area at the bottom of the well
    waste_diameter=50.0,
    end_thickness=90.0,    # solid moulded end
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
WALL = SPEC["wall"]
RIM = SPEC["rim_width"]
BOWL_Z = H - RIM


def _ring(sx, sy, r, z):
    """One rounded-rect loft section at height z.

    `rounded_rect_section` silently self-intersects when r > min(sx,sy)/2; a
    loft built from such a ring survives until the first boolean, which then
    returns an empty mesh. Clamp rather than trust.
    """
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=10)]


def build():
    acrylic = bkit.pbr("BathAcrylic", base=(0.93, 0.94, 0.94), rough=0.10,
                       coat=0.6)

    # Outer shell: a tall rounded-rect vessel. The corner radius grows toward
    # the rim so the bath has the soft, near-oval plan of a real one.
    tub = bkit.loft("Bath", [
        _ring(L - 260.0, W - 190.0, 130.0, 0.0),          # base, tucked under
        _ring(L - 120.0, W - 100.0, 170.0, 120.0),        # lower flank
        _ring(L - 30.0, W - 25.0, 210.0, 380.0),          # upper flank
        _ring(L, W, 235.0, BOWL_Z),                       # rim, outer
        _ring(L, W, 235.0, H),                            # rim top, outer
        _ring(L - RIM * 0.8, W - RIM * 0.8, 200.0, H),    # across the rim
        _ring(L - RIM * 0.8 - WALL, W - RIM * 0.8 - WALL, 195.0, BOWL_Z),
        _ring(L - RIM - 120.0, W - RIM - 120.0, 180.0, 190.0),   # inner wall
        _ring(SPEC["floor_flat_length"] + 240.0,
              W - RIM - 260.0, 150.0, 150.0),              # fillet into floor
        _ring(SPEC["floor_flat_length"], W - RIM - 340.0, 120.0, 140.0),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=acrylic)
    bkit.recalc(tub)

    # ---- waste -------------------------------------------------------------
    # Placed at the low end of the floor, offset from centre the way a real
    # bath waste is -- dead centre reads as a sink.
    bkit.bore(tub, SPEC["waste_diameter"] / 2.0, depth=180.0,
              centre=(-L / 2.0 + 330.0, 0.0, 140.0), axis="Z", host_segments=120)

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="length", mm=1700.0, tol=1.0, how="bbox_x", part="Bath"),
    dict(name="width", mm=750.0, tol=1.0, how="bbox_y", part="Bath"),
    dict(name="height", mm=560.0, tol=1.0, how="bbox_z", part="Bath"),
    dict(name="longest", mm=1700.0, tol=1.0, how="longest"),
]
