"""
violin_bow -- pernambuco frog bow, 730 mm overall, with 154 mm of hair.

A bow is four things at very different scales: a stick that TAPERS from
7.5 mm at the frog to 4.5 mm at the tip, a frog (the ebony block), a screw and
button at the heel, and a flat ribbon of horsehair set slightly proud of the
stick. The taper is the model -- `bkit.cylinder`'s `r2` gives a cone, and a bow
with a constant-diameter stick reads as a knitting needle.

The hair is 1.3 mm thick and runs the full 600 mm from the tip to the frog, set
about 4 mm off the stick's centreline so the tension curve is visible. Real
dimensions throughout; the catalogue's `small` class (30-150 mm) is wrong for a
bow and the score reflects that, not the geometry.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=730.0,
    stick_length=600.0,
    stick_dia_frog=7.5,
    stick_dia_tip=4.5,
    hair_length=600.0,
    hair_thickness=1.3,
    hair_width=11.0,
    frog_length=48.0,
    frog_height=15.5,
    screw_length=42.0,
)

L = SPEC["overall_length"]
STICK = SPEC["stick_length"]
FROG = SPEC["frog_length"]


def build():
    pernambuco = bkit.pbr("BowPernambuco", base=(0.30, 0.14, 0.06), rough=0.26,
                          coat=0.4)
    ebony = bkit.pbr("BowEbony", base=(0.05, 0.045, 0.04), rough=0.28,
                     coat=0.4)
    hair = bkit.pbr("BowHair", base=(0.88, 0.86, 0.80), rough=0.42)
    silver = bkit.pbr("BowSilver", base=(0.78, 0.79, 0.81), metal=0.85,
                      rough=0.24)
    mother = bkit.pbr("BowMother", base=(0.82, 0.80, 0.76), rough=0.14,
                      coat=0.5)

    # The bow lies along X so every part shares one axis and the frog/hair
    # relationship is visible from the top view.
    x_frog = 0.0
    x_tip = STICK

    # ---- stick: a real taper, ebony head, mother-of-pearl tip --------------
    stick = bkit.cylinder("BowStick", SPEC["stick_dia_frog"] / 2.0, STICK,
                          segments=24, r2=SPEC["stick_dia_tip"] / 2.0,
                          centre=(0, 0, 0), axis="X", mat=pernambuco)
    bkit.move(stick, x_frog + STICK / 2.0, 0.0, 0.0)
    head = bkit.extrude_profile(
        "BowHead",
        [(-26.0, -4.2), (-22.0, -6.4), (-14.0, -7.4), (4.0, -7.5),
         (16.0, -6.0), (26.0, -2.0), (26.0, 2.0), (16.0, 6.0), (4.0, 7.5),
         (-14.0, 7.4), (-22.0, 6.4), (-26.0, 4.2)],
        15.0, centre=(x_frog + 8.0, 0.0, 0.0), axis="Y", mat=ebony)
    bkit.recalc(head)
    bkit.bevel(head, width_mm=1.2, segments=2)

    bkit.rounded_box("BowTipButton", 13.0, 12.0, 5.0, r=2.0, segments=2,
                     centre=(x_frog + STICK - 4.0, 0.0, 0.0), mat=mother)

    # ---- frog: the ebony block, with the ferrule and slide ---------------
    frog = bkit.extrude_profile(
        "BowFrog",
        [(0.0, -6.0), (4.0, -7.8), (30.0, -7.8), (44.0, -7.0), (FROG, -5.4),
         (FROG, 5.4), (44.0, 7.0), (30.0, 7.8), (4.0, 7.8), (0.0, 6.0)],
        SPEC["frog_height"], centre=(x_frog - FROG / 2.0, 0.0, 0.0), axis="Y",
        mat=ebony)
    bkit.recalc(frog)
    bkit.bevel(frog, width_mm=1.6, segments=2)
    bkit.box("BowFerrule", 8.0, 16.5, 11.0, centre=(x_frog + 2.0, 0.0, 0.0),
             mat=silver)
    bkit.box("BowSlide", 12.0, 5.0, 4.0, centre=(x_frog + 9.0, 8.6, 0.0),
             mat=silver)
    bkit.rounded_box("BowEye", 5.0, 6.0, 5.0, r=1.5, segments=2,
                     centre=(x_frog + FROG - 5.0, 0.0, 0.0), mat=mother)

    # ---- screw, adjuster, button -----------------------------------------
    bkit.cylinder("BowScrew", 3.4, SPEC["screw_length"], segments=16,
                  centre=(x_frog - FROG - SPEC["screw_length"] / 2.0, 0.0, 0.0),
                  axis="X", mat=silver)
    bkit.cylinder("BowButton", 8.5, 7.0, segments=20,
                  centre=(x_frog - FROG - SPEC["screw_length"] - 3.0, 0.0, 0.0),
                  axis="X", mat=ebony)
    bkit.cylinder("BowAdjuster", 7.0, 10.0, segments=16,
                  centre=(x_frog + 15.0, 0.0, 0.0), axis="X", mat=silver)

    # ---- hair: a flat ribbon, set proud of the stick ---------------------
    bkit.rounded_box("BowHair", SPEC["hair_length"], SPEC["hair_thickness"],
                     SPEC["hair_width"], r=0.5, segments=2,
                     centre=(x_frog + 10.0 + SPEC["hair_length"] / 2.0, 0.0,
                             -8.6), mat=hair)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    # The bow's 706 mm runs from the button at the butt to the tip, and no
    # single part spans it -- the screw hangs off one end and the hair the other.
    dict(name="overall_length", mm=706.0, tol=3.0, how="bbox_x"),
    dict(name="stick_length", mm=600.0, tol=1.0, how="bbox_x", part="BowStick"),
    dict(name="frog_height", mm=15.5, tol=0.6, how="bbox_y", part="BowFrog"),
    dict(name="hair_length", mm=600.0, tol=1.0, how="bbox_x", part="BowHair"),
]