"""
projector -- 330 x 240 x 108 mm desktop projector: moulded chassis on four
feet, a 68 mm front lens barrel with real glass, a top cooling grille, a
rear air filter and a five-button control pad.

Two `perforated_panel` calls do the ventilation -- one mesh each, no booleans,
and the hole pitch is a real number (20 mm) rather than a decorative array of
dents. The lens barrel is the optics-domain trick from `camera_lens`: build the
revolve about Z, rotate 90 degrees about Y so the optical axis runs along +X,
then `bkit.move()` it out to the chassis face.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    chassis_width=330.0,
    chassis_depth=240.0,
    chassis_height=108.0,
    lens_barrel_diameter=68.0,
    lens_diameter=54.0,
    vent_holes=32,
    control_buttons=5,
)

CW, CD, CH = SPEC["chassis_width"], SPEC["chassis_depth"], SPEC["chassis_height"]
FOOT_H = 8.0
BODY_Z = FOOT_H + CH / 2.0            # chassis centre above the floor
LENS_X = CW / 2.0 - 12.0              # where the barrel profile starts


def build():
    shell = bkit.pbr("ProjShell", base=(0.80, 0.80, 0.79), rough=0.38)
    dark = bkit.pbr("ProjDark", base=(0.070, 0.070, 0.075), rough=0.42)
    lens_rim = bkit.preset("brushed_metal")
    glass = bkit.pbr("ProjGlass", base=(0.16, 0.24, 0.38), metal=0.40,
                     rough=0.03)
    led = bkit.pbr("ProjLed", base=(0.10, 0.30, 0.12),
                   emission=(0.25, 0.90, 0.35), emission_strength=2.2)

    # ---- chassis ----------------------------------------------------------
    bkit.rounded_box("ProjectorChassis", CW, CD, CH, r=14.0, segments=4,
                     centre=(0.0, 0.0, BODY_Z), mat=shell)

    feet = [bkit.cylinder("_foot", 10.0, 12.0, segments=20,
                          centre=(fx, fy, 6.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, CW - 70.0, CD - 70.0)]
    bkit.join(feet, name="ProjectorFeet")

    # ---- front lens: lathe about Z, then rotated so the axis runs along X --
    barrel = bkit.lathe("LensBarrel", [(0.0, 0.0), (34.0, 0.0), (34.0, 30.0),
                                       (28.0, 30.0), (28.0, 42.0),
                                       (0.0, 42.0)], segments=64, mat=dark)
    barrel.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(barrel, LENS_X, 0.0, BODY_Z)

    lens = bkit.lathe("FrontLens", [(0.0, 32.0), (27.0, 32.0), (27.0, 37.0),
                                    (0.0, 37.0)], segments=64, mat=glass)
    lens.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(lens, LENS_X, 0.0, BODY_Z)

    bkit.tube("LensRing", 35.5, 30.0, 5.0, segments=64,
              centre=(CW / 2.0 + 16.0, 0.0, BODY_Z), axis="X", mat=lens_rim)

    # ---- top cooling grille: 8 x 4 real holes at 20 mm pitch -------------
    bkit.perforated_panel("TopVent", 8, 4, 20.0, 20.0, 7.0, 170.0, 90.0, 4.0,
                          mat=dark)
    bkit.move(bpy.data.objects["TopVent"], 20.0, 34.0, BODY_Z + CH / 2.0)

    # ---- rear air filter, the same recipe turned to face -Y --------------
    filt = bkit.perforated_panel("RearFilter", 9, 5, 18.0, 18.0, 6.0, 170.0,
                                 98.0, 3.0, mat=dark)
    filt.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(filt, -60.0, -CD / 2.0 - 1.0, BODY_Z - 8.0)

    # ---- control pad: five buttons from one lay_out ----------------------
    bkit.rounded_box("ControlPad", 118.0, 34.0, 5.0, r=3.0, segments=2,
                     centre=(-88.0, -70.0, BODY_Z + CH / 2.0 - 1.0), mat=dark)
    buttons = []
    for i, (bx, bw) in enumerate(bkit.lay_out([14.0] * SPEC["control_buttons"],
                                              gap=8.0)):
        buttons.append(bkit.rounded_box(
            "Button%d" % i, bw, 20.0, 4.0, r=2.0, segments=2,
            centre=(-88.0 + bx - 52.0, -70.0, BODY_Z + CH / 2.0 + 1.0),
            mat=shell))
    bkit.join(buttons, name="ControlButtons")

    # ---- power lamp and two rear ports ----------------------------------
    bkit.cylinder("PowerLed", 4.0, 2.0, segments=16,
                  centre=(-150.0, -70.0, BODY_Z + CH / 2.0 + 1.0), mat=led)
    ports = []
    for i, (px, pw) in enumerate(bkit.lay_out([26.0, 26.0], gap=10.0)):
        ports.append(bkit.rounded_box("_port%d" % i, pw, 6.0, 14.0, r=1.5,
                                     segments=2,
                                     centre=(90.0 + px, -CD / 2.0 + 1.0,
                                             BODY_Z - 30.0), mat=dark))
    bkit.join(ports, name="RearPorts")

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="chassis_width", mm=330.0, tol=0.6, how="bbox_x",
         part="ProjectorChassis"),
    dict(name="chassis_depth", mm=240.0, tol=0.6, how="bbox_y",
         part="ProjectorChassis"),
    dict(name="chassis_height", mm=108.0, tol=0.6, how="bbox_z",
         part="ProjectorChassis"),
    dict(name="lens_barrel_diameter", mm=68.0, tol=0.6, how="diameter",
         part="LensBarrel"),
    dict(name="lens_diameter", mm=54.0, tol=0.6, how="diameter",
         part="FrontLens"),
]