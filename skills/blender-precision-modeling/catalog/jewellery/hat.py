"""
hat -- 260 mm brim felt hat, 170 mm crown, 132 mm overall height.

A hat is three lathed shells that share an axis: brim, crown, and the band
that grips the head. The brim is a genuine shell with thickness -- its
cross-section runs out along the underside, breaks at the edge and comes back
along the top -- because a brim modelled as a single cone surface has no
visible edge and reads as a lampshade.

The crown's profile starts and ends on the axis (r = 0), so lathe() welds both
ends into poles and the solid closes with no end caps. That is the difference
between a closed hat and a hat with a hole through the top: a profile that
returns to the axis by travelling ALONG the axis would generate a ring of
zero-area faces.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BRIM_R = 130.0
BRIM_T = 4.0
BRIM_DROP = 8.0          # how far the brim edge falls below the crown base
CROWN_R = 85.0
CROWN_H = 128.0
CROWN_TOP_R = 34.0
BAND_LO = 16.0
BAND_HI = 32.0
BAND_OUT = 4.0

SPEC = dict(brim_diameter=2.0 * BRIM_R,
            brim_thickness=BRIM_T,
            crown_diameter=2.0 * CROWN_R,
            crown_height=CROWN_H,
            band_height=BAND_HI - BAND_LO,
            overall_height=CROWN_H + 4.0 + BRIM_DROP)

def build():
    felt = bkit.pbr("HatFelt", base=(0.15, 0.13, 0.14), metal=0.0, rough=0.92)
    band = bkit.pbr("HatBand", base=(0.08, 0.07, 0.09), metal=0.0, rough=0.55)

    # ---- brim: a shell, out along the underside and back over the top -------
    # (r, z): axis -> outer edge on the underside, break, outer edge on top,
    # back to the axis. Both ends on the axis => lathe welds two poles.
    brim = bkit.lathe(
        "Brim",
        [(0.0, 0.0),
         (BRIM_R * 0.45, -BRIM_T * 0.35),
         (BRIM_R, -BRIM_DROP),
         (BRIM_R, -BRIM_DROP + BRIM_T),
         (BRIM_R * 0.45, BRIM_T * 0.55),
         (0.0, BRIM_T)],
        segments=96, mat=felt)

    # ---- crown: from the axis at the base, out to the wall, domed to a pole -
    crown = bkit.lathe(
        "Crown",
        [(0.0, 0.0),
         (CROWN_R, 0.0),
         (CROWN_R, CROWN_H * 0.42),
         (CROWN_R - 3.0, CROWN_H * 0.72),
         (CROWN_TOP_R + 6.0, CROWN_H * 0.93),
         (CROWN_TOP_R, CROWN_H),
         (0.0, CROWN_H + 4.0)],
        segments=96, mat=felt)

    # ---- hat band: a closed annulus revolved about the crown ---------------
    rb = CROWN_R + BAND_OUT
    rbi = CROWN_R - 2.0
    band_ob = bkit.lathe(
        "HatBand",
        [(rbi, BAND_LO), (rb, BAND_LO), (rb, BAND_HI), (rbi, BAND_HI),
         (rbi, BAND_LO)],
        segments=96, cap_ends=False, mat=band)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="brim_diameter", mm=260.0, tol=0.3, how="diameter", part="Brim"),
    dict(name="crown_diameter", mm=170.0, tol=0.3, how="diameter", part="Crown"),
    dict(name="crown_height", mm=132.0, tol=0.3, how="bbox_z", part="Crown"),
    dict(name="band_height", mm=16.0, tol=0.2, how="bbox_z", part="HatBand"),
    # the brim's edge falls 8 mm below the crown base, so the assembly is
    # crown top (132) + brim drop (8) = 140, not the crown height alone
    dict(name="overall_height", mm=140.0, tol=0.3, how="bbox_z", part=None)
]