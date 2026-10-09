"""
timer -- 90 x 90 x 84 mm 60-minute kitchen timer on three feet.

A kitchen timer is a drum with a 0-60 scale, a setting hand and a running
hand, a winder on top and a bell underneath -- and the two hands disagreeing is
the whole point, because a timer whose hands agree is a clock. So the setting
hand is at 4 minutes and the running hand at 22, with a red pointer for the
setting and a steel one for running.

The sixty-minute scale is twelve five-minute marks swept about the dial's own
centre, with the four quarter-hours longer than the rest, which is how a real
timer dial is drawn. The bell is under the drum and is why the drum stands on
three feet rather than sitting flat.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

CASE_R = 45.0
CASE_H = 58.0
FOOT_H = 9.0
FOOT_R = 7.0
FACE_R = 36.0
MARK_N = 12
MARK_W, MARK_L, MARK_T = 3.0, 9.0, 2.4
LONG_MARK_L = 15.0
SET_MIN, RUN_MIN = 4.0, 22.0
CROWN_R = 9.0
CROWN_L = 12.0
BELL_R = 18.0

SPEC = dict(diameter=2.0 * CASE_R, case_height=CASE_H,
            face_diameter=2.0 * FACE_R, mark_count=MARK_N,
            crown_diameter=2.0 * CROWN_R, foot_height=FOOT_H,
            overall_height=FOOT_H + CASE_H + CROWN_L - 2.0)


def _angle(minutes):
    return 90.0 - (minutes / 60.0) * 30.0 - (minutes % 60.0) * 0.5


def build():
    case_mat = bkit.pbr("TimerCase", base=(0.90, 0.88, 0.82), metal=0.0, rough=0.24,
                        coat=0.6)
    brass = bkit.pbr("TimerBrass", base=(0.93, 0.74, 0.34), metal=0.85, rough=0.20)
    dial_mat = bkit.pbr("TimerDial", base=(0.95, 0.93, 0.87), metal=0.0, rough=0.22)
    hand_mat = bkit.pbr("TimerHand", base=(0.06, 0.06, 0.07), metal=0.0, rough=0.26)
    set_mat = bkit.pbr("TimerSetHand", base=(0.74, 0.10, 0.09), metal=0.0, rough=0.26)

    cz = FOOT_H + CASE_H / 2.0
    hw = CASE_H / 2.0
    case = bkit.lathe(
        "Case",
        [(0.0, -hw), (CASE_R - 6.0, -hw), (CASE_R, -hw + 6.0),
         (CASE_R, hw - 5.0), (CASE_R - 5.0, hw), (FACE_R + 5.0, hw),
         (FACE_R + 5.0, hw - 4.0), (0.0, hw - 4.0)],
        segments=80, mat=case_mat)
    case.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(case, 0.0, 0.0, cz)

    dial = bkit.cylinder("Dial", FACE_R, 3.0, segments=72, axis="Y",
                         centre=(0.0, hw - 6.0, cz), mat=dial_mat)

    # ---- twelve five-minute marks, swept about the dial's own centre -------
    # The four quarter-hours are longer, so the one mark is built at the long
    # length and stepped to the short one for the remaining eight.
    mark = bkit.rounded_box("Marks", MARK_W, MARK_T, LONG_MARK_L, r=1.0, segments=2,
                            centre=(0.0, hw - 3.0, cz + FACE_R - LONG_MARK_L / 2.0 - 4.0),
                            mat=hand_mat)
    bkit.array_radial(mark, 4, axis="Y", centre=(0.0, 0.0, cz))
    short = bkit.rounded_box("Marks", MARK_W, MARK_T, MARK_L, r=0.8, segments=2,
                             centre=(0.0, hw - 3.0, cz + FACE_R - MARK_L / 2.0 - 4.0),
                             mat=hand_mat)
    short.rotation_euler = (math.radians(30.0), 0.0, 0.0)
    bkit.array_radial(short, 8, axis="Y", centre=(0.0, 0.0, cz))

    # ---- the two hands, at two different times -----------------------------
    for (name, minutes, length, width, mat, yoff) in (
            ("RunHand", RUN_MIN, 30.0, 3.4, hand_mat, -1.0),
            ("SetHand", SET_MIN, 26.0, 2.4, set_mat, 1.0)):
        h = bkit.rounded_box(name, width, 2.0, length, r=1.2, segments=2,
                             centre=(0.0, 0.0, length / 2.0 - 4.0), mat=mat)
        h.rotation_euler = (math.radians(_angle(minutes)), 0.0, 0.0)
        bkit.move(h, 0.0, hw - 3.0 + yoff, cz)
    bkit.cylinder("HandHub", 4.4, 8.0, segments=20, axis="Y",
                  centre=(0.0, hw - 0.5, cz), mat=brass)

    # ---- the winder on top, and the bell underneath ------------------------
    crown = bkit.cylinder("Winder", CROWN_R, CROWN_L, segments=28,
                          centre=(0.0, 0.0, FOOT_H + CASE_H + CROWN_L / 2.0 - 2.0),
                          mat=brass)
    bkit.lathe("Bell",
               [(0.0, 0.0), (BELL_R - 3.0, 0.0), (BELL_R, 3.0),
                (BELL_R, FOOT_H - 3.0), (BELL_R - 3.0, FOOT_H), (0.0, FOOT_H)],
               segments=48, centre=(0.0, 0.0, 0.0), mat=brass)
    bell_arm = bkit.cylinder("BellArm", 2.2, FOOT_H + 8.0, segments=12,
                             centre=(BELL_R - 2.0, 0.0, (FOOT_H + 8.0) / 2.0),
                             mat=brass)

    # ---- three feet ---------------------------------------------------------
    feet = []
    for (fx, fy) in ((-1.0, -1.0), (1.0, -1.0), (0.0, 1.0)):
        feet.append(bkit.cylinder("Feet", FOOT_R, FOOT_H, segments=18,
                                  centre=(fx * 28.0, fy * 24.0, FOOT_H / 2.0),
                                  mat=brass))
    bkit.join(feet, name="Feet")

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="diameter", mm=90.0, tol=0.2, how="diameter", part="Case"),
    dict(name="case_height", mm=58, tol=0.2, how="bbox_y",
         part="Case"),
    dict(name="face_diameter", mm=72.0, tol=0.2, how="diameter", part="Dial"),
    dict(name="crown_diameter", mm=18.0, tol=0.2, how="diameter", part="Winder"),
    dict(name="bell_diameter", mm=36.0, tol=0.2, how="diameter", part="Bell"),
    dict(name="foot_height", mm=9.0, tol=0.1, how="bbox_z", part="Feet"),
    dict(name="overall_height", mm=90, tol=0.2, how="bbox_z",
         part=None)
]