"""
laser_level -- self-levelling 360 degree laser level, 196 mm tall on a 108 mm
footprint.

A laser level is a pendulum in a box: a machined body, a vertical pitch pendulum
behind a glass window, a lens aperture, and a rubber foot with a threaded mount
underneath. The number that makes it read is the WINDOW -- a 96 mm glass door
with the pendulum's weight visible behind it -- because a level with no window
is a laser pointer in a box.

The foot's underside is z = 0, so the level stands on its own base.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    body_width=108.0,
    body_depth=76.0,
    body_height=128.0,
    window_height=96.0,
    window_width=70.0,
    lens_diameter=26.0,
    foot_diameter=92.0,
    overall_height=190.0,
)

CHECKS = [
    dict(name="body_width", mm=108.0, tol=0.8, how="bbox_x",
         part="LevelBody"),
    dict(name="body_depth", mm=76.0, tol=0.8, how="bbox_y",
         part="LevelBody"),
    dict(name="body_height", mm=128.0, tol=1.0, how="bbox_z",
         part="LevelBody"),
    dict(name="window_height", mm=96.0, tol=0.8, how="bbox_z",
         part="LevelWindow"),
    dict(name="window_width", mm=70.0, tol=0.8, how="bbox_x",
         part="LevelWindow"),
    dict(name="lens_diameter", mm=26.0, tol=0.8, how="diameter",
         part="LevelLens"),
    dict(name="foot_diameter", mm=92.0, tol=0.8, how="diameter",
         part="LevelFoot"),
    dict(name="overall_height", mm=190.0, tol=2.0, how="top_z",
         part="LevelCap"),
]

FZ = 22.0                  # foot height; the foot is the floor datum
BZ = FZ + SPEC["body_height"] / 2.0


def build():
    yellow = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    glass = bkit.pbr("LevelGlass", base=(0.80, 0.85, 0.88), rough=0.05,
                     transmission=0.70)
    lens_mat = bkit.pbr("LevelLensMat", base=(0.12, 0.35, 0.85), rough=0.08,
                        emission=(0.15, 0.45, 0.95), emission_strength=2.5)

    # ---- foot + machined body ---------------------------------------------
    bkit.lathe("LevelFoot",
               [(0.0, 0.0), (46.0, 0.0), (46.0, 12.0), (40.0, FZ),
                (16.0, FZ), (16.0, 6.0), (0.0, 6.0)],
               segments=40, centre=(0.0, 0.0, 0.0), mat=dark)
    mount = bkit.thread("LevelMount", 8.0, 1.5, 12.0, thread_h=1.0,
                        segments_per_turn=20, mat=steel)
    bkit.move(mount, 0.0, 0.0, 8.0)

    T.shell("LevelBody", SPEC["body_width"], SPEC["body_depth"],
            SPEC["body_height"], centre=(0.0, 0.0, BZ), r=10.0, mat=yellow)
    T.shell("LevelCap", 96.0, 66.0, 46.0, centre=(0.0, 0.0, BZ + 75.0),
            r=9.0, mat=dark)

    # ---- pendulum window: glass door, weight and pivot behind it ---------
    T.shell("LevelWindow", SPEC["window_width"], 12.0,
            SPEC["window_height"], centre=(0.0, -SPEC["body_depth"] / 2.0,
                                          BZ), r=3.0, mat=glass)
    bkit.rounded_box("LevelPendulum", 26.0, 10.0, 78.0, r=4.0, segments=2,
                     centre=(0.0, -SPEC["body_depth"] / 2.0 + 8.0, BZ - 6.0),
                     mat=steel)
    bkit.cylinder("LevelPivot", 6.0, 26.0, segments=16,
                  centre=(0.0, -SPEC["body_depth"] / 2.0 + 10.0, BZ + 34.0),
                  axis="X", mat=dark)

    # ---- laser aperture + indicators --------------------------------------
    bkit.tube("LevelLens", 13.0, 7.0, 16.0, segments=28,
              centre=(0.0, -SPEC["body_depth"] / 2.0 - 4.0, BZ - 40.0),
              axis="Y", mat=lens_mat)
    bkit.tube("LevelSideLens", 9.0, 5.0, 12.0, segments=24,
              centre=(SPEC["body_width"] / 2.0 - 2.0, 0.0, BZ + 30.0),
              axis="X", mat=lens_mat)
    for i, dx in enumerate((-30.0, 30.0)):
        bkit.rounded_box("LevelLed%d" % i, 12.0, 8.0, 8.0, r=1.5, segments=1,
                         centre=(dx, -SPEC["body_depth"] / 2.0 - 2.0,
                                 BZ + 46.0), mat=lens_mat)
    T.knob("LevelFineKnob", 14.0, 12.0, (0.0, 0.0, FZ + 30.0), mat=dark)

    return dict(spec=SPEC, parts=11)