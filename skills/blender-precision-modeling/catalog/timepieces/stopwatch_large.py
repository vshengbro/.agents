"""
stopwatch_large -- 100 x 100 x 58 mm split/lap timer with a crown and a lanyard.

A split timer is a stopwatch with a second crown: one resets, the other starts
and stops a lap. So the silhouette needs BOTH crowns -- a large knurled one on
the right and a smaller push button on the left -- and that pair is the whole
difference between a stopwatch and a split timer. Both are knurled, and the
knurl is a real ring of flutes swept about the crown's own axis, because a
smooth cylinder at this diameter reads as a peg.

The face is a 60-minute sweep with twelve five-minute marks, and the minute
hand is at 3:40 with the small seconds hand at 20 seconds, so the two hands
disagree the way a running stopwatch's do.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

CASE_R = 46.0
CASE_T = 30.0
FOOT_W, FOOT_D, FOOT_H = 34.0, 22.0, 10.0
FACE_R = 38.0
MARK_N = 12
MARK_W, MARK_L, MARK_T = 3.0, 8.0, 2.0
SUB_D = 11.0
HAND_L = 32.0
SUBHAND_L = 9.0
CROWN_R, CROWN_L, FLUTES = 9.0, 9.0, 18
BTN_R, BTN_L, BTN_FLUTES = 6.5, 6.0, 14
LOOP_R, LOOP_W = 5.0, 1.6
MINUTE, SECOND = 3.0 + 40.0 / 60.0, 20.0

SPEC = dict(diameter=2.0 * CASE_R, depth=CASE_T, face_diameter=2.0 * FACE_R,
            mark_count=MARK_N, crown_diameter=2.0 * CROWN_R,
            crown_flutes=FLUTES, button_diameter=2.0 * BTN_R,
            button_flutes=BTN_FLUTES, lanyard_diameter=2.0 * (LOOP_R + LOOP_W / 2.0))


def build():
    steel = bkit.pbr("StopwatchSteel", base=(0.86, 0.88, 0.91), metal=0.85, rough=0.14)
    dial_mat = bkit.pbr("StopwatchDial", base=(0.08, 0.08, 0.10), metal=0.0, rough=0.30)
    hand_mat = bkit.pbr("StopwatchHands", base=(0.93, 0.91, 0.86), metal=0.0, rough=0.24)
    sub_mat = bkit.pbr("StopwatchSubdial", base=(0.90, 0.88, 0.82), metal=0.0,
                       rough=0.32)

    # ---- case: a drum on its side, standing on a foot ----------------------
    hw = CASE_T / 2.0
    case = bkit.lathe(
        "Case",
        [(0.0, -hw - 2.0), (CASE_R - 8.0, -hw - 2.0), (CASE_R, -hw),
         (CASE_R, hw - 6.0), (CASE_R - 6.0, hw), (FACE_R + 4.0, hw),
         (FACE_R + 4.0, hw - 3.0), (0.0, hw - 3.0)],
        segments=88, mat=steel)
    case.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(case, 0.0, 0.0, CASE_R + FOOT_H)

    foot = bkit.rounded_box("Foot", FOOT_W, FOOT_D, FOOT_H, r=2.5, segments=3,
                            centre=(0.0, 0.0, FOOT_H / 2.0), mat=steel)

    # ---- the dial, the twelve marks and the small seconds sub-dial ----------
    fy = hw - 4.0
    cz = CASE_R + FOOT_H
    dial = bkit.cylinder("Dial", FACE_R, 2.0, segments=72, axis="Y",
                         centre=(0.0, fy, cz), mat=dial_mat)
    mark = bkit.rounded_box("Marks", MARK_W, MARK_T, MARK_L, r=0.9, segments=2,
                            centre=(0.0, fy + 1.6, cz + FACE_R - MARK_L / 2.0 - 5.0),
                            mat=hand_mat)
    bkit.array_radial(mark, MARK_N, axis="Y", centre=(0.0, 0.0, cz))
    sub = bkit.cylinder("Subdial", SUB_D, 1.4, segments=40, axis="Y",
                        centre=(0.0, fy + 1.6, cz - 16.0), mat=sub_mat)
    subhand = bkit.rounded_box("SecondHand", 0.9, 0.8, SUBHAND_L, r=0.3, segments=2,
                               centre=(0.0, 0.0, SUBHAND_L / 2.0 - 1.0), mat=hand_mat)
    subhand.rotation_euler = (math.radians(90.0 - SECOND * 6.0), 0.0, 0.0)
    bkit.move(subhand, 0.0, fy + 2.6, cz - 16.0)

    # ---- the minute hand, running ------------------------------------------
    hand = bkit.rounded_box("MinuteHand", 2.6, 1.8, HAND_L, r=1.0, segments=2,
                            centre=(0.0, 0.0, HAND_L / 2.0 - 4.0), mat=hand_mat)
    hand.rotation_euler = (math.radians(90.0 - MINUTE * 6.0), 0.0, 0.0)
    bkit.move(hand, 0.0, fy + 2.0, cz)
    bkit.cylinder("HandHub", 3.0, 5.0, segments=18, axis="Y",
                  centre=(0.0, fy + 3.0, cz), mat=steel)

    # ---- the large crown and the small lap button, both knurled ------------
    crown = bkit.cylinder("Crown", CROWN_R, CROWN_L, segments=40, axis="X",
                          centre=(CASE_R + CROWN_L / 2.0 - 1.0, 0.0, cz), mat=steel)
    flute = bkit.rounded_box("CrownFlutes", 1.6, 1.8, 2.0, r=0.5, segments=2,
                             centre=(CASE_R + CROWN_L / 2.0 - 1.0,
                                     CROWN_R - 0.4, cz), mat=steel)
    bkit.array_radial(flute, FLUTES, axis="X",
                      centre=(CASE_R + CROWN_L / 2.0 - 1.0, 0.0, cz))
    bflute = bkit.rounded_box("ButtonFlutes", 1.2, 1.4, 1.6, r=0.4, segments=2,
                              centre=(-(CASE_R + BTN_L / 2.0 - 1.0), BTN_R - 0.3, cz),
                              mat=steel)
    bkit.array_radial(bflute, BTN_FLUTES, axis="X",
                      centre=(-(CASE_R + BTN_L / 2.0 - 1.0), 0.0, cz))
    button = bkit.cylinder("LapButton", BTN_R, BTN_L, segments=32, axis="X",
                           centre=(-(CASE_R + BTN_L / 2.0 - 1.0), 0.0, cz), mat=steel)

    # ---- the lanyard loop on top --------------------------------------------
    loop = bkit.torus("LanyardLoop", LOOP_R, LOOP_W / 2.0, seg_major=36, seg_minor=10,
                      centre=(0.0, 0.0, 2.0 * CASE_R + FOOT_H - 2.0), axis="Y",
                      mat=steel)
    stem = bkit.cylinder("LanyardStem", 2.4, 8.0, segments=14, axis="Z",
                         centre=(0.0, 0.0, 2.0 * CASE_R + FOOT_H - 8.0), mat=steel)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="diameter", mm=92.0, tol=0.2, how="diameter", part="Case"),
    dict(name="depth", mm=32, tol=0.2, how="bbox_y",
         part="Case"),
    dict(name="face_diameter", mm=76.0, tol=0.2, how="diameter", part="Dial"),
    dict(name="crown_diameter", mm=18.0, tol=0.2, how="diameter", part="Crown"),
    dict(name="button_diameter", mm=13.0, tol=0.2, how="diameter", part="LapButton"),
    dict(name="lanyard_diameter", mm=11.6, tol=0.1, how="bbox_x",
         part="LanyardLoop"),
    dict(name="overall_height", mm=105.8, tol=0.3, how="bbox_z",
         part=None),
    dict(name="overall_width", mm=105, tol=0.3, how="bbox_x",
         part=None)
]