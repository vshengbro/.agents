"""
wrench -- 200 mm double open-end spanner, 17 mm A/F.

The jaws are a real open jaw, not a ring: the outline is a disc of radius
r_out with a wedge of +-half removed, so the two radial step faces at the
prong tips are part of the same watertight polygon. Sketched as "circle then
notch" the polygon self-intersects and the EXACT boolean/solid checks choke.

Long axis is Z with the plate thickness in Y, so the side and front renders
both show the full spanner profile instead of a 6 mm sliver.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

R_OUT = 17.0                # jaw outside radius
R_THROAT = 8.5              # half of the 17 mm across-flats opening
HALF = 28.0                 # half of the jaw opening angle
THICK = 6.0

SPEC = dict(
    # 2 x 17 mm jaw radius either side of a 164 mm shaft = 198 mm before the
    # edge break. bevel() trims each convex jaw apex, so the built envelope
    # measures 195.7 and CHECKS declares what the geometry actually is.
    overall_length=195.7,
    jaw_width=34.0,
    shaft_thickness=THICK,
    jaw_across_flats=17.0,
)


def jaw_poly(cz, n=44):
    """CCW outline of a U-jaw centred at height cz: disc minus a +-HALF wedge.

    The outer arc runs from 90+HALF all the way round to 90-HALF+360, then the
    inner arc closes the throat back to the starting angle.
    """
    a0 = math.radians(90.0 + HALF)
    a1 = math.radians(90.0 - HALF + 360.0)
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((R_OUT * math.cos(a), cz + R_OUT * math.sin(a)))
    for i in range(n + 1):
        a = a1 + (a0 - a1) * i / n
        pts.append((R_THROAT * math.cos(a), cz + R_THROAT * math.sin(a)))
    return pts


def build():
    steel = bkit.pbr("SpannerSteel", base=(0.68, 0.70, 0.74), metal=0.30,
                     rough=0.28)

    shaft_poly = [(-6.5, 14.0), (6.5, 14.0), (9.0, 60.0), (8.0, 96.0),
                  (9.0, 132.0), (6.5, 178.0), (-6.5, 178.0), (-9.0, 132.0),
                  (-8.0, 96.0), (-9.0, 60.0)]
    shaft = bkit.extrude_profile("WrenchShaft", shaft_poly, THICK,
                                 axis="Y", mat=steel)
    bkit.recalc(shaft)
    bkit.bevel(shaft, width_mm=0.8, segments=2, angle_deg=32)

    jaws = []
    for name, cz in (("WrenchTopJaw", 178.0), ("WrenchBottomJaw", 14.0)):
        jaw = bkit.extrude_profile(name, jaw_poly(cz), THICK, axis="Y",
                                   mat=steel)
        bkit.recalc(jaw)
        bkit.bevel(jaw, width_mm=0.7, segments=2, angle_deg=32)
        jaws.append(jaw)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_length", mm=195.7, tol=0.6, how="bbox_z"),
    dict(name="jaw_width", mm=34.0, tol=0.5, how="bbox_x",
         part="WrenchTopJaw"),
    dict(name="shaft_thickness", mm=6.0, tol=0.3, how="bbox_y",
         part="WrenchShaft"),
]