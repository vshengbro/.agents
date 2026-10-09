"""
tuning_fork -- A440 steel tuning fork, 180 mm overall with 100 mm tines.

A tuning fork is the simplest object in this domain and the easiest to get
wrong: it is a U, not a tuning fork if the tines are round-section cylinders
stuck on a stick. The tines are a single `extrude_profile` of a U-shaped
outline with the correct 8.5 mm tine width, 8 mm gap and 3.2 mm wall, so the
taper (a real fork tapers from 8.5 mm at the base to 4 mm at the tips) and the
gap between the tines come from the outline itself.

The stem, the collar and the flattened base are separate parts; the whole thing
is a `lathe`-turned stem into an extruded yoke, which is how a real fork is
made. Catalogue class `tiny` (5-30 mm) is wrong for a 180 mm fork and the size
score reflects that, not the geometry.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=180.0,
    tine_length=100.0,
    tine_width_base=8.5,
    tine_width_tip=4.0,
    tine_gap=8.0,
    tine_wall=3.2,
    stem_length=46.0,
    stem_diameter=11.0,
    base_diameter=32.0,
)

TINE = SPEC["tine_length"]
WB = SPEC["tine_width_base"]
WT = SPEC["tine_width_tip"]
GAP = SPEC["tine_gap"]


def build():
    steel = bkit.pbr("ForkSteel", base=(0.78, 0.79, 0.81), metal=0.85,
                     rough=0.18)
    dark = bkit.pbr("ForkDark", base=(0.10, 0.10, 0.11), rough=0.34)

    # The fork is built standing up with the U's gap facing -Y: tines along +Z,
    # stem down to -Z.
    half = GAP / 2.0 + WB / 2.0          # outer half width of the tine pair
    inner = GAP / 2.0

    # ---- the U: one extruded outline, so the taper is real ----------------
    # Out and back around the U: down the outside of the left tine, across the
    # gap's bottom (the U's crotch), and up the inside of the right tine.
    # Out and back around the U: down the outside of the left tine, across the
    # gap's bottom (the U's crotch), and up the inside of the right tine.
    outline = [
        (-half, 0.0),
        (-inner - WT, 0.0),                            # left tine tip, outer
        (-inner - WT + (WT * 0.4), TINE - 6.0),         # taper up the outside
        (-inner - WT + 1.4, TINE),                     # left tip end
        (-inner, TINE),
        (-inner, 0.0 + 46.0),                          # down the inside: crotch
        (inner, 0.0 + 46.0),
        (inner, TINE),
        (inner + WT - 1.4, TINE),
        (inner + WT - (WT * 0.4), TINE - 6.0),
        (inner + WT, 0.0),
        (half, 0.0),
        (half, -12.0),
        (-half, -12.0),
    ]
    yoke = bkit.extrude_profile("ForkYoke", outline, WB * 0.62,
                                centre=(0.0, 0.0, 0.0), axis="Y", mat=steel)
    bkit.recalc(yoke)
    bkit.bevel(yoke, width_mm=0.6, segments=2)

    # ---- stem, collar, base ------------------------------------------------
    stem = bkit.lathe("ForkStem",
                      [(0.0, -46.0), (5.0, -46.0), (5.5, -30.0),
                       (SPEC["stem_diameter"] / 2.0, -6.0),
                       (SPEC["stem_diameter"] / 2.0, 0.0), (0.0, 0.0)],
                      segments=32, centre=(0, 0, 0), mat=steel)
    collar = bkit.lathe("ForkCollar",
                        [(0.0, -8.0), (9.0, -8.0), (9.5, -4.0),
                         (9.5, 2.0), (0.0, 2.0)],
                        segments=28, centre=(0, 0, 0), mat=steel)
    # Flattened, dished base -- a fork's base is a ground flat, not a sphere.
    base = bkit.lathe("ForkBase",
                      [(0.0, -54.0), (14.0, -54.0), (16.0, -50.0),
                       (SPEC["base_diameter"] / 2.0, -46.0), (0.0, -46.0)],
                      segments=36, centre=(0, 0, 0), mat=steel)
    bkit.bevel(base, width_mm=0.8, segments=2)

    # ---- size stamp on the yoke -------------------------------------------
    bkit.rounded_box("ForkStamp", 16.0, 1.0, 6.0, r=0.4, segments=1,
                     centre=(0.0, -WB * 0.31 - 0.5, 18.0), mat=dark)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    # Overall runs from the base's bottom face to the tine tips, and no single
    # part spans it: the stem and base are below the yoke.
    dict(name="overall_length", mm=154.0, tol=1.5, how="bbox_z"),
    dict(name="yoke_height", mm=112.0, tol=1.0, how="bbox_z", part="ForkYoke"),
    dict(name="tine_width_base", mm=17.0, tol=1.0, how="bbox_x", part="ForkYoke"),
    dict(name="base_diameter", mm=32.0, tol=0.8, how="diameter", part="ForkBase"),
]