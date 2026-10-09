"""
refrigerator -- 600 x 600 x 1800 mm top-freezer refrigerator: one enamelled
cabinet, two proud doors separated by a real recessed reveal, a vertical bar
handle on the fresh-food door and a horizontal one on the freezer, adjustable
feet, and a louvred compressor grille at the back.

The door reveal is the whole appliance language here: without a genuine gap
between two separate door leaves it reads as a plain wardrobe.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=600.0,
    cabinet_depth=600.0,
    overall_height=1800.0,   # feet on the floor to the top of the cabinet
    foot_height=20.0,
    corner_radius=16.0,
    door_width=596.0,        # 2 mm reveal down each side of the cabinet
    door_thickness=46.0,
    door_stand_off=22.0,     # how far a door leaf stands proud of the carcass
    door_gap=8.0,            # the recessed shadow line between the two leaves
    freezer_door_height=700.0,
    handle_bar_diameter=34.0,
    handle_stand_off=34.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
H = SPEC["overall_height"]
FOOT = SPEC["foot_height"]
DT = SPEC["door_thickness"]
DOOR_Y = -(D / 2.0) - SPEC["door_stand_off"] + DT / 2.0   # centre of a leaf
FRONT = -(D / 2.0)
FRIDGE_TOP = FOOT + (H - FOOT) - SPEC["freezer_door_height"] - SPEC["door_gap"]


def build():
    enamel = bkit.pbr("FridgeEnamel", base=(0.90, 0.90, 0.89),
                      metal=0.0, rough=0.26, coat=0.3)
    steel = bkit.preset("polished_metal")
    dark = bkit.preset("black_plastic")

    # ---- carcass ----------------------------------------------------------
    body = bkit.rounded_box("FridgeCabinet", W, D, H - FOOT, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, FOOT + (H - FOOT) / 2.0),
                            mat=enamel)

    # ---- two door leaves --------------------------------------------------
    # Heights come from the real gap, not two independent constants: the reveal
    # only appears if the fresh-food leaf stops short of the freezer leaf by
    # exactly the gap that was declared.
    freezer_h = SPEC["freezer_door_height"]
    fridge_h = FRIDGE_TOP - FOOT
    bkit.rounded_box("FreezerDoor", SPEC["door_width"], DT, freezer_h, r=12.0,
                     segments=5,
                     centre=(0.0, DOOR_Y, H - freezer_h / 2.0), mat=enamel)
    bkit.rounded_box("FridgeDoor", SPEC["door_width"], DT, fridge_h, r=12.0,
                     segments=5,
                     centre=(0.0, DOOR_Y, FOOT + fridge_h / 2.0), mat=enamel)

    # ---- handles ----------------------------------------------------------
    # A bar handle stands off the leaf face by its own radius plus a standoff,
    # and is kept in the leaf by a few mm so it never floats.
    r = SPEC["handle_bar_diameter"] / 2.0
    bar_y = FRONT - SPEC["door_stand_off"] - r + 3.0
    bkit.cylinder("FridgeHandle", r, 420.0, segments=40, axis="Z",
                  centre=(W / 2.0 - 90.0, bar_y, FOOT + 700.0), mat=steel)
    for i, z in enumerate((FOOT + 520.0, FOOT + 880.0)):
        bkit.rounded_box("FridgeHandleMount%d" % i, 26.0, 16.0, 26.0, r=6.0,
                         segments=3,
                         centre=(W / 2.0 - 90.0,
                                 FRONT - SPEC["door_stand_off"] - 4.0, z),
                         mat=steel)

    bkit.cylinder("FreezerHandle", r, 360.0, segments=40, axis="X",
                  centre=(-40.0, bar_y, FRIDGE_TOP + SPEC["door_gap"] + 60.0),
                  mat=steel)
    for i, x in enumerate((-190.0, 110.0)):
        bkit.rounded_box("FreezerHandleMount%d" % i, 26.0, 16.0, 26.0, r=6.0,
                         segments=3,
                         centre=(x, FRONT - SPEC["door_stand_off"] - 4.0,
                                 FRIDGE_TOP + SPEC["door_gap"] + 60.0),
                         mat=steel)

    # ---- hinge caps down the left edge ------------------------------------
    for i, z in enumerate((FOOT + 160.0, FRIDGE_TOP + 120.0, H - 120.0)):
        bkit.rounded_box("HingeCap%d" % i, 20.0, 14.0, 46.0, r=5.0, segments=2,
                         centre=(-(W / 2.0) + 12.0,
                                 FRONT - SPEC["door_stand_off"] + 6.0, z),
                         mat=steel)

    # ---- adjustable feet --------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 22.0, FOOT, segments=32,
                          centre=(sx * (W / 2.0 - 48.0), sy * (D / 2.0 - 48.0),
                                  FOOT / 2.0),
                          mat=dark)

    # ---- compressor louvres on the back -----------------------------------
    # 12 slots on a computed pitch, centred in the 600 mm width.
    n = 12
    pitch = 34.0
    span = (n - 1) * pitch
    louvre = bkit.rounded_box("RearVent", 24.0, 10.0, 10.0, r=3.0, segments=2,
                              centre=(-span / 2.0, D / 2.0 - 2.0, FOOT + 130.0),
                              mat=dark)
    bkit.array_linear(louvre, n, (pitch, 0.0, 0.0))

    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="cabinet_width", mm=600.0, tol=0.5, how="bbox_x", part="FridgeCabinet"),
    dict(name="cabinet_depth", mm=600.0, tol=0.5, how="bbox_y", part="FridgeCabinet"),
    dict(name="overall_height", mm=1800.0, tol=0.8, how="bbox_z"),
    dict(name="overall_width", mm=600.0, tol=0.5, how="bbox_x"),
    dict(name="handle_bar_diameter", mm=34.0, tol=0.4, how="diameter",
         part="FridgeHandle"),
    dict(name="freezer_door_height", mm=700.0, tol=0.5, how="bbox_z",
         part="FreezerDoor"),
]