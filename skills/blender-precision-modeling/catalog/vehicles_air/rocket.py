"""
rocket -- a 46 m two-stage orbital launcher with a 2.4 m booster and four fins.

A rocket is a STACK OF LATHE PROFILES on one axis, and the mistake that costs
an hour is treating it as a cylinder. Five real sections are what make it read
as a launcher: the 9 m first stage, an interstage with a visible step, the
second stage, the ogive fairing, and a payload fairing split down the middle.

The four fins are the second repeated feature, arrayed RADIALLY about the
rocket's own axis with the radius carried in the mesh. The axis is the Z axis
here, so the array hub is the origin and `centre` is still passed explicitly.

The rocket is built standing on its four fins at z=0 -- which is why the fins
reach down to the ground line rather than to a pad height, and why
`sit_on_floor()` is a no-op.

Real small orbital launcher: 46000 mm tall, 2400 mm core diameter, four fins
on a 3300 mm envelope, ogive fairing 7000 mm long.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _craft as C

SPEC = dict(
    total_height=46000.0,
    core_dia=2400.0,
    first_stage=26000.0,
    interstage=3000.0,
    second_stage=10000.0,
    fairing_length=7000.0,
    fins=4,
    fin_envelope=3300.0,
    fin_root_chord=3000.0,
    engine_bells=9,
    engine_exit_dia=1000.0,
)

D = SPEC["core_dia"]
R = D / 2.0
FIN_R = SPEC["fin_envelope"] / 2.0 - 90.0
STACK = SPEC["first_stage"] + SPEC["interstage"] + SPEC["second_stage"]

CHECKS = [
    dict(name="total_height", mm=47400.0, tol=20.0, how="top_z",
         part="RocketFairing"),
    dict(name="core_dia", mm=2400.0, tol=8.0, how="bbox_x",
         part="RocketStage1"),
    dict(name="stage_length", mm=26000.0, tol=10.0, how="bbox_z",
         part="RocketStage1"),
    dict(name="fairing_envelope_dia", mm=3720.0, tol=12.0, how="bbox_x",
         part="RocketFairing"),
    dict(name="fin_envelope", mm=3300.0, tol=10.0, how="bbox_x",
         part="RocketFins"),
    dict(name="engine_row_span", mm=1581.4, tol=12.0, how="bbox_x",
         part="RocketEngine0"),
    dict(name="fin_on_floor", mm=0.0, tol=4.0, how="z_min", part="RocketFins"),
]


def build():
    white = bkit.pbr("RocketWhite", base=(0.90, 0.90, 0.88), rough=0.36)
    black = bkit.pbr("RocketBlack", base=(0.08, 0.08, 0.09), rough=0.42)
    steel = bkit.preset("brushed_metal")
    soot = bkit.pbr("RocketSoot", base=(0.14, 0.13, 0.12), rough=0.72)

    z0 = 1400.0          # the engine bells hang below the first stage

    # ---- first stage: a lathed barrel, not a cylinder ----------------
    bkit.lathe("RocketStage1",
               [(0.0, z0), (R, z0), (R, z0 + SPEC["first_stage"]),
                (0.0, z0 + SPEC["first_stage"])], segments=48, mat=white)
    # the thrust structure the engines hang from
    bkit.lathe("RocketThrustRing",
               [(R - 120.0, z0), (R, z0), (R, z0 + 500.0),
                (R - 120.0, z0 + 500.0)], segments=48, mat=steel)

    # ---- nine engine bells on a real bolt circle -------------------
    bell_r = 900.0
    bell = bkit.lathe("RocketEngine0",
                      [(0.0, 0.0), (120.0, 0.0), (110.0, 420.0),
                       (500.0, 1150.0), (500.0, 1300.0), (0.0, 1300.0)],
                      segments=32, mat=soot)
    C.place_in_mesh(bell, 300.0, 0.0, z0 - 1300.0)
    bkit.array_radial(bell, SPEC["engine_bells"], axis="Z",
                      centre=(0.0, 0.0, z0))

    # ---- interstage, second stage, engine of the upper stage --------
    z1 = z0 + SPEC["first_stage"]
    bkit.lathe("RocketInterstage",
               [(0.0, z1), (R, z1), (R, z1 + SPEC["interstage"]),
                (0.0, z1 + SPEC["interstage"])], segments=48, mat=black)
    z2 = z1 + SPEC["interstage"]
    bkit.lathe("RocketStage2",
               [(0.0, z2), (R, z2), (R, z2 + SPEC["second_stage"]),
                (0.0, z2 + SPEC["second_stage"])], segments=48, mat=white)
    bkit.lathe("RocketVacEngine",
               [(0.0, z2), (480.0, z2), (460.0, z2 - 500.0),
                (420.0, z2 - 700.0), (0.0, z2 - 700.0)], segments=32,
               mat=steel)
    # a descending lathe profile revolves inside-out: the faces come out
    # with inward normals and the part reports a negative volume.
    bkit.recalc(bpy.data.objects["RocketVacEngine"])

    # ---- interstage grid fins: a real pattern, not decoration ------
    for i in range(8):
        a = math.radians(45.0 * i)
        bkit.rounded_box("RocketGridFin%d" % i, 900.0, 26.0, 26.0, r=6.0,
                         segments=2,
                         centre=(0.0, 0.0, z1 + 400.0 + i * 240.0), mat=black)

    # ---- the ogive fairing, split into two halves -------------------
    z3 = z2 + SPEC["second_stage"]
    fl = SPEC["fairing_length"]
    secs = []
    for (t, r) in ((0.0, R), (0.10, R + 40.0), (0.35, R + 300.0),
                   (0.62, R + 560.0), (0.85, R + 640.0), (1.0, R + 660.0)):
        ring = bkit.superellipse_section(2.0 * r, 2.0 * r, n=2.2, steps=40)
        secs.append([(x, y, z3 + fl * t) for (x, y) in ring])
    fair = bkit.loft("RocketFairing", secs, mat=white)
    bkit.recalc(fair)
    bkit.shade_smooth(fair, 40.0)
    # the split line: a raised seam the length of the fairing
    for i, s in enumerate((-1, 1)):
        bkit.rounded_box("RocketFairingSeam%d" % i, 30.0, 30.0, fl * 0.92,
                         r=8.0, segments=2,
                         centre=(0.0, s * (R + 420.0), z3 + fl * 0.46),
                         mat=black)

    # ---- four fins, arrayed about the rocket's own axis -------------
    # the fins are centred on z=0 so the rocket STANDS on them: built
    # centred at half the chord and then dropped by a second half, the
    # fins hang 1500 mm below the floor and `sit_on_floor` lifts the whole
    # rocket 1500 mm, which moves every absolute height check with it.
    fin = bkit.rounded_box("RocketFins", 180.0, 120.0,
                           SPEC["fin_root_chord"], r=10.0, segments=2,
                           centre=(FIN_R, 0.0, SPEC["fin_root_chord"] / 2.0),
                           mat=black)
    bpy.context.view_layer.update()
    bkit.array_radial(fin, SPEC["fins"], axis="Z", centre=(0.0, 0.0, 0.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 3 + 8 + 1 + 2 + 1,
                note="Fins and engine bells are arrayed about the rocket axis "
                     "with the orbit radius in the mesh.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
