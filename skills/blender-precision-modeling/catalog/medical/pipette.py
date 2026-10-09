"""
pipette -- 10 ml volumetric pipette: a drawn tip, a stem, a 20 mm bulb, an
engraved calibration ring and a flared mouth, 175 mm overall.

The bulb is what makes the volume work: a straight 7 mm tube would need 350 mm
to hold 10 ml, so the profile carries a real 20 mm bulb. The section is built
closed -- up the outside from the tip face, over the lip, back down the inside,
and back onto the tip face -- because a revolve of an open section leaves a
hole at the axis and a non-manifold rim.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=175.0,
    stem_diameter=7.0,
    bulb_diameter=20.0,
    wall=1.0,
    volume_ml=10.0,
    calibration_ring_z=112.0,
)

SR = SPEC["stem_diameter"] / 2.0      # 3.5
BR_ = SPEC["bulb_diameter"] / 2.0     # 10.0
WALL = SPEC["wall"]
IR = SR - WALL                        # 2.5
L = SPEC["overall_length"]
TIP_R = 1.6
BULB_Z0, BULB_Z1 = 62.0, 98.0
FLARE_Z0, FLARE_Z1 = 150.0, 156.0
MOUTH_R = 5.6
RING_Z = SPEC["calibration_ring_z"]
RING_D = 0.4


def r_out(z):
    """Outside radius of the pipette at height z."""
    if z <= 0.0:
        return TIP_R
    if z < 24.0:                                   # drawn tip
        return TIP_R + (SR - TIP_R) * (z / 24.0) ** 0.85
    if z < BULB_Z0:                                # lower stem
        return SR
    if z <= BULB_Z1:                               # the bulb, a sine bulge
        t = (z - BULB_Z0) / (BULB_Z1 - BULB_Z0)
        return SR + (BR_ - SR) * math.sin(math.pi * t) ** 0.72
    if z < FLARE_Z0:                               # upper stem
        return SR
    if z <= FLARE_Z1:                              # flare to the mouth
        return SR + (MOUTH_R - SR) * (z - FLARE_Z0) / (FLARE_Z1 - FLARE_Z0)
    return MOUTH_R


def build():
    glass = bkit.pbr("PipetteGlass", base=(0.88, 0.92, 0.91), rough=0.05,
                     transmission=0.74, ior=1.47, coat=0.55)
    ink = bkit.pbr("PipetteInk", base=(0.08, 0.08, 0.09), rough=0.45)
    band = bkit.pbr("PipetteBand", base=(0.72, 0.18, 0.15), rough=0.40)

    # ---- the outside, monotonically rising so the section cannot self-cross -
    outer = [(TIP_R, 0.0)]
    for i in range(1, 13):                          # drawn tip
        z = 24.0 * i / 12.0
        outer.append((r_out(z), z))
    for i in range(1, 13):                          # lower stem
        z = 24.0 + (BULB_Z0 - 24.0) * i / 12.0
        outer.append((r_out(z), z))
    for i in range(1, 17):                          # the bulb
        z = BULB_Z0 + (BULB_Z1 - BULB_Z0) * i / 16.0
        outer.append((r_out(z), z))
    for i in range(1, 8):                           # upper stem
        z = BULB_Z1 + (FLARE_Z0 - BULB_Z1) * i / 8.0
        if z > RING_Z - 4.0:
            break
        outer.append((r_out(z), z))
    # the calibration ring: a 0.4 mm engraving in the wall, not a decal
    outer += [(SR, RING_Z - 4.0), (SR, RING_Z), (SR - RING_D, RING_Z),
              (SR - RING_D, RING_Z + 1.3), (SR, RING_Z + 1.3)]
    for i in range(1, 9):                           # upper stem above the ring
        z = RING_Z + 1.3 + (FLARE_Z0 - RING_Z - 1.3) * i / 8.0
        outer.append((r_out(min(z, FLARE_Z0)), z))
    for i in range(1, 5):                           # the flare
        z = FLARE_Z0 + (FLARE_Z1 - FLARE_Z0) * i / 4.0
        outer.append((r_out(z), z))
    outer.append((MOUTH_R, L - 6.0))
    outer.append((MOUTH_R - 0.5, L))                # rolled lip

    # ---- back down the inside: the same section, one wall thickness in -----
    inner = [(max(r - WALL, 0.2), z) for (r, z) in reversed(outer)]
    prof = inner[-1:] + outer + inner               # closed section

    pipette = bkit.lathe("PipetteBody", prof, segments=96, cap_ends=False,
                         mat=glass)

    # the ring engraving and the colour band, selected by the real radii
    bkit.assign_faces_by(pipette, ink, lambda c, n:
                         RING_Z - 0.05 <= c.z / bkit.MM <= RING_Z + 1.35
                         and _rad(c) / bkit.MM < SR - 0.05)
    bkit.assign_faces_by(pipette, band, lambda c, n:
                         FLARE_Z0 - 0.5 <= c.z / bkit.MM <= FLARE_Z1 + 0.5
                         and _rad(c) / bkit.MM > r_out(c.z / bkit.MM) - 0.35)

    return dict(spec=SPEC, parts=1)


def _rad(c):
    return (c.x ** 2 + c.y ** 2) ** 0.5


CHECKS = [
    dict(name="bulb_diameter", mm=20.0, tol=0.4, how="diameter",
         part="PipetteBody"),
    dict(name="overall_length", mm=175.0, tol=0.5, how="bbox_z",
         part="PipetteBody"),
    dict(name="assembly_length", mm=175.0, tol=0.5, how="bbox_z"),
]