"""
poker_chip -- 40 mm x 3.2 mm chip, five in a stack, six edge inlays each.

A poker chip is recognisable by its edge, not its face: the six inlay spots let
you count the stack by eye, and that is the feature a chip is designed around.
So the inlays are the modelled part that matters, one per chip, swept about
that chip's own centre by array_radial -- the one place in this catalog where
getting the array centre wrong is instantly visible, because a chip whose
inlays are off-centre reads as a washer with scratches.

The five chips are five separate objects so they can carry five different
colours, which is also how a real stack alternates. The stack pitch is 3.4 mm
against a 3.2 mm chip: the 0.2 mm gap keeps five coplanar faces from fighting
each other, and it is smaller than you can see.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

R = 20.0                # chip radius (40 mm, a real casino chip)
T = 3.2                 # chip thickness
EDGE_R = 2.2            # edge radius that rounds the rim
STACK_N = 5
STACK_PITCH = 3.4
INLAY_N = 6
INLAY_W = 7.0           # along the circumference
INLAY_T = 1.1           # how far the inlay stands proud of the rim

CHIP_MATS = [
    ("ClayRed", (0.55, 0.08, 0.09)),
    ("ClayIvory", (0.90, 0.88, 0.82)),
    ("ClayGreen", (0.06, 0.28, 0.14)),
    ("ClayBlack", (0.06, 0.06, 0.07)),
    ("ClayBlue", (0.07, 0.13, 0.44)),
]

SPEC = dict(chip_diameter=2.0 * R, chip_thickness=T,
            stack_count=STACK_N, stack_pitch=STACK_PITCH,
            inlay_count=INLAY_N, inlay_width=INLAY_W,
            stack_height=(STACK_N - 1) * STACK_PITCH + T)


def build():
    inlay_mat = bkit.pbr("ChipInlay", base=(0.93, 0.92, 0.88), metal=0.0, rough=0.30)

    # profile of one chip: flat faces, a rounded rim, flat faces
    hw = T / 2.0
    profile = [
        (0.0, -hw), (R - EDGE_R, -hw), (R, -hw + EDGE_R),
        (R, hw - EDGE_R), (R - EDGE_R, hw), (0.0, hw),
    ]

    chips, inlays = [], []
    for i in range(STACK_N):
        name, base = CHIP_MATS[i % len(CHIP_MATS)]
        mat = bkit.pbr("Chip" + name, base=base, metal=0.0, rough=0.42)
        z = T / 2.0 + i * STACK_PITCH
        chip = bkit.lathe("Chip", profile, segments=72, centre=(0.0, 0.0, z), mat=mat)
        chip.name = "Chip%d" % (i + 1)
        chips.append(chip)

        # one inlay on the +X rim, then swept six ways about the chip's centre
        inlay = bkit.rounded_box("ChipInlay", INLAY_T, INLAY_W, T - 0.8, r=0.5,
                                 segments=2, centre=(R - 0.6, 0.0, z), mat=inlay_mat)
        bkit.array_radial(inlay, INLAY_N, centre=(0.0, 0.0, z))
        inlay.name = "Inlays%d" % (i + 1)
        inlays.append(inlay)

    return dict(spec=SPEC, parts=STACK_N * 2)


CHECKS = [
    dict(name="chip_diameter", mm=40.0, tol=0.1, how="diameter", part="Chip1"),
    dict(name="chip_thickness", mm=3.2, tol=0.1, how="bbox_z", part="Chip1"),
    # 2 x inlay width + inlay thickness: the span of one chip's six spots
    dict(name="inlay_band", mm=39.9, tol=0.2, how="bbox_x",
         part="Inlays1"),
    dict(name="stack_height", mm=16.8, tol=0.1, how="bbox_z", part=None),
    dict(name="overall_diameter", mm=40, tol=0.1, how="diameter",
         part=None)
]