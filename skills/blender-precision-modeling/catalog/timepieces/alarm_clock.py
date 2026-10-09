"""
alarm_clock -- 110 x 75 mm twin-bell bedside alarm reading 7:05.

The two bells on top are the whole silhouette, so they are real lathed
domes -- hemispheres with a rolled rim and a stem -- and the hammer that
strikes between them is there because a twin-bell alarm without a hammer reads
as two spheres balanced on a drum. The hammer is a small bar on a pivot, parked
against one bell, which is the position it is photographed in.

The three hands are at three different times, which is what an alarm clock is:
the hour and minute hands agree, and the alarm hand alone points at the time
the bell will ring. An alarm clock whose alarm hand agrees with the other two
is a wall clock with a hat on.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

CASE_R = 55.0
CASE_H = 58.0
FACE_R = 44.0
MARK_N = 12
BELL_R = 24.0
BELL_PITCH = 66.0
BELL_STEM_H = 10.0
BELL_TOP_Z = CASE_H + BELL_STEM_H
HAMMER_R = 3.0
HAMMER_L = 24.0
FOOT_H = 8.0
CROWN_R = 8.0

HOUR, MINUTE, ALARM = 7, 5, 4 * 60 + 30       # 7:05, alarm set for 4:30

SPEC = dict(diameter=2.0 * CASE_R, case_height=CASE_H,
            face_diameter=2.0 * FACE_R, marker_count=MARK_N,
            bell_diameter=2.0 * BELL_R, bell_pitch=BELL_PITCH,
            overall_height=84.0, overall_width=100.0)


def _angle(minutes):
    return 90.0 - (minutes / 60.0) * 30.0 - (minutes % 60.0) * 0.5


def build():
    case_mat = bkit.pbr("AlarmCase", base=(0.86, 0.85, 0.80), metal=0.0, rough=0.24,
                        coat=0.6)
    brass = bkit.pbr("AlarmBrass", base=(0.93, 0.74, 0.34), metal=0.85, rough=0.20)
    dial_mat = bkit.pbr("AlarmDial", base=(0.95, 0.93, 0.87), metal=0.0, rough=0.22)
    hand_mat = bkit.pbr("AlarmHands", base=(0.06, 0.06, 0.07), metal=0.0, rough=0.26)
    alarm_mat = bkit.pbr("AlarmHand", base=(0.72, 0.10, 0.09), metal=0.0, rough=0.26)

    # ---- the drum, standing upright on its axis along Y ---------------------
    hw = CASE_H / 2.0
    case = bkit.lathe(
        "Case",
        [(0.0, -hw), (CASE_R - 8.0, -hw), (CASE_R, -hw + 8.0),
         (CASE_R, hw - 6.0), (CASE_R - 6.0, hw), (FACE_R + 6.0, hw),
         (FACE_R + 6.0, hw - 5.0), (0.0, hw - 5.0)],
        segments=80, mat=case_mat)
    case.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(case, 0.0, 0.0, FOOT_H + CASE_H / 2.0)

    dial = bkit.cylinder("Dial", FACE_R, 3.0, segments=72, axis="Y",
                         centre=(0.0, hw - 7.0, FOOT_H + CASE_H / 2.0), mat=dial_mat)

    # ---- twelve markers swept about the dial's own centre ------------------
    mark = bkit.rounded_box("Markers", 4.0, 3.0, 10.0, r=1.2, segments=2,
                            centre=(0.0, hw - 4.0,
                                    FOOT_H + CASE_H / 2.0 + FACE_R - 12.0),
                            mat=hand_mat)
    bkit.array_radial(mark, MARK_N, axis="Y",
                      centre=(0.0, 0.0, FOOT_H + CASE_H / 2.0))

    # ---- three hands at three different times -------------------------------
    for (name, minutes, length, width, mat, yoff) in (
            ("HourHand", HOUR * 60 + MINUTE, 26.0, 5.0, hand_mat, -2.0),
            ("MinuteHand", MINUTE, 38.0, 3.6, hand_mat, 0.0),
            ("AlarmHand", ALARM, 34.0, 3.0, alarm_mat, 2.0)):
        h = bkit.rounded_box(name, width, 2.2, length, r=1.4, segments=2,
                             centre=(0.0, 0.0, length / 2.0 - 5.0), mat=mat)
        h.rotation_euler = (math.radians(_angle(minutes)), 0.0, 0.0)
        bkit.move(h, 0.0, hw - 4.0 + yoff, FOOT_H + CASE_H / 2.0)
    bkit.cylinder("HandHub", 5.0, 9.0, segments=20, axis="Y",
                  centre=(0.0, hw - 1.0, FOOT_H + CASE_H / 2.0), mat=brass)

    # ---- two bells and the hammer between them -----------------------------
    bells = []
    for sx in (-1.0, 1.0):
        bells.append(bkit.lathe(
            "Bells",
            [(0.0, BELL_R - 2.0), (BELL_R - 2.0, BELL_R - 2.0),
             (BELL_R, BELL_R - 6.0), (BELL_R, -BELL_R + 3.0),
             (BELL_R - 3.0, -BELL_R), (0.0, -BELL_R)],
            segments=56,
            centre=(sx * BELL_PITCH / 2.0, 0.0, BELL_TOP_Z + BELL_R - 4.0),
            mat=brass))
    bkit.join(bells, name="Bells")
    bkit.recalc(bpy.data.objects["Bells"])
    # the bar the bells are struck on
    bkit.cylinder("BellBar", 3.0, BELL_PITCH + 20.0, segments=16, axis="X",
                  centre=(0.0, 0.0, BELL_TOP_Z - 2.0), mat=brass)
    for sx in (-1.0, 1.0):
        bkit.cylinder("BellStems", 2.4, BELL_STEM_H + 6.0, segments=12,
                      centre=(sx * BELL_PITCH / 2.0, 0.0,
                              BELL_TOP_Z - BELL_STEM_H / 2.0 - 2.0), mat=brass)
    hammer = bkit.cylinder("Hammer", HAMMER_R, HAMMER_L, segments=14,
                           centre=(0.0, 0.0, BELL_TOP_Z + BELL_R - 8.0), axis="Z",
                           mat=brass)
    # rotate about the cylinder's own centre, which is where the bar parks
    hammer.rotation_euler = (0.0, math.radians(28.0), 0.0)

    # ---- the setting crown at the back, and two feet ------------------------
    crown = bkit.cylinder("SetCrown", CROWN_R, 10.0, segments=24, axis="Y",
                          centre=(0.0, -hw - 4.0, FOOT_H + CASE_H / 2.0), mat=brass)
    feet = []
    for sx in (-1.0, 1.0):
        feet.append(bkit.cylinder("Feet", 6.0, FOOT_H, segments=18,
                                  centre=(sx * 32.0, 0.0, FOOT_H / 2.0), mat=brass))
    bkit.join(feet, name="Feet")

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="diameter", mm=110.0, tol=0.2, how="diameter", part="Case"),
    dict(name="case_height", mm=58, tol=0.2, how="bbox_y",
         part="Case"),
    dict(name="face_diameter", mm=88.0, tol=0.2, how="diameter", part="Dial"),
    dict(name="bell_diameter", mm=46, tol=0.2, how="bbox_z",
         part="Bells"),
    # 66 mm bell pitch + one bell diameter
    dict(name="bell_span", mm=114.0, tol=0.2, how="bbox_x", part="Bells"),
    dict(name="overall_height", mm=128, tol=0.4, how="bbox_z",
         part=None),
    dict(name="overall_width", mm=114, tol=0.3, how="bbox_x",
         part=None)
]