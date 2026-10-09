"""
stethoscope -- laid flat the way one is set down after use: a 116 mm loop of
tube, a 46 mm chest piece, and the two binaural arms with their ear tips.

The binaural arms need a circular arc through two known points, so the arc is
solved rather than guessed: from a chord and a sagitta the centre radius is
R = (s^2 + (d/2)^2)/2s, and the sweep is ordered so the arc bulges on the side
asked for. Everything is planar (XY) and lies on the floor, which is what makes
the top shot read as a stethoscope.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    tube_loop_diameter=116.0,    # outside of the main tubing loop
    tube_diameter=6.4,
    chestpiece_diameter=46.0,
    chestpiece_height=13.0,
    binaural_span=34.0,          # ear tip to ear tip
    ear_tip_diameter=13.0,
)

LOOP_R = SPEC["tube_loop_diameter"] / 2.0 - SPEC["tube_diameter"] / 2.0  # 54.8
TUBE_R = SPEC["tube_diameter"] / 2.0        # 3.2
CP_R = SPEC["chestpiece_diameter"] / 2.0    # 23.0
BIN_R = 2.7
GAP_A, GAP_B = 78.0, 436.0                  # loop sweep: a 2 deg gap at the top
SPLIT_A = 77.0                              # mid-gap, where the arms branch


def arc_between(name, p0, p1, sagitta, tube_r, seg=28, mat=None):
    """A capped tube on the XY-plane arc p0 -> p1, bulging `sagitta` to the left
    of the chord (the normal of p0->p1). Solved, not eyeballed:
    R = (s^2 + (d/2)^2) / (2s)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy)
    nx, ny = -dy / d, dx / d
    r_major = (sagitta ** 2 + (d / 2.0) ** 2) / (2.0 * sagitta)
    cx = (p0[0] + p1[0]) / 2.0 - nx * (r_major - sagitta)
    cy = (p0[1] + p1[1]) / 2.0 - ny * (r_major - sagitta)
    a0 = math.degrees(math.atan2(p0[1] - cy, p0[0] - cx))
    a1 = math.degrees(math.atan2(p1[1] - cy, p1[0] - cx))
    apex_a = math.degrees(math.atan2((p0[1] + p1[1]) / 2.0 + ny * sagitta - cy,
                                     (p0[0] + p1[0]) / 2.0 + nx * sagitta - cx))
    if not ((apex_a - a0) % 360.0) < ((a1 - a0) % 360.0):
        a0, a1 = a1, a0
    return bkit.arc_torus(name, r_major, tube_r, a0, a1,
                          centre=(cx, cy, p0[2]), plane="XY",
                          seg_major=seg, seg_minor=16, mat=mat)


def build():
    tube = bkit.pbr("StethoTube", base=(0.055, 0.055, 0.062), rough=0.55)
    steel = bkit.pbr("StethoSteel", base=(0.74, 0.76, 0.79), metal=0.80,
                     rough=0.22)
    bell = bkit.pbr("StethoBell", base=(0.80, 0.81, 0.83), metal=0.55,
                    rough=0.34)
    rubber = bkit.preset("rubber")

    # ---- main tube loop: one arc, 2 deg short of closed --------------------
    bkit.arc_torus("StethoMainTube", LOOP_R, TUBE_R, GAP_A, GAP_B,
                   centre=(0.0, 0.0, TUBE_R), plane="XY", seg_major=120,
                   seg_minor=16, mat=tube)

    # ---- the Y boss that hides the split where the loop closes -------------
    # Radius 3.2 keeps it exactly tangent to the floor: anything that dips
    # below z=0 makes sit_on_floor lift the whole assembly and silently adds its
    # depth to every height in the report.
    boss = (math.cos(math.radians(SPLIT_A)) * LOOP_R,
            math.sin(math.radians(SPLIT_A)) * LOOP_R, TUBE_R)
    bkit.uv_sphere("StethoYBoss", 3.2, segments=32, rings=16,
                   centre=boss, mat=tube)

    # ---- chest piece: bell, bezel, diaphragm ------------------------------
    cp_y = -LOOP_R - CP_R + 6.0        # 6 mm of overlap onto the loop
    bkit.cylinder("ChestpieceBell", CP_R, SPEC["chestpiece_height"], segments=64,
                  centre=(0.0, cp_y, SPEC["chestpiece_height"] / 2.0),
                  mat=bell)
    bkit.torus("ChestpieceBezel", CP_R - 1.6, 1.7, seg_major=64, seg_minor=16,
               centre=(0.0, cp_y, SPEC["chestpiece_height"] - 1.7), mat=steel)
    bkit.cylinder("ChestpieceDiaphragm", CP_R - 3.2, 1.2, segments=64,
                  centre=(0.0, cp_y, SPEC["chestpiece_height"] - 0.6),
                  mat=rubber)

    # ---- binaural arms and ear tips, mirrored about the split --------------
    tip_r = SPEC["ear_tip_diameter"] / 2.0
    span = SPEC["binaural_span"] / 2.0
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        tip = (boss[0] + sgn * span, boss[1] + 24.0, BIN_R)
        arc_between("StethoBinaural" + side, boss, tip, 8.0, BIN_R,
                    seg=24, mat=steel)
        bkit.lathe("StethoEarTip" + side, [
            (0.0, 0.0), (tip_r - 2.0, 0.0), (tip_r, 2.4),
            (tip_r, 11.0), (tip_r - 2.4, 13.0), (0.0, 13.0),
        ], segments=40, centre=(tip[0], tip[1] + 5.0, 0.0), mat=rubber)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    # The 116 mm loop is the widest thing in the assembly, so the scene's own
    # bounding box in X measures it directly.
    dict(name="tube_loop_diameter", mm=116.0, tol=0.6, how="bbox_x"),
    dict(name="chestpiece_diameter", mm=46.0, tol=0.3, how="diameter",
         part="ChestpieceBell"),
    dict(name="chestpiece_height", mm=13.0, tol=0.3, how="bbox_z",
         part="ChestpieceBell"),
    dict(name="overall_height", mm=13.0, tol=0.3, how="bbox_z"),
]