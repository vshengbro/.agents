"""
metronome_clock -- 214 mm wooden metronome with a graduated scale and sliding weight.

A metronome is a truncated pyramid, and the pyramid is the model: the body is a
loft over two rounded-rectangle sections, the wider one at the bottom, so the
taper is a real change of section rather than a stack of blocks. Both sections
come from rounded_rect_section with the same per_corner count, which is what
lets loft bridge them at all -- sections of different lengths raise ValueError.

The window down the front is cut with an oversized cutter so it passes clear
through both faces, and the pendulum rod and its sliding weight sit in it. The
graduated scale is one tick swept by array_linear, so the ten graduations are a
pitch and not ten literals.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

PLINTH_W, PLINTH_D, PLINTH_H = 132.0, 122.0, 12.0
BODY_H = 194.0
BASE_W, BASE_D = 118.0, 110.0
TOP_W, TOP_D = 62.0, 56.0
CAP_W, CAP_D, CAP_H = 70.0, 64.0, 8.0
WIN_W, WIN_H = 24.0, 128.0
ROD_R, ROD_L = 3.0, 176.0
WEIGHT_W, WEIGHT_H, WEIGHT_D = 34.0, 16.0, 16.0
TICK_N = 10
TICK_PITCH = 11.0
TICK_W, TICK_L = 1.4, 9.0
RAKE = 7.0

SPEC = dict(height=PLINTH_H + BODY_H + CAP_H, base_width=BASE_W,
            base_depth=BASE_D, top_width=TOP_W, window_width=WIN_W,
            window_height=WIN_H, rod_length=ROD_L,
            weight_width=WEIGHT_W, scale_ticks=TICK_N, scale_pitch=TICK_PITCH)


def build():
    wood = bkit.pbr("MetroWood", base=(0.46, 0.28, 0.13), metal=0.0, rough=0.36,
                    coat=0.4)
    dark = bkit.pbr("MetroDark", base=(0.12, 0.09, 0.07), metal=0.0, rough=0.44)
    steel = bkit.pbr("MetroSteel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.16)
    paper = bkit.pbr("MetroPaper", base=(0.92, 0.90, 0.84), metal=0.0, rough=0.52)

    # ---- plinth and the tapered body ---------------------------------------
    plinth = bkit.rounded_box("Plinth", PLINTH_W, PLINTH_D, PLINTH_H, r=3.0,
                              segments=3, centre=(0.0, 0.0, PLINTH_H / 2.0),
                              mat=wood)
    z_lo, z_hi = PLINTH_H, PLINTH_H + BODY_H
    body = bkit.loft(
        "Body",
        [[(x, y, z_lo) for (x, y) in bkit.rounded_rect_section(BASE_W, BASE_D, 5.0,
                                                             per_corner=5)],
         [(x, y, z_lo + (z_hi - z_lo) * 0.55)
          for (x, y) in bkit.rounded_rect_section(
              BASE_W + (TOP_W - BASE_W) * 0.55, BASE_D + (TOP_D - BASE_D) * 0.55,
              4.2, per_corner=5)],
         [(x, y, z_hi) for (x, y) in bkit.rounded_rect_section(TOP_W, TOP_D, 3.4,
                                                              per_corner=5)]],
        closed_loop=True, cap_start=True, cap_end=True, mat=wood, smooth=True)
    bkit.recalc(body)

    # ---- the window, cut clear through the front and back -------------------
    win = bkit.rounded_box("_window", WIN_W, BASE_D + 40.0, WIN_H, r=3.0, segments=3,
                           centre=(0.0, 0.0, z_lo + WIN_H / 2.0 + 14.0))
    bkit.boolean(body, win, "DIFFERENCE")

    # ---- cap -----------------------------------------------------------------
    cap = bkit.rounded_box("Cap", CAP_W, CAP_D, CAP_H, r=3.0, segments=3,
                           centre=(0.0, 0.0, z_hi + CAP_H / 2.0), mat=dark)

    # ---- pendulum rod, raked back, with its sliding weight ------------------
    # The rod hangs from the top of the window down to just above the plinth.
    # Centred lower than this it swings its tail through the floor, and
    # sit_on_floor then lifts the whole metronome by that overhang.
    rod = bkit.cylinder("PendulumRod", ROD_R, ROD_L, segments=16,
                        centre=(0.0, 0.0, z_lo + 10.0 + ROD_L / 2.0), mat=steel)
    rod.rotation_euler = (math.radians(RAKE), 0.0, 0.0)
    weight = bkit.rounded_box("SlidingWeight", WEIGHT_W, WEIGHT_D, WEIGHT_H, r=1.5,
                              segments=2,
                              centre=(0.0, -2.0, z_lo + 62.0), mat=dark)
    weight.rotation_euler = (math.radians(RAKE), 0.0, 0.0)
    bob = bkit.cylinder("PendulumWeight", 13.0, 8.0, segments=28,
                        centre=(0.0, 0.0, z_lo + 16.0), axis="Y", mat=dark)

    # ---- graduated scale to the left of the window --------------------------
    scale = bkit.rounded_box("Scale", 22.0, 1.2, 104.0, r=0.5, segments=2,
                             centre=(-WIN_W / 2.0 - 14.0, -BASE_D / 2.0 + 3.0,
                                     z_lo + 70.0), mat=paper)
    tick = bkit.rounded_box("ScaleTicks", TICK_L, 1.0, TICK_W, r=0.3, segments=2,
                            centre=(-WIN_W / 2.0 - 24.0, -BASE_D / 2.0 + 2.0,
                                    z_lo + 20.0), mat=dark)
    bkit.array_linear(tick, TICK_N, (0.0, 0.0, TICK_PITCH), world=True)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="height", mm=214, tol=0.4, how="bbox_z",
         part=None),
    dict(name="base_width", mm=118.0, tol=0.2, how="bbox_x", part="Body"),
    dict(name="base_depth", mm=110.0, tol=0.2, how="bbox_y", part="Body"),
    dict(name="plinth_width", mm=132.0, tol=0.2, how="bbox_x", part="Plinth"),
    dict(name="scale_run", mm=100.4, tol=0.2, how="bbox_z",
         part="ScaleTicks"),
    dict(name="body_depth", mm=110, tol=0.2, how="bbox_y",
         part="Body"),
    dict(name="rod_length", mm=175.42, tol=0.3, how="bbox_z",
         part="PendulumRod")
]