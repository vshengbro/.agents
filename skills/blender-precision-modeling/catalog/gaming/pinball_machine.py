"""
pinball_machine -- 2100 x 760 x 800 mm four-leg pinball with a backbox.

A pinball table is a long, shallow, tilted box, and everything that makes it
read as a pinball table is on the playfield: the rows of bumper posts, the two
flippers at the near end, the drain, and the plunger. The backbox is a second
box hinged up at the far end, which is why the machine's overall length is
2050 mm of cabinet plus 50 mm of overhang.

The bumpers are arrayed with array_linear on a world pitch, not placed: 5 posts
in a row at 180 mm and 2 rows at 620 mm is a layout, and a layout typed in as
literals is a layout with two posts in the same place. The flippers are
tapered lofts, because a flipper is a wedge, not a cylinder.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

L, W, H = 2050.0, 760.0, 800.0
LEG_H = 700.0
LEG_S = 70.0
DECK_T = 40.0
RAKE = 6.5                 # the playfield rises toward the back
BACKBOX_L, BACKBOX_H, BACKBOX_T = 560.0, 800.0, 260.0
BUMPER_R, BUMPER_H, BUMPER_N = 34.0, 52.0, 5
BUMPER_PITCH_X = 180.0
BUMPER_PITCH_Y = 300.0
FLIPPER_L = 150.0
FLIPPER_TIP = 26.0
FLIPPER_ROOT = 34.0
FLIPPER_PIVOT_X = 300.0
FLIPPER_PIVOT_Y = 210.0
PLUNGER_R = 26.0
PLUNGER_L = 180.0
RAMP_L = 520.0
RAMP_R = 22.0

SPEC = dict(cabinet_length=L, cabinet_width=W, leg_height=LEG_H,
            deck_thickness=DECK_T, playfield_rake=RAKE,
            backbox_height=BACKBOX_H, bumper_count=BUMPER_N,
            bumper_pitch_x=BUMPER_PITCH_X, flipper_length=FLIPPER_L,
            plunger_length=PLUNGER_L)


def build():
    body_mat = bkit.pbr("PinballBody", base=(0.10, 0.11, 0.14), metal=0.0, rough=0.32)
    play_mat = bkit.pbr("Playfield", base=(0.10, 0.24, 0.16), metal=0.0, rough=0.26,
                        coat=0.4)
    chrome = bkit.pbr("PinballChrome", base=(0.86, 0.88, 0.91), metal=0.85, rough=0.14)
    rubber = bkit.pbr("FlipperRubber", base=(0.86, 0.14, 0.12), metal=0.0, rough=0.45)
    post_mat = bkit.pbr("BumperPost", base=(0.92, 0.70, 0.14), metal=0.0, rough=0.30)
    backbox_mat = bkit.pbr("BackboxArt", base=(0.05, 0.06, 0.10), metal=0.0, rough=0.22,
                           emission=(0.30, 0.20, 0.45), emission_strength=1.1)

    # ---- cabinet: a long box on four legs ----------------------------------
    deck = bkit.rounded_box("Cabinet", L, W, DECK_T, r=5.0, segments=3,
                            centre=(0.0, 0.0, LEG_H + DECK_T / 2.0 + 60.0),
                            mat=body_mat)
    deck_top = LEG_H + DECK_T + 60.0
    # the playfield lies ON the deck, not inside it
    play = bkit.rounded_box("Playfield", L - 60.0, W - 60.0, 12.0, r=3.0,
                            segments=2, centre=(0.0, 0.0, deck_top + 6.0),
                            mat=play_mat)
    play.rotation_euler = (0.0, math.radians(RAKE), 0.0)

    legs = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            legs.append(bkit.rounded_box("Leg", LEG_S, LEG_S, LEG_H + 60.0, r=4.0,
                                         segments=2,
                                         centre=(sx * (L / 2.0 - 110.0),
                                                 sy * (W / 2.0 - 90.0),
                                                 (LEG_H + 60.0) / 2.0),
                                         mat=body_mat))
    bkit.join(legs, name="Legs")

    # ---- backbox, hinged up at the back of the deck -----------------------
    back = bkit.rounded_box("Backbox", BACKBOX_L, W, BACKBOX_H, r=6.0, segments=3,
                            centre=(0.0, 0.0, BACKBOX_H / 2.0), mat=body_mat)
    back.rotation_euler = (0.0, math.radians(-3.0), 0.0)
    bkit.move(back, -L / 2.0 + 60.0, 0.0, LEG_H + DECK_T + 120.0)
    back_art = bkit.rounded_box("BackboxArt", 12.0, W - 60.0, BACKBOX_H - 90.0,
                                r=3.0, segments=2,
                                centre=(-BACKBOX_L / 2.0 - 4.0, 0.0,
                                        BACKBOX_H / 2.0), mat=backbox_mat)
    back_art.rotation_euler = (0.0, math.radians(-3.0), 0.0)
    bkit.move(back_art, -L / 2.0 + 60.0, 0.0, LEG_H + DECK_T + 120.0)

    # ---- five bumper posts in a row, then a second row --------------------
    bumper = bkit.cylinder("Bumpers", BUMPER_R, BUMPER_H, segments=24,
                           centre=(-180.0, 0.0, deck_top + 40.0), mat=post_mat)
    bkit.array_linear(bumper, BUMPER_N, (BUMPER_PITCH_X, 0.0, 0.0), world=True)
    bumper2 = bkit.cylinder("BumpersBack", BUMPER_R, BUMPER_H, segments=24,
                            centre=(-180.0, BUMPER_PITCH_Y, deck_top + 40.0),
                            mat=post_mat)
    bkit.array_linear(bumper2, BUMPER_N, (BUMPER_PITCH_X, 0.0, 0.0), world=True)

    # ---- two flippers: tapered lofts, mirrored about the centre line -------
    # Each section sits at its own station along +X, so the loft is a wedge
    # that is fattest at the pivot and narrowest at the tip.
    sections = []
    for i in range(7):
        f = i / 6.0
        size = FLIPPER_ROOT + (FLIPPER_TIP - FLIPPER_ROOT) * f
        ring = bkit.rounded_rect_section(26.0, size, 9.0, per_corner=5)
        sections.append([(f * FLIPPER_L, u, v) for (u, v) in ring])
    flipper = bkit.loft("Flippers", sections, closed_loop=True, cap_start=True,
                        cap_end=True, mat=rubber, smooth=True)
    bkit.recalc(flipper)
    # bkit.duplicate() SETS rotation_euler, so the mirror's 28 deg has to be
    # restated (negated) rather than inherited.
    flipper.rotation_euler = (0.0, 0.0, math.radians(28.0))
    bkit.move(flipper, FLIPPER_PIVOT_X, FLIPPER_PIVOT_Y, deck_top + 18.0)
    bkit.duplicate(flipper, "Flippers", offset_mm=(0.0, -2.0 * FLIPPER_PIVOT_Y, 0.0),
                   rot_deg=(0.0, 0.0, -28.0))

    # ---- plunger in its housing at the near end ----------------------------
    housing = bkit.cylinder("PlungerHousing", 34.0, 120.0, segments=24,
                            centre=(L / 2.0 - 80.0, 0.0, deck_top + 4.0), mat=chrome)
    plunger = bkit.cylinder("Plunger", PLUNGER_R, PLUNGER_L, segments=24,
                            centre=(L / 2.0 + 30.0, 0.0, deck_top + 4.0), mat=chrome)

    # ---- one wire ramp along the left lane ---------------------------------
    ramp = bkit.arc_torus("Ramp", RAMP_R, 9.0, 0.0, 180.0, plane="XY",
                          seg_major=48, seg_minor=12,
                          centre=(-180.0, -240.0, deck_top + 60.0), mat=chrome)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="cabinet_length", mm=2050.0, tol=0.5, how="bbox_x", part="Cabinet"),
    dict(name="cabinet_width", mm=760.0, tol=0.2, how="bbox_y", part="Cabinet"),
    dict(name="backbox_height", mm=827.6, tol=0.4, how="bbox_z",
         part="Backbox"),
    dict(name="bumper_diameter", mm=68, tol=0.2, how="bbox_y",
         part="Bumpers"),
    # 4 x 180 pitch + one bumper diameter
    dict(name="bumper_row", mm=788.0, tol=0.3, how="bbox_x", part="Bumpers"),
    dict(name="flipper_length", mm=144.6, tol=0.3, how="bbox_x", part="Flippers"),
    dict(name="plunger_reach", mm=52, tol=0.2, how="bbox_x",
         part="Plunger"),
    dict(name="overall_height", mm=1690, tol=1, how="bbox_z",
         part=None)
]