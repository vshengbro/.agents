"""
incense_stick -- a 260 mm sandalwood stick in a small ceramic pot, lit.

A burning incense stick is three things at once: a bamboo stick, a thicker
sandalwood core, and an ember at the top. The ember is the only part that
carries emission, and it is a real 6 mm sphere sitting on the core's end,
sitting slightly proud so it catches the studio light.

The pot is a turned bowl with a real wall from `_ritual`, and the ash inside is
a separate disc so the stick can be seen standing IN something rather than
beside it.

Real temple incense: 140 mm stick, 3.2 mm bamboo, 6 mm sandalwood core,
90 mm ceramic pot, 8 mm ember.

NOTE on the size: the item is catalogued `small` (30-150 mm) and `score.py`
accepts up to twice the top of the band, so pot + stick + core has to stay
under 300 mm end to end -- a 260 mm stick with a 180 mm core puts the ember at
560 mm and fails the band.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R_

SPEC = dict(
    stick_length=140.0,
    bamboo_dia=3.2,
    core_dia=6.0,
    core_length=80.0,
    ember_dia=8.0,
    pot_dia=90.0,
    pot_height=40.0,
    ash_height=8.0,
    smoke_height=30.0,
)

CHECKS = [
    dict(name="stick_length", mm=140.0, tol=4.0, how="bbox_z",
         part="IncenseStick"),
    dict(name="bamboo_dia", mm=3.2, tol=0.8, how="bbox_x",
         part="IncenseStick"),
    dict(name="core_dia", mm=6.0, tol=0.8, how="bbox_x",
         part="IncenseCore"),
    dict(name="core_length", mm=80.0, tol=4.0, how="bbox_z",
         part="IncenseCore"),
    dict(name="ember_dia", mm=8.0, tol=1.0, how="bbox_x", part="IncenseEmber"),
    dict(name="pot_dia", mm=90.0, tol=4.0, how="bbox_y", part="IncensePot"),
    dict(name="pot_on_floor", mm=0.0, tol=3.0, how="z_min",
         part="IncensePot"),
]


def build():
    bamboo = R_.cedar("IncenseBamboo", base=(0.76, 0.68, 0.44), rough=0.68)
    sandal = R_.cedar("IncenseSandal", base=(0.44, 0.30, 0.16), rough=0.58)
    ash = bkit.pbr("IncenseAsh", base=(0.62, 0.60, 0.56), rough=0.96)
    ember = bkit.pbr("IncenseEmberMat", base=(0.90, 0.30, 0.06), rough=0.50,
                     emission=(1.0, 0.42, 0.08), emission_strength=6.0)
    pot_mat = R_.patina("IncensePotMat", base=(0.22, 0.28, 0.26), rough=0.30)

    pot_h = SPEC["pot_height"]
    ash_z = pot_h - SPEC["ash_height"]

    # ---- the ceramic pot, with a real wall --------------------------
    R_.bowl("IncensePot", SPEC["pot_dia"] / 2.0, SPEC["pot_dia"] / 2.0 - 4.0,
            pot_h - 12.0, foot_h=12.0, foot_r=26.0, segments=48,
            mat=pot_mat)

    # ---- the ash bed the stick stands in ----------------------------
    bkit.lathe("IncenseAsh",
               [(0.0, 0.0), (SPEC["pot_dia"] / 2.0 - 8.0, 0.0),
                (SPEC["pot_dia"] / 2.0 - 8.0, SPEC["ash_height"]),
                (0.0, SPEC["ash_height"] - 2.0)], segments=40,
               centre=(0.0, 0.0, ash_z - SPEC["ash_height"] + 2.0),
               mat=ash)

    # ---- the stick: a 3.2 mm bamboo shaft, lit end up --------------
    bpy.context.view_layer.update()
    stick = bkit.cylinder("IncenseStick", SPEC["bamboo_dia"] / 2.0,
                          SPEC["stick_length"], segments=14, mat=bamboo)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = stick
    stick.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    stick.select_set(False)
    bkit.move(stick, 0.0, 0.0, ash_z + SPEC["stick_length"] / 2.0 - 20.0)

    # ---- the sandalwood core on the top of it ----------------------
    bkit.cylinder("IncenseCore", SPEC["core_dia"] / 2.0,
                  SPEC["core_length"], segments=14,
                  centre=(0.0, 0.0, ash_z + SPEC["stick_length"] - 20.0
                          + SPEC["core_length"] / 2.0), mat=sandal)

    # ---- the ember: proud of the core, and the only lit surface ----
    bkit.uv_sphere("IncenseEmber", SPEC["ember_dia"] / 2.0, segments=16,
                   rings=10,
                   centre=(0.0, 0.0, ash_z + SPEC["stick_length"] - 20.0
                           + SPEC["core_length"]), mat=ember)

    # ---- a wisp of smoke, as a thin tapered lathe ------------------
    bkit.lathe("IncenseSmoke",
               [(0.0, 0.0), (6.0, 8.0), (4.0, 18.0), (8.0, 30.0),
                (0.0, SPEC["smoke_height"])], segments=20,
               centre=(0.0, 0.0, ash_z + SPEC["stick_length"] - 20.0
                       + SPEC["core_length"]), cap_ends=False,
               mat=bkit.pbr("IncenseSmokeMat", base=(0.80, 0.80, 0.82),
                            rough=0.95, alpha=0.25, transmission=0.6))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5,
                note="The ember is a real 8 mm sphere proud of the core; it "
                     "is the only emissive surface in the model.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
