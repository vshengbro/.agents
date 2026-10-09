"""
tarp -- a 6 x 4 m polythene tarpaulin, folded and tied: 1400 x 1000 x 240.

A folded tarp is a STACK OF ROUNDED LAYERS with a rope through it, and the fold
is the whole object: a flat slab reads as a sheet of card. Four layers, each a
`rounded_box` with a generous fillet, each set back slightly from the one below
so the edge stack is visible from every angle, and the tie rope threaded
through eyelets on the top layer.

The eyelets are the one feature that must be placed on a computed pitch: four
along each long edge, spaced from the sheet width rather than typed in, so the
rope passes through all of them.

Real 6 x 4 m tarp folded in quarters: 1400 x 1000 mm footprint, 240 mm thick
folded, 16 mm eyelets on a 250 mm pitch, 12 mm tie rope.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _agri as A

SPEC = dict(
    sheet_length=6000.0,
    sheet_width=4000.0,
    folded_length=1400.0,
    folded_width=1000.0,
    folded_height=240.0,
    layers=4,
    eyelet_dia=16.0,
    eyelet_pitch=250.0,
    rope_dia=12.0,
)

FL = SPEC["folded_length"]
FW = SPEC["folded_width"]
LAYER_H = SPEC["folded_height"] / SPEC["layers"]

CHECKS = [
    dict(name="folded_length", mm=1400.0, tol=4.0, how="bbox_x",
         part="TarpLayer0"),
    dict(name="folded_width", mm=1000.0, tol=4.0, how="bbox_y",
         part="TarpLayer0"),
    dict(name="folded_height", mm=240.0, tol=5.0, how="top_z",
         part="TarpLayer3"),
    dict(name="eyelet_outer_dia", mm=22.0, tol=1.0, how="bbox_x",
         part="TarpEyelet00"),
    dict(name="eyelet2_x", mm=-136.0, tol=3.0, how="x_min",
         part="TarpEyelet02"),
    dict(name="rope_dia", mm=12.0, tol=1.0, how="bbox_y", part="TarpRope0"),
    dict(name="tarp_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="TarpLayer0"),
]


def build():
    poly = bkit.pbr("TarpPoly", base=(0.16, 0.30, 0.42), rough=0.44, coat=0.3)
    poly_b = bkit.pbr("TarpPolyBack", base=(0.10, 0.21, 0.31), rough=0.50)
    steel = bkit.preset("brushed_metal")
    rope_mat = bkit.pbr("TarpRope", base=(0.72, 0.64, 0.40), rough=0.86)

    # ---- four layers, each set back, each a real fillet ---------------
    # the fillet radius IS the fold: at 4 mm the edges read as soft polythene
    # and the stack reads as cloth, not as four boxes.
    for i in range(SPEC["layers"]):
        lx = FL - i * 6.0
        ly = FW - i * 4.0
        bkit.rounded_box("TarpLayer%d" % i, lx, ly, LAYER_H, r=26.0,
                         segments=4,
                         centre=(0.0, 0.0, LAYER_H / 2.0 + i * LAYER_H),
                         mat=poly if i % 2 == 0 else poly_b)

    # ---- eyelets on a computed pitch along both long edges -----------
    holes = []
    for (x, _w) in bkit.lay_out([30.0] * 4, gap=SPEC["eyelet_pitch"] - 30.0):
        for s in (1, -1):
            holes.append((x, s * (FW / 2.0 - 55.0)))
    proto = bkit.tube("TarpEyelet00", SPEC["eyelet_dia"] / 2.0 + 3.0,
                      SPEC["eyelet_dia"] / 2.0, 8.0, segments=20,
                      mat=steel)
    # `duplicate()` SETS an absolute location, so every copy is handed its
    # own world position -- handing it a delta instead drops the whole ring
    # of eyelets onto the floor at z = 0.
    eyelet_z = SPEC["folded_height"] + 2.0
    for i, (x, y) in enumerate(holes[1:]):
        bkit.duplicate(proto, "TarpEyelet%02d" % (i + 1),
                       offset_mm=(x, y, eyelet_z))
    bkit.move(proto, holes[0][0], holes[0][1], eyelet_z)

    # ---- the tie rope: one arc per long edge, through every eyelet ----
    pitch = SPEC["eyelet_pitch"] - 30.0
    n = len(holes) // 2
    for s in (1, -1):
        y = s * (FW / 2.0 - 55.0)
        pts = []
        for i in range(n):
            x = (i - (n - 1) / 2.0) * pitch
            pts.append((x, y, SPEC["folded_height"] + 8.0 + (14.0 if i % 2 else 0.0)))
        for a, c in zip(pts[:-1], pts[1:]):
            A.tube_between("TarpRope%d" % (0 if s < 0 else 1), a, c,
                           SPEC["rope_dia"] / 2.0, mat=rope_mat)
        for i, p in enumerate(pts):
            bkit.cylinder("TarpKnot%d_%d" % (0 if s < 0 else 1, i),
                          SPEC["rope_dia"] / 2.0 + 5.0, 14.0, segments=12,
                          centre=p, mat=rope_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=SPEC["layers"] + len(holes) + 2 * n)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
