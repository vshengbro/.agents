"""
inductor_coil -- 48 x 48 x 86 mm solenoid: a bobbin with two end flanges, a
real helical winding of enamelled wire, a ferrite core rod and two lead-out
wires.

The winding is `bkit.thread` -- an actual triangular-section helix swept along
a helix, not a stack of rings. Its core radius is set to the bobbin's outer
radius exactly, so the first turn of wire sits ON the former instead of
floating beside it, which is what makes 17 turns read as a coil rather than as
a spring.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    bobbin_diameter=40.0,
    bobbin_length=84.0,
    flange_diameter=48.0,
    core_diameter=12.0,
    turns=17,
    wire_diameter=3.0,
    overall_height=86.0,
    leads=(2.0, 8.0),
)

BOBBIN_R = SPEC["bobbin_diameter"] / 2.0
FLANGE_R = SPEC["flange_diameter"] / 2.0
WIRE_R = SPEC["wire_diameter"] / 2.0
WIND_LEN = 76.0


def build():
    former = bkit.pbr("CoilFormer", base=(0.10, 0.10, 0.11), rough=0.52)
    copper = bkit.pbr("CoilWire", base=(0.72, 0.42, 0.20), metal=0.85,
                      rough=0.30)
    ferrite = bkit.pbr("CoilCore", base=(0.20, 0.19, 0.18), rough=0.66)

    # ---- bobbin and its two end flanges -----------------------------------
    bkit.tube("CoilBobbin", BOBBIN_R, 13.0, SPEC["bobbin_length"],
              segments=48, centre=(0.0, 0.0, 44.0), mat=former)
    # Bottom flange bottom face exactly at z=0 so sit_on_floor shifts nothing and
    # the declared overall height is the model's own.
    for zc, tag in ((2.0, "Bottom"), (84.0, "Top")):
        bkit.tube("Flange" + tag, FLANGE_R, 13.0, 4.0, segments=48,
                  centre=(0.0, 0.0, zc), mat=former)

    # ---- the winding: a real helix with its core on the former surface ---
    bkit.thread("CoilWinding", BOBBIN_R + WIRE_R, 4.5, WIND_LEN,
                turns=SPEC["turns"], thread_h=WIRE_R, mat=copper,
                segments_per_turn=32)
    bkit.move(bpy.data.objects["CoilWinding"], 0.0, 0.0, 44.0)

    # ---- ferrite core rod through the 26 mm bore -------------------------
    bkit.cylinder("CoilCoreRod", SPEC["core_diameter"] / 2.0, 80.0,
                  segments=32, centre=(0.0, 0.0, 44.0), mat=ferrite)

    # ---- two lead-out wires dropping out of the bottom flange ------------
    for side, mat in ((-1.0, copper), (1.0, bkit.preset("rubber"))):
        bkit.cylinder("Lead%d" % int(side), 1.6, 16.0, segments=16, axis="Y",
                      centre=(0.0, side * 6.0, 10.0), mat=mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="bobbin_diameter", mm=40.0, tol=0.5, how="diameter",
         part="CoilBobbin"),
    dict(name="flange_diameter", mm=48.0, tol=0.5, how="diameter",
         part="FlangeTop"),
    dict(name="core_diameter", mm=12.0, tol=0.4, how="diameter",
         part="CoilCoreRod"),
    dict(name="winding_outer_diameter", mm=43.0, tol=0.6, how="diameter",
         part="CoilWinding"),
    dict(name="overall_height", mm=86.0, tol=0.8, how="bbox_z"),
]