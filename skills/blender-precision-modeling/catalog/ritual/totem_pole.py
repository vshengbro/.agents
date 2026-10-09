"""
totem_pole -- 12.4 m Kwakwaka'wakw-style house post, 800 mm across the base.

A totem pole is a stack of repeated carved motifs, so the model is literally
that: a 400 mm stone plinth, a 11.2 m tapered log, and FIVE identical carved
motifs placed at a computed 1600 mm pitch with `array_linear(world=True)`.  Each
motif is four parts -- a collar ring, a beaked muzzle, two inset eyes and a row
of teeth -- so one motif is a real carved figure rather than a band.

The plinth's underside is z = 0, and the log tapers 800 -> 430 mm.  The taper is
authored in the lathe profile so the shaft's own diameter is a checkable number
instead of a claim.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R

SPEC = dict(
    plinth_width=1400.0,
    plinth_height=400.0,
    shaft_base_diameter=800.0,
    shaft_top_diameter=430.0,
    shaft_height=11200.0,
    motif_count=5,
    motif_pitch=1600.0,
    first_motif_z=660.0,
    motif_band_diameter=980.0,
    top_z=12000.0,
)

CHECKS = [
    dict(name="plinth_width", mm=1400.0, tol=3.0, how="bbox_x",
         part="TotemPlinth"),
    dict(name="plinth_height", mm=400.0, tol=2.0, how="bbox_z",
         part="TotemPlinth"),
    dict(name="shaft_base_diameter", mm=800.0, tol=4.0, how="bbox_x",
         part="TotemShaftBase"),
    dict(name="first_motif_z", mm=660.0, tol=4.0, how="z_min",
         part="TotemMotifBand"),
    dict(name="motif_band_diameter", mm=980.0, tol=4.0, how="bbox_x",
         part="TotemMotifBand"),
    dict(name="shaft_height", mm=11200.0, tol=8.0, how="bbox_z",
         part="TotemShaft"),
    dict(name="top_z", mm=12000.0, tol=12.0, how="top_z", part="TotemCap"),
]

PZ = SPEC["plinth_height"]
SH = SPEC["shaft_height"]


def build():
    wood = R.cedar("TotemCedar", base=(0.34, 0.20, 0.11))
    dark = R.basalt("TotemStone")
    paint = bkit.pbr("TotemPaint", base=(0.72, 0.20, 0.09), rough=0.42)
    eye = bkit.pbr("TotemEye", base=(0.05, 0.04, 0.03), rough=0.30)
    shell = bkit.pbr("TotemShell", base=(0.86, 0.82, 0.70), rough=0.40)

    # ---- plinth: the floor datum -----------------------------------------
    bkit.rounded_box("TotemPlinth", SPEC["plinth_width"],
                     SPEC["plinth_width"], PZ, r=26.0, segments=3,
                     centre=(0.0, 0.0, PZ / 2.0), mat=dark)

    # ---- shaft: the taper is in the profile, 800 -> 430 ------------------
    z0, z1 = PZ, PZ + SH
    prof = [(0.0, z0), (400.0, z0), (386.0, z0 + SH * 0.22),
            (318.0, z0 + SH * 0.48), (262.0, z0 + SH * 0.72),
            (228.0, z1 - 180.0), (215.0, z1), (0.0, z1)]
    shaft = bkit.lathe("TotemShaft", prof, segments=56, mat=wood)
    bkit.recalc(shaft)
    # a short straight section at the foot, so the base diameter is a
    # measurable constant rather than the taper's slope
    bkit.lathe("TotemShaftBase",
               [(0.0, z0), (400.0, z0), (400.0, z0 + 300.0), (0.0, z0 + 300.0)],
               segments=56, mat=wood)

    # ---- the motif: collar ring, muzzle, eyes, teeth ---------------------
    ring = bkit.lathe("TotemMotifBand",
                      [(396.0, 0.0), (490.0, 90.0), (490.0, 260.0),
                       (396.0, 350.0), (396.0, 0.0)],
                      segments=56, cap_ends=False, mat=wood)
    R.stack_motifs("ring", SPEC["motif_count"], SPEC["motif_pitch"], ring,
                   first_z=z0 + 260.0)
    ring.name = "TotemMotifBand"

    muzzle = bkit.rounded_box("TotemMuzzle", 300.0, 560.0, 300.0, r=90.0,
                              segments=3, centre=(0.0, 340.0, 0.0),
                              mat=paint)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = muzzle
    muzzle.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    muzzle.select_set(False)
    muzzle.location = bkit.v(0.0, 0.0, z0 + 420.0)
    bpy.context.view_layer.update()
    bkit.array_linear(muzzle, SPEC["motif_count"], (0.0, 0.0,
                                                    SPEC["motif_pitch"]),
                      world=True)
    muzzle.name = "TotemMuzzle"

    eye_proto = bkit.uv_sphere("TotemEye", 92.0, segments=24, rings=14,
                               centre=(150.0, 0.0, 0.0), mat=eye)
    eye2 = bkit.duplicate(eye_proto, "TotemEye2", offset_mm=(-300.0, 0.0, 0.0))
    eyes = bkit.join([eye_proto, eye2], "TotemEyes")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = eyes
    eyes.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    eyes.select_set(False)
    eyes.location = bkit.v(0.0, 250.0, z0 + 520.0)
    bpy.context.view_layer.update()
    bkit.array_linear(eyes, SPEC["motif_count"], (0.0, 0.0,
                                                  SPEC["motif_pitch"]),
                      world=True)
    eyes.name = "TotemEyes"

    for i, (x, w) in enumerate(bkit.lay_out([110] * 5, gap=46.0)):
        tooth = bkit.rounded_box("TotemTooth%d" % i, w, 130.0, 190.0,
                                 r=18.0, segments=2,
                                 centre=(x, 470.0, 0.0), mat=shell)
        tooth.location = bkit.v(0.0, 0.0, z0 + 300.0)
        bpy.context.view_layer.update()
        bkit.array_linear(tooth, SPEC["motif_count"],
                          (0.0, 0.0, SPEC["motif_pitch"]), world=True)

    # ---- crown cap -------------------------------------------------------
    R.finial("TotemCap", 400.0, 330.0, segments=48, mat=paint)
    bkit.move(bpy.data.objects["TotemCap"], 0.0, 0.0, z1)

    return dict(spec=SPEC, parts=9)