"""starfish -- a 130 mm ochre sea star: FIVE arms, a domed central disc, and
each arm tapering from a broad base to a blunt tip.

Five is the count. One arm is authored on +X and swept with
`array_radial(count=5, centre=HUB)` about the animal's own centre at
(0, 0, 14); four or six arms is the classic miss, and without the explicit
`centre` the copies orbit the world origin instead of the disc.

Construction: a lathed disc, one swept arm arrayed five times, and the
tubercles as a second material on the one solid. Nothing is booleaned.

Orientation: the animal lies flat, the disc dome up, so top.png shows the
five-point planform and side.png shows the arms lifting off the substrate.
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
    arm_span=130.0,
    disc_diameter=44.0,
    disc_height=22.0,
    arm_count=5,
    arm_length=62.0,
)

HUB = (0.0, 0.0, 14.0)
# one arm, authored on +X: out from the disc, tapering, with the tip lifting
ARM = [
    (16.0, 0.0, 14.0),
    (28.0, 0.0, 15.0),
    (42.0, 0.0, 13.0),
    (55.0, 0.0, 10.0),
    (62.0, 0.0, 7.0),
]
ARM_RAD = [(14.0, 9.0), (13.0, 8.5), (10.0, 7.0), (6.0, 4.5), (2.0, 1.6)]


def build():
    skin = bkit.pbr("StarSkin", base=(0.72, 0.38, 0.12), rough=0.68)
    pale = bkit.pbr("StarPale", base=(0.86, 0.66, 0.42), rough=0.72)
    tub = bkit.pbr("StarTubercle", base=(0.58, 0.28, 0.09), rough=0.74)

    disc = bkit.lathe("Disc",
                      [(0.0, 0.0), (14.0, 1.0), (21.0, 5.0), (22.0, 12.0),
                       (17.0, 19.0), (8.0, 22.0), (0.0, 22.0)],
                      segments=48, centre=(0.0, 0.0, 0.0), mat=skin)
    bkit.move(disc, 0.0, 0.0, 0.0)

    # ---- FIVE arms: one authored, arrayed about the disc's own centre
    arm = F.tube("Arm0", ARM, ARM_RAD, skin, n=2.6, steps=20)
    bkit.array_radial(arm, SPEC["arm_count"], centre=HUB)

    # ---- the pale underside is a second material on the one disc solid; a
    # second shell shaped like the belly would z-fight with the real surface
    bkit.assign_faces_by(disc, pale, lambda c, n: c.z / bkit.MM < 4.0)
    bkit.assign_faces_by(bpy.data.objects["Arm0"], tub,
                         lambda c, n: c.z / bkit.MM > 12.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2)


CHECKS = [
    # five arms at 72 degrees apart: the widest axis is not always X, so the
    # span is the arm ring's largest extent, not its bbox_x
    dict(name="arm_span", mm=120.0, tol=6.0, how="bbox_max", part="Arm0"),
    dict(name="disc_diameter", mm=44.0, tol=2.0, how="bbox_x", part="Disc"),
    dict(name="disc_height", mm=22.0, tol=2.0, how="bbox_z", part="Disc"),
    dict(name="stand_height", mm=24.0, tol=3.0, how="bbox_z"),
]