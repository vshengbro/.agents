"""
synthesizer -- 61-key velocity-sensitive keyboard synthesizer, 1052 x 320 x 92 mm.

The repetition job: 61 keys is 36 naturals and 25 sharps on a 22.5 mm pitch,
plus a control surface of 20 knobs, 8 buttons and a pitch wheel. All of it is
driven from one pitch constant and one gap; the knob row and the button grid go
through `bkit.lay_out` and `bkit.grid_positions` respectively so the control
surface cannot drift out of alignment with the keyboard.

The chassis is a `rounded_box` with the keyboard bed and the pitch-wheel slot
cut into it. The screen is a second material on the panel, not a second shell,
so nothing z-fights.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=1052.0,
    depth=320.0,
    height=92.0,
    keys=61,
    white_keys=36,
    black_keys=25,
    key_pitch=22.5,
    key_gap=1.2,
    key_height=18.0,
    knob_diameter=17.0,
    knob_count=20,
    buttons=8,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
PITCH, GAP = SPEC["key_pitch"], SPEC["key_gap"]

KB_W = 36 * PITCH                 # 810 mm of naturals
KB_X0 = -W / 2.0 + 130.0          # left end of the keyboard, in X
KB_FRONT = -D / 2.0 + 28.0        # front edge of the keyboard, in Y
CTRL_Z = H - 6.0                  # control surface height


def build():
    case_mat = bkit.pbr("SynthCase", base=(0.14, 0.145, 0.16), rough=0.34)
    panel = bkit.pbr("SynthPanel", base=(0.20, 0.21, 0.23), rough=0.36)
    nat = bkit.pbr("SynthNatural", base=(0.90, 0.89, 0.86), rough=0.34)
    sharp = bkit.pbr("SynthSharp", base=(0.045, 0.045, 0.05), rough=0.32)
    knob = bkit.pbr("SynthKnob", base=(0.55, 0.57, 0.60), rough=0.28)
    accent = bkit.pbr("SynthAccent", base=(0.72, 0.24, 0.06), rough=0.30)
    screen = bkit.pbr("SynthScreen", base=(0.06, 0.14, 0.18), rough=0.14,
                      emission=(0.10, 0.45, 0.62), emission_strength=1.6)

    case = bkit.rounded_box("SynthCase", W, D, H, r=7.0, segments=4,
                            centre=(0, 0, H / 2.0), mat=case_mat)
    # Keyboard well and pitch-wheel slot, both cut rather than assembled
    # around. The wheel slot is 3 mm deeper than the panel it passes through so
    # the cutter crosses the surface instead of landing tangent to it.
    bkit.boolean(case, bkit.rounded_box(
        "_kb", KB_W + 16.0, 210.0, 60.0, r=3.0, segments=2,
        centre=(KB_X0 + KB_W / 2.0, KB_FRONT + 96.0, H - 18.0)),
        "DIFFERENCE")
    bkit.boolean(case, bkit.rounded_box(
        "_wheel", 70.0, 130.0, 70.0, r=6.0, segments=2,
        centre=(W / 2.0 - 120.0, KB_FRONT + 90.0, H - 24.0)), "DIFFERENCE")

    bkit.rounded_box("SynthPanelTop", W - 40.0, 118.0, 8.0, r=4.0, segments=3,
                     centre=(0.0, D / 2.0 - 70.0, H - 4.0), mat=panel)

    # ---- 61 keys ----------------------------------------------------------
    # 61 keys is C to C over five octaves: 36 naturals, 25 sharps. The sharps
    # sit 0.58 of a pitch past their natural, so the rows interleave. Keys run
    # left-to-right in X starting at KB_X0 -- a centred lay_out would put the
    # leftmost key 400 mm off the left edge of a 1052 mm case.
    kx = KB_X0
    naturals = []
    for i, (x, w) in enumerate(bkit.lay_out([PITCH - GAP] * 36, gap=GAP,
                                            centre=False)):
        naturals.append(bkit.rounded_box(
            "SynthNaturalKey%02d" % i, w, 148.0, SPEC["key_height"], r=1.2,
            segments=2, centre=(kx + x, KB_FRONT + 74.0,
                                H - 16.0 + SPEC["key_height"] / 2.0), mat=nat))
    sharps = []
    n = 0
    for o in range(5):
        base = o * 7.0
        for k in (0.58, 1.58, 2.58, 4.58, 5.58):
            u = base + k
            if u >= 36.0:
                continue
            sharps.append(bkit.rounded_box(
                "SynthSharpKey%02d" % n, 11.0, 96.0, SPEC["key_height"] + 11.0,
                r=1.2, segments=2,
                centre=(kx + u * PITCH, KB_FRONT + 48.0,
                        H - 16.0 + SPEC["key_height"] + 5.5), mat=sharp))
            n += 1
    bkit.join(naturals, name="SynthNaturalKeys")
    bkit.join(sharps, name="SynthSharpKeys")

    # ---- control surface: 20 knobs, 8 buttons, wheels, screen --------------
    for i, (x, _w) in enumerate(bkit.lay_out([SPEC["knob_diameter"]] * 20,
                                             gap=22.0, centre=False)):
        y = D / 2.0 - 70.0 + (14.0 if i >= 10 else -14.0)
        bkit.cylinder("SynthKnob%02d" % i, SPEC["knob_diameter"] / 2.0, 16.0,
                      segments=18, centre=(-W / 2.0 + 60.0 + x, y, CTRL_Z + 8.0),
                      mat=knob)
        bkit.box("SynthKnobMark%02d" % i, 2.5, 9.0, 2.0,
                 centre=(-W / 2.0 + 60.0 + x, y - 5.0, CTRL_Z + 16.0),
                 mat=accent)

    for i, (x, y) in enumerate(bkit.grid_positions(cols=8, rows=1,
                                                    pitch_x=30.0, pitch_y=0.0)):
        bkit.rounded_box("SynthButton%d" % i, 24.0, 20.0, 9.0, r=2.5,
                         segments=2,
                         centre=(W / 2.0 - 200.0 + x, KB_FRONT + 26.0, H + 2.0),
                         mat=accent if i < 2 else panel)

    bkit.cylinder("SynthPitchWheel", 15.0, 54.0, segments=20,
                  centre=(W / 2.0 - 120.0, KB_FRONT + 90.0, H - 24.0), axis="X",
                  mat=knob)
    bkit.cylinder("SynthModWheel", 15.0, 54.0, segments=20,
                  centre=(W / 2.0 - 120.0, KB_FRONT + 132.0, H - 24.0), axis="X",
                  mat=knob)

    scr = bkit.rounded_box("SynthScreen", 210.0, 70.0, 3.0, r=2.0, segments=2,
                           centre=(W / 2.0 - 250.0, D / 2.0 - 70.0,
                                   CTRL_Z + 2.0), mat=screen)
    bkit.bevel(scr, width_mm=0.4, segments=1)

    # ---- rear ports and feet ----------------------------------------------
    for i, (x, _w) in enumerate(bkit.lay_out([48.0] * 4, gap=10.0,
                                              centre=False)):
        bkit.rounded_box("SynthPort%d" % i, 44.0, 14.0, 26.0, r=2.0, segments=2,
                         centre=(-W / 2.0 + 420.0 + x, D / 2.0 + 2.0, H - 34.0),
                         mat=knob)
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2, pitch_x=900.0,
                                                    pitch_y=200.0)):
        bkit.cylinder("SynthFoot%d" % i, 16.0, 12.0, segments=12,
                      centre=(x, y, -4.0), mat=bkit.preset("rubber"))

    return dict(spec=SPEC, parts=7, keys=36 + len(sharps))


CHECKS = [
    dict(name="width", mm=1052.0, tol=1.0, how="bbox_x", part="SynthCase"),
    dict(name="depth", mm=320.0, tol=1.0, how="bbox_y", part="SynthCase"),
    dict(name="height", mm=92.0, tol=1.5, how="bbox_z", part="SynthCase"),
    dict(name="keyboard_width", mm=808.8, tol=2.0, how="bbox_x",
         part="SynthNaturalKeys"),
]