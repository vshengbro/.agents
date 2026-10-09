"""
autoclave -- 600 x 700 x 845 mm bench-top steam steriliser: cabinet, a 340 mm
horizontal chamber with a 380 mm dished door on six lug bolts, a recessed
control readout with eight keys, a pressure gauge, top plate and exhaust stack.

The chamber is a `lathe` revolved about Z and then rotated -90 degrees about X
so its axis runs along +Y into the cabinet. That rotation sign matters: +90
sends the chamber out through the front of the machine, which is where the door
already is.

The door overlaps the chamber mouth by 10 mm rather than meeting it flush. A
dish that ends exactly at the flange touches it across a whole circle, and that
contact ring becomes a non-manifold edge.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    cabinet_width=600.0,
    cabinet_depth=700.0,
    cabinet_height=760.0,
    chamber_diameter=340.0,
    chamber_length=400.0,
    door_diameter=380.0,
    door_lugs=6,
    keypad_buttons=8,
    screen_width=180.0,
    overall_height=845.0,
)

CW, CD, CH = (SPEC["cabinet_width"], SPEC["cabinet_depth"],
              SPEC["cabinet_height"])
FRONT = -CD / 2.0                    # -350


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("AutoclaveShell", base=(0.82, 0.83, 0.82), rough=0.32)
    steel = bkit.preset("brushed_metal")
    dark = bkit.pbr("AutoclaveDark", base=(0.065, 0.065, 0.070), rough=0.42)
    screen = bkit.pbr("AutoclaveScreen", base=(0.05, 0.08, 0.07), rough=0.10,
                      emission=(0.24, 0.66, 0.52), emission_strength=1.2)

    # ---- cabinet and top plate --------------------------------------------
    bkit.rounded_box("AutoclaveCabinet", CW, CD, CH, r=10.0, segments=3,
                     centre=(0.0, 0.0, CH / 2.0), mat=shell)
    bkit.rounded_box("TopPlate", 620.0, 720.0, 30.0, r=8.0, segments=2,
                     centre=(0.0, 0.0, 765.0), mat=steel)
    feet = [bkit.cylinder("_foot", 16.0, 16.0, segments=20,
                          centre=(fx, fy, 8.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, 480.0, 560.0)]
    bkit.join(feet, name="AutoclaveFeet")

    # ---- 340 mm chamber, revolved about Z then turned to run along +Y -----
    chamber = bkit.lathe("Chamber", [(0.0, 0.0), (170.0, 0.0), (170.0, 400.0),
                                     (0.0, 400.0)], segments=64, mat=steel)
    chamber.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bkit.move(chamber, 0.0, -330.0, 400.0)

    # ---- 380 mm dished door, overlapping the chamber mouth by 10 mm ------
    door = bkit.lathe("ChamberDoor", [(0.0, 0.0), (190.0, 0.0), (190.0, 60.0),
                                      (150.0, 80.0), (0.0, 80.0)], segments=64,
                      mat=steel)
    door.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bkit.move(door, 0.0, -360.0, 400.0)

    # ---- six lug bolts, swept about the world Y axis at radius 210 -------
    lug = bkit.box("_lug", 14.0, 30.0, 14.0, centre=(0.0, 0.0, 210.0),
                   mat=dark)
    bkit.array_radial(lug, count=SPEC["door_lugs"], axis="Y")
    bkit.move(lug, 0.0, -360.0, 400.0)
    bkit.cylinder("DoorHandle", 16.0, 200.0, segments=28, axis="Z",
                  centre=(0.0, -440.0, 400.0), mat=dark)
    bkit.rounded_box("HandleMount", 44.0, 40.0, 24.0, r=5.0, segments=2,
                     centre=(0.0, -410.0, 400.0), mat=steel)

    # ---- recessed readout and an eight-key pad below the door ------------
    _recess("AutoclaveScreen", bpy.data.objects["AutoclaveCabinet"],
            SPEC["screen_width"], 60.0, -110.0, 120.0, screen)
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(4, 2, 30.0, 26.0)):
        keys.append(bkit.rounded_box(
            "_key%d" % i, 22.0, 7.0, 18.0, r=3.0, segments=2, mat=dark,
            centre=(-110.0 + kx, FRONT + 2.5, 50.0 + kz)))
    bkit.join(keys, name="AutoclaveKeypad")

    # ---- pressure gauge and a steam exhaust stack -------------------------
    bkit.cylinder("PressureGauge", 45.0, 20.0, segments=44, axis="Y",
                  centre=(-215.0, FRONT + 8.0, 200.0), mat=steel)
    bkit.cylinder("GaugeFace", 38.0, 3.0, segments=44, axis="Y",
                  centre=(-215.0, FRONT - 4.0, 200.0), mat=screen)
    bkit.cylinder("ExhaustStack", 40.0, 90.0, segments=32,
                  centre=(180.0, 180.0, 800.0), mat=steel)
    bkit.rounded_box("DrainValve", 40.0, 40.0, 60.0, r=6.0, segments=2,
                     centre=(180.0, -200.0, 60.0), mat=steel)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="cabinet_width", mm=600.0, tol=0.8, how="bbox_x",
         part="AutoclaveCabinet"),
    dict(name="cabinet_depth", mm=700.0, tol=0.8, how="bbox_y",
         part="AutoclaveCabinet"),
    # `diameter` is max(bbox_x, bbox_y) and the chamber's 400 mm AXIAL run along Y
    # beats its 340 mm bore, so bbox_min is the honest transverse extent.
    dict(name="chamber_diameter", mm=340.0, tol=0.8, how="bbox_min",
         part="Chamber"),
    dict(name="door_diameter", mm=380.0, tol=0.8, how="diameter",
         part="ChamberDoor"),
    dict(name="overall_height", mm=845.0, tol=2.0, how="bbox_z"),
]