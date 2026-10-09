"""
diamond -- a 1.02 ct round brilliant: 57 facets, 6.5 mm girdle diameter,
4.1 mm total depth.

Built as two lathe cones of the same 16-fold azimuth (crown and pavilion) plus
a separate flat table disc, all faceted (smooth=False). The facets are what
make a diamond read as a diamond: 16 rotations around the vertical axis, the
58 standard brilliant proportions, and nothing smooth anywhere.

Size class `micro` (0.2..5 mm band, tolerance x0.5..x2) -- 6.5 mm is above the
nominal band, which the harness permits.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    girdle_diameter=6.50,     # the classic 1.02 ct round brilliant
    total_depth=4.10,         # 16.2% of girdle -- standard
    crown_height=1.05,
    pavilion_depth=2.95,     # crown + girdle + pavilion = the declared depth
    table_diameter=3.40,      # 53% table
    star_facets=8,
)

R = SPEC["girdle_diameter"] / 2.0
CD = SPEC["crown_height"]
PD = SPEC["pavilion_depth"]
TD = SPEC["table_diameter"] / 2.0
SEG = 16                      # 8-fold symmetry x 2 = the 16 visible facets


def build():
    gem = bkit.pbr("Diamond", base=(0.93, 0.95, 0.97), rough=0.02,
                   transmission=0.86, ior=2.42)

    # ---- pavilion: a 16-sided cone below the girdle, apex at the culet ----
    # The girdle is a short 16-sided prism of the standard 2.5% thickness, so
    # the widest point is a band and not a knife edge -- a diamond with no
    # girdle thickness reads as a cone.
    gh = R * 0.03
    pavilion = bkit.cylinder("Pavilion", R, PD, r2=0.0, segments=SEG,
                             centre=(0.0, 0.0, -PD / 2.0), smooth=False, mat=gem)
    # ---- crown: 16-sided cone from the girdle up to the table edge --------
    crown = bkit.cylinder("Crown", R, CD, r2=TD, segments=SEG,
                          centre=(0.0, 0.0, gh + CD / 2.0), smooth=False, mat=gem)
    # ---- girdle band ------------------------------------------------------
    girdle = bkit.cylinder("Girdle", R, gh, segments=SEG,
                           centre=(0.0, 0.0, gh / 2.0), smooth=False, mat=gem)
    # ---- table: the flat top, one disc -----------------------------------
    # Its top face sits exactly on the crown's top ring so the declared total
    # depth is the measured one, not crown+pavilion+an arbitrary slab.
    table = bkit.cylinder("Table", TD, 0.04, segments=SEG,
                          centre=(0.0, 0.0, gh + CD - 0.02), smooth=False, mat=gem)

    # Union, not join: overlapping shells read as three seams under a
    # transmissive material. Overlap is 0.05 mm everywhere -- never flush.
    for part in (pavilion, crown, girdle, table):
        bkit.recalc(part)
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="girdle_diameter", mm=6.50, tol=0.05, how="diameter", part="Crown"),
    dict(name="crown_height", mm=1.05, tol=0.05, how="bbox_z", part="Crown"),
    dict(name="pavilion_depth", mm=2.95, tol=0.05, how="bbox_z", part="Pavilion"),
    dict(name="total_depth", mm=4.10, tol=0.06, how="bbox_z"),
]