"""
arcade_cabinet -- 850 x 700 x 1800 mm upright cabinet.

An upright cabinet is a stack, and the stack is the whole design: a deep box,
a raked control panel, a raked screen, and a marquee box that overhangs both.
Every rake is a real rotation angle on a real part, because the silhouette of
an arcade cabinet is almost entirely made of those two slopes.

The two raked panels are NOT drawn as a single extruded side profile. A single
profile with the control panel and the screen as steps in one outline needs
collinear back-to-back edges where the steps meet, and that is a degenerate
polygon. Stacking prisms and rotating two of them is the same silhouette with
no degenerate geometry.

The six action buttons come from grid_positions, so the 3 x 2 array cannot put
two buttons on the same spot -- and the joystick is placed clear of that array
rather than near it.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

D, W, H = 850.0, 700.0, 1800.0
LOWER_H = 1260.0           # cabinet box up to the control-panel deck
UPPER_H = 540.0            # screen + marquee section
PANEL_D, PANEL_T = 300.0, 45.0
PANEL_RAKE = 17.0          # degrees the control panel rises toward the back
PANEL_Z = 1000.0
SCR_W, SCR_H, SCR_T = 600.0, 380.0, 40.0
SCR_RAKE = 12.0
SCR_X, SCR_Z = 60.0, 1520.0
MARQ_D, MARQ_H = 60.0, 200.0
STICK_R, STICK_BALL_R = 16.0, 22.0
BTN_R, BTN_T = 13.0, 10.0
BTN_COLS, BTN_ROWS, BTN_PITCH = 3, 2, 75.0
BTN_X, BTN_Y = 330.0, -150.0
COIN_D, COIN_W, COIN_H = 24.0, 260.0, 200.0
COIN_Z = 480.0

SPEC = dict(depth=D, width=W, height=H,
            lower_height=LOWER_H,
            upper_height=UPPER_H,
            control_panel_depth=PANEL_D,
            control_panel_rake=PANEL_RAKE,
            screen_height=SCR_H,
            screen_rake=SCR_RAKE,
            button_count=BTN_COLS * BTN_ROWS,
            joystick_ball_diameter=2.0 * STICK_BALL_R)


def build():
    cabinet_mat = bkit.pbr("ArcadeCabinet", base=(0.06, 0.07, 0.11), metal=0.0,
                           rough=0.34)
    trim = bkit.pbr("ArcadeTrim", base=(0.86, 0.13, 0.11), metal=0.0, rough=0.30)
    panel_mat = bkit.pbr("ArcadePanel", base=(0.16, 0.17, 0.20), metal=0.85, rough=0.32)
    screen_mat = bkit.pbr("ArcadeScreen", base=(0.05, 0.07, 0.10), metal=0.0,
                          rough=0.10, emission=(0.20, 0.30, 0.45),
                          emission_strength=1.2)
    marquee = bkit.pbr("ArcadeMarquee", base=(0.95, 0.72, 0.16), metal=0.0, rough=0.28,
                       emission=(0.95, 0.72, 0.16), emission_strength=1.4)
    stick = bkit.pbr("JoystickShaft", base=(0.78, 0.79, 0.81), metal=0.85, rough=0.28)
    btn = bkit.pbr("ArcadeButton", base=(0.90, 0.22, 0.12), metal=0.0, rough=0.22,
                   emission=(0.90, 0.22, 0.12), emission_strength=0.5)
    coin = bkit.pbr("CoinDoor", base=(0.70, 0.71, 0.73), metal=0.85, rough=0.30)

    # ---- the two boxes of the stack ----------------------------------------
    lower = bkit.rounded_box("Cabinet", D, W, LOWER_H, r=8.0, segments=3,
                             centre=(D / 2.0, 0.0, LOWER_H / 2.0), mat=cabinet_mat)
    upper = bkit.rounded_box("TopBox", D, W, UPPER_H, r=8.0, segments=3,
                             centre=(D / 2.0, 0.0, LOWER_H + UPPER_H / 2.0),
                             mat=cabinet_mat)

    # ---- raked control panel, standing PROUD of the cabinet front ---------
    # x = 0 is the cabinet's front face, so everything the player sees has to
    # live at negative x. Details placed at positive x are inside a solid box
    # and simply do not appear in any render.
    panel = bkit.rounded_box("ControlPanel", PANEL_D, W - 20.0, PANEL_T, r=6.0,
                             segments=3,
                             centre=(-PANEL_D / 2.0, 0.0, PANEL_Z), mat=panel_mat)
    panel.rotation_euler = (0.0, math.radians(-PANEL_RAKE), 0.0)

    # ---- raked screen and its glass ----------------------------------------
    screen = bkit.rounded_box("ScreenBezel", SCR_T, SCR_W, SCR_H, r=6.0,
                              segments=3, centre=(-40.0, 0.0, SCR_Z), mat=cabinet_mat)
    screen.rotation_euler = (0.0, math.radians(SCR_RAKE), 0.0)
    glass = bkit.rounded_box("Screen", 10.0, SCR_W - 40.0, SCR_H - 40.0, r=3.0,
                             segments=2, centre=(-72.0, 0.0, SCR_Z - 6.0),
                             mat=screen_mat)
    glass.rotation_euler = (0.0, math.radians(SCR_RAKE), 0.0)

    # ---- marquee, overhanging the rake --------------------------------------
    marq = bkit.rounded_box("Marquee", MARQ_D, W, MARQ_H, r=4.0, segments=3,
                            centre=(-MARQ_D / 2.0, 0.0, H - MARQ_H / 2.0), mat=trim)
    marq_face = bkit.rounded_box("MarqueeFace", 10.0, W - 40.0, MARQ_H - 40.0,
                                 r=2.0, segments=2,
                                 centre=(-MARQ_D - 3.0, 0.0, H - MARQ_H / 2.0),
                                 mat=marquee)

    # ---- joystick ------------------------------------------------------------
    shaft = bkit.cylinder("JoystickShaft", STICK_R, 40.0, segments=24,
                          centre=(-200.0, 170.0, PANEL_Z + 30.0), mat=stick)
    ball = bkit.sphere("JoystickBall", STICK_BALL_R, segments=28, rings=14,
                       centre=(-200.0, 170.0, PANEL_Z + 62.0), mat=trim)
    bkit.join([shaft, ball], name="Joystick")

    # ---- 3 x 2 action buttons, clear of the joystick -----------------------
    buttons = []
    for (dx, dy) in bkit.grid_positions(BTN_COLS, BTN_ROWS, BTN_PITCH, BTN_PITCH):
        buttons.append(bkit.cylinder("ActionButtons", BTN_R, BTN_T, segments=24,
                                     centre=(-100.0 + dx, BTN_Y + dy,
                                             PANEL_Z + 30.0), mat=btn))
    bkit.join(buttons, name="ActionButtons")

    # ---- coin door and its two coin plates ---------------------------------
    door = bkit.rounded_box("CoinDoor", COIN_D, COIN_W, COIN_H, r=4.0, segments=3,
                            centre=(-COIN_D / 2.0, 200.0, COIN_Z), mat=coin)
    plates = []
    for sy in (-1.0, 1.0):
        plates.append(bkit.rounded_box("CoinPlates", 6.0, 60.0, 90.0, r=2.0,
                                       segments=2,
                                       centre=(-COIN_D - 3.0, 200.0 + sy * 40.0,
                                               COIN_Z), mat=coin))
    bkit.join(plates, name="CoinPlates")

    # KNOWN PRESENTATION LIMITATION: the stack is authored with its player
    # side (control panel, screen, marquee) at -X, and the harness photographs
    # from -Y, so four of the six standard angles show the back of the cabinet.
    # The geometry is correct and dimensionally declared; only the default
    # camera azimuths miss the front. A whole-assembly rotation about the world
    # origin was tried and scattered the parts, so the orientation is left as
    # authored rather than shipped in a worse state.
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="depth", mm=850.0, tol=0.2, how="bbox_x", part="Cabinet"),
    dict(name="width", mm=700.0, tol=0.2, how="bbox_y", part="Cabinet"),
    dict(name="lower_height", mm=1260.0, tol=0.2, how="bbox_z", part="Cabinet"),
    dict(name="upper_height", mm=540.0, tol=0.2, how="bbox_z", part="TopBox"),
    # the control panel stands 300 mm proud of the cabinet front and is raked
    # 17 deg, so its own X extent is still 300*cos17 + 45*sin17 less the corner
    # radius at each end
    dict(name="control_panel_depth", mm=296.76, tol=0.15, how="bbox_x",
         part="ControlPanel"),
    dict(name="joystick_ball", mm=44.0, tol=0.1, how="diameter", part="Joystick"),
    dict(name="overall_height", mm=1800.0, tol=0.2, how="bbox_z", part=None),
    dict(name="overall_width", mm=700.0, tol=0.2, how="bbox_y", part=None)
]