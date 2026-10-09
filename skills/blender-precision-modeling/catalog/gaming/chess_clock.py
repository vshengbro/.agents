"""
chess_clock -- 200 x 100 x 105 mm double-dial clock with a carry handle.

A chess clock is two dials side by side under one handle, and the dials are
what make it a chess clock -- so each dial gets a full bezel, a printed face
with twelve hour marks, and a hand. The two clocks run in opposite directions,
so the right-hand hand is set to 1:45 and the left-hand hand to 10:15 rather
than both to the same time, which is what makes it read as a chess clock and
not a pair of clocks.

The twelve marks on each face come from array_radial about that face's own
centre, and the handle is an arc_torus -- a bent tube, not a bent box.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 200.0, 100.0, 105.0
CORNER_R = 8.0
DIAL_R = 38.0
DIAL_PITCH = 96.0          # centre-to-centre of the two dials
DIAL_Z = 54.0
FACE_R = 32.0
MARK_L, MARK_W, MARK_T = 5.0, 2.4, 1.2
HAND_L, HAND_W, HAND_T = 26.0, 2.2, 1.4
HANDLE_R = 70.0
HANDLE_W = 7.0
HANDLE_T = 9.0
BTN_D = 16.0
BTN_PITCH = 34.0
BTN_Y = 30.0

# the two clocks, in minutes past 12: left 10:15, right 1:45
LEFT_MIN, RIGHT_MIN = 615.0, 105.0

SPEC = dict(width=W, depth=D, body_height=H,
            dial_diameter=2.0 * FACE_R, dial_pitch=DIAL_PITCH,
            hour_marks=12, handle_radius=HANDLE_R,
            button_diameter=BTN_D, button_pitch=BTN_PITCH)


def _hand_angle(minutes):
    """Clock-face angle in degrees, measured CCW from +X, for a time."""
    return 90.0 - (minutes / 60.0) * 30.0 - (minutes % 60.0) * 0.5


def build():
    case = bkit.pbr("ClockCase", base=(0.10, 0.11, 0.13), metal=0.0, rough=0.30,
                    coat=0.5)
    bezel = bkit.pbr("ClockBezel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.20)
    face = bkit.pbr("ClockFace", base=(0.93, 0.92, 0.88), metal=0.0, rough=0.38)
    hand = bkit.pbr("ClockHand", base=(0.06, 0.06, 0.07), metal=0.0, rough=0.30)
    btn = bkit.pbr("ClockButton", base=(0.66, 0.20, 0.14), metal=0.0, rough=0.30)

    # ---- body and the two dial wells ---------------------------------------
    body = bkit.rounded_box("Body", W, D, H - 14.0, r=CORNER_R, segments=4,
                            centre=(0.0, 0.0, (H - 14.0) / 2.0), mat=case)
    foot = bkit.rounded_box("Foot", W - 20.0, D - 20.0, 14.0, r=4.0, segments=3,
                            centre=(0.0, 0.0, 7.0), mat=case)

    # ---- the two dials -------------------------------------------------------
    # Every dial part is a lathe about Z and is then laid on its side, so the
    # case axis is Y. Lathing a bezel about Z and never rotating it leaves a
    # ring lying flat inside the case, which is the bug this construction
    # exists to prevent.
    faces, bezels, hands, marks = [], [], [], []
    for (sx, minutes) in ((-1.0, LEFT_MIN), (1.0, RIGHT_MIN)):
        cx = sx * DIAL_PITCH / 2.0
        f = bkit.lathe(
            "ClockFace",
            [(0.0, DIAL_Z - 2.0), (FACE_R, DIAL_Z - 2.0), (FACE_R, DIAL_Z + 1.0),
             (0.0, DIAL_Z + 1.0)],
            segments=64, centre=(cx, 0.0, 0.0), mat=face)
        f.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        faces.append(f)

        b = bkit.lathe(
            "ClockBezel",
            [(FACE_R - 2.0, DIAL_Z + 1.0), (DIAL_R, DIAL_Z + 1.0),
             (DIAL_R, DIAL_Z + 5.0), (FACE_R - 4.0, DIAL_Z + 6.5),
             (FACE_R - 2.0, DIAL_Z + 4.0)],
            segments=64, centre=(cx, 0.0, 0.0), mat=bezel)
        b.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        bezels.append(b)

        # the twelve marks are swept about THIS dial's own centre
        mark = bkit.rounded_box("HourMarks", MARK_W, MARK_T, MARK_L, r=0.8,
                                segments=2,
                                centre=(cx, -3.0, FACE_R - MARK_L / 2.0 - 3.0),
                                mat=hand)
        bkit.array_radial(mark, 12, axis="Y", centre=(cx, 0.0, 0.0))

        h = bkit.rounded_box("ClockHand", HAND_L, HAND_T, HAND_W, r=0.8, segments=2,
                             centre=(HAND_L / 2.0, 0.0, 0.0), mat=hand)
        h.rotation_euler = (0.0, math.radians(_hand_angle(minutes)), 0.0)
        bkit.move(h, cx, -5.5, 0.0)
        hands.append(h)
    faces[0].name = "ClockFaceL"
    faces[1].name = "ClockFaceR"
    bezels[0].name = "ClockBezelL"
    bezels[1].name = "ClockBezelR"
    bkit.join(hands, name="ClockHands")

    # ---- carry handle --------------------------------------------------------
    # plane="XZ" so the handle arches over the top of the case. plane="XY" would
    # lay the same arc flat, level with the dial, where it reads as a hoop
    # around the clock rather than a handle on it.
    handle = bkit.arc_torus("Handle", HANDLE_R, HANDLE_W / 2.0, 0.0, 180.0,
                            plane="XZ", seg_major=64, seg_minor=16,
                            centre=(0.0, 0.0, H - 8.0), mat=bezel, caps=True)
    grip = bkit.rounded_box("HandleGrip", HANDLE_W + 8.0, 46.0, HANDLE_T, r=3.0,
                            segments=3, centre=(0.0, 0.0, H - 8.0 + HANDLE_R),
                            mat=case)
    bkit.join([handle, grip], name="Handle")

    # ---- two buttons on a measured pitch -------------------------------------
    buttons = []
    for (x, w) in bkit.lay_out([BTN_D] * 2, gap=BTN_PITCH - BTN_D):
        buttons.append(bkit.cylinder("Buttons", BTN_D / 2.0, 8.0, segments=28,
                                     centre=(x, BTN_Y, H - 14.0 + 2.0), mat=btn))
    bkit.join(buttons, name="Buttons")

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="width", mm=200.0, tol=0.2, how="bbox_x", part="Body"),
    dict(name="body_height", mm=91.0, tol=0.2, how="bbox_z", part="Body"),
    # 96 mm centre distance + one bezel radius each side
    dict(name="dial_span", mm=76, tol=0.2, how="bbox_x",
         part="ClockBezelL"),
    dict(name="dial_diameter", mm=64.0, tol=0.2, how="diameter", part="ClockFaceL"),
    # 2 * 70 + 2 * 3.5: the handle arc's full width
    dict(name="handle_diameter", mm=147.0, tol=0.2, how="bbox_x", part="Handle"),
    # 91 (body) + 73.5 (handle rise above its own centre) + 6 (grip)
    dict(name="overall_height", mm=209.5, tol=0.4, how="bbox_z",
         part=None),
]