"""
handheld_console -- 160 x 90 x 28 mm portable console with a real D-pad.

The recognisable features of a handheld are the control layout, not the box:
a cross-shaped D-pad (two bars unioned, not four loose pads), two round action
buttons offset from each other the way they always are, a start/select pair
between the pad and the screen, and a speaker grille. The screen is recessed
0.5 mm inside its bezel so the bezel reads as holding it.

The D-pad's cross is a boolean UNION of two rounded bars that cross at the
centre, which is a well-behaved solid-solid cut; the offset between the two
action buttons is the real ergonomic one, 13 mm either side of centre.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 160.0, 90.0, 28.0
CORNER_R = 9.0
BEZEL_W, BEZEL_H, BEZEL_T = 84.0, 56.0, 4.0
SCR_W, SCR_H, SCR_T = 76.0, 48.0, 2.0
DPAD_ARM_L, DPAD_ARM_W, DPAD_T = 26.0, 8.0, 5.0
BTN_D, BTN_T = 11.0, 4.0
BTN_PITCH = 26.0
SHOULDER_W, SHOULDER_D, SHOULDER_H = 42.0, 12.0, 9.0
SPEAKER_COLS, SPEAKER_ROWS = 7, 2
SPEAKER_PITCH = 3.4
SPEAKER_R = 1.0

SPEC = dict(length=W, width=D, height=H,
            bezel_width=BEZEL_W,
            screen_width=SCR_W,
            dpad_arm_length=DPAD_ARM_L,
            button_diameter=BTN_D,
            button_pitch=BTN_PITCH,
            speaker_holes=SPEAKER_COLS * SPEAKER_ROWS)


def build():
    shell = bkit.pbr("HandheldShell", base=(0.14, 0.15, 0.18), metal=0.0, rough=0.38)
    screen = bkit.pbr("HandheldScreen", base=(0.04, 0.05, 0.07), metal=0.0, rough=0.08,
                      coat=0.8)
    pad = bkit.pbr("DpadRubber", base=(0.08, 0.08, 0.09), metal=0.0, rough=0.62)
    face = bkit.pbr("ActionButton", base=(0.72, 0.16, 0.13), metal=0.0, rough=0.28)
    small = bkit.pbr("SmallButton", base=(0.55, 0.56, 0.58), metal=0.0, rough=0.34)

    # ---- body ---------------------------------------------------------------
    body = bkit.rounded_box("Body", W, D, H, r=CORNER_R, segments=5,
                            centre=(0.0, 0.0, H / 2.0), mat=shell)

    # ---- screen in its bezel: a raised pad with a real window cut in it ----
    # A solid bezel with the screen inside it buries the screen; the bezel is a
    # frame, so the window is cut with an oversized cutter and the glass drops
    # in 1 mm below the bezel's top face.
    bezel = bkit.rounded_box("ScreenBezel", BEZEL_W, BEZEL_H, BEZEL_T + 1.0, r=2.5,
                             segments=3, centre=(-20.0, 0.0, H - (BEZEL_T + 1.0) / 2.0 + 1.5),
                             mat=shell)
    hole = bkit.rounded_box("_win", SCR_W + 2.0, SCR_H + 2.0, 3.0 * BEZEL_T, r=2.0,
                            segments=2,
                            centre=(-20.0, 0.0, H - (BEZEL_T + 1.0) / 2.0 + 1.5))
    bkit.boolean(bezel, hole, "DIFFERENCE")
    glass = bkit.rounded_box("Screen", SCR_W, SCR_H, SCR_T, r=1.5, segments=2,
                             centre=(-20.0, 0.0, H - 1.0), mat=screen)

    # ---- D-pad: two bars unioned into one cross ----------------------------
    dpad = bkit.rounded_box("DPad", DPAD_ARM_L, DPAD_ARM_W, DPAD_T, r=1.8,
                            segments=3, centre=(52.0, 0.0, H - 1.0), mat=pad)
    vert = bkit.rounded_box("_dpad_v", DPAD_ARM_W, DPAD_ARM_L, DPAD_T, r=1.8,
                            segments=3, centre=(52.0, 0.0, H - 1.0))
    bkit.boolean(dpad, vert, "UNION")

    # ---- two action buttons on the real 26 mm pitch ------------------------
    buttons = []
    for sy in (-1.0, 1.0):
        buttons.append(bkit.cylinder("ActionButtons", BTN_D / 2.0, BTN_T,
                                     segments=28,
                                     centre=(52.0, sy * BTN_PITCH / 2.0,
                                             H - 0.5), mat=face))
    bkit.join(buttons, name="ActionButtons")

    # ---- start / select pair ------------------------------------------------
    startsel = []
    for sy in (-1.0, 1.0):
        startsel.append(bkit.rounded_box("StartSelect", 9.0, 4.0, 3.0, r=1.2,
                                         segments=2,
                                         centre=(30.0, sy * 7.0, H - 0.5),
                                         mat=small))
    bkit.join(startsel, name="StartSelect")

    # ---- shoulder triggers ---------------------------------------------------
    shoulders = []
    for sy in (-1.0, 1.0):
        shoulders.append(bkit.rounded_box("Shoulders", SHOULDER_W, SHOULDER_D,
                                          SHOULDER_H, r=3.0, segments=3,
                                          centre=(-18.0, sy * (D / 2.0 - SHOULDER_D / 2.0),
                                                  H - 1.0), mat=shell))
    bkit.join(shoulders, name="Shoulders")

    # ---- speaker grille -------------------------------------------------------
    # the grille stands 0.5 mm proud of the shell; set flush it is inside the
    # body and does not appear at all
    speaker = bkit.perforated_panel("Speaker", SPEAKER_COLS, SPEAKER_ROWS,
                                    SPEAKER_PITCH, SPEAKER_PITCH, SPEAKER_R,
                                    SPEAKER_COLS * SPEAKER_PITCH,
                                    SPEAKER_ROWS * SPEAKER_PITCH, 1.6, mat=pad)
    bkit.move(speaker, -20.0, -32.0, H + 0.5)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="length", mm=160.0, tol=0.1, how="bbox_x", part="Body"),
    dict(name="width", mm=90.0, tol=0.1, how="bbox_y", part="Body"),
    dict(name="height", mm=28.0, tol=0.1, how="bbox_z", part="Body"),
    dict(name="screen_width", mm=76.0, tol=0.1, how="bbox_x", part="Screen"),
    dict(name="dpad_arm", mm=26.0, tol=0.1, how="bbox_x", part="DPad"),
    # the two buttons sit on a 26 mm pitch, so `diameter` (the larger of the two
    # spans) reports the 37 mm pair -- the button's own size is its X extent
    dict(name="button_diameter", mm=11.0, tol=0.05, how="bbox_x",
         part="ActionButtons")
]