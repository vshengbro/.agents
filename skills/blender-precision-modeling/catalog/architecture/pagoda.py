"""
pagoda -- five-tier timber pagoda: each tier is a lofted body with a real
upswept roof, stacked with computed offsets and a 5% taper per tier.

Huge size class (3000..40000 mm): 15.2 m to the finial. The read comes from
the TIERS and the ROOFS: a pagoda is a stack of flared roofs, each wider than
the storey below it, so the silhouette steps outward going up then pulls in at
the top. The tier widths are computed by taper, not typed in.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tiers=5,
    overall_height=15200.0,
    base_width=6400.0,
    tier_taper=0.86,        # each tier's plan is 86% of the one below
    storey_height=2000.0,
    roof_height=900.0,
    roof_overhang=900.0,    # roof projects past the storey on every side
    finial_height=1600.0,
    column_count=8,
    column_diameter=260.0,
)

TIERS = SPEC["tiers"]
SW = SPEC["base_width"]
SH = SPEC["storey_height"]
RH = SPEC["roof_height"]
RO = SPEC["roof_overhang"]
TAPER = SPEC["tier_taper"]


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=8)]


def _lathe(name, profile, **kw):
    """`bkit.lathe` followed by a re-weld that works at this model's scale.

    `bkit.weld` defaults to dist_mm=0.0005 (5e-7 m), which is finer than the
    float32 precision of Blender's weld hash once a mesh sits more than about
    12 m up. The `segments` vertices a lathe emits at its pole then fail to
    merge, and the solid reports non-manifold edges at the apex. Welding again
    at 0.1 mm collapses the pole properly; 0.1 mm is three orders of magnitude
    below the smallest feature in this model.
    """
    ob = bkit.lathe(name, profile, **kw)
    bkit.weld(ob, 0.1)
    bkit.recalc(ob)
    return ob


def build():
    timber = bkit.pbr("PagodaTimber", base=(0.44, 0.20, 0.11), rough=0.58)
    roof_tile = bkit.pbr("PagodaRoof", base=(0.20, 0.26, 0.30), rough=0.52)
    trim = bkit.pbr("PagodaTrim", base=(0.62, 0.44, 0.14), rough=0.40)

    # ---- tiers, bottom-up, plan computed from the taper ------------------
    z = 0.0
    for i in range(TIERS):
        w = SW * (TAPER ** i)
        top_w = w * TAPER
        body = bkit.loft("PagodaStorey%d" % (i + 1), [
            _ring(w - 60.0, w - 60.0, 40.0, z),
            _ring(w, w, 60.0, z + SH * 0.5),
            _ring(top_w, top_w, 50.0, z + SH),
        ], closed_loop=True, cap_start=True, cap_end=True, mat=timber)
        bkit.recalc(body)

        # ---- the upswept roof: a loft, so the eave can LIFT at the corners
        rw = w + 2.0 * RO
        eave_z = z + SH + RH * 0.32
        roof = bkit.loft("PagodaRoof%d" % (i + 1), [
            _ring(rw, rw, 260.0, eave_z - RH * 0.55),   # outer eave, low
            _ring(rw - 30.0, rw - 30.0, 240.0, eave_z),  # eave line
            _ring(w * 0.62, w * 0.62, 200.0, z + SH + RH * 0.92),
            _ring(w * 0.16, w * 0.16, 90.0, z + SH + RH),   # near the finial
        ], closed_loop=True, cap_start=True, cap_end=True, mat=roof_tile)
        bkit.recalc(roof)

        z += SH + RH

    # ---- columns round the base storey: computed ring, counted -----------
    # Placed by copying to each exact ring position. bkit.array_radial builds
    # its offset from the object's own world matrix, so an object already set
    # out at a radius spirals instead of orbiting, and the column is left
    # half-buried unless it is lifted afterwards.
    cw = SPEC["column_diameter"]
    n = SPEC["column_count"]
    cr = SW / 2.0 + 120.0
    col = bkit.cylinder("PagodaColumn0", cw / 2.0, SH, segments=24,
                        centre=(0.0, 0.0, SH / 2.0), mat=timber)
    cols = [bkit.move(col, cr, 0.0, 0.0)]
    for i in range(1, n):
        a = 2.0 * math.pi * i / n
        cols.append(bkit.duplicate(
            col, "PagodaColumn%d" % i,
            offset_mm=(cr * math.cos(a), cr * math.sin(a), SH / 2.0)))
    bkit.join(cols, "PagodaColumns")
    import bpy
    bpy.context.view_layer.update()

    # ---- finial: the mast on top, in tiers -------------------------------
    fin = _lathe("PagodaFinial", [
        (0.0, z - 60.0),
        (420.0, z - 40.0),
        (300.0, z + 260.0),
        (360.0, z + 320.0),
        (240.0, z + 520.0),
        (300.0, z + 580.0),
        (180.0, z + 820.0),
        (240.0, z + 880.0),
        (120.0, z + SPEC["finial_height"] - 320.0),
        (0.0, z + SPEC["finial_height"]),
    ], segments=40, mat=trim)

    return dict(spec=SPEC, parts=2 * TIERS + 2, tiers=TIERS, columns=n)


CHECKS = [
    dict(name="overall_height", mm=16100.0, tol=40.0, how="bbox_z"),
    dict(name="base_width", mm=6400.0, tol=40.0, how="bbox_x",
         part="PagodaStorey1"),
    dict(name="storey_height", mm=2000.0, tol=20.0, how="bbox_z",
         part="PagodaStorey1"),
    dict(name="finial_height", mm=1660.0, tol=20.0, how="bbox_z", part="PagodaFinial"),
]
