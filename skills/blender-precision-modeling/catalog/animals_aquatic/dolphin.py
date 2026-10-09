"""dolphin -- a 2.4 m bottlenose: the short blunt rostrum, the steep melon
forehead, the sickle-shaped dorsal, and horizontal tail flukes.

The dolphin reads as a dolphin because of the ROSTRUM: a dolphin is a whale with
a beak, and the transition from melon to beak -- a steep concave forehead
dropping onto a narrow snout -- is the whole silhouette cue. A smooth teardrop
with a fin on top is a fish.

Construction: one lofted body from a proportion table, a swept rostrum, flat
blade flukes, a sickle dorsal and paired flippers mirrored in world space.
Nothing is booleaned.

Orientation: rostrum at -Y, X lateral, Z up, so side.png shows the profile.
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
    overall_length=2350.0,
    body_length=1750.0,
    body_depth=480.0,
    body_width=400.0,
    rostrum_length=356.0,
    dorsal_height=195.0,
    fluke_span=560.0,
    flipper_length=336.0,
)

# (y, half_height, half_width, z_centre) -- melon -1000, peduncle +750
BODY = [
    (-1000.0, 120.0, 105.0, 420.0),
    (-960.0, 175.0, 150.0, 420.0),
    (-880.0, 215.0, 180.0, 420.0),
    (-760.0, 240.0, 200.0, 420.0),
    (-600.0, 248.0, 205.0, 418.0),
    (-400.0, 240.0, 198.0, 414.0),
    (-150.0, 220.0, 180.0, 410.0),
    (100.0, 185.0, 150.0, 408.0),
    (330.0, 145.0, 118.0, 408.0),
    (550.0, 105.0, 85.0, 410.0),
    (720.0, 70.0, 56.0, 412.0),
    (800.0, 45.0, 38.0, 414.0),
]
# the rostrum: short, blunt, and clearly separate from the melon
ROSTRUM = [
    (0.0, -980.0, 400.0), (0.0, -1090.0, 382.0), (0.0, -1210.0, 366.0),
    (0.0, -1320.0, 356.0),
]
ROSTRUM_RAD = [(88.0, 78.0), (72.0, 62.0), (58.0, 50.0), (40.0, 36.0)]
# sickle dorsal: concave trailing edge
DORSAL = [
    (-120.0, 560.0), (-30.0, 700.0), (90.0, 715.0), (160.0, 610.0),
    (110.0, 570.0), (20.0, 545.0), (-80.0, 520.0),
]
# horizontal flukes
FLUKE = [
    (0.0, 740.0), (110.0, 850.0), (250.0, 950.0), (275.0, 1030.0),
    (190.0, 1010.0), (80.0, 900.0), (0.0, 830.0), (-80.0, 900.0),
    (-190.0, 1010.0), (-275.0, 1030.0), (-250.0, 950.0), (-110.0, 850.0),
]
FLIPPER = [
    (0.0, 0.0), (140.0, -170.0), (300.0, -280.0), (380.0, -250.0),
    (290.0, -60.0), (150.0, 40.0),
]


def build():
    hide = bkit.pbr("DolphinHide", base=(0.34, 0.38, 0.42), rough=0.34,
                    coat=0.3)
    pale = bkit.pbr("DolphinBelly", base=(0.78, 0.79, 0.79), rough=0.40)
    dark = bkit.pbr("DolphinDark", base=(0.10, 0.12, 0.14), rough=0.36)
    eye = bkit.pbr("DolphinEye", base=(0.015, 0.015, 0.02), rough=0.08)

    torso = F.body("Body", BODY, hide, n=2.7, steps=40)
    bkit.assign_faces_by(torso, pale, lambda c, n: c.z / bkit.MM < 350.0)

    F.tube("Rostrum", ROSTRUM, ROSTRUM_RAD, hide, n=2.4, steps=24)
    F.plate_yz("FinDorsal", DORSAL, 20.0, x=0.0, mat=hide)

    fluke = F.plate_xy("Fluke", FLUKE, 42.0, mat=hide)
    bkit.move(fluke, 0.0, 0.0, 414.0)
    flip = F.plate_xy("FlipperL", FLIPPER, 26.0, mat=hide)
    bkit.move(flip, 120.0, -420.0, 300.0)
    F.bake_rot(flip, "Y", -32.0)
    F.mirror_copy(flip, "FlipperR")

    # ---- mouth line as a second material on the one rostrum, and the eye
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 22.0, segments=20, rings=10,
                       centre=(sx * 108.0, -930.0, 470.0), mat=eye)

    bkit.assign_faces_by(bpy.data.objects["Rostrum"], dark,
                         lambda c, n: c.z / bkit.MM < 372.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="overall_length", mm=2350.0, tol=40.0, how="bbox_y"),
    dict(name="body_length", mm=1800.0, tol=25.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=496.0, tol=20.0, how="bbox_z", part="Body"),
    dict(name="body_width", mm=410.0, tol=15.0, how="bbox_x", part="Body"),
    dict(name="rostrum_length", mm=356.0, tol=15.0, how="bbox_y",
         part="Rostrum"),
    dict(name="dorsal_height", mm=195.0, tol=15.0, how="bbox_z",
         part="FinDorsal"),
    dict(name="fluke_span", mm=550.0, tol=20.0, how="bbox_x", part="Fluke"),
    dict(name="flipper_length", mm=336.0, tol=20.0, how="bbox_x",
         part="FlipperL"),
]