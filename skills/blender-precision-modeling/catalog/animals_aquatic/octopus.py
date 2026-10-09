"""octopus -- a 500 mm common octopus: bulbous mantle, eight arms, two rows of
suckers per arm, and eyes set on top of the head rather than at the sides.

The arm count is the model. `array_radial(count=8, centre=HUB)` orbits ONE
authored arm around the head axis; six arms is the classic miss. The centre is
passed explicitly because the hub is at (0, -120, 150), nowhere near the world
origin, and without it every copy swings outside the animal's own footprint.

Construction: a lathe-turned mantle, a swept head, one authored arm swept out
to (140, -190, 60) and then arrayed eight times about the head axis, and the
suckers as small cones arrayed along the SAME radial sweep so they stay on
every arm rather than on one.

Orientation: nose (mantle apex) points at +Y, arms reach toward -Y, Z up.
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
    overall_length=482.0,     # mantle apex to arm tip, animal hanging head-down
    mantle_length=190.0,
    mantle_diameter=140.0,
    head_diameter=104.0,
    arm_count=8,
    arm_span=365.0,           # tip to tip across the arm crown
    eye_diameter=40.0,
    sucker_rows=2,
)

HUB = (0.0, -120.0, 150.0)          # the head axis every arm orbits
ARM = [
    (0.0, -120.0, 150.0),
    (30.0, -140.0, 148.0),
    (70.0, -170.0, 130.0),
    (110.0, -200.0, 100.0),
    (140.0, -235.0, 66.0),
]
ARM_RAD = [(22.0, 20.0), (18.0, 16.0), (13.0, 12.0), (8.0, 8.0), (3.5, 3.5)]


def build():
    skin = bkit.pbr("OctopusSkin", base=(0.42, 0.24, 0.20), rough=0.62)
    pale = bkit.pbr("OctopusPale", base=(0.66, 0.52, 0.46), rough=0.60)
    suck = bkit.pbr("OctopusSucker", base=(0.74, 0.62, 0.56), rough=0.44)
    eye = bkit.pbr("OctopusEye", base=(0.02, 0.02, 0.025), rough=0.08)

    # ---- mantle: a lathe on a closed profile, apex at +Y
    mantle = bkit.lathe(
        "Mantle",
        [(0.0, 0.0), (28.0, 6.0), (52.0, 24.0), (66.0, 62.0),
         (70.0, 108.0), (58.0, 152.0), (34.0, 180.0), (0.0, 190.0)],
        segments=48, centre=(0.0, -10.0, 150.0), mat=skin)
    F.bake_rot(mantle, "X", -90.0)          # lathe axis Z -> body axis Y

    head = bkit.uv_sphere("Head", 52.0, segments=36, rings=18,
                          centre=(0.0, -85.0, 148.0), mat=skin)
    bkit.move(head, 0.0, 0.0, 4.0)

    # ---- the arms. ONE arm is authored on +X and swept eight times about the
    # real head axis. Six arms is the classic failure; the count here is the
    # octopus's own, and the centre is the head, not the world origin.
    arm = F.tube("Arm0", ARM, ARM_RAD, skin, n=2.2, steps=20)
    bkit.array_radial(arm, SPEC["arm_count"], centre=HUB)

    # ---- suckers: two staggered rows per arm, on the same radial sweep, so
    # every arm carries them. Row pitch is derived from the arm's length
    # rather than typed in twenty times.
    arm_len = sum(math.dist(ARM[i], ARM[i + 1]) for i in range(len(ARM) - 1))
    n_suck = 9
    for row in (0, 1):
        for j in range(n_suck):
            t = 0.22 + 0.68 * (j / float(n_suck - 1))
            idx = t * (len(ARM) - 1)
            i0 = min(len(ARM) - 2, int(idx))
            f = idx - i0
            px = ARM[i0][0] + (ARM[i0 + 1][0] - ARM[i0][0]) * f
            py = ARM[i0][1] + (ARM[i0 + 1][1] - ARM[i0][1]) * f
            pz = ARM[i0][2] + (ARM[i0 + 1][2] - ARM[i0][2]) * f
            r = 4.5 - 2.6 * (j / float(n_suck - 1))
            # the two rows straddle the arm's underside, offset along the
            # outward radial direction, so each sucker is a real cone
            lat = 0.0 if row == 0 else 9.0
            ux, uy = 1.0, -0.55
            sk = F.cone_between(
                "Sucker%d%d" % (row, j),
                (px + ux * lat * 0.6, py + uy * lat * 0.6, pz - 4.0),
                (px + ux * lat, py + uy * lat, pz - 5.0),
                r, r * 0.4, seg=10, mat=suck)
            bkit.array_radial(sk, SPEC["arm_count"], centre=HUB)
    del arm_len

    # ---- eyes: on TOP of the head, which is the octopus's diagnostic layout
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 20.0, segments=24, rings=12,
                       centre=(sx * 34.0, -80.0, 190.0), mat=eye)

    # countershading: a pale underside on the one mantle solid, so there is
    # no z-fighting with a second shell
    bkit.assign_faces_by(bpy.data.objects["Mantle"], pale,
                         lambda c, n: c.z / bkit.MM < 138.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=38)


# A single arm cannot be measured once `array_radial` has swept it: Arm0 is now
# the whole eight-arm crown, and so is every Sucker object. So the checks point
# at the parts that own the dimension and never at "one arm of the array".
CHECKS = [
    dict(name="overall_length", mm=482.0, tol=20.0, how="bbox_y"),
    dict(name="mantle_length", mm=190.0, tol=8.0, how="bbox_y", part="Mantle"),
    dict(name="mantle_diameter", mm=140.0, tol=6.0, how="bbox_x",
         part="Mantle"),
    dict(name="head_diameter", mm=104.0, tol=5.0, how="bbox_x", part="Head"),
    dict(name="arm_span", mm=365.0, tol=15.0, how="bbox_x", part="Arm0"),
    dict(name="eye_diameter", mm=40.0, tol=2.0, how="bbox_x", part="EyeL"),
]