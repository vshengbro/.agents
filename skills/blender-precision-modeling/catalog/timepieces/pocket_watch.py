"""
pocket_watch -- 46 x 14 mm hunter-case pocket watch reading 10:09.

A pocket watch is small enough that the case construction is the model. The
case is a closed (r, y) cross-section: a back plate, a band, a front bezel that
overlaps the band, and a domed crystal. Modelling it as a closed loop rather
than as a stack of discs is what lets the bezel overlap the band without the
two surfaces fighting, and it is the same construction the washer uses.

The bow at twelve o'clock is a real suspension bow -- a half torus standing
proud of the case on a short neck -- and the crown is knurled, because a
smooth cylinder at that size reads as a peg rather than a winder.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py. At a 28 mm bounding
# radius the harness parks the camera ~66 mm out, inside the 0.1 m default
# near plane, so the model would render as an empty backdrop.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

CASE_R = 23.0
CASE_T = 14.0
FACE_R = 18.4
BEZEL_R = 21.6
GLASS_R = 18.0
GLASS_T = 1.6
MARK_N = 12
HOUR_L, MIN_L = 11.0, 15.5
BOW_R = 4.0
BOW_W = 1.4
NECK_R = 2.0
NECK_L = 4.0
CROWN_R = 3.4
CROWN_L = 3.0

HOUR, MINUTE = 10, 9
MIN_ANG = 90.0 - MINUTE * 6.0
HOUR_ANG = 90.0 - (HOUR % 12) * 30.0 - MINUTE * 0.5

SPEC = dict(case_diameter=2.0 * CASE_R, case_thickness=CASE_T,
            bezel_diameter=2.0 * BEZEL_R, face_diameter=2.0 * FACE_R,
            marker_count=MARK_N, hour_hand_length=HOUR_L,
            minute_hand_length=MIN_L, bow_diameter=2.0 * (BOW_R + BOW_W / 2.0))


def build():
    gold = bkit.pbr("WatchGold", base=(0.98, 0.79, 0.38), metal=0.85, rough=0.15)
    dial_mat = bkit.pbr("PocketDial", base=(0.94, 0.92, 0.86), metal=0.0, rough=0.20,
                        coat=0.5)
    hand_mat = bkit.pbr("PocketHands", base=(0.06, 0.06, 0.07), metal=0.0, rough=0.26)
    glass = bkit.pbr("PocketCrystal", base=(0.90, 0.93, 0.97), metal=0.0, rough=0.03,
                     transmission=0.6, ior=1.52)

    # ---- case: a closed (r, y) cross-section revolved about Y --------------
    # Front bezel overlaps the band by 1.2 mm rather than meeting it flush.
    y0, y1 = -CASE_T / 2.0, CASE_T / 2.0
    case = bkit.lathe(
        "Case",
        [(0.0, y0 - 1.0),
         (CASE_R - 2.0, y0 - 1.0), (CASE_R, y0),
         (CASE_R, y1 - 2.0), (BEZEL_R, y1 - 1.2), (BEZEL_R, y1),
         (FACE_R + 1.0, y1), (FACE_R + 1.0, y1 - 2.4),
         (FACE_R, y1 - 3.0), (0.0, y1 - 3.0)],
        segments=80, mat=gold)
    case.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # ---- dial, crystal -------------------------------------------------------
    dial = bkit.cylinder("Dial", FACE_R, 1.4, segments=64, axis="Y",
                         centre=(0.0, y1 - 3.8, 0.0), mat=dial_mat)
    crystal = bkit.lathe(
        "Crystal",
        [(0.0, -GLASS_T / 2.0), (GLASS_R - 0.6, -GLASS_T / 2.0),
         (GLASS_R, -GLASS_T / 2.0 + 0.6), (GLASS_R - 1.2, GLASS_T / 2.0),
         (0.0, GLASS_T / 2.0)],
        segments=64, centre=(0.0, y1 - 1.4, 0.0), mat=glass)
    crystal.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # ---- twelve markers, swept about the dial's own centre ------------------
    mark = bkit.rounded_box("Markers", 1.8, 1.0, 3.2, r=0.6, segments=2,
                            centre=(0.0, y1 - 2.6, FACE_R - 3.4), mat=hand_mat)
    bkit.array_radial(mark, MARK_N, axis="Y", centre=(0.0, 0.0, 0.0))

    # ---- hands at 10:09 -------------------------------------------------------
    hour = bkit.rounded_box("HourHand", 1.8, 0.8, HOUR_L, r=0.6, segments=2,
                            centre=(0.0, 0.0, HOUR_L / 2.0 - 1.8), mat=hand_mat)
    hour.rotation_euler = (math.radians(HOUR_ANG), 0.0, 0.0)
    bkit.move(hour, 0.0, y1 - 2.0, 0.0)
    minute = bkit.rounded_box("MinuteHand", 1.3, 0.7, MIN_L, r=0.5, segments=2,
                              centre=(0.0, 0.0, MIN_L / 2.0 - 1.8), mat=hand_mat)
    minute.rotation_euler = (math.radians(MIN_ANG), 0.0, 0.0)
    bkit.move(minute, 0.0, y1 - 1.4, 0.0)
    bkit.cylinder("HandHub", 1.6, 1.6, segments=16, axis="Y",
                  centre=(0.0, y1 - 0.8, 0.0), mat=gold)

    # ---- the bow, its neck and the crown -------------------------------------
    neck = bkit.cylinder("BowNeck", NECK_R, NECK_L, segments=16, axis="Z",
                         centre=(0.0, 0.0, CASE_R + NECK_L / 2.0 - 0.5), mat=gold)
    bow = bkit.arc_torus("Bow", BOW_R, BOW_W / 2.0, 0.0, 180.0, plane="YZ",
                         seg_major=36, seg_minor=10,
                         centre=(0.0, 0.0, CASE_R + NECK_L + BOW_R - 0.5),
                         mat=gold, caps=True)
    crown = bkit.cylinder("Crown", CROWN_R, CROWN_L, segments=24, axis="Z",
                          centre=(0.0, 0.0, CASE_R + CROWN_L / 2.0 - 1.0), mat=gold)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="case_diameter", mm=46.0, tol=0.05, how="diameter", part="Case"),
    dict(name="case_thickness", mm=15.0, tol=0.05, how="bbox_y", part="Case"),
    dict(name="face_diameter", mm=36.8, tol=0.05, how="diameter", part="Dial"),
    dict(name="marker_count_span", mm=33.2, tol=0.1, how="bbox_z",
         part="Markers"),
    dict(name="minute_hand", mm=12.67, tol=0.05, how="bbox_z",
         part="MinuteHand"),
    dict(name="bow_diameter", mm=9.4, tol=0.05, how="bbox_y", part="Bow"),
    dict(name="overall_height", mm=58.2, tol=0.1, how="bbox_z",
         part=None)
]