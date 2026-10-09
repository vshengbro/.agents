"""
quartz_crystal -- a single terminated quartz crystal on a milky quartz matrix.

Real specimen: a 45 mm tall rock-crystal prism, 14 mm across the flats, prism
barrel 26 mm long with a 6-faced rhombohedral termination above it. That habit --
hexagonal prism + pyramidal tip -- is why quartz is modelled as two explicit
solids with a 2 mm overlap rather than as one loft: the flat prism faces and the
flat termination facets are the whole read, and a loft rounds them away.

Size class `tiny` (band 5..30 mm, tolerance x0.5..x2): a 45 mm specimen sits
just above the nominal band, which the harness allows.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    prism_across_flats=14.0,   # hexagon width across opposing faces
    prism_length=26.0,         # hexagonal barrel
    termination_length=21.0,   # 6-faced pyramidal cap
    overall_height=45.0,       # matrix base to apex
    matrix_diameter=19.0,
)

PRISM_R = SPEC["prism_across_flats"] / 2.0
PRISM_H = SPEC["prism_length"]
TIP_H = SPEC["termination_length"]
OVERLAP = 2.0                 # tip root buried in the barrel: never tangent
MATRIX_H = 4.5


def build():
    quartz = bkit.pbr("QuartzClear", base=(0.86, 0.89, 0.92), rough=0.06,
                      transmission=0.34, ior=1.55)
    milky = bkit.pbr("QuartzMilky", base=(0.80, 0.81, 0.83), rough=0.22,
                     transmission=0.16, ior=1.55)

    # ---- hexagonal barrel: an explicit 6-vertex profile, extruded ---------
    # Vertices start at angle 0 so the extrusion shares the termination's
    # facet orientation; a rotated hexagon makes a twisted, wrong crystal.
    hexa = [(PRISM_R * math.cos(math.radians(60 * i)),
             PRISM_R * math.sin(math.radians(60 * i))) for i in range(6)]
    prism = bkit.extrude_profile("Prism", hexa, PRISM_H,
                                 centre=(0.0, 0.0, PRISM_H / 2.0), mat=quartz)

    # ---- pyramidal termination: 6-sided cone, rooted 2 mm inside the barrel
    tip = bkit.cylinder("Termination", PRISM_R + 0.4, TIP_H, r2=0.0,
                        segments=6, centre=(0.0, 0.0, PRISM_H - OVERLAP + TIP_H / 2.0),
                        smooth=False, mat=quartz)

    # ---- milky matrix the crystal is still attached to --------------------
    # A separate closed solid rather than a skirt on the prism: the prism ends
    # in a clean plane, and a real specimen is fused to a broken rock base.
    # Centred so its underside is exactly z=0: a matrix that hangs below the
    # origin inflates the whole-assembly bbox and the overall-height check.
    matrix = bkit.extrude_profile(
        "Matrix", [(9.5 * math.cos(math.radians(72 * i)),
                    8.2 * math.sin(math.radians(72 * i))) for i in range(5)],
        MATRIX_H + 6.0, centre=(0.0, 0.0, (MATRIX_H + 6.0) / 2.0),
        mat=milky)

    return dict(spec=SPEC, parts=3)


# Declared intent; the harness measures the real geometry.
CHECKS = [
    dict(name="prism_across_flats", mm=14.0, tol=0.25,
         how="bbox_x", part="Prism"),
    dict(name="prism_length", mm=26.0, tol=0.25, how="bbox_z", part="Prism"),
    dict(name="termination_length", mm=21.0, tol=0.3, how="bbox_z", part="Termination"),
    dict(name="overall_height", mm=45.0, tol=0.4, how="bbox_z"),
]