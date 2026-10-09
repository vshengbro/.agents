"""
defibrillator -- 380 x 280 x 210 mm portable defibrillator/monitor: a moulded
body, a bezel and screen, a battery block, a carry handle, a printer slot and
two shock paddles in their side cradles.

The paddles sit in cradles that overlap the body wall by 3 mm -- flush-mounted
paddles leave the two surfaces touching along an edge, which is one of the three
ways a boolean quietly produces a non-manifold mesh, and here it would also
show as a seam in the render.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    body_size=330.0,
    depth=280.0,
    overall_height=255.0,
    screen_size=200.0,
    paddle_diameter=110.0,
)

W, D = SPEC["body_size"], SPEC["depth"]
BODY_H = 150.0
FOOT_H = 16.0
BODY_TOP = FOOT_H + BODY_H
PAD_R = SPEC["paddle_diameter"] / 2.0


def build():
    shell = bkit.pbr("DefibShell", base=(0.90, 0.88, 0.82), rough=0.34)
    dark = bkit.pbr("DefibDark", base=(0.12, 0.12, 0.13), rough=0.42)
    screen_mat = bkit.pbr("DefibScreen", base=(0.06, 0.10, 0.12), rough=0.12,
                          emission=(0.20, 0.62, 0.48), emission_strength=0.9)
    paddle_mat = bkit.pbr("DefibPaddle", base=(0.20, 0.21, 0.23), rough=0.40)
    accent = bkit.pbr("DefibAccent", base=(0.78, 0.16, 0.12), rough=0.30)

    # ---- feet and body -----------------------------------------------------
    feet = [bkit.cylinder("_foot", 12.0, FOOT_H, segments=24,
                          centre=(fx, fy, FOOT_H / 2.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, W - 60.0, D - 50.0)]
    bkit.join(feet, name="DefibFeet")

    bkit.rounded_box("DefibBody", W, D, BODY_H, r=18.0, segments=4,
                     centre=(0, 0, FOOT_H + BODY_H / 2.0), mat=shell)

    # ---- screen, bezel and the four soft keys under it --------------------
    fy = -D / 2.0
    bkit.rounded_box("ScreenBezel", SPEC["screen_size"] + 16.0, 10.0, 136.0,
                     r=6.0, segments=3,
                     centre=(-42.0, fy - 3.0, FOOT_H + 82.0), mat=dark)
    bkit.rounded_box("DefibScreen", SPEC["screen_size"], 6.0, 116.0, r=3.0,
                     segments=2,
                     centre=(-42.0, fy - 7.0, FOOT_H + 82.0), mat=screen_mat)
    keys = [bkit.rounded_box("SoftKey", kw, 8.0, 16.0, r=3.0, segments=2,
                             centre=(-42.0 + kx, fy - 6.0, FOOT_H + 14.0),
                             mat=accent)
            for (kx, kw) in bkit.lay_out([34.0] * 4, gap=10.0)]
    bkit.join(keys, name="DefibKeys")

    # ---- carry handle: an arch over the top ------------------------------
    bkit.arc_torus("CarryHandle", 78.0, 9.0, 8.0, 172.0,
                   centre=(0.0, 0.0, BODY_TOP + 2.0), plane="XZ",
                   seg_major=40, mat=dark, caps=True)
    for sign in (-1.0, 1.0):
        bkit.rounded_box("HandleMount", 26.0, 40.0, 16.0, r=4.0, segments=3,
                         centre=(sign * 74.0, 0.0, BODY_TOP + 2.0), mat=dark)

    # ---- printer slot on the right cheek ---------------------------------
    bkit.rounded_box("PrinterSlot", 90.0, 14.0, 26.0, r=3.0, segments=2,
                     centre=(112.0, -D / 2.0 - 2.0, FOOT_H + 60.0), mat=dark)

    # ---- two shock paddles in side cradles -------------------------------
    for side, sign in (("L", -1.0), ("R", 1.0)):
        cx = sign * (W / 2.0 + 12.0)
        bkit.rounded_box("PaddleCradle" + side, 34.0, 150.0, 130.0, r=8.0,
                         segments=3,
                         centre=(sign * (W / 2.0 - 8.0), 0.0,
                                 FOOT_H + 74.0), mat=dark)
        # the paddle is a disc FACING OUTWARD: its axis runs along X, not Z
        paddle = bkit.lathe("Paddle" + side, [
            (0.0, 0.0), (PAD_R - 6.0, 0.0), (PAD_R, 5.0), (PAD_R, 20.0),
            (PAD_R - 5.0, 26.0), (PAD_R - 24.0, 26.0), (0.0, 26.0),
        ], segments=64, mat=paddle_mat)
        paddle.rotation_euler = (0.0, math.radians(90.0 * sign), 0.0)
        bkit.move(paddle, cx, 0.0, FOOT_H + 74.0)
        rim = bkit.torus("PaddleRim" + side, PAD_R - 1.0, 3.0, seg_major=48,
                         seg_minor=12, mat=accent)
        rim.rotation_euler = (0.0, math.radians(90.0 * sign), 0.0)
        bkit.move(rim, cx + sign * 22.0, 0.0, FOOT_H + 74.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


CHECKS = [
    dict(name="body_size", mm=330.0, tol=0.5, how="bbox_x", part="DefibBody"),
    dict(name="depth", mm=280.0, tol=0.5, how="bbox_y", part="DefibBody"),
    dict(name="overall_height", mm=255.0, tol=4.0, how="bbox_z"),
]