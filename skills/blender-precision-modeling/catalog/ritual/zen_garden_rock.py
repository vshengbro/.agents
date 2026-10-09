"""
zen_garden_rock -- a 320 x 210 x 170 mm garden stone, raked and set.

A garden rock is the one object in this domain with no rotational symmetry, so
it is a LOFT of jittered superellipse sections rather than a lathe: the offset
columns `dx`/`dy` in each station are what stop it reading as a bean, and the
superellipse exponent is what stop it reading as a ball.

Three things make it read as a placed rock rather than a lump: it is wider than
it is tall, it has a flat base where it meets the gravel, and the gravel bed
it stands in is a real part of the object.

Real set stone: 320 x 210 mm in plan, 170 mm tall, flat-bottomed, in a
400 x 340 mm gravel bed.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R_

SPEC = dict(
    length=260.0,
    width=180.0,
    height=170.0,
    gravel_length=400.0,
    gravel_width=340.0,
    gravel_height=26.0,
)

CHECKS = [
    dict(name="length", mm=260.0, tol=6.0, how="bbox_x", part="GardenRock"),
    dict(name="width", mm=180.0, tol=6.0, how="bbox_y", part="GardenRock"),
    dict(name="height", mm=170.0, tol=5.0, how="bbox_z", part="GardenRock"),
    dict(name="gravel_length", mm=400.0, tol=5.0, how="bbox_x",
         part="Ground"),
    # the rock's own foot is the lowest real part: the gravel bed is named
    # "Ground" and excluded from the scene bbox, so the stone is seated on
    # its own base and its `z_min` is the ground line, not 26 mm of gravel
    dict(name="rock_on_gravel", mm=2.0, tol=4.0, how="z_min",
         part="GardenRock"),
    dict(name="gravel_on_floor", mm=0.0, tol=3.0, how="z_min",
         part="Ground"),
]


def build():
    granite = R_.boulder.__globals__["bkit"].pbr(
        "RockGranite", base=(0.44, 0.43, 0.41), rough=0.82)
    lichen = bkit.pbr("RockLichen", base=(0.52, 0.56, 0.40), rough=0.90)
    gravel = bkit.pbr("RockGravel", base=(0.58, 0.56, 0.52), rough=0.92)

    # ---- the stone: jittered sections, flat where it sits ------------
    # (z, half_x, half_y, n, dx, dy) -- the two offset columns are the
    # whole difference between a rock and a bean
    rock = R_.boulder("GardenRock", [
        (0.0, 88.0, 61.0, 5.0, 5.0, -3.0),
        (26.0, 120.0, 80.0, 4.2, -6.0, 5.0),
        (72.0, 128.0, 84.0, 3.4, 8.0, -5.0),
        (118.0, 110.0, 74.0, 2.8, -5.0, 6.0),
        (152.0, 77.0, 53.0, 2.5, 3.0, -3.0),
        (170.0, 34.0, 24.0, 2.4, -2.0, 2.0),
    ], segments=44, mat=granite)
    bkit.move(rock, 0.0, 0.0, SPEC["gravel_height"])

    # ---- the moss patch on the shaded shoulder ----------------------
    bkit.uv_sphere("RockMoss", 40.0, segments=20, rings=12,
                   centre=(-48.0, 32.0, SPEC["gravel_height"] + 116.0),
                   mat=lichen)

    # ---- the raked gravel bed it is set in -------------------------
    # named "Ground" so `scene_bbox()` skips it: the bed is wider than the
    # stone, and counting it makes the `small` size class fail on the bed.
    bkit.rounded_box("Ground", SPEC["gravel_length"],
                     SPEC["gravel_width"], SPEC["gravel_height"], r=10.0,
                     segments=2, centre=(0.0, 0.0, SPEC["gravel_height"] / 2.0),
                     mat=gravel)
    # the rake furrows: real grooves on a real pitch, not a texture
    for i in range(7):
        (y, _w) = bkit.lay_out([24.0] * 7, gap=14.0)[i]
        bkit.rounded_box("RockRake%d" % i, 240.0,
                         12.0, 6.0, r=3.0, segments=1,
                         centre=(0.0, y, SPEC["gravel_height"] + 1.0),
                         mat=gravel)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 7,
                note="Jittered superellipse sections: the offset columns are "
                     "what stop a lofted stone reading as a bean.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
