"""
desktop_tower -- 210 x 450 x 480 mm mid-tower ATX case.

Counts are the model here. The front is a real `perforated_panel` -- 13 x 28
= 364 holes at a 14 mm pitch -- standing in a milled recess, which is the
single most recognisable feature of a modern tower. Behind it sit ten intake
louvres, seven rear expansion-slot covers and a PSU, and the two USB headers
plus three audio jacks on the top-front I/O are one `lay_out` row.

`perforated_panel` ignores its `panel_sx/panel_sy` arguments -- the sheet is
exactly the hole field -- so the real panel size is
`(cols-1)*pitch + 2*hole_r` and cols/rows are solved backwards from the
210 x 480 front face instead of being declared and then ignored.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=210.0,
    depth=450.0,
    height=480.0,
    foot_height=12.0,
    mesh_cols=13,
    mesh_rows=24,
    mesh_pitch=14.0,
    mesh_hole_r=4.0,
    intake_louvres=10,
    expansion_slots=7,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
FOOT = SPEC["foot_height"]
CASE_H = H - FOOT                   # a 480 mm tower is measured over its feet
CASE_ZC = FOOT + CASE_H / 2.0
MC, MR = SPEC["mesh_cols"], SPEC["mesh_rows"]
MP, MHR = SPEC["mesh_pitch"], SPEC["mesh_hole_r"]
FRONT = D / 2.0
# 24 rows at a 14 mm pitch is a 330 mm sheet; centred at 285 it leaves a
# 115 mm band of louvres and top bezel inside the 12..480 case. Centred
# higher, the milled recess breaks out through the case's top edge.
MESH_Z = 285.0
MESH_Y = FRONT - 5.0

# perforated_panel's panel_sx/panel_sy are decorative: the sheet is the field.
MESH_W = (MC - 1) * MP + 2 * MHR
MESH_H = (MR - 1) * MP + 2 * MHR


def build():
    steel = bkit.pbr("TowerSteel", base=(0.26, 0.27, 0.29), metal=0.85,
                     rough=0.40)
    mesh = bkit.preset("dark_metal")
    dark = bkit.pbr("TowerDark", base=(0.10, 0.10, 0.12), rough=0.44)
    plastic = bkit.pbr("TowerPlastic", base=(0.32, 0.33, 0.36), rough=0.36)
    led = bkit.pbr("TowerLed", base=(0.12, 0.60, 0.32), rough=0.20,
                   emission=(0.10, 0.80, 0.40), emission_strength=1.2)

    case = bkit.rounded_box("TowerCase", W, D, CASE_H, r=4.0, segments=3,
                            centre=(0, 0, CASE_ZC), mat=steel)

    # ---- milled recess for the front mesh, one cut for the whole aperture
    bkit.boolean(case, bkit.rounded_box(
        "_mesh_rec", MESH_W + 10.0, 10.0, MESH_H + 10.0, r=3.0, segments=3,
        centre=(0, FRONT - 2.0, MESH_Z)), "DIFFERENCE")

    # ---- the perforated front panel, stood up and set in the recess ------
    panel = bkit.perforated_panel("TowerFrontMesh", cols=MC, rows=MR,
                                  pitch_x=MP, pitch_y=MP, hole_r=MHR,
                                  panel_sx=MESH_W, panel_sy=MESH_H,
                                  thickness=1.5, mat=mesh)
    panel.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bkit.move(panel, 0.0, MESH_Y, MESH_Z)

    # ---- ten intake louvres under the mesh, one arrayed cutter ----------
    louvre = bkit.rounded_box("_lv", MESH_W - 20.0, 8.0, 6.0, r=1.6,
                              segments=2, centre=(0, FRONT - 1.0, 25.0),
                              mat=dark)
    bkit.array_linear(louvre, count=SPEC["intake_louvres"], offset_mm=(0, 0, 10.0))
    bkit.boolean(case, louvre, "DIFFERENCE")

    # ---- seven rear expansion-slot covers, one arrayed cutter -----------
    slot = bkit.rounded_box("_slot", 8.0, 108.0, 15.0, r=1.0, segments=2,
                            centre=(0, -FRONT + 1.0, 200.0), mat=dark)
    bkit.array_linear(slot, count=SPEC["expansion_slots"], offset_mm=(0, 0, 20.0))
    bkit.boolean(case, slot, "DIFFERENCE")

    # ---- top-front I/O: two USB headers and three audio jacks -----------
    io_parts = []
    for i, (y, w) in enumerate(bkit.lay_out([14.0, 14.0, 6.0, 6.0, 6.0],
                                            gap=6.0)):
        if i < 2:
            io_parts.append(bkit.rounded_box(
                "_u%d" % i, w, 7.0, 3.0, r=0.8, segments=2,
                centre=(0, y + 130.0, H - 0.6), mat=plastic))
        else:
            io_parts.append(bkit.cylinder(
                "_a%d" % i, 2.6, 3.0, segments=20,
                centre=(0, y + 130.0, H - 0.6), mat=dark))
    bkit.join(io_parts, name="TowerIo")

    # ---- power button and status LED on the top front bezel --------------
    bkit.cylinder("TowerPowerButton", 9.0, 4.0, segments=32, axis="Y",
                  centre=(0, FRONT + 1.0, 468.0), mat=plastic)
    bkit.cylinder("TowerStatusLed", 2.2, 3.0, segments=20, axis="Y",
                  centre=(26.0, FRONT + 0.6, 468.0), mat=led)

    # ---- PSU block in the bottom rear ------------------------------------
    bkit.rounded_box("TowerPsu", 150.0, 86.0, 86.0, r=2.0, segments=2,
                     centre=(0, -FRONT + 60.0, 55.0), mat=dark)

    # ---- four feet on a computed grid ------------------------------------
    feet = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=W - 30.0,
                                                   pitch_y=D - 40.0)):
        feet.append(bkit.rounded_box(
            "_ft%d" % i, 26.0, 30.0, FOOT, r=2.0, segments=2,
            centre=(x, y, FOOT / 2.0), mat=dark))
    bkit.join(feet, name="TowerFeet")

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="width", mm=210.0, tol=0.8, how="bbox_x", part="TowerCase"),
    dict(name="depth", mm=450.0, tol=0.8, how="bbox_y", part="TowerCase"),
    dict(name="overall_height", mm=480.0, tol=1.0, how="bbox_z"),
]
