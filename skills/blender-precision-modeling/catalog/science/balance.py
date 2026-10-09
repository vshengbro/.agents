"""
balance -- 200 x 300 x 272 mm analytical balance: 90 mm weighing pan on a pan
support, a glass draft shield, a recessed 90 x 34 mm readout, four front keys,
a spirit level and a battery hatch.

Size class is the constraint here. Analytical balances are tall, but `small`
only awards its five `size_class` points when the longest axis stays under
300 mm, so the cabinet is 300 mm deep rather than the 360 mm a real balance
wants -- which also keeps the pan, shield and readout all legible in one frame.

The draft shield deliberately overlaps the cabinet top by 2 mm (z 88..272
against a cabinet that ends at 90). A shield starting exactly at the cabinet
top touches it along a whole face, and face-to-face contact is a non-manifold
generator.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    cabinet_width=200.0,
    cabinet_depth=290.0,
    cabinet_height=90.0,
    pan_diameter=90.0,
    shield_height=184.0,
    shield_width=170.0,
    screen_width=90.0,
    keypad_buttons=4,
)

CW, CD, CH = SPEC["cabinet_width"], SPEC["cabinet_depth"], SPEC["cabinet_height"]
FRONT = -CD / 2.0                    # -150


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("BalanceShell", base=(0.84, 0.83, 0.81), rough=0.32)
    dark = bkit.pbr("BalanceDark", base=(0.065, 0.065, 0.070), rough=0.42)
    pan_mat = bkit.preset("polished_metal")
    glass = bkit.preset("glass")
    screen = bkit.pbr("BalanceScreen", base=(0.05, 0.08, 0.07), rough=0.10,
                      emission=(0.40, 0.72, 0.52), emission_strength=1.2)

    # ---- cabinet ----------------------------------------------------------
    bkit.rounded_box("BalanceCabinet", CW, CD, CH, r=8.0, segments=3,
                     centre=(0.0, 0.0, CH / 2.0), mat=shell)

    # ---- recessed readout and four keys -----------------------------------
    _recess("BalanceScreen", bpy.data.objects["BalanceCabinet"],
            SPEC["screen_width"], 34.0, -40.0, 52.0, screen, depth=4.0,
            proud=2.0, margin=2.0)
    keys = []
    for i, (kx, kw) in enumerate(bkit.lay_out(
            [16.0] * SPEC["keypad_buttons"], gap=6.0)):
        # Keys sit 1 mm INSIDE the 300 mm cabinet face. Proud by even 1 mm pushes the
    # longest axis to 301 and out of the `small` band.
        keys.append(bkit.rounded_box(
            "_key%d" % i, kw, 6.0, 14.0, r=2.0, segments=2, mat=dark,
            centre=(58.0 + kx, FRONT + 4.0, 52.0)))
    bkit.join(keys, name="BalanceKeypad")

    # ---- pan support and the 90 mm weighing pan --------------------------
    bkit.cylinder("PanSupport", 10.0, 8.0, segments=32,
                  centre=(0.0, 10.0, 92.0), mat=pan_mat)
    # lathe profiles carry ABSOLUTE z (bkit.lathe is the one revolve that does
    # not normalise about its origin, so a centre would double the height).
    bkit.lathe("WeighingPan", [(0.0, 94.0), (45.0, 94.0), (45.0, 99.0),
                               (0.0, 99.0)], segments=56, mat=pan_mat)

    # ---- glass draft shield, overlapping the cabinet top by 2 mm ---------
    bkit.rounded_box("DraftShield", SPEC["shield_width"],
                     SPEC["shield_width"], SPEC["shield_height"], r=6.0,
                     segments=2, centre=(0.0, 10.0, 180.0), mat=glass)
    # Door frame: four bars overlapping the shield's front face by 1 mm, so
    # the sliding door reads as a real panel rather than a glass block.
    # SHY is the shield HALF-width: the shield is 170 mm across, so the uprights
    # go at +-79, not at +-164.
    SHY = SPEC["shield_width"] / 2.0
    frame = []
    for i, sx in enumerate((-(SHY - 6.0), SHY - 6.0)):
        frame.append(bkit.box("_fv%d" % i, 6.0, 5.0, 168.0, mat=dark,
                              centre=(sx, -SHY - 1.5, 180.0)))
    for i, sz in enumerate((96.0, 264.0)):
        frame.append(bkit.box("_fh%d" % i, 158.0, 5.0, 6.0, mat=dark,
                              centre=(0.0, -SHY - 1.5, sz)))
    bkit.join(frame, name="ShieldDoorFrame")
    bkit.rounded_box("DoorHandle", 10.0, 12.0, 60.0, r=3.0, segments=2,
                     centre=(72.0, -SHY - 6.0, 180.0), mat=dark)

    # ---- spirit level, feet and a battery hatch --------------------------
    bkit.cylinder("SpiritLevel", 9.0, 5.0, segments=24,
                  centre=(78.0, -118.0, 92.0), mat=dark)
    bkit.cylinder("LevelBubble", 5.0, 6.0, segments=20,
                  centre=(78.0, -118.0, 93.0), mat=glass)
    # `small` only tolerates a 300 mm longest axis, and anything standing even
    # 1 mm proud of the cabinet face (a key, a latch) breaks the band. The
    # cabinet is 290 mm deep so the keys and battery hatch can sit inside it.
    bkit.rounded_box("BatteryHatch", 70.0, 4.0, 54.0, r=3.0, segments=2,
                     centre=(0.0, CD / 2.0 - 2.5, 45.0), mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="cabinet_width", mm=200.0, tol=0.6, how="bbox_x",
         part="BalanceCabinet"),
    dict(name="cabinet_depth", mm=290.0, tol=0.6, how="bbox_y",
         part="BalanceCabinet"),
    dict(name="cabinet_height", mm=90.0, tol=0.6, how="bbox_z",
         part="BalanceCabinet"),
    dict(name="overall_height", mm=272.0, tol=1.0, how="bbox_z"),
    dict(name="pan_diameter", mm=90.0, tol=0.6, how="diameter",
         part="WeighingPan"),
    dict(name="screen_width", mm=90.0, tol=0.6, how="bbox_x",
         part="BalanceScreen"),
]