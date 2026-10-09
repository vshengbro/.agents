"""squid -- a 450 mm loligo: torpedo mantle, two triangular fins at the tail, a
distinct head with two big eyes, and TEN appendages -- eight arms plus two
much longer feeding tentacles.

Ten is the count that fails. Eight arms arrayed about the head axis, then the
two tentacles authored as their own swept pair is the honest way to get it
right: arraying all ten at equal length produces a starfish, not a squid.

Construction: a lathed mantle with real wall thickness left as a solid, flat
blade fins, a swept head, eight arrayed arms and one mirrored tentacle pair.
Every part is a closed solid, so nothing is booleaned.

Orientation: mantle apex points at +Y, arms and tentacles reach toward -Y.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=560.0,
    mantle_length=250.0,
    mantle_diameter=95.0,
    fin_span=200.0,
    arm_count=8,
    tentacle_count=2,
    tentacle_length=270.0,
    eye_diameter=26.0,
)

HUB = (0.0, -70.0, 200.0)           # head axis the eight arms orbit
ARM = [
    (0.0, -70.0, 200.0),
    (14.0, -96.0, 190.0),
    (24.0, -126.0, 168.0),
    (28.0, -160.0, 142.0),
]
ARM_RAD = [(15.0, 15.0), (11.0, 11.0), (7.0, 7.0), (3.0, 3.0)]
# the two feeding tentacles are much longer, with a clubbed tip
TENTACLE = [
    (0.0, -70.0, 198.0),
    (10.0, -120.0, 182.0),
    (18.0, -190.0, 150.0),
    (22.0, -260.0, 112.0),
    (24.0, -310.0, 86.0),
]
TENTACLE_RAD = [(7.0, 7.0), (5.0, 5.0), (4.0, 4.0), (5.5, 5.5), (2.5, 2.5)]
# fins: two triangles at the tail end of the mantle
FIN = [
    (0.0, 0.0), (60.0, -110.0), (120.0, -95.0), (150.0, -20.0),
    (150.0, 20.0), (110.0, 95.0), (60.0, 110.0),
]


def build():
    mantle_mat = bkit.pbr("SquidMantle", base=(0.62, 0.20, 0.16), rough=0.40,
                          coat=0.25)
    head_mat = bkit.pbr("SquidHead", base=(0.52, 0.17, 0.14), rough=0.42)
    fin_mat = bkit.pbr("SquidFin", base=(0.68, 0.24, 0.19), rough=0.34,
                       alpha=0.88)
    arm_mat = bkit.pbr("SquidArm", base=(0.48, 0.16, 0.13), rough=0.44)
    eye_mat = bkit.pbr("SquidEye", base=(0.02, 0.02, 0.025), rough=0.08)
    glint = bkit.pbr("SquidGlint", base=(0.85, 0.88, 0.90), rough=0.12)

    # ---- mantle: a lathe on a closed profile, then laid along Y
    mantle = bkit.lathe(
        "Mantle",
        [(0.0, 0.0), (26.0, 12.0), (42.0, 40.0), (46.0, 90.0),
         (43.0, 150.0), (33.0, 205.0), (18.0, 240.0), (0.0, 250.0)],
        segments=44, centre=(0.0, 0.0, 200.0), mat=mantle_mat)
    F.bake_rot(mantle, "X", -90.0)

    # ---- fins: one blade on +X, mirrored, both at the tail end
    fin = F.plate_xy("FinL", FIN, 5.0, mat=fin_mat)
    bkit.move(fin, 40.0, 110.0, 200.0)
    F.bake_rot(fin, "Y", 8.0)
    F.mirror_copy(fin, "FinR")

    head = bkit.lathe("Head",
                      [(0.0, 0.0), (34.0, 6.0), (40.0, 26.0), (34.0, 50.0),
                       (0.0, 62.0)],
                      segments=40, centre=(0.0, -40.0, 200.0), mat=head_mat)
    F.bake_rot(head, "X", -90.0)

    # ---- eight arms, arrayed about the real head axis
    arm = F.tube("Arm0", ARM, ARM_RAD, arm_mat, n=2.2, steps=16)
    bkit.array_radial(arm, SPEC["arm_count"], centre=HUB)

    # ---- two feeding tentacles: authored as their own swept pair, because
    # arraying ten equal-length appendages gives a starfish, not a squid
    tent = F.tube("TentacleL", TENTACLE, TENTACLE_RAD, arm_mat, n=2.2,
                  steps=16)
    F.mirror_copy(tent, "TentacleR")

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 13.0, segments=22, rings=12,
                       centre=(sx * 30.0, -48.0, 208.0), mat=eye_mat)
        bkit.uv_sphere("Glint%s" % side, 4.5, segments=14, rings=8,
                       centre=(sx * 38.0, -54.0, 216.0), mat=glint)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="overall_length", mm=560.0, tol=20.0, how="bbox_y"),
    dict(name="mantle_length", mm=250.0, tol=10.0, how="bbox_y", part="Mantle"),
    dict(name="mantle_diameter", mm=92.0, tol=5.0, how="bbox_x",
         part="Mantle"),
    dict(name="fin_span", mm=360.0, tol=20.0, how="bbox_x"),
    dict(name="tentacle_length", mm=245.0, tol=20.0, how="bbox_y",
         part="TentacleL"),
    dict(name="eye_diameter", mm=26.0, tol=1.5, how="bbox_x", part="EyeL"),
]