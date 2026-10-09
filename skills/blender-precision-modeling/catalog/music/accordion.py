"""
accordion -- 41-key piano accordion, 460 x 210 x 400 mm.

The bellows are the model: 21 pleats of folded card between the two end
frames, each pleat a real rib. They come from `array_linear` on ONE pleat, not
from 21 hand-placed boxes, so the pleat count and the gap between the end
frames can never disagree -- the bellows length IS count x pitch.

The right-hand keyboard is 41 keys (24 naturals, 17 sharps) at the same
23.5 mm pitch the pianos use, and the left-hand bass board is a grid of 120
buttons from `bkit.grid_positions`. The grilles on both ends are
`perforated_panel`, which gives the real holes in one mesh with no booleans.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=460.0,
    depth=623.0,
    height=400.0,
    keys=41,
    white_keys=24,
    black_keys=17,
    key_pitch=23.5,
    key_gap=1.2,
    bellows_pleats=21,
    bellows_pitch=13.0,
    bass_buttons=120,
    grille_cols=6,
    grille_rows=9,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
PITCH, GAP = SPEC["key_pitch"], SPEC["key_gap"]
PLEATS = SPEC["bellows_pleats"]
PP = SPEC["bellows_pitch"]

# A piano accordion is WIDE across its keyboard and shallow front-to-back, so:
# the keyboard span runs in Y (across the 460 mm width), the bellows stack in X
# (the ~290 mm depth the instrument gains when the bellows are open), and the
# cases are 400 tall. 24 naturals at a 23.5 mm pitch is 564 mm, so the keyboard
# overhangs the 460 mm case slightly -- as it does on a real 41-key accordion.
KEY_SPAN = 24 * PITCH                    # 564 mm of naturals
BELLOWS = PLEATS * PP                    # 21 x 13 = 273 mm
CASE_R = 200.0        # right-hand (keyboard) end, in X
CASE_L = 150.0        # left-hand (bass) end, in X


def build():
    body = bkit.pbr("AccBody", base=(0.55, 0.09, 0.09), rough=0.26, coat=0.5)
    black = bkit.pbr("AccBlack", base=(0.07, 0.07, 0.08), rough=0.34)
    chrome = bkit.pbr("AccChrome", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.16)
    grille = bkit.pbr("AccGrille", base=(0.82, 0.70, 0.36), metal=0.85,
                      rough=0.30)
    nat = bkit.pbr("AccNatural", base=(0.93, 0.92, 0.88), rough=0.28)
    sharp = bkit.pbr("AccSharp", base=(0.045, 0.045, 0.05), rough=0.30)
    ivory = bkit.pbr("AccIvory", base=(0.90, 0.88, 0.80), rough=0.32)

    # ---- two end frames ---------------------------------------------------
    # The right case carries the keyboard; the left carries the bass board.
    # The cases are sized in X (the bellows axis) and full WIDTH in Y.
    bkit.rounded_box("AccRightCase", CASE_R, W, H, r=14.0, segments=4,
                     centre=(BELLOWS / 2.0 + CASE_R / 2.0, 0, H / 2.0),
                     mat=body)
    bkit.rounded_box("AccLeftCase", CASE_L, W, H, r=14.0, segments=4,
                     centre=(-BELLOWS / 2.0 - CASE_L / 2.0, 0, H / 2.0),
                     mat=body)
    bkit.rounded_box("AccRightTop", CASE_R + 8.0, W + 8.0, 16.0, r=10.0,
                     segments=3,
                     centre=(BELLOWS / 2.0 + CASE_R / 2.0, 0, H + 6.0),
                     mat=black)
    bkit.rounded_box("AccLeftTop", CASE_L + 8.0, W + 8.0, 16.0, r=10.0,
                     segments=3,
                     centre=(-BELLOWS / 2.0 - CASE_L / 2.0, 0, H + 6.0),
                     mat=black)

    # ---- bellows: one pleat, arrayed --------------------------------------
    # The pleat is a real folded-card plate. Arrayed 21 times at 13 mm, the
    # bellows are exactly 273 mm long, and the count and the length can never
    # disagree because one number drives both.
    pleat = bkit.extrude_profile(
        "AccBellowsPleat0",
        [(-PP / 2.0, -W / 2.0), (PP / 2.0, -W / 2.0),
         (PP / 2.0, W / 2.0), (-PP / 2.0, W / 2.0)],
        H - 24.0, centre=(0, 0, (H - 24.0) / 2.0 + 12.0), mat=ivory)
    bkit.array_linear(pleat, PLEATS, offset_mm=(PP, 0, 0))
    bkit.move(pleat, -BELLOWS / 2.0 + PP / 2.0, 0.0, 0.0)

    # Corner folds: the pleat array is rectangular, so the four long edges get
    # their own strips to close the bellows into a box.
    for i, y in enumerate((W / 2.0 - 5.0, -W / 2.0 + 5.0)):
        strip = bkit.rounded_box("AccBellowsEdge%d" % i,
                                 BELLOWS, 10.0, H - 24.0, r=3.0, segments=2,
                                 centre=(0.0, y, (H - 24.0) / 2.0 + 12.0),
                                 mat=ivory)
        bkit.move(strip, 0.0, 0.0, 0.0)
    for i, z in enumerate((14.0, H - 14.0)):
        strap = bkit.rounded_box("AccBellowsStrap%d" % i,
                                 BELLOWS + 6.0, W - 10.0, 8.0, r=3.0,
                                 segments=2, centre=(0.0, 0.0, z), mat=black)
    # Bellows corners (metal protectors).
    for i, x in enumerate((-BELLOWS / 2.0 + 8.0, BELLOWS / 2.0 - 8.0)):
        bkit.rounded_box("AccBellowsCorner%d" % i, 16.0, W - 14.0, H - 24.0,
                         r=6.0, segments=2,
                         centre=(x, 0.0, (H - 24.0) / 2.0 + 12.0), mat=chrome)

    # ---- right-hand keyboard: 41 keys, 24 naturals + 17 sharps -----------
    # Keys run ACROSS the case width (Y), so a key's long dimension is in X:
    # it reaches back toward the bellows. `centre=False` anchors the run at
    # the case's front edge instead of straddling the origin.
    kx = BELLOWS / 2.0 + CASE_R - 26.0
    naturals = []
    for i, (y, w) in enumerate(bkit.lay_out([PITCH - GAP] * 24, gap=GAP,
                                            centre=False)):
        naturals.append(bkit.rounded_box(
            "AccNaturalKey%02d" % i, 150.0, w, 20.0, r=1.2, segments=2,
            centre=(kx - 60.0, -KEY_SPAN / 2.0 + y, 300.0), mat=nat))
    sharps = []
    n = 0
    for o in range(4):
        base = o * 7.0
        for k in (0.58, 1.58, 2.58, 4.58, 5.58):
            u = base + k
            if u >= 24.0:
                continue
            sharps.append(bkit.rounded_box(
                "AccSharpKey%02d" % n, 96.0, 11.0, 30.0, r=1.2, segments=2,
                centre=(kx - 86.0, -KEY_SPAN / 2.0 + u * PITCH, 315.0),
                mat=sharp))
            n += 1
    bkit.join(naturals, name="AccNaturalKeys")
    bkit.join(sharps, name="AccSharpKeys")
    bkit.rounded_box("AccKeyFrame", 190.0, KEY_SPAN + 20.0, 26.0, r=4.0,
                     segments=2, centre=(kx + 30.0, 0.0, 278.0), mat=black)

    # ---- left-hand bass board: 120 buttons on a grid ----------------------
    bkx = -BELLOWS / 2.0 - CASE_L
    for i, (x, y) in enumerate(bkit.grid_positions(
            cols=12, rows=10, pitch_x=26.0, pitch_y=26.0)):
        bkit.cylinder("AccBassButton%03d" % i, 8.0, 7.0, segments=14,
                      centre=(bkx + 14.0, y - 117.0, 190.0 + x), axis="X",
                      mat=ivory)
    # Strap buttons: a single row of six, the reference notes.
    for i, (y, _z) in enumerate(bkit.lay_out([18.0] * 6, gap=14.0)):
        bkit.cylinder("AccStrapButton%d" % i, 9.5, 8.0, segments=14,
                      centre=(bkx + 14.0, y, 40.0), axis="X", mat=chrome)

    # ---- grilles: real holes, one mesh, no booleans -----------------------
    # perforated_panel builds its sheet in XY with the thickness on Z, so each
    # grille is built flat, then stood upright against its case face with one
    # 90-degree Y rotation.
    gr = bkit.perforated_panel("AccRightGrille", cols=SPEC["grille_cols"],
                               rows=SPEC["grille_rows"], pitch_x=22.0,
                               pitch_y=22.0, hole_r=7.5, panel_sx=150.0,
                               panel_sy=220.0, thickness=3.0, mat=grille)
    gr.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(gr, kx + 78.0, 0.0, 300.0)

    gl = bkit.perforated_panel("AccLeftGrille", cols=SPEC["grille_cols"],
                               rows=SPEC["grille_rows"], pitch_x=22.0,
                               pitch_y=22.0, hole_r=7.5, panel_sx=150.0,
                               panel_sy=220.0, thickness=3.0, mat=grille)
    gl.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(gl, bkx + 26.0, 0.0, 300.0)

    # ---- shoulder straps, hand strap, register switches -------------------
    for i, side in enumerate((-1.0, 1.0)):
        bkit.arc_torus("AccShoulderStrap%d" % i, 150.0, 9.0, 200.0, 340.0,
                       centre=(0.0, side * 130.0, H + 90.0), plane="YZ",
                       seg_major=32, mat=black, caps=True)
    bkit.rounded_box("AccHandStrap", 40.0, 120.0, 26.0, r=8.0, segments=3,
                     centre=(kx - 20.0, -W / 2.0 - 26.0, H - 70.0), mat=black)
    for i, (z, _w) in enumerate(bkit.lay_out([16.0] * 3, gap=12.0)):
        bkit.cylinder("AccRegisterSwitch%d" % i, 9.0, 12.0, segments=16,
                      centre=(kx - 40.0, -W / 2.0 + 60.0, 120.0 + z), axis="X",
                      mat=chrome)

    return dict(spec=SPEC, parts=8, keys=24 + len(sharps),
                pleats=PLEATS)


CHECKS = [
    dict(name="width", mm=460.0, tol=1.5, how="bbox_y", part="AccRightCase"),
    dict(name="height", mm=400.0, tol=1.5, how="bbox_z", part="AccRightCase"),
    dict(name="bellows_length", mm=273.0, tol=2.0, how="bbox_x",
         part="AccBellowsPleat0"),
    dict(name="keyboard_width", mm=564.0, tol=3.0, how="bbox_y",
         part="AccNaturalKeys"),
]