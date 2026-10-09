"""
belt -- 1000 x 35 x 4 mm leather strap, roller buckle, five punched holes.

A belt is a strip, so everything interesting is in the ends and the hardware.
The strap is a rounded box (4 mm of leather has a real edge radius, not a sharp
one), the holes are cut on a 28 mm pitch -- the real spacing between belt holes
-- and the buckle is a rectangular frame made the same way a pair of sunglasses
frame is: a rounded-rect annulus swept four sides and closed on itself, plus a
prong and a centre bar.

The holes go all the way through. A belt photographed with dimples instead of
holes reads as a belt sample, and the boolean is well behaved here because the
host is a box: a box has no coaxial curved facets for a cutter to coincide
with, so bkit.bore()'s +7-segment trick is not needed (nor harmful).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

STRAP_L = 1000.0
STRAP_W = 35.0
STRAP_T = 4.0
EDGE_R = 2.0
HOLE_N = 5
HOLE_PITCH = 28.0
HOLE_D = 5.4
HOLE_X0 = -330.0            # centre of the first hole
BUCKLE_L = 60.0
BUCKLE_W = 48.0
BUCKLE_BAR = 6.0
BUCKLE_T = 3.0
BUCKLE_X = STRAP_L / 2.0 - BUCKLE_L / 2.0 + 6.0
PRONG_L = 34.0

SPEC = dict(strap_length=STRAP_L,
            strap_width=STRAP_W,
            strap_thickness=STRAP_T,
            hole_count=HOLE_N,
            hole_pitch=HOLE_PITCH,
            hole_diameter=HOLE_D,
            buckle_length=BUCKLE_L,
            buckle_width=BUCKLE_W)


def build():
    leather = bkit.pbr("BeltLeather", base=(0.14, 0.085, 0.055), metal=0.0, rough=0.52)
    nickel = bkit.pbr("BuckleNickel", base=(0.82, 0.84, 0.87), metal=0.85, rough=0.20)

    # ---- strap --------------------------------------------------------------
    strap = bkit.rounded_box("Strap", STRAP_L, STRAP_W, STRAP_T, r=EDGE_R,
                             segments=3, centre=(0.0, 0.0, STRAP_T / 2.0),
                             mat=leather)

    # ---- five punched holes on a real 28 mm pitch --------------------------
    for i in range(HOLE_N):
        x = HOLE_X0 + i * HOLE_PITCH
        cut = bkit.cylinder("_hole", HOLE_D / 2.0, STRAP_T + 6.0, segments=24,
                            centre=(x, 0.0, STRAP_T / 2.0))
        bkit.boolean(strap, cut, "DIFFERENCE")

    # ---- buckle: a rounded-rect frame, a solid prism with a through-cut ----
    # A four-band loft closed on itself puts four faces on every interior
    # vertex of the seam ring, so this is a prism minus an oversized cutter
    # instead -- the same part, watertight, with no seam.
    outer = bkit.rounded_rect_section(BUCKLE_L, BUCKLE_W, 8.0, per_corner=6,
                                      centre=(BUCKLE_X, 0.0))
    frame = bkit.extrude_profile("BuckleFrame", outer, BUCKLE_T, axis="Z",
                                 centre=(0.0, 0.0, STRAP_T + BUCKLE_T / 2.0),
                                 mat=nickel)
    inner = bkit.rounded_rect_section(BUCKLE_L - 2.0 * BUCKLE_BAR,
                                      BUCKLE_W - 2.0 * BUCKLE_BAR,
                                      8.0 - BUCKLE_BAR, per_corner=6,
                                      centre=(BUCKLE_X, 0.0))
    hole = bkit.extrude_profile("_buckle_hole", inner, BUCKLE_T + 6.0, axis="Z",
                                centre=(0.0, 0.0, STRAP_T + BUCKLE_T / 2.0))
    bkit.boolean(frame, hole, "DIFFERENCE")

    # centre bar the strap threads through, and the prong
    bar = bkit.rounded_box("BuckleBar", BUCKLE_T, BUCKLE_W - 2.0 * BUCKLE_BAR, 4.0,
                           r=1.0, segments=2,
                           centre=(BUCKLE_X, 0.0, STRAP_T + 2.0), mat=nickel)
    prong = bkit.rounded_box("Prong", PRONG_L, 3.0, 2.4, r=1.0, segments=2,
                             centre=(BUCKLE_X - 1.0, 0.0, STRAP_T + 5.0),
                             mat=nickel)
    prong.rotation_euler = (0.0, 0.0, math.radians(90.0))

    # ---- keeper loop holding the loose end ----------------------------------
    # Inner radius is 1.4 mm clear of the strap on each side: a keeper that
    # touched the strap tangentially would produce non-manifold edges.
    keeper = bkit.torus("Keeper", STRAP_W / 2.0 + 3.4, 2.6, seg_major=48,
                        seg_minor=14,
                        centre=(HOLE_X0 + 4.0 * HOLE_PITCH + 24.0, 0.0, STRAP_T / 2.0),
                        axis="X", mat=leather)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="strap_length", mm=1000.0, tol=0.2, how="bbox_x", part="Strap"),
    dict(name="strap_width", mm=35.0, tol=0.1, how="bbox_y", part="Strap"),
    dict(name="strap_thickness", mm=4.0, tol=0.1, how="bbox_z", part="Strap"),
    dict(name="buckle_length", mm=60.0, tol=0.2, how="bbox_x", part="BuckleFrame"),
    dict(name="buckle_width", mm=48.0, tol=0.2, how="bbox_y", part="BuckleFrame")
]