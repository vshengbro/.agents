"""
spectrometer -- 450 x 350 x 245 mm bench FTIR/NIR spectrometer: base cabinet,
a lid overlapping it by 15 mm, a sample compartment with a real recessed door,
a 140 x 60 mm readout, six control keys, a grating turret knob on the side,
two side ventilation grilles and a fibre port.

`medium` band, so the longest axis must land in [75, 1200] mm -- 450 mm sits
squarely inside. The compartment door is the part that matters: a real pocket
with the door standing 3 mm proud inside it, so the door reads as a hinged panel
rather than as a decal.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    base_width=450.0,
    base_depth=350.0,
    base_height=200.0,
    overall_height=245.0,
    screen_width=140.0,
    keypad_buttons=6,
    turret_diameter=60.0,
    grille_holes=16,
)

BW, BD, BH = SPEC["base_width"], SPEC["base_depth"], SPEC["base_height"]
FRONT = -BD / 2.0                    # -175


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("SpectroShell", base=(0.83, 0.83, 0.81), rough=0.34)
    lid_mat = bkit.pbr("SpectroLid", base=(0.80, 0.80, 0.79), rough=0.30)
    dark = bkit.pbr("SpectroDark", base=(0.065, 0.065, 0.070), rough=0.42)
    steel = bkit.preset("brushed_metal")
    screen = bkit.pbr("SpectroScreen", base=(0.05, 0.08, 0.07), rough=0.10,
                      emission=(0.34, 0.62, 0.80), emission_strength=1.1)

    # ---- base cabinet and lid, overlapping by 15 mm -----------------------
    bkit.rounded_box("SpectroBase", BW, BD, BH, r=10.0, segments=3,
                     centre=(0.0, 0.0, BH / 2.0), mat=shell)
    bkit.rounded_box("SpectroLid", BW - 10.0, BD - 10.0, 60.0, r=8.0,
                     segments=3, centre=(0.0, 0.0, 215.0), mat=lid_mat)
    bkit.rounded_box("LidHandle", 120.0, 26.0, 20.0, r=6.0, segments=2,
                     centre=(0.0, -150.0, 215.0), mat=dark)

    # ---- recessed readout and six keys ------------------------------------
    _recess("SpectroScreen", bpy.data.objects["SpectroBase"],
            SPEC["screen_width"], 60.0, -120.0, 132.0, screen)
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(3, 2, 26.0, 22.0)):
        keys.append(bkit.rounded_box(
            "_key%d" % i, 18.0, 7.0, 15.0, r=2.5, segments=2, mat=dark,
            centre=(130.0 + kx, FRONT + 2.5, 132.0 + kz)))
    bkit.join(keys, name="SpectroKeypad")

    # ---- sample compartment: a real pocket with a proud door -------------
    bkit.boolean(bpy.data.objects["SpectroBase"], bkit.rounded_box(
        "_pocket", 200.0, 12.0, 90.0, r=4.0, segments=2,
        centre=(0.0, FRONT + 2.0, 46.0)), "DIFFERENCE")
    bkit.rounded_box("SampleDoor", 190.0, 6.0, 80.0, r=4.0, segments=2,
                     centre=(0.0, FRONT + 3.0, 46.0), mat=steel)
    bkit.rounded_box("DoorLatch", 26.0, 12.0, 10.0, r=3.0, segments=2,
                     centre=(82.0, FRONT + 1.0, 46.0), mat=dark)
    bkit.rounded_box("SampleTray", 160.0, 120.0, 8.0, r=3.0, segments=2,
                     centre=(0.0, -40.0, 20.0), mat=steel)

    # ---- grating turret knob on the right flank --------------------------
    bkit.cylinder("TurretKnob", SPEC["turret_diameter"] / 2.0, 30.0,
                  segments=48, axis="X", centre=(BW / 2.0 + 8.0, -40.0, 120.0),
                  mat=dark)
    bkit.box("TurretPointer", 3.0, 8.0, 24.0, mat=steel,
             centre=(BW / 2.0 - 9.0, -40.0, 132.0))

    # ---- two side ventilation grilles, 4 x 2 holes each ------------------
    for side in (-1.0, 1.0):
        tag = "L" if side < 0 else "R"
        g = bkit.perforated_panel("SideGrille" + tag, 4, 2, 16.0, 16.0, 5.0,
                                  70.0, 40.0, 4.0, mat=dark)
        g.rotation_euler = (0.0, math.radians(90.0 * side), 0.0)
        bkit.move(g, side * (BW / 2.0 + 1.0), 90.0, 120.0)

    # ---- fibre port and rear connectors -----------------------------------
    bkit.cylinder("FibrePort", 12.0, 40.0, segments=28, axis="X",
                  centre=(BW / 2.0 + 10.0, -110.0, 60.0), mat=steel)
    conn = []
    for i, (cy, cw) in enumerate(bkit.lay_out([30.0, 30.0], gap=12.0)):
        conn.append(bkit.cylinder("_c%d" % i, 10.0, 8.0, segments=24,
                                  axis="Y", mat=steel,
                                  centre=(120.0 + cy, BD / 2.0 + 2.0, 60.0)))
    bkit.join(conn, name="RearConnectors")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="base_width", mm=450.0, tol=0.8, how="bbox_x",
         part="SpectroBase"),
    dict(name="base_depth", mm=350.0, tol=0.8, how="bbox_y",
         part="SpectroBase"),
    dict(name="base_height", mm=200.0, tol=0.8, how="bbox_z",
         part="SpectroBase"),
    dict(name="overall_height", mm=245.0, tol=1.0, how="bbox_z"),
    dict(name="screen_width", mm=140.0, tol=0.8, how="bbox_x",
         part="SpectroScreen"),
    dict(name="turret_diameter", mm=60.0, tol=0.8, how="diameter",
         part="TurretKnob"),
]