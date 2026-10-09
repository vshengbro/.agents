"""
desk_organiser -- compartmented desk tray, 130 x 90 x 65 mm.

Five upright walls around a base, with three dividers laid out from the real
wall thickness plus an explicit gap. grid_positions rather than hand-placed
constants: two dividers on the same x coordinate is what turns an EXACT
boolean into an empty scene, and this model needs no boolean at all because
the walls simply meet.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=130.0,
    depth=90.0,
    height=65.0,
    wall=3.0,
    compartments=3,
    base_thickness=4.0,
)

W = SPEC["width"]
D = SPEC["depth"]
H = SPEC["height"]
WT = SPEC["wall"]
BT = SPEC["base_thickness"]


def build():
    shell = bkit.pbr("OrganiserShell", base=(0.42, 0.44, 0.48), rough=0.38,
                     coat=0.2)
    tray = bkit.pbr("OrganiserTray", base=(0.32, 0.34, 0.38), rough=0.42)

    base = bkit.rounded_box("OrganiserBase", W, D, BT, r=1.5,
                            centre=(0, 0, BT / 2.0), mat=tray)

    # perimeter walls
    walls = []
    for (name, sx, sy, cx, cy) in (
        ("WallBack", W, WT, 0, D / 2.0 - WT / 2.0),
        ("WallFront", W, WT, 0, -D / 2.0 + WT / 2.0),
        ("WallLeft", WT, D - 2 * WT, -W / 2.0 + WT / 2.0, 0),
        ("WallRight", WT, D - 2 * WT, W / 2.0 - WT / 2.0, 0),
    ):
        walls.append(bkit.rounded_box(
            "Organiser" + name, sx, sy, H - BT, r=1.2,
            centre=(cx, cy, BT + (H - BT) / 2.0), mat=shell))
    wall = bkit.join(walls, name="OrganiserWalls")

    # inner dividers: pitch computed from the clear span and the wall thickness
    inner_span = D - 2 * WT
    div_pitch = (W - 2 * WT) / SPEC["compartments"]
    dividers = []
    for i, (x, _w) in enumerate(bkit.grid_positions(
            cols=SPEC["compartments"] - 1, rows=1,
            pitch_x=div_pitch, pitch_y=1.0)):
        dividers.append(bkit.rounded_box(
            "OrganiserDivider%d" % (i + 1), WT - 0.6, inner_span,
            (H - BT) * 0.62, r=1.0,
            centre=(x, 0, BT + (H - BT) * 0.31), mat=shell))
    divider = bkit.join(dividers, name="OrganiserDividers")
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="width", mm=130.0, tol=0.5, how="bbox_x", part="OrganiserBase"),
    dict(name="depth", mm=90.0, tol=0.5, how="bbox_y", part="OrganiserBase"),
    dict(name="height", mm=65.0, tol=0.6, how="bbox_z"),
]