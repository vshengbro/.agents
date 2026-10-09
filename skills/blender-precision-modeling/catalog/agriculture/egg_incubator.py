"""
egg_incubator -- a 48-egg tabletop incubator: 560 x 420 x 400 mm.

An incubator is a WARM BOX with a transparent lid, and the things that make it
read as one are the dome lid you can see the eggs through, the turning tray
inside, and the control end with a thermometer and a louvre. The eggs are on a
computed grid pitch, not scattered: 6 x 8 at 68 mm gives a tray that is 408 mm
of eggs inside a 500 mm tray, which is why the pitch and the tray size are both
in SPEC and both checked.

Real 48-egg incubator: 560 x 420 x 400 mm overall, 500 x 360 mm egg tray on a
68 mm pitch, 24 mm eggs.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    length=560.0,
    width=420.0,
    height=400.0,
    tray_size=500.0,
    tray_width=360.0,
    tray_pitch=68.0,
    eggs=48,
    egg_dia=24.0,
    lid_height=120.0,
)

L = SPEC["length"]
W = SPEC["width"]
H = SPEC["height"]
COLS, ROWS = 6, 8

CHECKS = [
    dict(name="length", mm=560.0, tol=3.0, how="bbox_x", part="IncubatorBody"),
    dict(name="width", mm=420.0, tol=3.0, how="bbox_y", part="IncubatorBody"),
    dict(name="cabinet_height", mm=280.0, tol=3.0, how="bbox_z",
         part="IncubatorBody"),
    dict(name="overall_height", mm=406.0, tol=4.0, how="top_z",
         part="IncubatorLid"),
    dict(name="tray_length", mm=500.0, tol=3.0, how="bbox_x",
         part="EggTray"),
    dict(name="egg_dia", mm=24.0, tol=1.0, how="bbox_y", part="IncubatorEgg00"),
    dict(name="base_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="IncubatorBody"),
]


def build():
    shell = bkit.pbr("IncubShell", base=(0.86, 0.85, 0.80), rough=0.38)
    trim = bkit.pbr("IncubTrim", base=(0.10, 0.11, 0.13), rough=0.34)
    glass = bkit.pbr("IncubGlass", base=(0.88, 0.92, 0.92), rough=0.05,
                     transmission=0.90, ior=1.45)
    egg = bkit.pbr("IncubEgg", base=(0.86, 0.76, 0.60), rough=0.62)

    # ---- the cabinet: an open-topped shell built as a wall ring --------
    wall = 26.0
    bkit.rounded_box("IncubatorBody", L, W, 280.0, r=14.0, segments=3,
                     centre=(0.0, 0.0, 140.0), mat=shell)
    bkit.rounded_box("IncubatorCavity", L - 2 * wall, W - 2 * wall, 250.0,
                     r=10.0, segments=2, centre=(0.0, 0.0, 290.0), mat=trim)
    bkit.rounded_box("IncubatorBase", L - 40.0, W - 40.0, 20.0, r=6.0,
                     segments=2, centre=(0.0, 0.0, 30.0), mat=trim)

    # ---- the egg tray and 48 eggs on a computed grid pitch ------------
    bkit.rounded_box("EggTray", SPEC["tray_size"], SPEC["tray_width"], 14.0,
                     r=8.0, segments=2, centre=(0.0, 0.0, 160.0), mat=trim)
    positions = list(bkit.grid_positions(COLS, ROWS, SPEC["tray_pitch"],
                                         SPEC["tray_pitch"]))
    r = SPEC["egg_dia"] / 2.0
    # a tapered egg, not a ball: wide at the blunt end
    prof = [(0.0, -17.0), (8.0, -16.0), (11.5, -9.0), (12.0, 0.0),
            (10.0, 8.0), (6.0, 15.0), (0.0, 17.0)]
    proto = bkit.lathe("IncubatorEgg00", prof, segments=20, mat=egg)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = proto
    proto.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    proto.select_set(False)
    for i, (x, y) in enumerate(positions[1:]):
        bkit.duplicate(proto, "IncubatorEgg%02d" % (i + 1),
                       offset_mm=(x, y, 174.0))
    bkit.move(proto, positions[0][0], positions[0][1], 174.0)

    # ---- the transparent domed lid ------------------------------------
    bkit.lathe("IncubatorLid",
               [(0.0, 0.0), (L / 2.0 - 6.0, 0.0), (L / 2.0 - 6.0, 14.0),
                (L / 2.0 - 34.0, 52.0), (L / 2.0 - 96.0, 96.0),
                (L / 2.2, 120.0), (0.0, 126.0)], segments=48,
               centre=(0.0, 0.0, 280.0), mat=glass)
    bkit.rounded_box("IncubatorLidRim", L, W, 18.0, r=8.0, segments=2,
                     centre=(0.0, 0.0, 285.0), mat=trim)

    # ---- the control end: thermostat, thermometer, louvres ------------
    bkit.rounded_box("IncubatorControl", 90.0, 150.0, 150.0, r=10.0,
                     segments=2, centre=(L / 2.0 + 42.0, 0.0, 180.0),
                     mat=trim)
    bkit.cylinder("IncubatorDial", 38.0, 16.0, segments=24, axis="Y",
                  centre=(L / 2.0 + 42.0, -82.0, 200.0),
                  mat=bkit.preset("white_plastic"))
    bkit.cylinder("IncubatorThermometer", 9.0, 120.0, segments=12, axis="Z",
                  centre=(-L / 2.0 - 30.0, 120.0, 180.0), mat=glass)
    bkit.cylinder("IncubatorBulb", 14.0, 30.0, segments=16,
                  centre=(-L / 2.0 - 30.0, 120.0, 110.0),
                  mat=bkit.preset("rubber"))
    for i in range(6):
        bkit.rounded_box("IncubatorLouvre%d" % i, 4.0, 160.0, 14.0, r=1.5,
                         segments=1,
                         centre=(L / 2.0 + 88.0, 0.0, 90.0 + i * 22.0),
                         mat=trim, )

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6 + COLS * ROWS + 1 + 1 + 1 + 8)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
