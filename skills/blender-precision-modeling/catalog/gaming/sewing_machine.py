"""
sewing_machine -- 400 x 200 x 300 mm domestic machine: bed, pillar, arm, head.

A sewing machine is a C in side view, and the C is made of two boxes -- a
vertical pillar and a horizontal arm -- meeting at one corner. Everything else
sits on that frame: the needle head at the free end of the arm, the handwheel
on the pillar, and the needle plate on the bed under the needle.

The needle bar is a thin cylinder hanging out of the head with the needle below
it, and the presser foot is a small L on the bed. Those two are the parts that
say "sewing machine" from the front, so they get real geometry rather than a
suggestion. The stitch plate is recessed into the bed with an oversized cutter
so the recess has no tangency with the bed's top face.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BED_W, BED_D, BED_H = 400.0, 200.0, 26.0
PILLAR_W, PILLAR_D = 92.0, 150.0
PILLAR_H = 232.0
ARM_W, ARM_D, ARM_H = 250.0, 84.0, 80.0
PILLAR_X = 140.0
ARM_X0 = 30.0
HEAD_W, HEAD_D, HEAD_H = 56.0, 84.0, 112.0
HEAD_X = -30.0
WHEEL_R = 46.0
WHEEL_T = 24.0
WHEEL_X = PILLAR_X + PILLAR_W / 2.0 + WHEEL_T / 2.0 - 6.0
BAR_R, BAR_L = 5.0, 90.0
NEEDLE_R, NEEDLE_L = 1.1, 40.0
FOOT_W, FOOT_D = 26.0, 18.0
PLATE_W, PLATE_D = 70.0, 50.0
ARM_TOP = BED_H + PILLAR_H

SPEC = dict(bed_width=BED_W, bed_depth=BED_D, bed_height=BED_H,
            pillar_height=PILLAR_H, arm_length=ARM_W,
            handwheel_diameter=2.0 * WHEEL_R, needle_bar_diameter=2.0 * BAR_R,
            needle_length=NEEDLE_L, overall_height=ARM_TOP + ARM_H)


def build():
    body = bkit.pbr("MachineBody", base=(0.88, 0.87, 0.84), metal=0.0, rough=0.24,
                    coat=0.6)
    black = bkit.pbr("MachineBlack", base=(0.07, 0.07, 0.08), metal=0.0, rough=0.30)
    steel = bkit.pbr("MachineSteel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.18)
    gold = bkit.pbr("MachineGold", base=(0.92, 0.72, 0.32), metal=0.85, rough=0.22)

    # ---- bed, pillar and arm: the C frame ----------------------------------
    bed = bkit.rounded_box("Bed", BED_W, BED_D, BED_H, r=5.0, segments=3,
                           centre=(0.0, 0.0, BED_H / 2.0), mat=body)
    pillar = bkit.rounded_box("Pillar", PILLAR_W, PILLAR_D, PILLAR_H, r=10.0,
                              segments=4,
                              centre=(PILLAR_X, 0.0, BED_H + PILLAR_H / 2.0),
                              mat=body)
    arm = bkit.rounded_box("Arm", ARM_W, ARM_D, ARM_H, r=12.0, segments=4,
                           centre=(ARM_X0, 0.0, BED_H + PILLAR_H - ARM_H / 2.0),
                           mat=body)
    head = bkit.rounded_box("Head", HEAD_W, HEAD_D, HEAD_H, r=6.0, segments=4,
                            centre=(HEAD_X, 0.0, BED_H + PILLAR_H - HEAD_H / 2.0),
                            mat=body)

    # ---- handwheel on the pillar's outboard face ----------------------------
    wheel = bkit.lathe(
        "Handwheel",
        [(0.0, -WHEEL_T / 2.0), (WHEEL_R - 6.0, -WHEEL_T / 2.0),
         (WHEEL_R, -WHEEL_T / 2.0 + 6.0), (WHEEL_R, WHEEL_T / 2.0 - 6.0),
         (WHEEL_R - 6.0, WHEEL_T / 2.0), (0.0, WHEEL_T / 2.0)],
        segments=56, mat=black)
    wheel.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(wheel, WHEEL_X, 0.0, BED_H + PILLAR_H * 0.62)
    hub = bkit.cylinder("HandwheelHub", 9.0, WHEEL_T + 8.0, segments=24,
                        centre=(WHEEL_X, 0.0, BED_H + PILLAR_H * 0.62), axis="X",
                        mat=gold)

    # ---- needle bar, needle and presser foot --------------------------------
    # The bar hangs out of the head's underside and the needle runs on from the
    # bar's lower end almost to the plate; a bar that stops short leaves a gap
    # and the machine has no needle.
    bar_bottom = BED_H + 45.0
    bar = bkit.cylinder("NeedleBar", BAR_R, BAR_L, segments=20,
                        centre=(HEAD_X, 0.0, bar_bottom + BAR_L / 2.0), mat=steel)
    needle = bkit.cylinder("Needle", NEEDLE_R, NEEDLE_L, segments=12,
                           centre=(HEAD_X, 0.0, bar_bottom - NEEDLE_L / 2.0 + 3.0),
                           mat=steel)
    foot = bkit.rounded_box("PresserFoot", FOOT_W, FOOT_D, 5.0, r=1.5, segments=2,
                            centre=(HEAD_X, -18.0, BED_H + 2.5), mat=steel)

    # ---- needle plate recessed into the bed --------------------------------
    plate = bkit.rounded_box("NeedlePlate", PLATE_W, PLATE_D, 6.0, r=3.0, segments=2,
                             centre=(HEAD_X, -6.0, BED_H - 1.0), mat=steel)
    recess = bkit.rounded_box("_recess", PLATE_W - 2.0, PLATE_D - 2.0, 12.0, r=2.0,
                              segments=2, centre=(HEAD_X, -6.0, BED_H + 1.0))
    bkit.boolean(bed, recess, "DIFFERENCE")

    # ---- the balance wheel, outboard of the pillar --------------------------
    balance = bkit.cylinder("BalanceWheel", 30.0, 8.0, segments=40,
                            centre=(HEAD_X - 6.0, -PILLAR_D / 2.0 - 6.0,
                                    BED_H + 150.0), axis="Y", mat=gold)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="bed_width", mm=400.0, tol=0.2, how="bbox_x", part="Bed"),
    dict(name="bed_depth", mm=200.0, tol=0.2, how="bbox_y", part="Bed"),
    dict(name="bed_height", mm=26.0, tol=0.2, how="bbox_z", part="Bed"),
    dict(name="pillar_height", mm=232.0, tol=0.2, how="bbox_z", part="Pillar"),
    dict(name="arm_length", mm=250.0, tol=0.2, how="bbox_x", part="Arm"),
    dict(name="handwheel", mm=92.0, tol=0.2, how="diameter", part="Handwheel"),
    dict(name="needle_length", mm=40, tol=0.2, how="bbox_z",
         part="Needle"),
    dict(name="overall_height", mm=258, tol=0.3, how="bbox_z",
         part=None)
]