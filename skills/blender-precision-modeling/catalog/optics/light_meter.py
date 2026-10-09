"""
light_meter -- 56 x 32 x 176 mm handheld photographic exposure meter: body,
40 mm hemispherical incident dome, recessed LCD, a knurled calculating dial
with 18 swept ribs and a four-key pad.

Small instrument, science-domain furniture in an optics housing. The dome is a
`lathe` hemisphere rather than a sphere: a full sphere half-buried in the body
leaves a visible seam, and a real meter's dome is a hemisphere that sits ON the
top face. The 18 dial ribs are a `box` at radius 17 swept about Y.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    body_width=56.0,
    body_depth=32.0,
    overall_height=176.0,
    dome_diameter=40.0,
    dial_diameter=34.0,
    dial_ribs=18,
    keypad_buttons=4,
    screen_size=44.0,
)

BODY_W, BODY_D = SPEC["body_width"], SPEC["body_depth"]
BODY_H = 150.0
BODY_Z = BODY_H / 2.0 + 12.0        # body centre; 12 mm clear of the floor


def build():
    shell = bkit.pbr("MeterShell", base=(0.78, 0.77, 0.74), rough=0.36)
    dark = bkit.pbr("MeterDark", base=(0.075, 0.075, 0.080), rough=0.42)
    lcd = bkit.pbr("MeterLcd", base=(0.10, 0.13, 0.10), rough=0.09,
                   emission=(0.42, 0.62, 0.34), emission_strength=1.1)
    chrome = bkit.preset("polished_metal")

    # ---- body, recessed a hair above the floor on its switch tab ---------
    bkit.rounded_box("MeterBody", BODY_W, BODY_D, BODY_H, r=8.0, segments=3,
                     centre=(0.0, 0.0, BODY_Z), mat=shell)
    bkit.rounded_box("SwitchTab", 30.0, 20.0, 18.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 9.0), mat=dark)

    # ---- 40 mm incident dome. lathe profiles carry ABSOLUTE z. -----------
    bkit.lathe("MeterDome", [(0.0, 160.0), (20.0, 160.0), (19.0, 167.0),
                             (15.0, 172.0), (9.0, 175.0), (0.0, 176.0)],
               segments=48, mat=chrome)

    # ---- LCD: a bezel standing 3 mm proud, the glass 1 mm behind it -------
    bezel_z = BODY_Z + 38.0
    bkit.rounded_box("ScreenBezel", 50.0, 6.0, 32.0, r=3.0, segments=2,
                     centre=(0.0, -14.0, bezel_z), mat=dark)
    bkit.rounded_box("MeterScreen", SPEC["screen_size"], 4.0, 24.0, r=2.0,
                     segments=2, centre=(0.0, -12.0, bezel_z), mat=lcd)

    # ---- calculating dial on the front, with 18 swept ribs ---------------
    dial_z = BODY_Z - 12.0
    bkit.cylinder("MeterDial", 17.0, 14.0, segments=48, axis="Y",
                  centre=(0.0, -15.0, dial_z), mat=dark)
    # 18 ribs, built at radius 17.4 from the world Y axis so array_radial has a
    # real axis to orbit, then moved onto the dial centre. Placing the rib at
    # the dial's own z would sweep it round the origin at that radius instead.
    rib = bkit.box("_rib", 2.4, 12.0, 1.4, centre=(0.0, 0.0, 17.4),
                   mat=chrome)
    bkit.array_radial(rib, count=SPEC["dial_ribs"], axis="Y")
    bkit.move(rib, 0.0, -15.0, dial_z)
    bkit.cylinder("DialPointer", 1.6, 4.0, segments=12, axis="Y",
                  centre=(11.0, -20.0, dial_z), mat=chrome)

    # ---- four keys from one grid ----------------------------------------
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(2, 2, 24.0, 18.0)):
        keys.append(bkit.rounded_box(
            "MeterKey%d" % i, 18.0, 5.0, 13.0, r=2.5, segments=2,
            centre=(kx, -14.0, BODY_Z - 56.0 + kz), mat=dark))
    bkit.join(keys, name="MeterKeypad")

    # ---- rear photocell and a strap eye ----------------------------------
    bkit.cylinder("RearCell", 9.0, 4.0, segments=24, axis="Y",
                  centre=(0.0, 17.0, BODY_Z + 50.0), mat=dark)
    bkit.torus("StrapEye", 7.0, 2.0, seg_major=28, seg_minor=10, axis="Y",
               centre=(0.0, 0.0, BODY_Z + 78.0), mat=chrome)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="body_width", mm=56.0, tol=0.4, how="bbox_x", part="MeterBody"),
    dict(name="body_depth", mm=32.0, tol=0.4, how="bbox_y", part="MeterBody"),
    dict(name="overall_height", mm=176.0, tol=0.6, how="bbox_z"),
    dict(name="dome_diameter", mm=40.0, tol=0.4, how="diameter",
         part="MeterDome"),
    dict(name="dial_diameter", mm=34.0, tol=0.4, how="diameter",
         part="MeterDial"),
]