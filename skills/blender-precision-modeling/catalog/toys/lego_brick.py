"""
lego_brick -- a 2x4 stud brick at true LEGO scale.

The whole system is defined by one number: the 8.0 mm stud pitch. A 2x4 brick
is four studs by two, so the body measures 31.8 x 15.8 mm across and 9.6 mm
tall, and each stud is 4.8 mm in diameter and rises 1.8 mm above the top face.
Stud placement therefore comes from `grid_positions(cols=4, rows=2, 8.0, 8.0)`
rather than from typed constants: hand-placed studs drift off the 8 mm grid and
a brick whose studs are not on the grid reads as a box with bumps, not as Lego.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real LEGO dimensions, millimetres -------------------------------------
SPEC = dict(
    stud_pitch=8.0,
    studs_x=4,
    studs_y=2,
    brick_length=31.8,     # 4 studs of pitch, minus the outer half-pitch
    brick_width=15.8,      # 2 studs of pitch
    brick_height=9.6,      # body height, top of the fillet
    stud_diameter=4.8,
    stud_height=1.8,
    overall_height=11.4,   # body plus stud
)

NX = int(SPEC["studs_x"])
NY = int(SPEC["studs_y"])
PITCH = SPEC["stud_pitch"]
LX = SPEC["brick_length"]
LY = SPEC["brick_width"]
LZ = SPEC["brick_height"]
SD = SPEC["stud_diameter"]
SH = SPEC["stud_height"]


def build():
    red = bkit.preset("red_paint")

    # ---- body: a filleted box. A real brick has a chamfer along its top edge,
    # and that chamfer is what separates it from a plain extruded block.
    body = bkit.rounded_box("Brick", LX, LY, LZ, r=0.8, segments=3,
                            centre=(0.0, 0.0, LZ / 2.0), mat=red)

    # ---- studs: every one of them on the 8 mm grid. They stay SEPARATE
    # objects rather than being joined: a joined "Studs" part has a bounding
    # box spanning the whole array, so a diameter check pointed at it measures
    # 28.8 mm and proves nothing about a single 4.8 mm stud.
    for i, (x, y) in enumerate(bkit.grid_positions(cols=NX, rows=NY,
                                                    pitch_x=PITCH, pitch_y=PITCH)):
        bkit.cylinder("Stud_%d" % i, SD / 2.0, SH, segments=24,
                      centre=(x, y, LZ + SH / 2.0), mat=red)

    return dict(spec=SPEC, parts=1 + NX * NY)


# How each dimension is measured. The harness measures the geometry; the model
# only declares which part owns the dimension and how to read it off.
CHECKS = [
    dict(name="brick_length", mm=31.8, tol=0.2, how="bbox_x", part="Brick"),
    dict(name="brick_width", mm=15.8, tol=0.2, how="bbox_y", part="Brick"),
    dict(name="brick_height", mm=9.6, tol=0.2, how="bbox_z", part="Brick"),
    dict(name="stud_diameter", mm=4.8, tol=0.2, how="diameter", part="Stud_0"),
    dict(name="stud_height", mm=1.8, tol=0.2, how="bbox_z", part="Stud_0"),
    dict(name="overall_height", mm=11.4, tol=0.2, how="bbox_z"),
]
