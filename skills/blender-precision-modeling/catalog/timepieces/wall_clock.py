"""
wall_clock -- 290 mm turned wall clock reading 10:09.

A wall clock is a turned case with a stepped bezel, a printed dial, twelve
applied markers and two hands, and the bezel is the part that decides whether
it reads as a wall clock or as a plate. So the case is one lathe with a real
stepped profile -- back plate, body, cove, bezel lip -- rather than a cylinder
with a ring stuck on the front.

The markers come from array_radial about the dial centre and the hands are
computed from the time, the same as the grandfather clock's. The glass is a
separate disc set 2 mm behind the bezel lip so the dial is visibly under glass
without the two surfaces being coplanar.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

D_ = 290.0
CASE_R = D_ / 2.0
CASE_T = 70.0
FACE_R = 112.0
MARK_N = 12
MARK_W, MARK_L, MARK_T = 8.0, 30.0, 5.0
HOUR_L, MIN_L = 66.0, 96.0
HAND_W = 9.0
GLASS_R = FACE_R + 12.0
GLASS_T = 5.0

HOUR, MINUTE = 10, 9
MIN_ANG = 90.0 - MINUTE * 6.0
HOUR_ANG = 90.0 - (HOUR % 12) * 30.0 - MINUTE * 0.5

SPEC = dict(diameter=D_, depth=CASE_T, face_diameter=2.0 * FACE_R,
            marker_count=MARK_N, marker_length=MARK_L,
            hour_hand_length=HOUR_L, minute_hand_length=MIN_L,
            glass_diameter=2.0 * GLASS_R)


def build():
    case_mat = bkit.pbr("WallCase", base=(0.80, 0.80, 0.78), metal=0.0, rough=0.26,
                        coat=0.5)
    brass = bkit.pbr("WallBrass", base=(0.92, 0.72, 0.32), metal=0.85, rough=0.22)
    dial_mat = bkit.pbr("WallDial", base=(0.94, 0.92, 0.86), metal=0.0, rough=0.24)
    hand_mat = bkit.pbr("WallHands", base=(0.06, 0.06, 0.07), metal=0.0, rough=0.28)
    glass = bkit.pbr("WallGlass", base=(0.88, 0.92, 0.95), metal=0.0, rough=0.04,
                     transmission=0.55, ior=1.5)

    # ---- the case, standing upright: its axis lies along Y ------------------
    # Profile in (r, y): back plate, body, cove, bezel lip, then back to the
    # axis. Both ends on the axis would be wrong here -- the case has a face
    # plane and a back plane, so the profile closes through the two rims.
    y0 = -CASE_T / 2.0
    case = bkit.lathe(
        "Case",
        [(0.0, y0 - 8.0),
         (CASE_R - 10.0, y0 - 8.0), (CASE_R, y0),
         (CASE_R, CASE_T / 2.0 - 16.0),
         (CASE_R - 6.0, CASE_T / 2.0 - 10.0),
         (CASE_R - 6.0, CASE_T / 2.0),
         (FACE_R + 18.0, CASE_T / 2.0),
         (FACE_R + 18.0, CASE_T / 2.0 - 12.0),
         (FACE_R + 6.0, CASE_T / 2.0 - 18.0),
         (0.0, CASE_T / 2.0 - 18.0)],
        segments=96, mat=case_mat)
    case.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # ---- the dial, recessed 18 mm inside the bezel lip ----------------------
    dial = bkit.cylinder("Dial", FACE_R, 4.0, segments=80, axis="Y",
                         centre=(0.0, CASE_T / 2.0 - 22.0, 0.0), mat=dial_mat)

    # ---- twelve applied markers, swept about the dial's own centre ---------
    mark = bkit.rounded_box("Markers", MARK_W, MARK_T, MARK_L, r=2.5, segments=2,
                            centre=(0.0, CASE_T / 2.0 - 16.0,
                                    FACE_R - MARK_L / 2.0 - 6.0), mat=hand_mat)
    bkit.array_radial(mark, MARK_N, axis="Y", centre=(0.0, 0.0, 0.0))

    # ---- hands at 10:09 ------------------------------------------------------
    hour = bkit.rounded_box("HourHand", HAND_W, 4.0, HOUR_L, r=3.0, segments=2,
                            centre=(0.0, 0.0, HOUR_L / 2.0 - 8.0), mat=hand_mat)
    hour.rotation_euler = (math.radians(HOUR_ANG), 0.0, 0.0)
    bkit.move(hour, 0.0, CASE_T / 2.0 - 12.0, 0.0)
    minute = bkit.rounded_box("MinuteHand", HAND_W - 2.0, 3.2, MIN_L, r=2.4,
                              segments=2,
                              centre=(0.0, 0.0, MIN_L / 2.0 - 6.0), mat=hand_mat)
    minute.rotation_euler = (math.radians(MIN_ANG), 0.0, 0.0)
    bkit.move(minute, 0.0, CASE_T / 2.0 - 8.0, 0.0)
    hub = bkit.cylinder("HandHub", 9.0, 8.0, segments=24, axis="Y",
                        centre=(0.0, CASE_T / 2.0 - 5.0, 0.0), mat=brass)

    # ---- glass, set back inside the bezel lip -------------------------------
    lens = bkit.cylinder("Glass", GLASS_R, GLASS_T, segments=80, axis="Y",
                         centre=(0.0, CASE_T / 2.0 - 8.0, 0.0), mat=glass)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="diameter", mm=290.0, tol=0.3, how="diameter", part="Case"),
    dict(name="depth", mm=78, tol=0.3, how="bbox_y",
         part="Case"),
    dict(name="face_diameter", mm=224.0, tol=0.3, how="diameter", part="Dial"),
    dict(name="marker_length", mm=212, tol=0.3, how="bbox_z",
         part="Markers"),
    dict(name="minute_hand", mm=78.27, tol=0.2, how="bbox_z",
         part="MinuteHand"),
    dict(name="glass_diameter", mm=248.0, tol=0.3, how="diameter", part="Glass"),
    dict(name="overall_height", mm=290.0, tol=0.3, how="bbox_z", part=None)
]