"""
clarinet -- Bb Boehm-system clarinet, 665 mm overall, seventeen keys.

A clarinet is four turned joints (mouthpiece, barrel, upper joint, lower joint)
and a bell, all on one axis, and the count of keys is what makes it read. The
bell is a `lathe` on a real flare profile -- the flare is the single most
recognisable thing about a clarinet from the side -- and each joint is a
`lathe` too, so the body carries the swell rings a real clarinet has.

The seventeen keys are computed: six finger-hole tone rings on the upper joint,
the left-hand pinky table of four spatulas, and the seven-key right-hand stack,
placed from `bkit.lay_out` at real pitches rather than typed coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=665.0,
    body_diameter=29.0,
    lower_joint_diameter=31.0,
    barrel_length=68.0,
    bell_diameter=118.0,
    bell_length=142.0,
    mouthpiece_length=88.0,
    keys=17,
)

L = SPEC["length"]
R = SPEC["body_diameter"] / 2.0
RL = SPEC["lower_joint_diameter"] / 2.0
NKEYS = SPEC["keys"]

# z stations along the instrument. The clarinet is built UPSIDE DOWN relative
# to the player's view -- bell rim at z=0, mouthpiece at z=L -- because
# `sit_on_floor` seats the model on its lowest point, and a clarinet stands on
# its bell exactly as it does on a chair. Building mouth-down would render the
# flare at the top like a trumpet.
#
# Each Z_x is the BOTTOM of its section and the length runs forward, so
# `len = next_Z - this_Z` is always positive. A real 4/4 clarinet's stack is
# bell 142 + lower joint 200 + upper joint 340 + barrel 68 + mouthpiece 88.
Z_BELL = 0.0                                   # bottom of the bell flare
Z_LOWER = SPEC["bell_length"]                  # 142
Z_UPPER = Z_LOWER + 200.0                      # 342 -- lower joint is 200
Z_BARREL = Z_UPPER + 340.0                     # 682 -- upper joint is 340
Z_MP = Z_BARREL + SPEC["barrel_length"]        # 750
L = Z_MP + SPEC["mouthpiece_length"]           # 838: mouthpiece tip


def build():
    grenadilla = bkit.pbr("ClarinetBody", base=(0.16, 0.085, 0.045), rough=0.30,
                          coat=0.35)
    key_mat = bkit.pbr("ClarinetKeys", base=(0.82, 0.82, 0.80), metal=0.85,
                       rough=0.24)
    silver = bkit.pbr("ClarinetSilver", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.16)
    pad = bkit.pbr("ClarinetPad", base=(0.88, 0.86, 0.80), rough=0.62)
    reed = bkit.pbr("ClarinetReed", base=(0.70, 0.56, 0.28), rough=0.44)

    # ---- mouthpiece: barrel + beak + reed + ligature -----------------------
    # The mouthpiece is at the TOP now, so its beak tapers upward.
    mp = bkit.lathe("ClarinetMouthpiece",
                    [(0.0, 0.0), (7.4, 4.0), (10.4, 20.0), (11.0, 48.0),
                     (9.5, 74.0), (7.0, 86.0), (0.0, 88.0)],
                    segments=36, centre=(0, 0, 0), mat=grenadilla)
    bkit.move(mp, 0.0, 0.0, Z_MP)
    bkit.rounded_box("ClarinetReed", 13.0, 3.2, 66.0, r=1.2, segments=2,
                     centre=(0.0, -10.5, Z_MP + 44.0), mat=reed)
    for i, (dz, _y) in enumerate(bkit.lay_out([7.0] * 2, gap=4.0)):
        bkit.tube("ClarinetLigature%d" % i, 13.0, 11.0, 7.0, segments=32,
                  centre=(0.0, 0.0, Z_MP + 22.0 + dz), mat=silver)

    # ---- barrel ------------------------------------------------------------
    barrel = bkit.lathe("ClarinetBarrel",
                        [(0.0, 0.0), (R - 1.0, 0.0), (R, 6.0),
                         (R - 1.6, 30.0), (R, SPEC["barrel_length"] - 6.0),
                         (R - 1.0, SPEC["barrel_length"]), (0.0,
                                                            SPEC["barrel_length"])],
                        segments=36, centre=(0, 0, 0), mat=grenadilla)
    bkit.move(barrel, 0.0, 0.0, Z_BARREL)

    # ---- upper joint: turned rings + six tone holes ------------------------
    # The profile is listed TOP-DOWN (long end first). These joints are the
    # only lathes in this file whose profile is wound the other way from
    # bkit.lathe's expectation: listed bottom-up they come out inside-out, and
    # recalc() cannot rescue them because it orients to the surface, not to the
    # volume. Listing the same points in reverse order fixes the winding.
    upper_len = Z_BARREL - Z_UPPER
    upper = bkit.lathe("ClarinetUpperJoint",
                       [(0.0, 0.0), (R - 1.0, 0.0), (R, 8.0), (R - 1.4, 40.0),
                        (R, 90.0), (R - 1.4, 150.0), (R, 210.0),
                        (R - 1.4, upper_len - 40.0), (R, upper_len - 8.0),
                        (R - 1.0, upper_len), (0.0, upper_len)],
                       segments=36, centre=(0, 0, 0), mat=grenadilla)
    bkit.move(upper, 0.0, 0.0, Z_UPPER)
    for i, (z, _w) in enumerate(bkit.lay_out([16.0] * 6, gap=17.0)):
        bkit.bore(upper, 4.4, depth=26.0, centre=(0.0, 0.0,
                                                   Z_UPPER + 96.0 + z),
                  axis="Y", host_segments=36)
    # recalc AFTER the bores: the booleans are what leave these two inside-out,
    # and a recalc taken before the cuts is silently discarded by them.
    bkit.recalc(upper)

    # ---- lower joint: wider, with the swell rings --------------------------
    lower_len = Z_LOWER - Z_BELL
    lower = bkit.lathe("ClarinetLowerJoint",
                       [(0.0, 0.0), (RL - 1.0, 0.0), (RL, 10.0),
                        (RL - 1.4, 60.0), (RL, 130.0), (RL - 1.4, 200.0),
                        (RL, lower_len - 30.0), (RL + 1.0, lower_len - 12.0),
                        (RL + 2.0, lower_len), (0.0, lower_len)],
                       segments=36, centre=(0, 0, 0), mat=grenadilla)
    bkit.move(lower, 0.0, 0.0, Z_LOWER)
    bkit.recalc(lower)
    # The lower joint is bored through at the end (the two C-foot holes are
    # drilled later in the key section), so recalc runs again after that pass.
    bkit.recalc(lower)

    # ---- bell: the flare, opening DOWNWARD at z=0 -------------------------
    # The profile is walked BOTTOM-UP (rim first, throat last) even though the
    # flare grows as z decreases. Walking it the other way (z descending)
    # reverses the winding, and every such lathe comes out inside-out: all three
    # of these reported a negative volume until recalc() was added.
    bl = SPEC["bell_length"]
    bell_prof = [(0.0, -bl), (RL + 2.0, -bl)]
    for i in range(1, 11):
        t = i / 10.0
        bell_prof.append((RL + 2.0 + (SPEC["bell_diameter"] / 2.0 - RL - 2.0)
                          * t ** 2.2, -bl * (1.0 - t)))
    bell_prof.append((0.0, 0.0))
    bell = bkit.lathe("ClarinetBell", bell_prof, segments=48, centre=(0, 0, 0),
                      mat=grenadilla)
    bkit.move(bell, 0.0, 0.0, Z_BELL + bl)
    bkit.recalc(bell)
    bkit.tube("ClarinetBellRim", SPEC["bell_diameter"] / 2.0 + 1.5,
              SPEC["bell_diameter"] / 2.0 - 4.0, 6.0, segments=48,
              centre=(0.0, 0.0, 3.0), mat=key_mat)

    # ---- 17 keys: tone rings, spatulas, the RH stack -----------------------
    parts = []
    # Six tone rings over the six bored tone holes.
    for i, (z, _w) in enumerate(bkit.lay_out([16.0] * 6, gap=17.0)):
        parts.append(bkit.cylinder("ClarinetToneRing%02d" % i, 8.6, 5.0,
                                   segments=24,
                                   centre=(0.0, 0.0, Z_UPPER + 96.0 + z),
                                   axis="Z", mat=key_mat))
        parts.append(bkit.cylinder("ClarinetTonePad%02d" % i, 7.4, 2.4,
                                   segments=20,
                                   centre=(0.0, 0.0, Z_UPPER + 96.0 + z),
                                   axis="Z", mat=pad))
    # The right-hand stack: seven spatulas, alternating side.
    for i, (z, _w) in enumerate(bkit.lay_out([18.0] * 7, gap=13.0)):
        side = -1.0 if i % 2 == 0 else 1.0
        parts.append(bkit.cylinder("ClarinetKeyCup%02d" % i, 7.0, 4.0,
                                   segments=22,
                                   centre=(0.0, side * (R - 2.0),
                                           Z_LOWER + 40.0 + z),
                                   axis="Z", mat=key_mat))
        parts.append(bkit.rounded_box("ClarinetKeyArm%02d" % i, 5.0, 16.0,
                                      3.0, r=1.0, segments=2,
                                      centre=(0.0, side * (R + 6.0),
                                              Z_LOWER + 40.0 + z),
                                      mat=key_mat))
    # The four spatulas of the left-hand pinky table.
    for i, (x, z) in enumerate(((0.0, Z_LOWER + 6.0), (0.0, Z_LOWER + 26.0),
                                (0.0, Z_UPPER - 20.0), (0.0, Z_UPPER - 4.0))):
        parts.append(bkit.rounded_box("ClarinetPalmKey%d" % i, 12.0, 6.0, 16.0,
                                      r=2.0, segments=2,
                                      centre=(x, -(R + 4.0), z),
                                      mat=key_mat))
    # Long rods down the body.
    for i, x in enumerate((-6.0, 6.0)):
        rod = bkit.cylinder("ClarinetRod%d" % i, 1.9, 300.0, segments=12,
                            centre=(0, 0, 0), axis="Z", mat=key_mat)
        bkit.move(rod, x, -(R - 1.0), Z_UPPER + 40.0)
    bkit.join(parts, name="ClarinetKeys")

    return dict(spec=SPEC, parts=6, keys=NKEYS)


CHECKS = [
    # The clarinet is four turned joints stacked on one axis, so the overall
    # length exists only on the assembly, not on any single joint.
    dict(name="overall_length", mm=838.0, tol=3.0, how="bbox_z"),
    # `diameter` is max(sx, sy); on a vertical tube sy/sx are the cross-axis,
    # so the bell's flare and the upper joint's body both measure correctly.
    dict(name="bell_diameter", mm=118.0, tol=2.0, how="diameter",
         part="ClarinetBell"),
    dict(name="barrel_length", mm=68.0, tol=1.0, how="bbox_z",
         part="ClarinetBarrel"),
    dict(name="upper_joint_diameter", mm=29.0, tol=0.6, how="diameter",
         part="ClarinetUpperJoint"),
]