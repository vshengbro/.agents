"""
thermos -- 0.5 litre vacuum flask: a lathed steel body with a rolled shoulder
and a screw-on cup that doubles as the lid.

Two lathed parts, each with its own closed cross-section. The wall of the body
follows the shoulder all the way round so the neck is hollow, which is what a
real flask is; a single-surface revolve of the outside would leave the cup
sitting on a lid-less tube.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=72.0,       # widest point of the flask body
    body_height=200.0,        # base to the top of the neck collar
    wall=2.0,
    neck_diameter=48.0,
    cup_diameter=52.0,
    cup_height=35.0,
    overall_height=235.0,     # including the cup
    volume_ml=500.0,
)

R = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]


def build():
    shell = bkit.pbr("FlaskShell", base=(0.82, 0.83, 0.85), metal=1.0, rough=0.24)
    shell_paint = bkit.pbr("FlaskPaint", base=(0.06, 0.30, 0.46), metal=0.25,
                           rough=0.32)
    cup_mat = bkit.pbr("FlaskCup", base=(0.10, 0.11, 0.13), rough=0.38)

    # ---- flask body: base -> outside -> shoulder -> neck -> inside ---------
    prof = [
        (0.0, 0.0),
        (31.0, 0.0),
        (35.0, 2.0),
        (R, 8.0),                     # full body radius
        (R, 90.0),
        (35.0, 120.0),
        (33.0, 140.0),                # shoulder begins
        (26.0, 160.0),
        (24.0, 170.0),                # neck
        (24.0, 196.0),
        (25.5, 196.0),                # collar bead
        (25.5, BH),
        (23.0, BH),                   # across the top
        (23.0, 172.0),
        (21.0, 165.0),                # inside of the shoulder
        (30.5, 138.0),
        (33.5, 10.0),                 # down the inside wall
        (29.0, 3.0),
        (0.0, 3.0),                   # across the inner floor
    ]
    body = bkit.lathe("FlaskBody", prof, segments=96, mat=shell)
    bkit.assign_faces_by(
        body, shell_paint,
        lambda c, n: 6.0 < c.z / bkit.MM < 150.0,
    )

    # ---- cup: a real cup profile, hollow, seated on the neck ----------------
    cup_prof = [
        (0.0, 0.0),
        (24.0, 0.0),
        (26.0, 2.0),
        (26.0, 32.0),
        (25.0, 35.0),                 # rolled rim
        (22.0, 35.0),
        (22.0, 3.0),
        (0.0, 3.0),
    ]
    cup = bkit.lathe("FlaskCup", cup_prof, segments=96,
                     centre=(0.0, 0.0, BH), mat=cup_mat)

    # ---- silicone seal ring at the joint ------------------------------------
    seal = bkit.tube("FlaskSeal", 24.4, 21.0, 4.0, segments=64,
                     centre=(0.0, 0.0, BH - 2.0), mat=cup_mat)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_diameter", mm=72.0, tol=0.4, how="diameter", part="FlaskBody"),
    dict(name="cup_diameter", mm=52.0, tol=0.4, how="diameter", part="FlaskCup"),
    dict(name="overall_height", mm=235.0, tol=0.4, how="bbox_z"),
]
