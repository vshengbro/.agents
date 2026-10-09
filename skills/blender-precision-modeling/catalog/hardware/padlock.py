"""
padlock -- 50 mm brass body padlock with a 10 mm shackle.

A 50 mm padlock is named for the shackle's span, not the body, so the shackle
leg centres sit 34 mm apart and the body's 50 mm width is what leaves the
shoulders. The shackle is a swept tube (arc_torus with real end caps) plus two
straight legs that overlap it, rather than a torus with its ends floating:
the arc's caps are buried inside the legs, so the part is watertight and there
is no coincident-face seam to z-fight.

The keyhole is cut as a real profile -- a round barrel with a tapered slot
below it -- because a padlock photographed without one reads as a blank brick.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BODY_L = 50.0           # X
BODY_T = 22.0           # Y
BODY_H = 55.0           # Z
SHACKLE_D = 10.0        # bar diameter
LEG_SPAN = 34.0         # shackle leg centre distance
BEND_Z = BODY_H - 3.0   # centre height of the U bend

SPEC = dict(body_length=BODY_L,
            body_thickness=BODY_T,
            body_height=BODY_H,
            shackle_diameter=SHACKLE_D,
            leg_span=LEG_SPAN,
            overall_height=BEND_Z + LEG_SPAN / 2.0 + SHACKLE_D / 2.0)


def build():
    brass = bkit.pbr("PadlockBrass", base=(0.95, 0.72, 0.32), metal=0.80,
                     rough=0.24)
    steel = bkit.pbr("ShackleSteel", base=(0.74, 0.76, 0.79), metal=0.74,
                     rough=0.22)

    # ---- body: rounded brass case with a keyhole -------------------------
    body = bkit.rounded_box("LockBody", BODY_L, BODY_T, BODY_H, r=4.0,
                            segments=4, centre=(0, 0, BODY_H / 2.0), mat=brass)
    barrel = bkit.cylinder("Keyhole", 3.2, 8.0, segments=32,
                           centre=(0, -BODY_T / 2.0 + 1.0, 20.0), axis="Y",
                           mat=None)
    bkit.boolean(body, barrel, "DIFFERENCE")
    slot = bkit.box("KeySlot", 2.0, 8.0, 9.0,
                    centre=(0, -BODY_T / 2.0 + 1.0, 14.5))
    bkit.boolean(body, slot, "DIFFERENCE")

    # ---- shackle: U bend plus two legs overlapping its ends --------------
    # For plane="XZ" the angle runs counter-clockwise from +X, so 0 -> 180 is
    # the UPPER half: right leg, over the top, left leg. (180 -> 360 would be
    # the lower half and hang the bow underneath the body.)
    r_major = LEG_SPAN / 2.0
    bend = bkit.arc_torus("ShackleBend", r_major, SHACKLE_D / 2.0,
                          0.0, 180.0, centre=(0, 0, BEND_Z), plane="XZ",
                          seg_major=72, seg_minor=32, mat=steel, caps=True)
    legs = [bkit.cylinder("ShackleLeg", SHACKLE_D / 2.0, 11.0, segments=40,
                          centre=(sign * r_major, 0, BEND_Z - 4.5),
                          mat=steel)
            for sign in (-1.0, 1.0)]
    bkit.join([bend] + legs, name="Shackle")

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_length", mm=50.0, tol=0.05, how="bbox_x", part="LockBody"),
    dict(name="body_height", mm=55.0, tol=0.05, how="bbox_z", part="LockBody"),
    dict(name="shackle_width", mm=44.0, tol=0.05, how="bbox_x", part="Shackle"),
    dict(name="overall_height", mm=74.0, tol=0.05, how="bbox_z", part=None),
]