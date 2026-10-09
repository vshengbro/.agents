"""
watch -- 40 mm wristwatch case, 11.6 mm thick, hands read 10:09.

A watch is a stack of thin discs, so almost every part here is a lathe: the
case, the bezel, the dial and the crystal each have a circular silhouette whose
profile changes along its own axis. The case is turned WITH a hollow interior
and a separate dial laid inside it, rather than a solid puck with a disc stuck
on the front -- a real watch has a dial recessed below the bezel and a gap for
the hands to move in, and that gap is most of what makes the profile read.

The hands are set to a real time, 10:09, because that is the time every watch
catalogue is shot at and an arbitrary hand angle reads as a mistake. The angles
are computed from the time, not typed in: minute = 9 * 6 degrees clockwise
from 12, hour = (10 + 9/60) * 30 degrees clockwise from 12, second = 0.
Twelve hour markers come from array_radial about the dial centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

CASE_D = 40.0
CASE_H = 11.6
BEZEL_H = 1.8
DIAL_D = 30.0
DIAL_T = 0.8
CRYSTAL_D = 32.4
CRYSTAL_T = 1.2
CROWN_D = 6.0
CROWN_L = 3.2
LUG_W = 5.0
LUG_L = 7.0
STRAP_W = 20.0
STRAP_T = 3.2
STRAP_L = 22.0

# The real time, and the clock angles it implies.
HOUR, MINUTE, SECOND = 10, 9, 0
MIN_ANG = 90.0 - MINUTE * 6.0                       # 36 deg in math convention
HOUR_ANG = 90.0 - (HOUR % 12) * 30.0 - MINUTE * 0.5  # 145.5 deg
SEC_ANG = 90.0

DIAL_TOP = CASE_H / 2.0 - 1.0
DIAL_Z = DIAL_TOP - DIAL_T / 2.0

SPEC = dict(case_diameter=CASE_D,
            case_height=CASE_H,
            bezel_height=BEZEL_H,
            dial_diameter=DIAL_D,
            crystal_diameter=CRYSTAL_D,
            crown_diameter=CROWN_D,
            strap_width=STRAP_W,
            overall_length=CASE_D + 2.0 * (LUG_L + STRAP_L))


def build():
    steel = bkit.pbr("WatchSteel", base=(0.85, 0.87, 0.90), metal=0.85, rough=0.18)
    dial_mat = bkit.pbr("WatchDial", base=(0.06, 0.07, 0.09), metal=0.0, rough=0.28)
    hand_mat = bkit.pbr("WatchHands", base=(0.92, 0.90, 0.84), metal=0.4, rough=0.22)
    crystal = bkit.pbr("WatchCrystal", base=(0.86, 0.90, 0.94), metal=0.0,
                       rough=0.04, transmission=0.5, ior=1.5)
    leather = bkit.pbr("WatchStrap", base=(0.16, 0.10, 0.07), metal=0.0, rough=0.62)

    # ---- case: a turned shell, hollow, with a stepped bezel ----------------
    rc, rt, ri = CASE_D / 2.0, CASE_H / 2.0, CASE_D / 2.0 - 2.2
    case = bkit.lathe(
        "Case",
        [(ri, -rt + 1.0), (rc - 1.2, -rt), (rc, -rt + 1.2), (rc, rt - BEZEL_H),
         (rc - 1.0, rt), (ri + 1.6, rt), (ri, rt - 1.6), (ri, -rt + 1.0)],
        segments=96, cap_ends=False, mat=steel)

    # ---- dial, recessed inside the case ------------------------------------
    dial = bkit.lathe(
        "Dial",
        [(0.0, -DIAL_T / 2.0), (DIAL_D / 2.0, -DIAL_T / 2.0),
         (DIAL_D / 2.0, DIAL_T / 2.0), (0.0, DIAL_T / 2.0)],
        segments=72, centre=(0.0, 0.0, DIAL_Z), mat=dial_mat)

    # ---- twelve applied hour markers, swept about the dial centre ----------
    marker = bkit.rounded_box("Markers", 2.0, 5.0, 0.9, r=0.35, segments=2,
                              centre=(0.0, DIAL_D / 2.0 - 4.0,
                                      DIAL_Z + DIAL_T / 2.0 + 0.45),
                              mat=hand_mat)
    bkit.array_radial(marker, 12, centre=(0.0, 0.0, DIAL_Z + DIAL_T / 2.0 + 0.45))

    # ---- hands at 10:09 ----------------------------------------------------
    hand_z = DIAL_Z + DIAL_T / 2.0
    hour = bkit.rounded_box("HourHand", 9.5, 2.6, 0.7, r=0.3, segments=2,
                            centre=(4.75, 0.0, hand_z + 0.35), mat=hand_mat)
    hour.rotation_euler = (0.0, 0.0, math.radians(HOUR_ANG))
    minute = bkit.rounded_box("MinuteHand", 13.0, 1.9, 0.6, r=0.25, segments=2,
                              centre=(6.5, 0.0, hand_z + 0.95), mat=hand_mat)
    minute.rotation_euler = (0.0, 0.0, math.radians(MIN_ANG))
    second = bkit.rounded_box("SecondHand", 13.5, 0.8, 0.5, r=0.2, segments=2,
                              centre=(4.0, 0.0, hand_z + 1.45),
                              mat=bkit.pbr("WatchSecond", base=(0.75, 0.12, 0.10),
                                           metal=0.0, rough=0.3))
    second.rotation_euler = (0.0, 0.0, math.radians(SEC_ANG))
    cap = bkit.cylinder("HandCap", 1.5, 1.4, segments=24,
                        centre=(0.0, 0.0, hand_z + 1.4), mat=hand_mat)

    # ---- crystal -----------------------------------------------------------
    lens = bkit.lathe(
        "Crystal",
        [(0.0, -CRYSTAL_T / 2.0), (CRYSTAL_D / 2.0, -CRYSTAL_T / 2.0),
         (CRYSTAL_D / 2.0, CRYSTAL_T / 2.0 - 0.5),
         (CRYSTAL_D / 2.0 - 0.8, CRYSTAL_T / 2.0), (0.0, CRYSTAL_T / 2.0)],
        segments=72, centre=(0.0, 0.0, CASE_H / 2.0 - CRYSTAL_T / 2.0 + 0.2),
        mat=crystal)

    # ---- crown at 3 o'clock -------------------------------------------------
    crown = bkit.cylinder("Crown", CROWN_D / 2.0, CROWN_L, segments=28,
                          centre=(CASE_D / 2.0 + CROWN_L / 2.0 - 0.6, 0.0, 0.0),
                          axis="X", mat=steel)

    # ---- four lugs and two strap stubs -------------------------------------
    lugs = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            lugs.append(bkit.rounded_box(
                "Lug", LUG_W, LUG_L, 3.4, r=1.2, segments=2,
                centre=(sx * (CASE_D / 2.0 - LUG_W / 2.0 - 0.6),
                        sy * (CASE_D / 2.0 + LUG_L / 2.0 - 0.6), 0.0),
                mat=steel))
    bkit.join(lugs, name="Lugs")

    # The second strap stub is a mirror of the first about the case, so the
    # world-space step is exactly the centre-to-centre distance of the pair.
    strap_y = CASE_D / 2.0 + LUG_L + STRAP_L / 2.0 - 2.0
    strap = bkit.rounded_box("Strap", STRAP_W, STRAP_L, STRAP_T, r=1.2, segments=2,
                             centre=(0.0, strap_y, 0.0), mat=leather)
    bkit.array_linear(strap, 2, (0.0, -2.0 * strap_y, 0.0), world=True)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="case_diameter", mm=40.0, tol=0.1, how="diameter", part="Case"),
    dict(name="case_height", mm=11.6, tol=0.1, how="bbox_z", part="Case"),
    dict(name="dial_diameter", mm=30.0, tol=0.1, how="diameter", part="Dial"),
    dict(name="crown_diameter", mm=6.0, tol=0.1, how="diameter", part="Crown"),
    dict(name="strap_width", mm=20.0, tol=0.1, how="bbox_x", part="Strap"),
    dict(name="strap_thickness", mm=3.2, tol=0.1, how="bbox_z", part="Strap")
]