"""
obelisk -- a 21 m granite obelisk on a stepped base: a lofted square shaft
that tapers to a point, a pyramidion, and a sarcophagus-style plinth.

Huge size class. An obelisk is the simplest object at the largest scale, which
makes it the right place to get the SHAFT TAPER exactly right: the sides taper
from a 1.9 m base to a 1.15 m shaft, then a short pyramidion takes the last
2.8 m to the point. One lathe cannot make a square, so the taper is a loft over
rounded-rect sections with a small corner radius.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=21000.0,
    base_width=3600.0,
    base_height=1500.0,
    plinth_width=2700.0,
    plinth_height=700.0,
    shaft_base_width=1900.0,
    shaft_top_width=1150.0,
    shaft_height=15800.0,
    pyramidion_height=2800.0,
    corner_radius=40.0,
)

BH = SPEC["base_height"]
PH = SPEC["plinth_height"]
SB = SPEC["shaft_base_width"]
ST = SPEC["shaft_top_width"]
SH = SPEC["shaft_height"]
PY = SPEC["pyramidion_height"]
CR = SPEC["corner_radius"]

Z0 = BH + PH


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=4)]


def build():
    granite = bkit.pbr("ObeliskGranite", base=(0.70, 0.66, 0.58), rough=0.64)
    granite_dk = bkit.pbr("ObeliskGraniteDark", base=(0.58, 0.55, 0.48),
                          rough=0.68)

    # ---- stepped base -----------------------------------------------------
    base = bkit.loft("ObeliskBase", [
        _ring(SPEC["base_width"], SPEC["base_width"], 60.0, 0.0),
        _ring(SPEC["base_width"], SPEC["base_width"], 60.0, BH - 320.0),
        _ring(SPEC["base_width"] - 240.0, SPEC["base_width"] - 240.0, 50.0,
              BH - 60.0),
        _ring(SPEC["base_width"] - 240.0, SPEC["base_width"] - 240.0, 50.0, BH),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=granite_dk)
    bkit.recalc(base)

    plinth = bkit.loft("ObeliskPlinth", [
        _ring(SPEC["plinth_width"], SPEC["plinth_width"], 45.0, 0.0),
        _ring(SPEC["plinth_width"] - 120.0, SPEC["plinth_width"] - 120.0, 40.0,
              PH - 120.0),
        _ring(SPEC["plinth_width"] - 180.0, SPEC["plinth_width"] - 180.0, 35.0,
              PH),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=granite)
    bkit.recalc(plinth)
    bkit.move(plinth, 0.0, 0.0, BH)

    # ---- shaft: the taper -------------------------------------------------
    # Four faces, four corners: the loft interpolates the plan linearly, which
    # IS the obelisk's taper (each face is a trapezoid in elevation).
    shaft = bkit.loft("ObeliskShaft", [
        _ring(SB, SB, CR, 0.0),
        _ring(SB - (SB - ST) * 0.34, SB - (SB - ST) * 0.34, CR * 0.9,
              SH * 0.34),
        _ring(SB - (SB - ST) * 0.67, SB - (SB - ST) * 0.67, CR * 0.8,
              SH * 0.67),
        _ring(ST, ST, CR * 0.7, SH),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=granite)
    bkit.recalc(shaft)
    bkit.move(shaft, 0.0, 0.0, Z0)

    # ---- pyramidion: the short pyramid on top ---------------------------
    pyr = bkit.loft("ObeliskPyramidion", [
        _ring(ST, ST, CR * 0.7, 0.0),
        _ring(ST * 0.62, ST * 0.62, CR * 0.5, PY * 0.55),
        _ring(ST * 0.26, ST * 0.26, CR * 0.3, PY * 0.88),
        _ring(120.0, 120.0, 20.0, PY),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=granite)
    bkit.recalc(pyr)
    bkit.move(pyr, 0.0, 0.0, Z0 + SH)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="overall_height", mm=20800.0, tol=30.0, how="bbox_z"),
    dict(name="base_width", mm=3600.0, tol=20.0, how="diameter",
         part="ObeliskBase"),
    dict(name="shaft_height", mm=15800.0, tol=30.0, how="bbox_z",
         part="ObeliskShaft"),
    dict(name="shaft_base_width", mm=1900.0, tol=15.0, how="bbox_x",
         part="ObeliskShaft"),
    dict(name="pyramidion_height", mm=2800.0, tol=20.0, how="bbox_z",
         part="ObeliskPyramidion"),
]
