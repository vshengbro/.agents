"""
silo -- a 6 m farm grain silo: corrugated cylinder, conical roof, 4 legs.

A silo is a LATHE, and the corrugation is what makes it read as a farm silo
rather than as a water tank: the sheet is rolled into a helical rib, and that
rib is what carries the load and what you can see the wind on.

So the barrel is one `lathe` whose PROFILE CONTAINS THE CORRUGATION -- a zigzag
in (radius, z) with 34 ribs over the 5.6 m shell. Doing it in the profile
rather than with 34 separate rings means the corrugation is part of one closed
solid: no gaps, no coincident faces, and one object whose measured height is the
silo's height.

    barrel       3000 mm dia, 5.6 m shell, 34 corrugations at 165 mm pitch
    roof         a 45 deg cone, 900 mm tall
    legs         4 x 150 mm square legs on a 2.4 m square, with cross bracing
    ladder       a caged access ladder up one leg
    outlet       a slide gate at the base

The hopper is deliberately absent: this is a flat-bottom farm silo on legs,
which is what a grain store on a smallholding actually is.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    barrel_dia=3000.0,
    barrel_height=5600.0,
    corrugations=34,
    corrugation_depth=35.0,
    roof_angle_deg=45.0,
    roof_height=900.0,
    leg_section=150.0,
    leg_spacing=2400.0,
    leg_height=900.0,
    ladder_width=420.0,
    outlet_dia=300.0,
)

BD = SPEC["barrel_dia"]
RB = BD / 2.0
BH = SPEC["barrel_height"]
NC = SPEC["corrugations"]
CD = SPEC["corrugation_depth"]
LS = SPEC["leg_section"]
LSP = SPEC["leg_spacing"]
LH = SPEC["leg_height"]

# one corrugation: a rib and a valley, so the profile is a closed zigzag
PROF = []
half = NC * 2
for i in range(half):
    z = BH * i / float(half)
    r = RB + (CD if i % 2 == 0 else -CD)
    PROF.append((r, z))
# close the shell: an inner wall back down at the plain sheet radius, then back
# to the STARTING point.
#
# The inner radius must clear the corrugation VALLEYS, not the plain sheet: a
# valley sits at RB - CD, so an inner wall at RB - 4 lies outside it, the revolved
# solid self-intersects, and `health()` reports a negative volume that `recalc`
# cannot fix (the winding is ambiguous once the surface crosses itself).
INNER = RB - CD - 4.0
PROF.append((INNER, BH))
PROF.append((INNER, 0.0))
PROF.append(PROF[0])

ROOF_H = SPEC["roof_height"]
TOTAL_H = LH + BH + ROOF_H

CHECKS = [
    # the corrugation adds CD to the radius at each rib, so the barrel measures
    # 3000 + 2 * 35 across the ribs -- the plain 3000 is the SHEET diameter
    dict(name="barrel_dia", mm=3070.0, tol=6.0, how="diameter", part="SiloBarrel"),
    dict(name="barrel_height", mm=5600.0, tol=6.0, how="bbox_z", part="SiloBarrel"),
    dict(name="leg_spacing", mm=2550.0, tol=4.0, how="bbox_x", part="SiloLegs"),
    dict(name="overall_height", mm=7570.0, tol=20.0, how="bbox_z", part=None),
    dict(name="overall_dia", mm=3660.0, tol=12.0, how="diameter", part=None),
]


def build():
    galv = bkit.pbr("SiloGalv", base=(0.70, 0.71, 0.72), metal=0.84, rough=0.32)
    steel = bkit.preset("dark_metal")

    # ---- the corrugated barrel: corrugation in the lathe profile ----
    # `lathe` revolves the (radius, z) list, so the profile is walked UP the
    # outside and back DOWN the inside: a closed shell. `cap_ends` must be off
    # -- the profile already returns to its start, so capping would add two
    # discs across a hollow barrel.
    barrel = bkit.lathe("SiloBarrel", PROF, segments=64, centre=(0.0, 0.0, LH),
                        mat=galv, cap_ends=False)
    # A revolved shell is exactly the case where the sweep direction leaves the
    # normals inward, and `recalc` is what makes `health()`'s volume test
    # trustworthy rather than reporting a plausible negative. `weld` then
    # collapses the seam where the closed profile's last point meets its first.
    bkit.recalc(barrel)
    bkit.weld(barrel)

    # ---- the conical roof ------------------------------------------
    a = math.radians(SPEC["roof_angle_deg"])
    roof_r = RB / math.cos(a)
    roof = bkit.cylinder("SiloRoof", RB + 60.0, ROOF_H, segments=64, axis="Z",
                         centre=(0.0, 0.0, LH + BH + ROOF_H / 2.0),
                         r2=70.0, mat=galv)
    # a roof vent at the apex
    bkit.cylinder("SiloRoofVent", 90.0, 220.0, segments=24,
                  centre=(0.0, 0.0, LH + BH + ROOF_H + 60.0), mat=steel)

    # ---- 4 legs on the 2.4 m square, with cross bracing -------------
    leg_x = [(-1.0 + 2.0 * i) * LSP / 2.0 for i in range(2)]
    for i, (lx, ly) in enumerate(((leg_x[0], leg_x[0]), (leg_x[0], leg_x[1]),
                                  (leg_x[1], leg_x[1]), (leg_x[1], leg_x[0]))):
        bkit.box("SiloLeg%d" % i, LS, LS, LH,
                 centre=(lx, ly, LH / 2.0), mat=steel)
    # the leg frame: 4 rails + 2 diagonals, so `leg_spacing` is one number.
    # The array is seeded on the FIRST leg ring at -LSP/2 and stepped by the
    # spacing; seeding at 0 instead puts the run half a spacing off centre.
    ring = bkit.box("SiloLegs", LS, LSP, LS,
                    centre=(-LSP / 2.0, 0.0, LH - LS / 2.0), mat=steel)
    bkit.array_linear(ring, 2, (LSP, 0.0, 0.0))
    cross = bkit.box("SiloLegBrace0", LSP, LS * 0.7, LS * 0.7,
                     centre=(0.0, -LSP / 2.0, LH * 0.45), mat=steel)
    bkit.array_linear(cross, 2, (0.0, LSP, 0.0))

    # ---- the caged access ladder up one leg -------------------------
    lw = SPEC["ladder_width"]
    for i, sx in enumerate((-1, 1)):
        bkit.cylinder("SiloLadderStile%d" % i, 22.0, BH - 200.0, segments=12,
                      axis="Z", centre=(sx * lw / 2.0, RB + 220.0,
                                        LH + (BH - 200.0) / 2.0), mat=steel)
    nrungs = int((BH - 200.0) / 300.0)
    # The rung is an UNROTATED box, not `cylinder(axis="X")`. `array_linear`
    # applies its offset in the object's local space and `place()` leaves a
    # rotation on every oriented primitive, so a (0, 0, 300) offset on a rung
    # lying along X is a WORLD move along X -- the ladder rungs walk 5 m out
    # sideways instead of climbing the silo.
    rung = bkit.box("SiloLadderRungs", lw, 24.0, 24.0,
                    centre=(0.0, RB + 220.0, LH + 150.0), mat=steel)
    bkit.array_linear(rung, nrungs, (0.0, 0.0, 300.0))
    # the safety cage hoops above 2.2 m
    for k in range(6):
        bkit.tube("SiloLadderCage%d" % k, 380.0, 360.0, 30.0, segments=24,
                  axis="Z",
                  centre=(0.0, RB + 220.0, LH + 2400.0 + k * 550.0), mat=steel)

    # ---- the slide-gate outlet at the base --------------------------
    bkit.cylinder("SiloOutlet", SPEC["outlet_dia"] / 2.0, 420.0, segments=24,
                  axis="Z", centre=(0.0, 0.0, 210.0), mat=steel)

    return dict(spec=SPEC, parts=2 + 4 + 2 + 2 + 1 + nrungs + 6 + 1,
                corrugations=NC)


def bpy_new():
    import bpy
    bpy.context.view_layer.update()