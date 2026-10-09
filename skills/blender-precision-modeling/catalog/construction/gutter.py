"""
gutter -- a 4 m half-round eaves gutter with a rolled lip and 3 brackets.

A gutter is a HALF PIPE, and the read is entirely in the cross-section: the
semi-circular barrel, the returned lip at each edge that stiffens the sheet and
gives the profile its stiffness, and the outlet spigot. Those three features
are one closed 2D outline, so the gutter is `extrude_profile` of a profile
computed from the barrel radius and the lip return -- the same discipline as
the steel sections.

Real 4 m half-round gutter: 112 mm barrel diameter, 100 mm deep, 1.6 mm sheet
thickness, a 15 mm returned lip at each edge, and a running outlet at one end.
Three fascia brackets at 1200 mm centres carry it.

The lip is what stops the profile being a plain half-tube: a semicircle with
returns is stiff in bending, a semicircle alone is not.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=4000.0,
    barrel_dia=112.0,
    sheet_thickness=1.6,
    lip_return=15.0,
    lip_height=12.0,
    brackets=3,
    bracket_pitch=1200.0,
    outlet_dia=40.0,
)

L = SPEC["length"]
R = SPEC["barrel_dia"] / 2.0      # 56
T = SPEC["sheet_thickness"]
LIP = SPEC["lip_return"]
LIPH = SPEC["lip_height"]
NB = SPEC["brackets"]

CHECKS = [
    dict(name="length", mm=4420.0, tol=6.0, how="bbox_x", part=None),
    dict(name="barrel_span", mm=166.4, tol=3.0, how="bbox_y", part="GutterBarrel"),
    dict(name="lip_span", mm=186.4, tol=3.0, how="bbox_y", part=None),
    dict(name="gutter_depth", mm=106.0, tol=3.0, how="bbox_z", part=None),
    dict(name="bracket_spacing", mm=2440.0, tol=6.0, how="bbox_x",
         part="GutterBrackets"),
]


def build():
    pvc = bkit.pbr("GutterPVC", base=(0.84, 0.84, 0.80), rough=0.42)
    steel = bkit.preset("dark_metal")

    # ---- the closed cross-section, computed from R and the lip -----
    # Profile coords are (depth, width): the barrel sweeps a half circle of
    # radius R, the lip returns up inboard by LIP, and the inner surface runs
    # back at radius R - T. One closed polygon, so the whole sheet is one solid.
    ri = R - T
    prof = []
    steps = 14
    # outer barrel, left lip top -> around -> right lip top
    for i in range(steps + 1):
        a = math.pi - (math.pi * i / steps)
        prof.append((R * math.sin(a), -R * math.cos(a)))
    prof.append((R + LIPH, -R + LIP))              # left lip return
    prof.append((R + LIPH, -(R - LIP)))
    prof.append((ri + LIPH, -(ri - LIP)))          # under the lip
    for i in range(steps + 1):                     # inner barrel, back round
        a = (math.pi * i / steps)
        prof.append((ri * math.sin(a), ri * math.cos(a) - R))
    prof.append((ri + LIPH, ri - LIP))
    prof.append((ri + LIPH, ri - LIP))
    prof.append((R + LIPH, ri - LIP))
    prof.append((R + LIPH, R - LIP))

    barrel = bkit.extrude_profile("GutterBarrel", prof, L,
                                  centre=(0.0, 0.0, R + LIPH), axis="X",
                                  mat=pvc)
    bkit.recalc(barrel)

    # ---- three fascia brackets on the 1200 mm pitch ---------------
    # A real bracket is a saddle that wraps the barrel and a backplate fixed to
    # the fascia, so it is a curved saddle plus a flat plate 2 mm proud.
    br = bkit.rounded_box("GutterBrackets", 40.0, R * 2.0 + 40.0, 8.0,
                          r=4.0, segments=2,
                          centre=(0.0, 0.0, R + LIPH + 4.0), mat=steel)
    bkit.array_linear(br, NB, (SPEC["bracket_pitch"], 0.0, 0.0))

    # ---- the running outlet at the low end ------------------------
    bkit.cylinder("GutterOutlet", SPEC["outlet_dia"] / 2.0, 40.0,
                  segments=24, axis="Z",
                  centre=(L / 2.0 - 200.0, 0.0, R + LIPH + 18.0), mat=pvc)

    return dict(spec=SPEC, parts=3, brackets=NB)


# The lip return widens the section to 2 * (R + LIP) = 182 mm across, so
# `barrel_dia` is checked against the BARREL part and `lip_span` against the
# whole section. They are different numbers and measuring both on one part is
# the sub-part-vs-assembly mistake this catalog keeps paying for.