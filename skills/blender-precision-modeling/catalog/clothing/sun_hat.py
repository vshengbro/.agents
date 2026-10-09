"""
sun_hat -- a 400 mm brim straw sun hat, 137 mm to the crown apex.

A hat is the one clothing item that is genuinely a solid of revolution, so it
is the one item in this domain built with lathe() instead of a sweep. The
thickness has to be built into the profile: the walk goes out over the TOP of
the brim, round the outer edge, back along the UNDERSIDE, then up the inside of
the crown to the inside apex. A profile that only describes the outside would
lathed into a paper disc with no brim thickness at all.

The band is a real tube with a bore, not a torus -- a torus around a 380 mm
crown is a circle, and this crown is not one.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    brim_diameter=400.0,
    crown_diameter=186.0,
    crown_height=137.0,
    brim_thickness=8.0,
    crown_thickness=8.0,
    band_height=24.0,
    band_outer=208.0,
)

# (r, z) walking the shell: apex -> over the brim -> round the edge -> back
# under the brim -> up the inside of the crown -> inside apex.
HAT_PROFILE = [
    (0.0, 137.0),      # apex, outside
    (26.0, 133.0),
    (56.0, 124.0),
    (80.0, 106.0),
    (90.0, 78.0),
    (93.0, 44.0),
    (96.0, 20.0),
    (112.0, 8.0),      # brim meets the crown
    (150.0, 4.0),
    (190.0, 4.0),
    (200.0, 8.0),      # outer brim edge, top
    (193.0, 0.0),      # round the edge
    (150.0, -4.0),     # underside of the brim
    (112.0, 0.0),
    (86.0, 14.0),      # inside of the crown
    (85.0, 44.0),
    (82.0, 76.0),
    (72.0, 100.0),
    (50.0, 116.0),
    (26.0, 122.0),
    (0.0, 125.0),      # inside apex
]


def _mm(v):
    return v / bkit.MM


def build():
    straw = bkit.pbr("HatStraw", base=(0.775, 0.680, 0.455), rough=0.93)
    straw_in = bkit.pbr("HatStrawUnder", base=(0.640, 0.550, 0.360), rough=0.95)
    ribbon = bkit.pbr("HatRibbon", base=(0.235, 0.290, 0.395), rough=0.80)

    hat = bkit.lathe("SunHat", HAT_PROFILE, segments=96, mat=straw)
    bkit.recalc(hat)
    # Underside of the brim and the inside of the crown: faces whose normal
    # points back toward the axis or downward are the lining side.
    bkit.assign_faces_by(
        hat, straw_in,
        lambda c, n: _mm(n.z) < -0.25 or _mm(c.z) < 6.0,
    )

    # ---- grosgrain band: a real tube with a bore, sitting on the crown ---
    bkit.tube("SunHatBand", SPEC["band_outer"] / 2.0, 98.0, SPEC["band_height"],
              segments=96, centre=(0.0, 0.0, 40.0), axis="Z", mat=ribbon)

    # ---- bow at the front of the band ------------------------------------
    bkit.rounded_box("SunHatBowL", 46.0, 16.0, 30.0, r=6.0, segments=3,
                     centre=(-26.0, -100.0, 40.0), mat=ribbon)
    bkit.rounded_box("SunHatBowR", 46.0, 16.0, 30.0, r=6.0, segments=3,
                     centre=(26.0, -100.0, 40.0), mat=ribbon)
    bkit.cylinder("SunHatKnot", 9.0, 18.0, segments=20,
                  centre=(0.0, -104.0, 40.0), axis="Y", mat=ribbon)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="brim_diameter", mm=400.0, tol=2.0, how="diameter",
         part="SunHat"),
    dict(name="overall_height", mm=141.0, tol=2.0, how="bbox_z", part="SunHat"),
    dict(name="band_outer", mm=208.0, tol=2.0, how="bbox_y",
         part="SunHatBand"),
    dict(name="band_height", mm=24.0, tol=1.0, how="bbox_z",
         part="SunHatBand"),
]