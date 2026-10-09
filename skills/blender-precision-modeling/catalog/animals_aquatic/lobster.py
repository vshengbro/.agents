"""lobster -- a 380 mm American lobster: segmented abdomen, a fanned tail, two
massive crusher claws, four pairs of walking legs, and long antennae.

The abdomen is the other count that fails after arms and legs. Six segments is
a shrimp; a lobster has six abdominal segments PLUS the telson, and here the
segment count is a real table length with a real per-segment length, which is
what makes the body read as articulated rather than as one tapered tube.

Construction: a lathed carapace, six swept abdominal plates stepped along Y at
a derived pitch, a five-blade tail fan built from one authored blade rotated in
equal steps, two mirrored claw arms with two-part chelae, and eight arrayed
walking legs about the body axis.

Orientation: head at -Y, tail at +Y, X lateral, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=425.0,
    carapace_length=150.0,
    carapace_width=76.0,
    abdomen_segments=6,
    abdomen_pitch=26.0,
    tail_fan_span=55.0,
    leg_count=8,
    claw_length=95.0,
)

CENTRE = (0.0, 10.0, 60.0)        # body axis the walking legs orbit
# one walking leg, authored on +X
LEG = [
    (26.0, 0.0, 60.0),
    (52.0, 14.0, 52.0),
    (74.0, 30.0, 30.0),
    (86.0, 44.0, 8.0),
]
LEG_RAD = [(6.0, 6.0), (5.0, 5.0), (3.5, 3.5), (1.5, 1.5)]
# the abdomen: SIX segments of a derived pitch, tapering as real ones do
ABDOMEN_N = 6
ABDOMEN_PITCH = 26.0
ABDOMEN_W = [34.0, 32.0, 29.0, 25.0, 21.0, 17.0]
ABDOMEN_H = [26.0, 24.0, 22.0, 19.0, 16.0, 13.0]
# one tail-fan blade, rotated about the telson joint in equal steps
FAN = [(0.0, 0.0), (26.0, -18.0), (52.0, -14.0), (60.0, -3.0), (30.0, 6.0)]
FAN_SPREAD = 22.0
CLAWARM = [
    (0.0, -70.0, 60.0),
    (22.0, -100.0, 52.0),
    (34.0, -128.0, 42.0),
]
CLAWARM_RAD = [(11.0, 11.0), (10.0, 10.0), (12.0, 12.0)]


def build():
    shell = bkit.pbr("LobsterShell", base=(0.40, 0.10, 0.07), rough=0.40,
                     coat=0.25)
    pale = bkit.pbr("LobsterPale", base=(0.80, 0.62, 0.52), rough=0.46)
    clawm = bkit.pbr("LobsterClaw", base=(0.46, 0.13, 0.09), rough=0.36,
                     coat=0.3)
    dark = bkit.pbr("LobsterAntenna", base=(0.16, 0.06, 0.05), rough=0.42)
    eye = bkit.pbr("LobsterEye", base=(0.02, 0.02, 0.025), rough=0.08)

    # ---- carapace: a lathed tube, then squashed laterally like a real one
    cara = bkit.lathe("Carapace",
                      [(0.0, 0.0), (22.0, 4.0), (36.0, 26.0), (38.0, 90.0),
                       (30.0, 138.0), (0.0, 150.0)],
                      segments=44, centre=(0.0, 0.0, 60.0), mat=shell)
    F.bake_rot(cara, "X", -90.0)
    bkit.move(cara, 0.0, -70.0, 0.0)

    F.cone_between("Rostrum", (0.0, -74.0, 62.0), (0.0, -96.0, 60.0),
                   9.0, 2.0, seg=12, mat=shell)

    # ---- abdomen: six plates at a derived pitch. The per-segment length is
    # what makes this read as an articulated lobster rather than a cone.
    for i in range(ABDOMEN_N):
        y0 = 6.0 + i * ABDOMEN_PITCH
        F.tube("Abdomen%d" % (i + 1),
               [(0.0, y0, 60.0), (0.0, y0 + ABDOMEN_PITCH * 0.5, 60.0),
                (0.0, y0 + ABDOMEN_PITCH + 3.0, 60.0)],
               [(ABDOMEN_W[i], ABDOMEN_H[i]),
                (ABDOMEN_W[i] * 0.97, ABDOMEN_H[i] * 0.97),
                (ABDOMEN_W[i + 1] * 0.95 if i + 1 < ABDOMEN_N
                 else ABDOMEN_W[i] * 0.8,
                 (ABDOMEN_H[i + 1] if i + 1 < ABDOMEN_N
                  else ABDOMEN_H[i] * 0.8) * 0.95)],
               shell, n=2.4, steps=24)
        # a second material on the one plate: the pale membrane between segments
        bkit.assign_faces_by(
            bpy.data.objects["Abdomen%d" % (i + 1)], pale,
            lambda c, n: c.y / bkit.MM > y0 + ABDOMEN_PITCH * 0.72)

    # ---- tail fan: five blades from ONE authored blade outline, rotated in
    # equal steps about the telson joint. Each blade is its own closed solid:
    # array_radial would work too, but a radial array of a 60 mm blade about a
    # 12 mm radius sweeps copies over each other, and the fan's blades overlap
    # by design.
    joint_y = 6.0 + ABDOMEN_N * ABDOMEN_PITCH - 6.0
    for k in range(5):
        blade = F.plate_xy("TailBlade%d" % k, FAN, 5.0, mat=shell)
        # the fan spreads by rotating the authored blade in equal steps about
        # the telson joint -- a computed rotation, never five hand-placed
        # outlines that would drift apart
        F.bake_rot(blade, "Z", -FAN_SPREAD + k * FAN_SPREAD)
        bkit.move(blade, 0.0, joint_y, 60.0)

    telson = F.plate_yz("Telson", [(0.0, 0.0), (46.0, -8.0), (52.0, 0.0),
                                   (46.0, 8.0)], 12.0, x=0.0, mat=shell)
    bkit.move(telson, 0.0, joint_y + 2.0, 60.0)
    F.bake_rot(telson, "Y", -90.0)

    # ---- eight walking legs about the body axis
    leg = F.tube("Leg0", LEG, LEG_RAD, shell, n=2.2, steps=14)
    bkit.array_radial(leg, SPEC["leg_count"], centre=CENTRE)

    # ---- two crusher claws: forearm, palm, fixed finger, moving finger
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.tube("ClawArm%s" % side,
               [(sx * p[0], p[1], p[2]) for p in CLAWARM],
               CLAWARM_RAD, clawm, n=2.4, steps=16)
        bkit.uv_sphere("Palm%s" % side, 17.0, segments=24, rings=12,
                       centre=(sx * 36.0, -132.0, 42.0), mat=clawm)
        F.tube("FingerFixed%s" % side,
               [(sx * 38.0, -142.0, 42.0), (sx * 42.0, -162.0, 40.0),
                (sx * 44.0, -180.0, 38.0)],
               [(7.0, 6.0), (4.5, 4.0), (2.0, 2.0)], clawm, n=2.4, steps=12)
        F.tube("FingerMove%s" % side,
               [(sx * 32.0, -144.0, 44.0), (sx * 33.0, -164.0, 44.0),
                (sx * 33.0, -182.0, 43.0)],
               [(6.0, 5.0), (4.0, 3.6), (1.8, 1.8)], pale, n=2.4, steps=12)

        # ---- antennae: two long whips, swept out and back
        F.tube("Antenna%s" % side,
               [(sx * 12.0, -92.0, 66.0), (sx * 26.0, -130.0, 80.0),
                (sx * 34.0, -175.0, 92.0), (sx * 38.0, -215.0, 96.0)],
               [(3.2, 3.2), (2.4, 2.4), (1.6, 1.6), (0.9, 0.9)],
               dark, n=2.2, steps=12)
        bkit.uv_sphere("Eye%s" % side, 4.5, segments=16, rings=8,
                       centre=(sx * 15.0, -88.0, 76.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=30)


CHECKS = [
    dict(name="overall_length", mm=425.0, tol=25.0, how="bbox_y"),
    dict(name="carapace_length", mm=150.0, tol=8.0, how="bbox_y",
         part="Carapace"),
    dict(name="carapace_width", mm=76.0, tol=5.0, how="bbox_x",
         part="Carapace"),
    dict(name="abdomen_pitch", mm=29.0, tol=4.0, how="bbox_y",
         part="Abdomen1"),
    dict(name="tail_fan_span", mm=55.0, tol=8.0, how="bbox_x",
         part="TailBlade0"),
    dict(name="leg_span", mm=172.0, tol=10.0, how="bbox_x", part="Leg0"),
]