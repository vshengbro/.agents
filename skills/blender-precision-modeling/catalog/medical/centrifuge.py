"""
centrifuge -- 260 x 230 x 200 mm benchtop microcentrifuge: a moulded body, a
lid with a real inspection window over a rotor, a control panel with a display,
two buttons and a dial, and four feet.

The panel furniture is laid out with `lay_out`/`grid_positions` so the display,
the buttons and the dial cannot land on the same coordinate. The rotor sits
inside the lid cavity instead of inside the body -- the body is a solid, so a
rotor modelled at its "natural" height would be invisible from every angle.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_size=260.0,
    depth=230.0,
    overall_height=200.0,
    window_diameter=120.0,
    rotor_diameter=140.0,
)

W = SPEC["body_size"]
D = SPEC["depth"]
FOOT_H = 14.0
BODY_H = 146.0
LID_H = 40.0
BODY_TOP = FOOT_H + BODY_H          # 160.0
WIN_R = SPEC["window_diameter"] / 2.0
LID_R = WIN_R + 22.0
CAVITY_Z = BODY_TOP + 4.0           # floor of the lid cavity
PANEL_Y = -D / 2.0 - 3.0


def build():
    shell = bkit.pbr("CentrifugeShell", base=(0.87, 0.87, 0.86), rough=0.36)
    dark = bkit.pbr("CentrifugeDark", base=(0.13, 0.13, 0.14), rough=0.40)
    steel = bkit.pbr("CentrifugeSteel", base=(0.78, 0.80, 0.83), metal=0.80,
                     rough=0.22)
    window = bkit.pbr("CentrifugeWindow", base=(0.72, 0.80, 0.84), rough=0.05,
                      transmission=0.70, ior=1.52, coat=0.6)
    screen = bkit.pbr("CentrifugeScreen", base=(0.10, 0.22, 0.18), rough=0.20,
                      emission=(0.30, 0.70, 0.55), emission_strength=0.6)

    # ---- feet first, so the body lands on them ----------------------------
    feet = [bkit.cylinder("_foot", 11.0, FOOT_H, segments=24,
                          centre=(fx, fy, FOOT_H / 2.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, W - 34.0, D - 34.0)]
    bkit.join(feet, name="CentrifugeFeet")

    bkit.rounded_box("CentrifugeBody", W, D, BODY_H, r=16.0, segments=4,
                     centre=(0, 0, FOOT_H + BODY_H / 2.0), mat=shell)

    # ---- lid: a stepped dome with a real recess and window bore ------------
    bkit.lathe("CentrifugeLid", [
        (0.0, BODY_TOP - 18.0),                 # skirt, buried in the body
        (LID_R - 10.0, BODY_TOP - 18.0),
        (LID_R, BODY_TOP + 4.0),
        (LID_R, BODY_TOP + LID_H - 7.0),
        (LID_R - 9.0, BODY_TOP + LID_H),
        (WIN_R + 9.0, BODY_TOP + LID_H),
        (WIN_R + 9.0, BODY_TOP + LID_H - 5.0),
        (WIN_R, BODY_TOP + LID_H - 5.0),
        (WIN_R, CAVITY_Z),                      # window bore wall
        (0.0, CAVITY_Z),                        # cavity floor
    ], segments=128, mat=shell)
    bkit.tube("CentrifugeWindow", WIN_R - 0.6, WIN_R - 3.6, 4.0, segments=64,
              centre=(0.0, 0.0, BODY_TOP + LID_H - 3.0), mat=window)

    # ---- rotor, standing in the cavity so it is actually visible ----------
    bkit.cylinder("CentrifugeRotor", SPEC["rotor_diameter"] / 2.0, 32.0,
                  segments=64, centre=(0.0, 0.0, CAVITY_Z + 8.0), mat=dark)
    bkit.tube("RotorBore", 34.0, 29.0, 24.0, segments=48,
              centre=(0.0, 0.0, CAVITY_Z + 12.0), mat=steel)

    # ---- control panel -----------------------------------------------------
    bkit.rounded_box("ControlPanel", 200.0, 10.0, 54.0, r=4.0, segments=3,
                     centre=(-30.0, PANEL_Y, FOOT_H + 52.0), mat=dark)
    bkit.rounded_box("PanelDisplay", 84.0, 6.0, 34.0, r=2.0, segments=2,
                     centre=(-70.0, PANEL_Y - 4.0, FOOT_H + 52.0), mat=screen)
    for (bx, bw) in bkit.lay_out([22.0, 22.0], gap=12.0):
        bkit.rounded_box("PanelButton", bw, 8.0, 22.0, r=3.0, segments=2,
                         centre=(8.0 + bx, PANEL_Y - 4.0, FOOT_H + 52.0),
                         mat=steel)
    bkit.cylinder("PanelDial", 15.0, 14.0, segments=32,
                  centre=(52.0, PANEL_Y - 3.0, FOOT_H + 52.0), axis="Y",
                  mat=steel)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="body_size", mm=260.0, tol=0.5, how="bbox_x",
         part="CentrifugeBody"),
    dict(name="depth", mm=230.0, tol=0.5, how="bbox_y", part="CentrifugeBody"),
    dict(name="overall_height", mm=200.0, tol=1.0, how="bbox_z"),
]