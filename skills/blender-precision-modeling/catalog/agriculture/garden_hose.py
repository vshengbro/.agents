"""
garden_hose -- a 19 mm garden hose coiled flat on the ground, with its nozzle.

A coiled hose is a HELIX with a round section, and the only way to get a round
section along a curved path is to loft: one vertical ring per step of the spiral,
each ring centred on the path and carried round with it. Scaled from
`bkit.thread`, whose profile is a triangular helix blade -- correct for a bolt,
and a screw-shaped ribbon rather than a hose if you use it here.

The coil is a spiral, not concentric rings: three turns from a 250 mm mean radius
in to 150 mm, which is how a hose actually piles up when you drop it.

Real coil: 519 mm outer diameter, 3 turns, 19 mm bore, 34 mm brass coupling.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy

SPEC = dict(
    hose_dia=19.0,
    coil_outer_dia=502.3,
    coil_turns=3,
    coil_outer_radius=250.0,
    coil_inner_radius=150.0,
    coupling_dia=34.0,
    nozzle_length=150.0,
    overall_length=912.8,
)

R0 = SPEC["coil_outer_radius"]
R1 = SPEC["coil_inner_radius"]
TURNS = SPEC["coil_turns"]
HR = SPEC["hose_dia"] / 2.0

CHECKS = [
    dict(name="hose_dia", mm=19.0, tol=1.0, how="bbox_z", part="HoseCoil"),
    dict(name="coil_outer_dia", mm=502.3, tol=6.0, how="bbox_x", part="HoseCoil"),
    dict(name="hose_on_floor", mm=0.0, tol=2.0, how="z_min", part="HoseCoil"),
    dict(name="coupling_dia", mm=34.0, tol=1.5, how="bbox_y",
         part="HoseCoupling"),
    dict(name="nozzle_length", mm=150.0, tol=4.0, how="bbox_x",
         part="HoseNozzle"),
]


def build():
    hose = bkit.pbr("HoseRubber", base=(0.16, 0.26, 0.09), rough=0.62)
    brass = bkit.pbr("HoseBrass", base=(0.78, 0.62, 0.28), metal=0.85,
                     rough=0.28)

    # ---- the coil: a lofted spiral, one vertical ring per step -----------
    steps = 3 * 96
    secs = []
    for s in range(steps + 1):
        t = s / float(steps)
        ang = 2.0 * math.pi * TURNS * t
        r = R0 + (R1 - R0) * t
        cx, cy = r * math.cos(ang), r * math.sin(ang)
        secs.append([(cx + HR * math.cos(2.0 * math.pi * j / 12.0), cy,
                      HR + HR * math.sin(2.0 * math.pi * j / 12.0))
                     for j in range(12)])
    coil = bkit.loft("HoseCoil", secs, mat=hose)
    bkit.recalc(coil)
    bkit.shade_smooth(coil, 50.0)

    # ---- the tail: off the OUTER end of the coil, along the ground, so
    #      it never lies back through its own turns ------------------------
    bkit.cylinder("HoseTail", HR, 270.0, segments=16, axis="X",
                  centre=(385.0, 0.0, 14.0), mat=hose)

    # ---- the brass coupling inboard of the nozzle ----------------------
    bkit.cylinder("HoseCoupling", 17.0, 60.0, segments=20,
                  centre=(485.0, 0.0, 17.0), axis="X", mat=brass)

    # ---- the nozzle: a tapered body and a grip, lying on the tail axis ---
    # `place(..., "X")` stands the lathe on end: the profile's local Z becomes
    # the world's X, so the nozzle lies down instead of standing on the ground
    # and lifting the whole coil 45 mm when `sit_on_floor` seats the model.
    noz = bkit.lathe("HoseNozzle",
                     [(0.0, -75.0), (26.0, -75.0), (26.0, -30.0),
                      (17.0, -24.0), (17.0, 60.0), (30.0, 60.0),
                      (30.0, 75.0), (0.0, 75.0)],
                     segments=24, mat=brass)
    bkit.place(noz, (595.0, 0.0, 30.0), "X")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4,
                note="The coil is a lofted spiral, not `thread()`: a thread "
                     "profile is a triangular helix blade, which is a screw, "
                     "not a hose.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
