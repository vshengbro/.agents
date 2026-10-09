"""
dice_tower -- 220 x 70 x 70 mm tower with a roof, a ramp and a landing tray.

A dice tower only works if you can see the three things that make it work: the
roof that the die rolls off, the internal ramp that catches it, and the tray at
the bottom that stops it. So the roof, the ramp and the tray are all separate
solids inside a two-walled shell, and the two walls are a single extruded side
profile rather than five boxes.

The side profile is a plain L with a chamfered foot -- no collinear
back-to-back edges, which is what makes a stepped profile degenerate when it
is tried in one outline. The die that lands in the tray is 16 mm on a 70 mm
inside width, the real 16 mm die this tower is sized for.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

H = 220.0               # tower height
W = 70.0                 # width across the die channel
D = 70.0                 # depth (the two side walls)
WALL_T = 5.0
RAMP_RAKE = 52.0         # degrees the internal ramp falls at
RAMP_T = 4.0
TRAY_H = 34.0
TRAY_L = 62.0
ROOF_L = 58.0
ROOF_T = 5.0
DIE = 16.0

SPEC = dict(height=H, width=W, depth=D, wall_thickness=WALL_T,
            ramp_rake=RAMP_RAKE, tray_height=TRAY_H,
            roof_length=ROOF_L, die_size=DIE)


def build():
    wood = bkit.pbr("TowerWood", base=(0.36, 0.22, 0.11), metal=0.0, rough=0.50)
    dark = bkit.pbr("TowerDark", base=(0.10, 0.08, 0.07), metal=0.0, rough=0.60)
    felt = bkit.pbr("TowerFelt", base=(0.08, 0.22, 0.12), metal=0.0, rough=0.90)
    ivory = bkit.pbr("TowerDie", base=(0.92, 0.90, 0.84), metal=0.0, rough=0.28)

    # ---- the two side walls: one profile, extruded across the channel ------
    # Profile in (x = depth, z = height): a plain rectangle with the front foot
    # chamfered. Every vertex is a real corner, so the polygon is simple.
    wall_profile = [
        (0.0, 0.0),
        (D, 0.0),
        (D, H),
        (0.0, H),
        (0.0, 22.0),
        (14.0, 0.0),
    ]
    walls = []
    for sx in (-1.0, 1.0):
        walls.append(bkit.extrude_profile("TowerWall", wall_profile, WALL_T,
                                          axis="Y",
                                          centre=(0.0, sx * (W / 2.0 - WALL_T / 2.0),
                                                  0.0), mat=wood))
    bkit.join(walls, name="TowerWalls")

    # ---- the back and the roof ---------------------------------------------
    back = bkit.rounded_box("TowerBack", WALL_T, W - 2.0 * WALL_T, H - 10.0, r=1.5,
                            segments=2,
                            centre=(D / 2.0 - WALL_T / 2.0, 0.0, (H - 10.0) / 2.0),
                            mat=wood)
    roof = bkit.rounded_box("Roof", ROOF_L, W - 2.0 * WALL_T, ROOF_T, r=2.0,
                            segments=2,
                            centre=(D / 2.0 - ROOF_L / 2.0 + 4.0, 0.0,
                                    H - 12.0), mat=wood)
    roof.rotation_euler = (0.0, math.radians(-12.0), 0.0)

    # ---- the internal ramp --------------------------------------------------
    ramp = bkit.rounded_box("Ramp", 96.0, W - 2.0 * WALL_T - 1.0, RAMP_T, r=1.5,
                            segments=2,
                            centre=(D / 2.0 - 44.0, 0.0, H * 0.56), mat=wood)
    ramp.rotation_euler = (0.0, math.radians(-RAMP_RAKE), 0.0)
    # a felt strip glued to the ramp: the thing that actually stops the die
    bkit.rounded_box("RampFelt", 92.0, W - 2.0 * WALL_T - 6.0, 1.2, r=0.5, segments=2,
                     centre=(D / 2.0 - 44.0, 0.0, H * 0.56 - 3.4), mat=felt)

    # ---- the landing tray at the foot ---------------------------------------
    tray = bkit.rounded_box("LandingTray", TRAY_L, W - 2.0 * WALL_T - 1.0, TRAY_H,
                            r=3.0, segments=3,
                            centre=(D / 2.0 - TRAY_L / 2.0 - 2.0, 0.0,
                                    TRAY_H / 2.0 + 1.0), mat=dark)
    bkit.rounded_box("TrayFelt", TRAY_L - 10.0, W - 2.0 * WALL_T - 8.0, 1.2, r=0.5,
                     segments=2,
                     centre=(D / 2.0 - TRAY_L / 2.0 - 2.0, 0.0, TRAY_H - 1.0),
                     mat=felt)

    # ---- one 16 mm die, resting in the tray --------------------------------
    die = bkit.rounded_box("Die", DIE, DIE, DIE, r=2.6, segments=3,
                           centre=(D / 2.0 - TRAY_L / 2.0, 0.0, TRAY_H + DIE / 2.0),
                           mat=ivory)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="height", mm=220.0, tol=0.2, how="bbox_z", part="TowerWalls"),
    dict(name="width", mm=70.0, tol=0.1, how="bbox_y", part="TowerWalls"),
    dict(name="depth", mm=70.0, tol=0.1, how="bbox_x", part="TowerWalls"),
    dict(name="tray_height", mm=34.0, tol=0.2, how="bbox_z", part="LandingTray"),
    dict(name="die_size", mm=16.0, tol=0.1, how="bbox_x", part="Die")
]