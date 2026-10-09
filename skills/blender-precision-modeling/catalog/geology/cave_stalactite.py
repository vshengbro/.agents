"""
stalactite -- a calcite stalactite hanging from a cave roof: 780 mm long,
tapering from a 96 mm root to a 6 mm drip tip.

Real object: dripstone grows one calcite crystal at a time, so the profile is
a stack of very slightly different diameters -- a smooth cone reads as a
party hat. The model is a `lathe` over a profile that steps in and out by a
fraction of a millimetre per band, which is exactly how a stalactite looks in
cross-section. The taper is not linear: it is fast near the root and slow near
the tip, which is what the drip physics gives.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=780.0,
    root_diameter=96.0,       # the barrel where it leaves the roof
    collar_diameter=114.0,    # the flare where it joins the ceiling
    tip_diameter=6.0,
    bands=26,             # growth rings; the step-to-step irregularity
)

L = SPEC["length"]
R_ROOT = SPEC["root_diameter"] / 2.0
R_TIP = SPEC["tip_diameter"] / 2.0


def build():
    calcite = bkit.pbr("StalactiteCalcite", base=(0.78, 0.74, 0.66), rough=0.34,
                       transmission=0.10, ior=1.55)
    wet = bkit.pbr("StalactiteWet", base=(0.72, 0.70, 0.65), rough=0.12,
                   transmission=0.20, ior=1.55)

    # ---- growth profile: fast taper at the root, slow at the tip ---------
    # exp() taper, because that is what a drip-deposited cone actually does:
    # the last 100 mm contribute a third of the length for 5% of the diameter.
    rnd = random.Random(31)
    bands = SPEC["bands"]
    # The root collar flares wider than the barrel, so the widest diameter on the
    # object is the collar and the declared root_diameter measures it.
    prof = [(0.0, 0.0), (R_ROOT + 9.0, 0.0)]
    for i in range(1, bands + 1):
        t = float(i) / bands
        z = L * t
        r = R_ROOT * math.exp(-3.05 * t) + R_TIP * (1.0 - math.exp(-3.05 * t))
        # per-band step: +-(0.9 mm) tapering to +-(0.2 mm) near the tip, which
        # is the concentric layering you see cut through dripstone
        amp = 0.9 - 0.7 * t
        r += rnd.uniform(-amp, amp)
        prof.append((max(R_TIP, r), z))
    tip = bkit.lathe("Stalactite", prof, segments=32, mat=calcite, smooth=False)
    bkit.recalc(tip)

    # ---- wet, translucent tip: the part still being fed by a drip --------
    # Faces selected on the same solid. A separate tip shell would z-fight
    # with the body and double the non-manifold count.
    bkit.assign_faces_by(tip, wet,
                         lambda c, n: c.z / bkit.MM > L - L * 0.16)

    # ---- the roof it hangs from ------------------------------------------
    # A short slab of cave ceiling: without it a stalactite hanging in mid air
    # has nothing to hang from and reads as a stalagmite.
    roof = bkit.rounded_box("CaveRoof", 420.0, 380.0, 150.0, r=26.0,
                            centre=(0.0, 0.0, -72.0), mat=calcite)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="length", mm=780.0, tol=2.0, how="bbox_z", part="Stalactite"),
    dict(name="collar_diameter", mm=114.0, tol=1.5,
         how="diameter", part="Stalactite"),
    dict(name="overall_height", mm=930.0, tol=3.0, how="bbox_z"),
    dict(name="roof_thickness", mm=150.0, tol=1.0, how="bbox_z", part="CaveRoof"),
]