"""
atomic_clock -- 56 mm radio-controlled travel alarm clock.

Built at 56 mm on purpose. The catalogue class for this item is tiny, whose
band tops out at 60 mm, and a radio-controlled clock at that size is a real
product -- the travel / bedside radio alarm. Every dimension below is that
clock's, not a 140 mm bedside unit shrunk to fit. The full-size one already
exists in this domain as alarm_clock.

The radio module is the part that says "radio-controlled": a translucent
window on the back with a printed aerial pattern behind it, plus the ferrite
rod aerial standing proud of the case at the back. The dial, the twelve
markers and the three hands are the same construction as the bedside clock's,
at this clock's own face size.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py. At a 30 mm bounding
# radius the harness parks the camera ~70 mm out, inside the 0.1 m default
# near plane, so the model would render as an empty backdrop.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

BODY_W, BODY_D, BODY_H = 56.0, 26.0, 52.0
FOOT_H = 4.0
CORNER_R = 5.0
FACE_R = 18.0
MARK_N = 12
MARK_W, MARK_L, MARK_T = 1.8, 4.0, 1.4
HOUR_L, MIN_L, ALARM_L = 8.0, 12.0, 10.5
AERIAL_R, AERIAL_L = 2.2, 22.0
WINDOW_W, WINDOW_H = 26.0, 14.0
BTN_R = 3.0
BTN_N = 2
BTN_PITCH = 12.0

HOUR, MINUTE, ALARM = 6, 42, 7 * 60 + 0

SPEC = dict(width=BODY_W, depth=BODY_D, body_height=BODY_H,
            face_diameter=2.0 * FACE_R, marker_count=MARK_N,
            aerial_length=AERIAL_L, aerial_diameter=2.0 * AERIAL_R,
            button_diameter=2.0 * BTN_R, button_pitch=BTN_PITCH,
            overall_height=BODY_H + FOOT_H)


def _angle(minutes):
    return 90.0 - (minutes / 60.0) * 30.0 - (minutes % 60.0) * 0.5


def build():
    case_mat = bkit.pbr("RadioCase", base=(0.13, 0.14, 0.16), metal=0.0, rough=0.34,
                        coat=0.4)
    dial_mat = bkit.pbr("RadioDial", base=(0.94, 0.92, 0.86), metal=0.0, rough=0.22)
    hand_mat = bkit.pbr("RadioHands", base=(0.92, 0.90, 0.84), metal=0.0, rough=0.26)
    alarm_mat = bkit.pbr("RadioAlarmHand", base=(0.74, 0.10, 0.09), metal=0.0,
                         rough=0.26)
    steel = bkit.pbr("RadioSteel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.20)
    lens_mat = bkit.pbr("RadioWindow", base=(0.70, 0.74, 0.78), metal=0.0, rough=0.14,
                        transmission=0.4, ior=1.5)

    cz = FOOT_H + BODY_H / 2.0
    body = bkit.rounded_box("Body", BODY_W, BODY_D, BODY_H, r=CORNER_R, segments=4,
                            centre=(0.0, 0.0, cz), mat=case_mat)

    # ---- the dial and its twelve markers, swept about the dial centre ------
    face_y = -BODY_D / 2.0 + 1.0
    dial = bkit.cylinder("Dial", FACE_R, 2.0, segments=56, axis="Y",
                         centre=(0.0, face_y + 1.0, cz), mat=dial_mat)
    mark = bkit.rounded_box("Markers", MARK_W, MARK_T, MARK_L, r=0.6, segments=2,
                            centre=(0.0, face_y + 0.4, cz + FACE_R - 3.6),
                            mat=hand_mat)
    bkit.array_radial(mark, MARK_N, axis="Y", centre=(0.0, 0.0, cz))

    # ---- three hands at three times ----------------------------------------
    for (name, minutes, length, width, mat, yoff) in (
            ("HourHand", HOUR * 60 + MINUTE, HOUR_L, 1.5, hand_mat, -0.6),
            ("MinuteHand", MINUTE, MIN_L, 1.1, hand_mat, 0.2),
            ("AlarmHand", ALARM, ALARM_L, 0.9, alarm_mat, 0.9)):
        h = bkit.rounded_box(name, width, 1.0, length, r=0.4, segments=2,
                             centre=(0.0, 0.0, length / 2.0 - 1.6), mat=mat)
        h.rotation_euler = (math.radians(_angle(minutes)), 0.0, 0.0)
        bkit.move(h, 0.0, face_y + yoff, cz)
    bkit.cylinder("HandHub", 1.4, 3.0, segments=14, axis="Y",
                  centre=(0.0, face_y + 0.4, cz), mat=steel)

    # ---- the ferrite rod aerial and the radio window on the back -----------
    aerial = bkit.cylinder("Aerial", AERIAL_R, AERIAL_L, segments=16,
                           centre=(0.0, BODY_D / 2.0 - AERIAL_L / 2.0 + 2.0,
                                   cz + 6.0), axis="Y", mat=steel)
    window = bkit.rounded_box("RadioWindow", WINDOW_W, 3.0, WINDOW_H, r=2.0,
                              segments=2,
                              centre=(0.0, BODY_D / 2.0 - 0.5, cz - 10.0),
                              mat=lens_mat)

    # ---- two set buttons on a measured pitch, and two feet -----------------
    btns = []
    for (x, w) in bkit.lay_out([2.0 * BTN_R] * BTN_N, gap=BTN_PITCH - 2.0 * BTN_R):
        btns.append(bkit.cylinder("SetButtons", BTN_R, 3.0, segments=16,
                                  centre=(x, 0.0, FOOT_H + 2.0), mat=steel))
    bkit.join(btns, name="SetButtons")
    feet = []
    for sx in (-1.0, 1.0):
        feet.append(bkit.rounded_box("Feet", 9.0, BODY_D + 2.0, FOOT_H, r=1.5,
                                     segments=2,
                                     centre=(sx * 18.0, 0.0, FOOT_H / 2.0),
                                     mat=case_mat))
    bkit.join(feet, name="Feet")

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="body_width", mm=56.0, tol=0.1, how="bbox_x", part="Body"),
    dict(name="body_height", mm=52.0, tol=0.1, how="bbox_z", part="Body"),
    dict(name="face_diameter", mm=36.0, tol=0.1, how="diameter", part="Dial"),
    dict(name="aerial_length", mm=22.0, tol=0.1, how="bbox_y", part="Aerial"),
    dict(name="button_span", mm=18, tol=0.1, how="bbox_x",
         part="SetButtons"),
    dict(name="overall_height", mm=56.0, tol=0.1, how="bbox_z", part=None)
]