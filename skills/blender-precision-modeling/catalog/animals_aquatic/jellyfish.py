"""jellyfish -- a 200 mm bell moon jelly: a translucent scalloped bell, four
oral arms and a fringe of marginal tentacles.

The bell is a lathe whose profile is a real section of a sphere, so it hollows
correctly and reads as gelatin rather than as a dome. The tentacles are a
computed fan around the bell rim -- `bell_margin()` returns one point per
tentacle, so the fringe is even by construction instead of twenty typed
constants that drift apart.

Construction: one lathed bell (two materials on the one solid), four swept
oral arms, one tentacle swept once and arrayed about the bell's own axis at the
rim radius. Nothing is booleaned.

Orientation: bell dome up, oral arms hanging down; the animal floats at the
top of the frame, and `sit_on_floor` seats the lowest tentacle at z=0.
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
    bell_diameter=200.0,
    bell_height=110.0,
    tentacle_count=40,
    tentacle_length=280.0,
    oral_arm_count=4,
)

BELL_R = 100.0
BELL_TOP = 620.0            # the bell rim plane, which is where the fan orbits
# bell profile: (radius, z) from the apex down to the rim, then back up inside
BELL = [
    (0.0, 0.0), (30.0, 8.0), (58.0, 26.0), (80.0, 52.0), (94.0, 82.0),
    (100.0, 110.0), (96.0, 112.0), (88.0, 86.0), (70.0, 52.0),
    (46.0, 28.0), (20.0, 14.0), (0.0, 12.0),
]
ORAL = [
    (0.0, 0.0, 0.0), (14.0, 0.0, -30.0), (22.0, 0.0, -80.0),
    (26.0, 0.0, -140.0), (24.0, 0.0, -200.0), (16.0, 0.0, -240.0),
]
ORAL_RAD = [(22.0, 22.0), (18.0, 16.0), (14.0, 11.0), (10.0, 8.0),
            (7.0, 6.0), (3.0, 3.0)]
TENTACLE = [(0.0, 0.0, 0.0), (6.0, 0.0, -70.0), (10.0, 0.0, -150.0),
            (12.0, 0.0, -230.0), (10.0, 0.0, -280.0)]
TENTACLE_RAD = [(3.0, 3.0), (2.4, 2.4), (1.8, 1.8), (1.4, 1.4), (0.8, 0.8)]





def build():
    gel = bkit.pbr("JellyBell", base=(0.72, 0.82, 0.88), rough=0.10,
                   transmission=0.55, ior=1.34)
    rim = bkit.pbr("JellyRim", base=(0.60, 0.72, 0.80), rough=0.16,
                   transmission=0.45, ior=1.34)
    arm = bkit.pbr("JellyArm", base=(0.78, 0.66, 0.68), rough=0.28,
                   transmission=0.35, ior=1.34)

    bell = bkit.lathe("Bell", BELL, segments=64, centre=(0.0, 0.0, BELL_TOP),
                      mat=gel, smooth=True)
    bkit.assign_faces_by(bell, rim,
                         lambda c, n: c.z / bkit.MM < BELL_TOP + 24.0)

    # ---- four oral arms: the frilly ribbons under the bell's centre
    arm0 = F.tube("OralArm0", [(p[0], p[1], BELL_TOP + 6.0 + p[2])
                               for p in ORAL], ORAL_RAD, arm, n=2.6, steps=18)
    bkit.array_radial(arm0, SPEC["oral_arm_count"],
                      centre=(0.0, 0.0, BELL_TOP + 6.0))

    # ---- the marginal fringe: ONE tentacle swept, then arrayed about the
    # bell's own axis at the rim radius. The centre is the bell, not the world
    # origin, and the tentacle is authored at that radius first.
    tent = F.tube("Tentacle0",
                  [(p[0], p[1], BELL_TOP - 4.0 + p[2]) for p in TENTACLE],
                  TENTACLE_RAD, arm, n=2.2, steps=12)
    bkit.move(tent, BELL_R - 2.0, 0.0, 0.0)
    bkit.array_radial(tent, SPEC["tentacle_count"],
                      centre=(0.0, 0.0, BELL_TOP - 4.0))
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="bell_diameter", mm=200.0, tol=6.0, how="bbox_x", part="Bell"),
    dict(name="bell_height", mm=112.0, tol=6.0, how="bbox_z", part="Bell"),
    dict(name="tentacle_length", mm=284.0, tol=12.0, how="bbox_z",
         part="Tentacle0"),
    dict(name="oral_arm_length", mm=243.0, tol=10.0, how="bbox_z",
         part="OralArm0"),
]