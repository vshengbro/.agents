"""
dishwasher -- 600 x 600 x 850 mm fully integrated dishwasher: enamelled
cabinet on four feet, one tall door leaf with a recessed shadow gap all round
it, a recessed pocket handle across the top rail, a control strip with a lit
display and five keys, and a toe kick.

Integrated dishwashers have no visible hinges or knobs -- the whole read is
the gap between the leaf and the carcass plus that top pocket handle.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=600.0,
    cabinet_depth=600.0,
    cabinet_height=820.0,
    overall_height=850.0,     # feet to the top of the cabinet
    foot_height=30.0,
    corner_radius=8.0,
    door_width=588.0,         # 6 mm shadow gap down each side
    door_height=700.0,
    door_thickness=30.0,
    door_stand_off=20.0,
    toe_kick_height=70.0,
    key_diameter=18.0,
    key_pitch=40.0,
    option_keys=5,
    display_width=120.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
H = SPEC["cabinet_height"]
FOOT = SPEC["foot_height"]
TOP = FOOT + H
FRONT = -(D / 2.0)
DT = SPEC["door_thickness"]
DOOR_Y = FRONT - SPEC["door_stand_off"] + DT / 2.0
DOOR_Z0 = FOOT + SPEC["toe_kick_height"] + 8.0
DOOR_Z1 = DOOR_Z0 + SPEC["door_height"]
STRIP_Z = DOOR_Z1 - 26.0                 # control strip on the top edge
HANDLE_Z = DOOR_Z1 - 76.0                # pocket handle below the strip


def build():
    enamel = bkit.pbr("DwasherEnamel", base=(0.90, 0.90, 0.88),
                      metal=0.0, rough=0.24, coat=0.3)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("black_plastic")
    lamp = bkit.pbr("DwasherDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.40, 0.78, 0.95), emission_strength=1.5)

    # ---- carcass ----------------------------------------------------------
    body = bkit.rounded_box("DwasherCabinet", W, D, H, r=SPEC["corner_radius"],
                            segments=5, centre=(0.0, 0.0, FOOT + H / 2.0),
                            mat=enamel)

    # ---- door leaf --------------------------------------------------------
    # Set 12 mm proud of the carcass with a 6 mm reveal down each side, so the
    # leaf casts a real shadow line instead of merging into the cabinet face.
    bkit.rounded_box("DoorLeaf", SPEC["door_width"], DT, SPEC["door_height"],
                     r=10.0, segments=5,
                     centre=(0.0, DOOR_Y, (DOOR_Z0 + DOOR_Z1) / 2.0), mat=enamel)
    leaf = bpy.data.objects["DoorLeaf"]
    LEAF_FRONT = DOOR_Y - DT / 2.0

    # ---- pocket handle ----------------------------------------------------
    # A genuine opening cut through the top rail of the leaf, not a bar stuck
    # on the front: the blade is deliberately deeper than the leaf is thick so
    # it exits the back face instead of ending tangent to it.
    hz = HANDLE_Z
    cut = bkit.rounded_box("_handle_cut", 300.0, DT + 20.0, 44.0, r=8.0,
                           segments=3, centre=(0.0, DOOR_Y, hz))
    bkit.boolean(leaf, cut, "DIFFERENCE")
    bkit.recalc(leaf)
    bkit.health(leaf)

    bkit.rounded_box("HandleLip", 296.0, 10.0, 38.0, r=6.0, segments=3,
                     centre=(0.0, DOOR_Y + 4.0, hz), mat=steel)

    # ---- control strip ----------------------------------------------------
    # Mounted on the leaf face, so it sits proud of LEAF_FRONT, not of the
    # carcass: against the carcass it would be buried inside the door.
    bkit.rounded_box("ControlStrip", SPEC["door_width"] - 60.0, 12.0, 40.0,
                     r=5.0, segments=3,
                     centre=(0.0, LEAF_FRONT - 2.0, STRIP_Z), mat=dark)
    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 8.0, 32.0, r=3.0,
                     segments=2,
                     centre=(-(SPEC["door_width"] / 2.0) + 100.0,
                             LEAF_FRONT - 9.0, STRIP_Z),
                     mat=lamp)

    kd = SPEC["key_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["option_keys"], gap=SPEC["key_pitch"] - kd,
                         centre=False)):
        bkit.cylinder("OptionKey%d" % i, kd / 2.0, 10.0, segments=28, axis="Y",
                      centre=(-60.0 + x, LEAF_FRONT - 7.0, STRIP_Z), mat=steel)

    # ---- toe kick ---------------------------------------------------------
    bkit.rounded_box("ToeKick", W - 12.0, 22.0, SPEC["toe_kick_height"], r=4.0,
                     segments=3, centre=(0.0, FRONT + 6.0, FOOT + 35.0),
                     mat=steel)

    # ---- feet -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 22.0, FOOT, segments=32,
                          centre=(sx * (W / 2.0 - 54.0), sy * (D / 2.0 - 54.0),
                                  FOOT / 2.0),
                          mat=dark)

    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="cabinet_width", mm=600.0, tol=0.5, how="bbox_x", part="DwasherCabinet"),
    dict(name="cabinet_depth", mm=600.0, tol=0.5, how="bbox_y", part="DwasherCabinet"),
    dict(name="overall_height", mm=850.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=600.0, tol=0.5, how="bbox_x"),
    dict(name="door_width", mm=588.0, tol=0.5, how="bbox_x", part="DoorLeaf"),
    dict(name="door_height", mm=700.0, tol=0.5, how="bbox_z", part="DoorLeaf"),
]