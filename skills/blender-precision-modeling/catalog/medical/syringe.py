"""
syringe -- 10 ml Luer-slip syringe, 151 mm overall, built standing on the tip.

Five parts, each one that a syringe is read by: a transparent barrel with a real
wall, a thumb flange with a real rod bore, a conical tip with a 1.6 mm lumen
that runs the whole length of the bore, the plunger rod with its elastomer
seal, and the thumb pad.

The scale is the part that makes it read as a syringe rather than a tube: a
10 ml syringe is graduated in 0.2 ml steps, so there are 50 lines over the
57 mm graduated length (1.14 mm pitch) -- long lines on the whole-millilitre
positions, short lines between them -- and every line is a thin arc tube lying
on the barrel wall, printed on one side the way a real scale is.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=151.0,        # tip to the top of the thumb pad
    barrel_diameter=20.0,       # outside diameter of the barrel
    barrel_length=88.0,         # tip shoulder to the rear of the barrel
    wall=2.5,
    capacity_ml=10.0,
    graduated_length=57.0,      # the 10 ml scale
    graduation_step_ml=0.2,
    flange_diameter=42.0,
    rod_diameter=10.0,
    pad_diameter=30.0,
    lumen_diameter=1.6,
)

BARREL_R = SPEC["barrel_diameter"] / 2.0        # 10.0
BORE_R = BARREL_R - SPEC["wall"]               # 7.5
TIP_Z = 16.0                    # top of the conical luer tip
BARREL_Z = TIP_Z + SPEC["barrel_length"]       # 104.0
FLANGE_T = 5.0
FLANGE_R = SPEC["flange_diameter"] / 2.0       # 21.0
ROD_R = SPEC["rod_diameter"] / 2.0             # 5.0
ROD_BORE = 5.3                  # flange bore: 0.3 mm clear of the rod
GRAD_TOP = BARREL_Z - 0.5
GRAD_BOT = GRAD_TOP - SPEC["graduated_length"]  # 46.5
PAD_R = SPEC["pad_diameter"] / 2.0             # 15.0
LUMEN_R = SPEC["lumen_diameter"] / 2.0         # 0.8


def graduations():
    """(z, is_whole_ml) for every 0.2 ml line, spaced by the real bore area.

    10 ml in this barrel occupies per_ml = area * graduated_length / 1000 mm,
    which is what puts 50 lines at 1.13 mm pitch over the 57 mm scale instead of
    an arbitrary number of rings.
    """
    area = math.pi * BORE_R ** 2                      # mm^2
    per_ml = area * SPEC["graduated_length"] / 1000.0  # mm of barrel per ml
    out, i = [], 1
    while i * SPEC["graduation_step_ml"] <= SPEC["capacity_ml"] + 1e-9:
        vol = i * SPEC["graduation_step_ml"]
        out.append((GRAD_BOT + vol / per_ml * SPEC["graduated_length"],
                    i % 5 == 0))
        i += 1
    return out


def build():
    # A clear barrel renders dark against this studio's dark backdrop, and a dark
    # ink scale on a dark barrel is invisible. So this is a smoke-tinted barrel
    # with a PALE printed scale -- contrast that survives 5 px line pitch.
    clear = bkit.pbr("SyringeBarrel", base=(0.55, 0.60, 0.64), rough=0.14,
                     transmission=0.30, ior=1.49, coat=0.6)
    ink = bkit.pbr("SyringeInk", base=(0.95, 0.96, 0.96), rough=0.35)
    plastic = bkit.preset("white_plastic")
    rubber = bkit.pbr("SyringeSeal", base=(0.62, 0.64, 0.66), metal=0.0,
                      rough=0.55)
    pad_mat = bkit.pbr("SyringePad", base=(0.90, 0.90, 0.89), rough=0.30)

    # ---- barrel: luer tip -> bore -> barrel wall -> rear opening -----------
    # The lumen is a real hole running the length of the barrel, and the tip is
    # a luer taper from 5.2 mm to 14 mm over 16 mm, not a cone stuck on.
    barrel = bkit.lathe("SyringeBarrel", [
        (LUMEN_R, 0.0),
        (2.6, 0.0),                   # tip end face (annulus, lumen open)
        (7.0, TIP_Z),                 # luer taper outside
        (BARREL_R, TIP_Z + 1.5),      # shoulder into the barrel
        (BARREL_R, BARREL_Z - 1.0),
        (BORE_R + 0.6, BARREL_Z),     # rear opening, chamfered
        (BORE_R, BARREL_Z - 1.6),     # rear face, over the bore
        (BORE_R, TIP_Z + 3.0),        # down the inside of the barrel
        (LUMEN_R, TIP_Z - 0.6),       # taper into the luer lumen
        (LUMEN_R, 0.0),
    ], segments=96, cap_ends=False, mat=clear)

    # ---- thumb flange: a washer with a real bore for the rod ----------------
    flange = bkit.lathe("SyringeFlange", [
        (ROD_BORE, BARREL_Z - 1.0),
        (FLANGE_R - 2.0, BARREL_Z - 1.0),
        (FLANGE_R, BARREL_Z + 1.2),
        (FLANGE_R, BARREL_Z + FLANGE_T - 1.2),
        (FLANGE_R - 2.0, BARREL_Z + FLANGE_T),
        (ROD_BORE, BARREL_Z + FLANGE_T),
        (ROD_BORE, BARREL_Z - 1.0),
    ], segments=96, cap_ends=False, mat=plastic)

    # ---- plunger: rod, elastomer seal, thumb pad ---------------------------
    rod_top = SPEC["overall_length"] - 6.0
    bkit.cylinder("PlungerRod", ROD_R, rod_top - 76.0, segments=48,
                  centre=(0, 0, (76.0 + rod_top) / 2.0), mat=plastic)
    seal = bkit.lathe("PlungerSeal", [
        (ROD_R - 0.3, 86.0),
        (BORE_R - 0.4, 86.0),         # 0.4 mm clear of the barrel bore
        (BORE_R - 0.4, 98.0),
        (BORE_R - 1.6, 100.0),
        (ROD_R - 0.3, 100.0),
        (ROD_R - 0.3, 86.0),
    ], segments=96, cap_ends=False, mat=rubber)

    pad = bkit.lathe("PlungerPad", [
        (0.0, rod_top - 1.0),
        (PAD_R - 1.5, rod_top - 1.0),
        (PAD_R, rod_top + 0.8),
        (PAD_R, rod_top + 4.6),
        (PAD_R - 1.5, rod_top + 6.0),
        (0.0, rod_top + 6.0),
    ], segments=96, mat=pad_mat)

    # ---- the scale: one thin arc per line, lying on the barrel wall --------
    # Each arc tube is buried 0.3 mm into the barrel, so it is a printed mark
    # and not a floating shell: no coincidence, no z-fight, one watertight
    # solid once joined.
    # Each line is a thin arc tube lying on the barrel wall, printed on one side
    # the way a real scale is: long lines on the whole-millilitre positions,
    # short lines between them. The arcs have to be WIDE (+-42 deg is 13 mm of
    # barrel) so a line reads as a line, and the tubes have to be HAIRLINE
    # (0.22 / 0.30 mm) -- at the 1.13 mm pitch the geometry forces, anything
    # thicker touches its neighbour and the whole scale merges into one band.
    marks = []
    for z, whole in graduations():
        minor = 0.15 if whole else 0.11
        half = 42.0 if whole else 26.0
        r_major = BARREL_R - 0.02
        marks.append(bkit.arc_torus(
            "_mark", r_major, minor, -half, half,
            centre=(0.0, 0.0, z), plane="XZ", seg_major=14, seg_minor=8,
            caps=True, mat=ink))
    scale = bkit.join(marks, name="SyringeGraduations")

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="barrel_diameter", mm=20.0, tol=0.2, how="diameter",
         part="SyringeBarrel"),
    # tip tip to the rear opening of the barrel: 88 mm of barrel plus the
    # 16 mm luer tip, which is what this part's own bounding box can prove.
    dict(name="tip_to_rear", mm=104.0, tol=0.5, how="bbox_z",
         part="SyringeBarrel"),
    dict(name="flange_diameter", mm=42.0, tol=0.3, how="diameter",
         part="SyringeFlange"),
    dict(name="overall_length", mm=151.0, tol=1.0, how="bbox_z"),
]