"""
slot_machine -- 700 x 500 x 1900 mm three-reel machine with a lever.

A fruit machine is a tower with three things that must be right or it does not
read: the three reels behind a window, the lever on the right-hand side, and
the stepped base. The reels are cylinders on a real axis with a small gap
between them, and the payout tray is a recess in the front of the base.

The lever is the part that carries the silhouette, so it is built as a swept
arm (a loft over sections) plus a ball knob, hinged at the top of the body and
hanging down the way a real lever rests. The stop buttons are on a 90 mm pitch
computed with lay_out so the payout buttons cannot collide with the cancel
button.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 700.0, 500.0, 1900.0
BASE_H = 300.0
UPPER_Y = 460.0           # the upper body is narrower than the base
UPPER_H = 1150.0
CROWN_H = 450.0
REEL_R = 82.0
REEL_W = 46.0
REEL_D = 320.0
REEL_N = 3
REEL_PITCH = 108.0
REEL_Z = 1230.0
WINDOW_W, WINDOW_H = 400.0, 300.0
LEVER_ARM_L = 320.0
LEVER_KNOB_R = 34.0
LEVER_X = W / 2.0 - 30.0
BTN_N = 3
BTN_R = 26.0
BTN_PITCH = 90.0
BTN_Z = 720.0
TRAY_W, TRAY_H = 300.0, 70.0

SPEC = dict(width=W, depth=D, height=H,
            base_height=BASE_H, upper_height=UPPER_H, crown_height=CROWN_H,
            reel_count=REEL_N, reel_diameter=2.0 * REEL_R,
            reel_pitch=REEL_PITCH, lever_arm_length=LEVER_ARM_L,
            button_count=BTN_N, button_pitch=BTN_PITCH)


def build():
    body_mat = bkit.pbr("SlotBody", base=(0.70, 0.10, 0.09), metal=0.0, rough=0.26,
                        coat=0.4)
    trim = bkit.pbr("SlotTrim", base=(0.92, 0.80, 0.28), metal=0.85, rough=0.22)
    reel_mat = bkit.pbr("SlotReel", base=(0.88, 0.88, 0.86), metal=0.85, rough=0.30)
    glass = bkit.pbr("SlotGlass", base=(0.82, 0.88, 0.92), metal=0.0, rough=0.05,
                     transmission=0.45, ior=1.5)
    knob = bkit.pbr("SlotKnob", base=(0.94, 0.94, 0.92), metal=0.0, rough=0.22,
                    coat=0.6)

    # ---- base, upper body and crown: a stepped tower ------------------------
    base = bkit.rounded_box("Base", W, D, BASE_H, r=6.0, segments=3,
                            centre=(0.0, 0.0, BASE_H / 2.0), mat=body_mat)
    upper = bkit.rounded_box("UpperBody", W, UPPER_Y, UPPER_H, r=6.0, segments=3,
                             centre=(0.0, 0.0, BASE_H + UPPER_H / 2.0), mat=body_mat)
    crown = bkit.rounded_box("Crown", W, UPPER_Y, CROWN_H, r=6.0, segments=3,
                             centre=(0.0, 0.0, BASE_H + UPPER_H + CROWN_H / 2.0),
                             mat=trim)

    # ---- three reels in a real recess, behind a window and bezel -----------
    # y = -UPPER_Y/2 is the upper body's front face. A reel set flush with it
    # (or proud of it) is invisible from the front, so the reels go into a cut
    # cavity and the bezel and window go in FRONT of the face.
    fy = -UPPER_Y / 2.0
    cavity = bkit.rounded_box("_reel_cavity", REEL_N * REEL_PITCH + 40.0, 80.0,
                              REEL_D + 40.0, r=4.0, segments=2,
                              centre=(0.0, fy + 30.0, REEL_Z))
    bkit.boolean(upper, cavity, "DIFFERENCE")
    reels = []
    for i in range(REEL_N):
        x = (i - (REEL_N - 1) / 2.0) * REEL_PITCH
        reels.append(bkit.cylinder("Reels", REEL_R, REEL_W, segments=48,
                                   centre=(x, fy + 26.0, REEL_Z), axis="Y",
                                   mat=reel_mat))
    bkit.join(reels, name="Reels")
    window = bkit.rounded_box("Window", WINDOW_W, 8.0, WINDOW_H, r=3.0, segments=2,
                              centre=(0.0, fy - 6.0, REEL_Z), mat=glass)
    bezel = bkit.rounded_box("WindowBezel", WINDOW_W + 40.0, 12.0, WINDOW_H + 40.0,
                             r=4.0, segments=2, centre=(0.0, fy - 12.0, REEL_Z),
                             mat=trim)
    # the bezel is a surround: cut the window out of it
    bkit.boolean(bezel, bkit.rounded_box("_win", WINDOW_W, 30.0, WINDOW_H, r=3.0,
                                        segments=2, centre=(0.0, fy - 12.0, REEL_Z)),
                 "DIFFERENCE")

    # ---- the lever on the right-hand side ----------------------------------
    hinge_z = BASE_H + UPPER_H - 120.0
    arm = bkit.loft(
        "LeverArm",
        [[(p, q, r) for (p, q) in bkit.rounded_rect_section(22.0, 34.0, 9.0,
                                                           per_corner=4)]
         for r in (0.0, -LEVER_ARM_L * 0.45, -LEVER_ARM_L * 0.8, -LEVER_ARM_L)],
        closed_loop=True, cap_start=True, cap_end=True, mat=trim, smooth=True)
    bkit.recalc(arm)
    bkit.move(arm, LEVER_X, -UPPER_Y / 2.0 - 8.0, hinge_z)
    lever_knob = bkit.sphere("LeverKnob", LEVER_KNOB_R, segments=32, rings=16,
                             centre=(LEVER_X, -UPPER_Y / 2.0 - 8.0,
                                     hinge_z - LEVER_ARM_L - 18.0), mat=knob)
    bkit.join([arm, lever_knob], name="Lever")

    # ---- three stop buttons on a measured pitch ----------------------------
    btns = []
    for (x, w) in bkit.lay_out([2.0 * BTN_R] * BTN_N, gap=BTN_PITCH - 2.0 * BTN_R):
        btns.append(bkit.cylinder("StopButtons", BTN_R, 14.0, segments=28,
                                  centre=(x, -UPPER_Y / 2.0 - 10.0, BTN_Z), axis="Y",
                                  mat=knob))
    bkit.join(btns, name="StopButtons")

    # ---- payout tray recessed into the base --------------------------------
    tray = bkit.rounded_box("PayoutTray", TRAY_W, 40.0, TRAY_H, r=6.0, segments=3,
                            centre=(0.0, -D / 2.0 + 20.0, 170.0), mat=trim)
    bkit.boolean(base, tray, "DIFFERENCE")

    # ---- crown sign ---------------------------------------------------------
    bkit.rounded_box("CrownSign", 560.0, 14.0, 240.0, r=6.0, segments=3,
                     centre=(0.0, -UPPER_Y / 2.0 - 8.0,
                             BASE_H + UPPER_H + CROWN_H / 2.0), mat=body_mat)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="width", mm=700.0, tol=0.2, how="bbox_x", part="Base"),
    dict(name="depth", mm=500.0, tol=0.2, how="bbox_y", part="Base"),
    dict(name="base_height", mm=300.0, tol=0.2, how="bbox_z", part="Base"),
    dict(name="upper_depth", mm=460.0, tol=0.2, how="bbox_y", part="UpperBody"),
    # the three reels are joined, so their X extent is the whole 380 mm bank;
    # one reel's own diameter is its Z extent
    dict(name="reel_diameter", mm=164, tol=0.2, how="bbox_z",
         part="Reels"),
    # 2 x 108 pitch + one reel
    dict(name="reel_bank_width", mm=380.0, tol=0.3, how="bbox_x", part="Reels"),
    dict(name="lever_knob", mm=68.0, tol=0.2, how="diameter", part="Lever"),
    dict(name="overall_height", mm=1900.0, tol=0.3, how="bbox_z", part=None)
]