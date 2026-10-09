"""
greek_column -- Doric column with a real entasis, 20 flutes, and an
echinus/abacus capital.

A Doric column is defined by its ratios, so those are the SPEC: the height is
10.0 m, the lower shaft diameter is 1.60 m (1/6.25 of height) and the upper
diameter 1.28 m, giving the entasis that stops a column looking like a pipe.

Flutes and entasis are ONE lofted solid, not a lathe plus twenty boolean
cutters: a cutter standing at a fixed radius cannot flute a shaft that tapers
from 800 mm to 640 mm, so the old boolean only reached the lower third.

This file also no longer uses `array_radial()`. That call was not merely
clumsy here: `bkit.array_radial()` returns COINCIDENT copies instead of an
orbit whenever the object carries a non-identity matrix_world, and a DIFFERENCE
against coincident volumes returns an empty mesh -- which is how ColumnShaft
came to have 0 vertices while every other part stayed clean, and why
`shaft_height` measured 0.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    height=10000.0,          # floor to the top of the abacus
    base_height=320.0,
    base_width=2100.0,
    shaft_base_diameter=1600.0,
    shaft_top_diameter=1280.0,
    neck_height=260.0,       # smooth collar under the capital
    neck_diameter=1400.0,
    echinus_height=300.0,
    abacus_height=260.0,
    abacus_width=1900.0,
    flute_count=20,
    flute_depth=34.0,
    flute_width=76.0,
)

H = SPEC["height"]
BASE_H = SPEC["base_height"]
NECK_H = SPEC["neck_height"]
ECHI_H = SPEC["echinus_height"]
ABAC_H = SPEC["abacus_height"]
ABAC_W = SPEC["abacus_width"]
R_TOP = SPEC["shaft_top_diameter"] / 2.0
R_BOT = SPEC["shaft_base_diameter"] / 2.0

SHAFT_H = H - BASE_H - NECK_H - ECHI_H - ABAC_H


FLUTE_PER = 24          # angular samples per flute


def _shaft(stone):
    """The shaft as ONE lofted solid carrying both the entasis and the flutes.

    The flutes were cut by a boolean against a ring of twenty cylindrical
    cutters, which cannot work on this shaft: the cutters stand at a FIXED
    radius (R_BOT - flute_depth) while the shaft tapers from 800 mm to 640 mm,
    so a cutter only reaches the wall where the shaft is still near its base --
    measured, the flutes stopped after the lower third. Sinking the flutes into
    the section makes them follow the taper over the FULL height, gives the
    declared `flute_depth` at every station, and drops the boolean (and this
    model's dependence on `array_radial`) altogether.
    """
    n = SPEC["flute_count"]
    steps = 20
    m = n * FLUTE_PER
    period = 2.0 * math.pi / n
    half_w = SPEC["flute_width"] / 2.0
    sections = []
    for j in range(steps + 1):
        f = j / float(steps)
        z = BASE_H + SHAFT_H * f
        R = R_BOT + (R_TOP - R_BOT) * f + 62.0 * math.sin(math.pi * f) * 0.62
        ring = []
        for i in range(m):
            a = 2.0 * math.pi * i / m
            # offset within the flute sector, as an arc distance in mm
            k = (a + period / 2.0) % period - period / 2.0
            q = min(1.0, abs(k * R) / half_w)
            dip = math.sqrt(max(0.0, 1.0 - q * q))   # semicircular flute
            r = R - SPEC["flute_depth"] * dip
            ring.append((r * math.cos(a), r * math.sin(a), z))
        sections.append(ring)
    ob = bkit.loft("ColumnShaft", sections, mat=stone)
    bkit.recalc(ob)
    return ob


def build():
    stone = bkit.pbr("DoricStone", base=(0.78, 0.76, 0.70), rough=0.62)
    shadow_stone = bkit.pbr("DoricStoneShade", base=(0.68, 0.66, 0.61),
                            rough=0.66)

    # ---- stepped base: two plinths, the upper one narrower ---------------
    base = bkit.lathe("ColumnBase", [
        (0.0, 0.0),
        (SPEC["base_width"] / 2.0, 0.0),
        (SPEC["base_width"] / 2.0, 130.0),
        (R_BOT + 70.0, 165.0),                 # scotia in
        (R_BOT + 70.0, BASE_H - 95.0),
        (R_BOT + 20.0, BASE_H - 40.0),         # torus out
        (R_BOT, BASE_H),
        (0.0, BASE_H),
    ], segments=96, mat=stone)

    # ---- shaft: ONE lofted solid carrying the entasis AND the 20 flutes ---
    shaft = _shaft(stone)

    # ---- 20 flutes ------------------------------------------------------
    # The flutes are in the shaft's own sections (see `_shaft`). They were once
    # cut with a boolean against a ring of 20 cylinders standing at a FIXED
    # radius, which cannot flute a shaft that tapers from 800 mm to 640 mm --
    # the cutter only reached the wall over the lower third. Nothing is cut
    # here now, and nothing here depends on `array_radial()`.

    # ---- neck: the smooth annulus under the capital -----------------------
    neck = bkit.lathe("ColumnNeck", [
        (0.0, BASE_H + SHAFT_H),
        (R_TOP + 30.0, BASE_H + SHAFT_H),
        (SPEC["neck_diameter"] / 2.0, BASE_H + SHAFT_H + NECK_H - 40.0),
        (SPEC["neck_diameter"] / 2.0, BASE_H + SHAFT_H + NECK_H),
        (0.0, BASE_H + SHAFT_H + NECK_H),
    ], segments=96, mat=shadow_stone)

    # ---- capital: echinus flare, then a square abacus ---------------------
    z0 = BASE_H + SHAFT_H + NECK_H
    echinus = bkit.lathe("ColumnEchinus", [
        (0.0, z0),
        (SPEC["neck_diameter"] / 2.0, z0),
        (ABAC_W / 2.0 - 40.0, z0 + ECHI_H - 70.0),
        (ABAC_W / 2.0, z0 + ECHI_H),
        (0.0, z0 + ECHI_H),
    ], segments=96, mat=stone)

    abacus = bkit.rounded_box("ColumnAbacus", ABAC_W, ABAC_W, ABAC_H, r=26.0,
                              segments=3, centre=(0.0, 0.0, z0 + ECHI_H + ABAC_H / 2.0),
                              mat=stone)

    return dict(spec=SPEC, parts=5, flutes=SPEC["flute_count"])


CHECKS = [
    dict(name="overall_height", mm=10000.0, tol=8.0, how="bbox_z"),
    dict(name="base_width", mm=2100.0, tol=4.0, how="diameter", part="ColumnBase"),
    dict(name="abacus_width", mm=1900.0, tol=4.0, how="bbox_x", part="ColumnAbacus"),
    dict(name="abacus_height", mm=260.0, tol=3.0, how="bbox_z", part="ColumnAbacus"),
    dict(name="shaft_height", mm=8860.0, tol=8.0, how="bbox_z", part="ColumnShaft"),
]
