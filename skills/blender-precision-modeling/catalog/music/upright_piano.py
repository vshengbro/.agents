"""
upright_piano -- 88-key upright piano, 1500 x 615 x 1250 mm.

The 88 keys are the model. A 88 spans A0 to C8: 52 naturals and 36 sharps, and
a piano that renders 52 white keys with the wrong number of black ones reads
instantly as a toy. Nothing here is hand-placed -- one key pitch (23.5 mm) and
one key gap drive both rows. The naturals tile their run through
`bkit.lay_out`; the sharps come from an octave pattern of unit offsets, because
the sharps sit BETWEEN naturals (at 0.58 of the pitch past the natural, not on
a pitch of their own) and no gap value can express that.

The case is a `rounded_box` shell with the keyboard bed and the fallboard cut
into it, the pedal lyre is three lathed pedals, and the two front legs carry
castors. An upright is a tall box with a hole for the keys, and getting that
hole in the right place is most of the silhouette.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=1500.0,
    depth=615.0,
    height=1250.0,
    keys=88,
    white_keys=52,
    black_keys=36,
    key_pitch=23.5,
    key_gap=1.2,
    white_key_length=148.0,
    white_key_width=22.3,
    black_key_length=96.0,
    black_key_width=11.0,
    key_height=22.0,
    fallboard_height=330.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
PITCH, GAP = SPEC["key_pitch"], SPEC["key_gap"]
WW = SPEC["white_key_width"]
# The case runs from y=-D/2 (the flat back, against the wall) to y=+D/2 (the
# front). The keyboard is recessed INTO the front: the keys project 30 mm past
# the case face and the rest runs back under the fallboard.
FRONT = D / 2.0
KEY_Z = 740.0                       # keybed shelf height
KEY_FRONT = FRONT + 30.0            # front end of the naturals
NAT_CY = KEY_FRONT - SPEC["white_key_length"] / 2.0
SHARP_CY = KEY_FRONT - SPEC["black_key_length"] / 2.0


def build():
    case_mat = bkit.pbr("PianoCase", base=(0.13, 0.13, 0.145), rough=0.24,
                        coat=0.5)
    panel = bkit.pbr("PianoPanel", base=(0.10, 0.10, 0.115), rough=0.26)
    hw = bkit.pbr("PianoHardware", base=(0.80, 0.81, 0.83), metal=0.85,
                  rough=0.26)
    brass = bkit.pbr("PianoBrass", base=(0.84, 0.68, 0.30), metal=0.85,
                     rough=0.26)
    nat = bkit.pbr("PianoNatural", base=(0.92, 0.91, 0.87), rough=0.30)
    sharp = bkit.pbr("PianoSharp", base=(0.045, 0.045, 0.05), rough=0.32)
    felt = bkit.pbr("PianoFelt", base=(0.42, 0.06, 0.07), rough=0.70)

    # ---- case: the tall box, with the keyboard bed cut out of the front ----
    case = bkit.rounded_box("PianoCase", W, D, H, r=6.0, segments=3,
                            centre=(0, 0, H / 2.0), mat=case_mat)
    # The bed is cut, not assembled around: an upright's front face is one
    # surface with a rectangular hole for the keys. The cutter overshoots the
    # front face by 80 mm and undershoots the bed floor by 6 mm, so it crosses
    # both surfaces instead of landing tangent to them.
    bkit.boolean(case, bkit.box("_bed", W - 150.0, 320.0, 150.0,
                                centre=(0, FRONT - 60.0, KEY_Z - 20.0)),
                 "DIFFERENCE")

    # ---- upper panel, fallboard, lid, music desk --------------------------
    bkit.rounded_box("PianoUpperPanel", W - 120.0, 16.0, 380.0, r=5.0,
                     segments=3, centre=(0, FRONT - 14.0, KEY_Z + 300.0),
                     mat=panel)
    bkit.rounded_box("PianoFallboard", W - 60.0, 34.0,
                     SPEC["fallboard_height"], r=4.0, segments=3,
                     centre=(0, FRONT - 60.0, KEY_Z + 190.0), mat=case_mat)
    bkit.rounded_box("PianoKeySlip", W - 40.0, 30.0, 44.0, r=6.0, segments=3,
                     centre=(0, FRONT - 46.0, KEY_Z + 34.0), mat=case_mat)
    bkit.rounded_box("PianoLid", W, D, 34.0, r=5.0, segments=3,
                     centre=(0, 0, H + 17.0), mat=case_mat)
    bkit.rounded_box("PianoMusicDesk", 420.0, 14.0, 300.0, r=4.0, segments=3,
                     centre=(0, FRONT - 70.0, KEY_Z + 500.0), mat=panel)

    # ---- 88 keys ----------------------------------------------------------
    # Naturals first: one lay_out over 52 identical widths and one gap gives
    # the whole 1222 mm run, so the keyboard cannot drift out of the case.
    naturals = []
    for i, (x, w) in enumerate(bkit.lay_out([WW] * 52, gap=GAP)):
        naturals.append(bkit.rounded_box(
            "PianoNaturalKey%02d" % i, w, SPEC["white_key_length"],
            SPEC["key_height"], r=1.2, segments=2,
            centre=(x, NAT_CY, KEY_Z + SPEC["key_height"] / 2.0), mat=nat))

    # Sharps: A0 is the first key, and the sharps follow the A#-C#-D#-F#-G#-A#
    # pattern of each octave. Each is placed 0.58 of a pitch past its natural so
    # the rows interleave the way a real keyboard does.
    octave_offsets = [0.58, 1.58, 2.58, 4.58, 5.58, 6.58]
    sharps = []
    n = 0
    for o in range(7):
        base = 1.0 + o * 7.0
        for k in octave_offsets:
            u = base + k
            if u >= 52.0:
                continue
            x = -52.0 * PITCH / 2.0 + u * PITCH
            sharps.append(bkit.rounded_box(
                "PianoSharpKey%02d" % n, SPEC["black_key_width"],
                SPEC["black_key_length"], SPEC["key_height"] + 12.0,
                r=1.2, segments=2,
                centre=(x, SHARP_CY, KEY_Z + SPEC["key_height"] + 6.0),
                mat=sharp))
            n += 1
    bkit.join(naturals, name="PianoNaturalKeys")
    bkit.join(sharps, name="PianoSharpKeys")

    # ---- keybed shelf and felt strip --------------------------------------
    bkit.rounded_box("PianoKeyBed", W - 60.0, 300.0, 26.0, r=3.0, segments=2,
                     centre=(0, FRONT - 150.0, KEY_Z - 30.0), mat=case_mat)
    bkit.box("PianoFeltStrip", 52 * PITCH, 12.0, 8.0,
             centre=(0, KEY_FRONT - 6.0, KEY_Z + 40.0), mat=felt)

    # ---- pedal lyre, three pedals, legs, castors -------------------------
    # The lyre and pedals are at the FRONT, below the keyboard: a player faces
    # the front of an upright, which is the same face the keys are cut into.
    bkit.rounded_box("PianoPedalLyre", 150.0, 30.0, 210.0, r=6.0, segments=3,
                     centre=(0, FRONT + 26.0, 130.0), mat=panel)
    pedals = []
    for i, (x, _w) in enumerate(bkit.lay_out([38.0] * 3, gap=18.0)):
        pedals.append(bkit.rounded_box(
            "PianoPedal%d" % i, 38.0, 150.0, 12.0, r=4.0, segments=2,
            centre=(x, FRONT + 76.0, 46.0), mat=brass))
    bkit.join(pedals, name="PianoPedals")

    # Two front legs flanking the keyboard, one central and one at the back.
    for i, (x, y) in enumerate(((-W / 2.0 + 110.0, FRONT - 90.0),
                                (W / 2.0 - 110.0, FRONT - 90.0),
                                (0.0, -D / 2.0 + 90.0))):
        bkit.cylinder("PianoLeg%d" % i, 58.0, KEY_Z + 10.0, segments=24,
                      centre=(x, y, (KEY_Z + 10.0) / 2.0), mat=case_mat)
        bkit.cylinder("PianoCastor%d" % i, 34.0, 26.0, segments=16,
                      centre=(x, y, 34.0), axis="X", mat=brass)

    bkit.rounded_box("PianoTopTrim", W + 20.0, 30.0, 18.0, r=6.0, segments=2,
                     centre=(0, -D / 2.0 + 4.0, H + 8.0), mat=hw)

    return dict(spec=SPEC, parts=12, keys=52 + len(sharps))


CHECKS = [
    dict(name="width", mm=1500.0, tol=1.0, how="bbox_x", part="PianoCase"),
    dict(name="depth", mm=615.0, tol=1.0, how="bbox_y", part="PianoCase"),
    dict(name="height", mm=1250.0, tol=1.5, how="bbox_z", part="PianoCase"),
    dict(name="keyboard_width", mm=1219.0, tol=2.0, how="bbox_x",
         part="PianoNaturalKeys"),
]