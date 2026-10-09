"""
dresser -- four-drawer chest of drawers, 1040 x 480 mm top, 850 mm high.

Chest-of-drawers proportion is a stack: four equal drawer fronts at 145 mm with
20 mm reveals fill the 700 mm carcass, the 100 mm recessed plinth lifts the
whole mass off the floor, and the 50 mm top overhangs on every side so the
piece reads as furniture rather than as a filing cabinet.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=1040.0,              # width over the top
    depth=480.0,               # depth over the top
    height=850.0,
    top_thickness=50.0,
    carcass_width=1000.0,
    carcass_depth=450.0,
    carcass_height=700.0,
    plinth_height=100.0,
    plinth_inset=20.0,
    drawer_count=4,
    drawer_front_width=940.0,
    drawer_front_height=145.0,
    drawer_front_thickness=22.0,
    drawer_gap=20.0,
    handle_length=160.0,
    handle_diameter=18.0,
)

TOP_W, TOP_D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
CW, CD, CH = SPEC["carcass_width"], SPEC["carcass_depth"], SPEC["carcass_height"]
PLINTH_H = SPEC["plinth_height"]
PLINTH_Z0 = PLINTH_H
CARC_Z0 = PLINTH_H
CARC_CZ = CARC_Z0 + CH / 2.0            # 450
TOP_CZ = CARC_Z0 + CH + SPEC["top_thickness"] / 2.0   # 825
DF_W = SPEC["drawer_front_width"]
DF_H = SPEC["drawer_front_height"]
DF_T = SPEC["drawer_front_thickness"]
DF_Y = -CD / 2.0 - DF_T / 2.0
FRONT_Z = CARC_Z0 + CH / 2.0            # vertical centre of the drawer bank

CHECKS = [
    dict(name="overall_width", mm=1040.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=850.0, tol=0.3, how="bbox_z"),
    dict(name="top_thickness", mm=50.0, tol=0.3, how="bbox_z", part="Top"),
    dict(name="carcass_height", mm=700.0, tol=0.3, how="bbox_z", part="Carcass"),
    dict(name="drawer_front_width", mm=940.0, tol=0.3, how="bbox_x",
         part="DrawerFront0"),
    dict(name="drawer_front_height", mm=145.0, tol=0.3, how="bbox_z",
         part="DrawerFront0"),
]


def build():
    wood = bkit.pbr("DresserOak", base=(0.44, 0.29, 0.15), metal=0.0, rough=0.38)
    wood_dark = bkit.pbr("DresserPlinth", base=(0.31, 0.19, 0.09), metal=0.0,
                         rough=0.45)
    brass = bkit.preset("gold")

    inset = SPEC["plinth_inset"]
    bkit.rounded_box("Plinth", CW - 2 * inset, CD - 2 * inset, PLINTH_H, r=4.0,
                     segments=2, centre=(0, 0, PLINTH_H / 2.0), mat=wood_dark)
    bkit.rounded_box("Carcass", CW, CD, CH, r=6.0, segments=3,
                     centre=(0, 0, CARC_CZ), mat=wood)
    bkit.rounded_box("Top", TOP_W, TOP_D, SPEC["top_thickness"], r=7.0,
                     segments=4, centre=(0, 0, TOP_CZ), mat=wood)

    # ---- drawer bank: 4 x 145 mm fronts with 20 mm reveals -----------------
    rows = bkit.lay_out([DF_H] * SPEC["drawer_count"], gap=SPEC["drawer_gap"])
    for i, (dz, _w) in enumerate(rows):
        cz = FRONT_Z + dz
        bkit.rounded_box("DrawerFront%d" % i, DF_W, DF_T, DF_H, r=4.0,
                         segments=3, centre=(0, DF_Y, cz), mat=wood)
        bkit.cylinder("Handle%d" % i, SPEC["handle_diameter"] / 2.0,
                      SPEC["handle_length"], segments=32,
                      centre=(0, DF_Y - DF_T / 2.0 - 16.0, cz), axis="X",
                      mat=brass)

    return dict(spec=SPEC, parts=11)
