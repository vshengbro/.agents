"""
crutches -- a pair of 1150 mm axillary crutches, laid side by side on the floor.

The handgrip is not a second cylinder but the top of the shaft's elbow: an arc
solved from the shaft axis up to the grip, so grip and shaft read as one
pressing. Parts stay separate and named -- shaft, ferrule, pad, elbow, grip --
so each dimension can be measured on the part that owns it, and the second
crutch is a duplicate of each of them at the real pair spacing.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_length=1150.0,
    shaft_diameter=22.0,
    shaft_foot_diameter=18.0,
    grip_diameter=26.0,
    grip_length=130.0,
    pad_size=95.0,
    pair_spacing=110.0,
    ferrule_diameter=27.0,
)

L = SPEC["overall_length"]
SH_R = SPEC["shaft_diameter"] / 2.0        # 11.0
GR_R = SPEC["grip_diameter"] / 2.0        # 13.0
Z_AXIS = SH_R + 14.0                      # 25.0: shaft axis above the floor
ELBOW_R = 78.0                            # arc from the shaft up to the grip
GRIP_X0, GRIP_X1 = 250.0, 250.0 + SPEC["grip_length"]
PAD_X = L - 78.0


def one_crutch(suffix, y):
    """Build one crutch's five named parts at lateral offset `y`."""
    # At metal=0.84 the shafts have almost no diffuse term and mirror the dark
    # part of the studio, so the whole crutch rendered as a near-black stick
    # with no visible edge. Real crutch tubing is bright mill-finish aluminium:
    # a high base value with metal pulled back to 0.55 keeps the metallic read
    # while still catching enough diffuse light to show the tube's round section.
    alu = bkit.pbr("CrutchAlu", base=(0.90, 0.91, 0.93), metal=0.55, rough=0.20)
    # the grips and pads were 0.10-0.12 base, i.e. effectively black; a real
    # crutch grip is dark grey rubber, still light enough to hold an edge
    grip_mat = bkit.pbr("CrutchGrip", base=(0.30, 0.30, 0.32), rough=0.62)
    pad_mat = bkit.pbr("CrutchPad", base=(0.26, 0.26, 0.28), rough=0.58)
    rubber = bkit.pbr("CrutchFerrule", base=(0.20, 0.20, 0.21), rough=0.72)

    shaft = bkit.cylinder("Shaft" + suffix,
                          SPEC["shaft_foot_diameter"] / 2.0, L - 25.0,
                          segments=32, axis="X", r2=SH_R,
                          centre=(25.0 + (L - 25.0) / 2.0, y, Z_AXIS),
                          mat=alu)

    # the ferrule is a revolve; lay it on its side so it runs along the shaft
    ferrule = bkit.lathe("Ferrule" + suffix, [
        (0.0, 0.0), (SPEC["ferrule_diameter"] / 2.0 - 1.0, 0.0),
        (SPEC["ferrule_diameter"] / 2.0, 2.5),
        (SPEC["ferrule_diameter"] / 2.0, 46.0),
        (SH_R + 0.5, 50.0), (0.0, 50.0),
    ], segments=32, mat=rubber)
    ferrule.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(ferrule, 0.0, y, SPEC["ferrule_diameter"] / 2.0)

    pad = bkit.rounded_box("UnderarmPad" + suffix, SPEC["pad_size"], 74.0,
                           26.0, r=10.0, segments=3,
                           centre=(PAD_X, y, Z_AXIS + 21.0), mat=pad_mat)
    stem = bkit.cylinder("PadStem" + suffix, 13.0, 26.0, segments=24,
                         centre=(PAD_X, y, Z_AXIS + 3.0), mat=alu)

    elbow = bkit.arc_torus("GripElbow" + suffix, ELBOW_R, SH_R - 0.6,
                           90.0, 180.0, centre=(GRIP_X0, y, Z_AXIS),
                           plane="XZ", seg_major=28, mat=alu, caps=True)

    grip = bkit.cylinder("Handgrip" + suffix, GR_R, SPEC["grip_length"],
                         segments=32, axis="X",
                         centre=((GRIP_X0 + GRIP_X1) / 2.0, y,
                                 Z_AXIS + ELBOW_R), mat=grip_mat)
    return [shaft, ferrule, pad, stem, elbow, grip]


def build():
    one_crutch("", 0.0)
    one_crutch("B", SPEC["pair_spacing"])
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="overall_length", mm=1150.0, tol=4.0, how="bbox_x"),
    # The shaft and the grip both run along X, so `diameter` (the larger of
    # bbox_x/bbox_y) would measure their LENGTH. bbox_y is the diameter.
    dict(name="shaft_diameter", mm=22.0, tol=0.4, how="bbox_y", part="Shaft"),
    dict(name="grip_diameter", mm=26.0, tol=0.4, how="bbox_y",
         part="Handgrip"),
    dict(name="pad_size", mm=95.0, tol=0.4, how="bbox_x", part="UnderarmPad"),
]