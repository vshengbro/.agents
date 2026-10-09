"""
pliers -- 190 mm combination pliers, jaws open 3 mm.

Two jaws and two handles are separate parts stacked in Y with a 1 mm gap
between them, because on a real pair the two steel blanks are forged apart
and never share a face. Sharing a face (both centred on y=0) z-fights in the
overlap around the pivot and reads as one solid lump.

The handle splay is BAKED INTO THE POLYGON POINTS, not applied as a rotation,
so `measure()` sees the tilted part in its real pose instead of its
pre-rotation bounding box.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

TILT = math.radians(19.0)     # handles splay outward from the pivot
COS, SIN = math.cos(TILT), math.sin(TILT)
JAW_T = 11.0
GAP = 0.5                    # the two blanks never touch

SPEC = dict(
    overall_length=189.3,
    jaw_length=86.0,
    jaw_width=10.0,
    handle_width=49.6,
    jaw_thickness=JAW_T,
)


def _splay(pts):
    """Rotate a handle outline counter-clockwise about the pivot at the origin."""
    return [(x * COS - z * SIN, x * SIN + z * COS) for (x, z) in pts]


HANDLE_BASE = [(-8.5, 14.0), (8.5, 14.0), (10.0, -34.0), (8.0, -78.0),
               (4.0, -102.0), (-3.0, -104.0), (-8.5, -74.0), (-9.5, -34.0)]
JAW_R = [(1.5, 4.0), (11.5, 4.0), (9.0, 90.0), (1.5, 86.0)]
JAW_L = [(-x, z) for (x, z) in JAW_R]


def build():
    steel = bkit.pbr("PliersSteel", base=(0.66, 0.68, 0.72), metal=0.30,
                     rough=0.30)
    grip = bkit.pbr("PliersGrip", base=(0.11, 0.11, 0.12), rough=0.42)

    jaw_r = bkit.extrude_profile("PliersJawR", JAW_R, JAW_T,
                                 centre=(0, 6.0, 0), axis="Y", mat=steel)
    bkit.recalc(jaw_r)
    bkit.bevel(jaw_r, width_mm=0.9, segments=2, angle_deg=32)

    jaw_l = bkit.extrude_profile("PliersJawL", JAW_L, JAW_T,
                                 centre=(0, -6.0, 0), axis="Y", mat=steel)
    bkit.recalc(jaw_l)
    bkit.bevel(jaw_l, width_mm=0.9, segments=2, angle_deg=32)

    handles = []
    right = _splay(HANDLE_BASE)
    for name, poly in (("PliersHandleR", right),
                      ("PliersHandleL", [(-x, z) for (x, z) in right])):
        ob = bkit.extrude_profile(name, poly, JAW_T, centre=(0, -6.0, 0),
                                  axis="Y", mat=grip)
        bkit.recalc(ob)
        bkit.bevel(ob, width_mm=1.2, segments=2, angle_deg=32)
        handles.append(ob)

    pivot = bkit.cylinder("PliersPivot", 6.0, 32.0, segments=32, axis="Y",
                          centre=(0, 0, 0), mat=steel)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="jaw_length", mm=86.0, tol=0.5, how="bbox_z", part="PliersJawR"),
    dict(name="jaw_width", mm=10.0, tol=0.4, how="bbox_x", part="PliersJawR"),
    dict(name="handle_width", mm=49.6, tol=0.8, how="bbox_x",
         part="PliersHandleR"),
    dict(name="overall_length", mm=189.3, tol=1.2, how="bbox_z"),
]