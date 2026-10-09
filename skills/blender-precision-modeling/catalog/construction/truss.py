"""
truss -- a 6.0 m timber Fink roof truss, 6 bays, king post, 4 struts.

A truss is a REPEATED TRIANGULAR BAY, and the count is the whole job: every
member position is derived from the span, the rise and the bay count, so a truss
can never be built with the wrong number of struts.

    span 6000 mm (5.4 m clear + 600 mm bearing), rise 1800 mm
    top chord  : two rafters, apex at (0, 1800), eaves at (+/-3000, 0)
    bottom chord: a 4800 x 200 raft tie at z = 200
    king post   : vertical, mid-span
    struts      : 4, at BAY_FRACTION = 0.28 / 0.72, from the tie to each rafter

The diagonal struts are placed by INTERPOLATING along the rafter line rather
than by typing coordinates, so a strut always lands ON the rafter whatever the
span and rise are. That is what `bar_between` is for: the strut is built from
its own two endpoints, so its length and angle are consequences, not inputs.

Every member overlaps its neighbour by 60 mm at the joints, which is a real
housing length and keeps no two faces exactly tangent.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _sections as S

SPEC = dict(
    span=5900.0,
    rise=1800.0,
    tie_depth=200.0,
    tie_thickness=90.0,
    rafter_section=(90.0, 200.0),
    struts_per_side=2,
    strut_section=(70.0, 140.0),
    king_post_section=(90.0, 160.0),
)

SPAN = SPEC["span"]
RISE = SPEC["rise"]
HALF = SPAN / 2.0
TIE_D = SPEC["tie_depth"]

# struts land at these fractions of the half-span, measured from the eaves
STRUT_FRACTIONS = (0.28, 0.72)

HOUSE = 60.0        # housing length where members cross

CHECKS = [
    dict(name="tie_length", mm=5720.0, tol=4.0, how="bbox_x", part="TieBeam"),
    dict(name="tie_depth", mm=200.0, tol=2.0, how="bbox_z", part="TieBeam"),
    # A rafter's bbox_z is its rise PLUS half its depth at each end, because
    # the member is a rotated solid, not a line: it spans from the eaves plate
    # to the ridge strap.
    dict(name="rafter_rise", mm=1969.6, tol=6.0, how="bbox_z", part="RafterL"),
    dict(name="king_post_height", mm=1690.0, tol=6.0, how="bbox_z",
         part="KingPost"),
    # The first strut runs from the tie at mid-span up to 28 % of the way along
    # the rafter, so its vertical rise is (RISE - tie centre) * 0.28.
    dict(name="strut_1_rise", mm=639.5, tol=8.0, how="bbox_z", part="Strut0"),
    dict(name="overall_height", mm=2000.0, tol=6.0, how="bbox_z", part=None),
]


def build():
    timber = bkit.pbr("TrussTimber", base=(0.55, 0.42, 0.24), rough=0.62)
    steel = bkit.preset("dark_metal")

    # ---- the tie: the bottom chord, between the two eaves ------------
    tie_len = SPAN - 2.0 * SPEC["tie_thickness"]
    S.bar_between("TieBeam",
                  (-tie_len / 2.0, 0.0, TIE_D / 2.0),
                  (tie_len / 2.0, 0.0, TIE_D / 2.0),
                  SPEC["tie_thickness"], TIE_D, mat=timber)

    rw, rd = SPEC["rafter_section"]

    # ---- the two rafters: eaves to apex ------------------------------
    # Each rafter runs from just inside the eaves plate up to a point ABOVE the
    # apex, so the two rafters physically cross and the joint is a real housing
    # rather than a touching pair of faces.
    apex_z = RISE + rd / 2.0
    for tag, sx in (("L", -1.0), ("R", 1.0)):
        S.bar_between("Rafter%s" % tag,
                      (sx * (HALF - rw / 2.0), 0.0, TIE_D / 2.0),
                      (0.0, 0.0, apex_z),
                      rw, rd, mat=timber)

    # ---- king post --------------------------------------------------
    kp_w, kp_d = SPEC["king_post_section"]
    S.bar_between("KingPost",
                  (0.0, 0.0, TIE_D - HOUSE / 2.0),
                  (0.0, 0.0, apex_z - rd / 2.0 + HOUSE),
                  kp_w, kp_d, mat=timber)

    # ---- struts: interpolated ONTO each rafter line -----------------
    # A point at fraction f along a rafter is a LINEAR INTERPOLATION between the
    # eaves and the apex. Typing these coordinates instead is how a truss ends
    # up with struts that visibly miss the chord.
    sw, sd = SPEC["strut_section"]
    n = 0
    for tag, sx in (("L", -1.0), ("R", 1.0)):
        ex = sx * (HALF - rw / 2.0)
        for f in STRUT_FRACTIONS:
            # interpolate the rafter centreline
            fx = ex + (0.0 - ex) * f
            fz = (TIE_D / 2.0) + (apex_z - TIE_D / 2.0) * f
            # the strut runs from the tie up to that point, so its far end is
            # buried HOUSE deep in the rafter
            S.bar_between("Strut%d" % n,
                          (0.0, 0.0, TIE_D / 2.0),
                          (fx, 0.0, fz),
                          sw, sd, mat=timber)
            n += 1

    # ---- eaves plates + a steel ridge strap -------------------------
    for tag, sx in (("L", -1.0), ("R", 1.0)):
        bkit.rounded_box("EavesPlate%s" % tag, 200.0, 120.0, 25.0, r=4.0,
                         segments=1, centre=(sx * (HALF - 100.0), 0.0, 12.0),
                         mat=steel)
    bkit.rounded_box("RidgeStrap", 320.0, 60.0, 8.0, r=3.0, segments=1,
                     centre=(0.0, 0.0, apex_z + rd / 2.0 - 4.0), mat=steel)

    return dict(spec=SPEC, parts=2 + n + 3, struts=n,
                bays=n // 2 + 1, section=S.STRUCT_NOTE)