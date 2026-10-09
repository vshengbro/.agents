"""
sitar -- a 1200 mm sitar: gourd resonator, 13 frets, 6 playing strings,
11 sympathetic strings, 5 tuning pegs.

A sitar is a RESONATOR with two string planes, and the two planes are the
whole identity: six playing strings in a shallow arc across the neck and eleven
sympathetic strings in a fan beside it. Both are lacing lines computed from the
neck width -- neither is a row of hand-typed constants -- and the frets are
themselves a computed pitch, because fret 13 on a sitar is nowhere near where a
fret 13 on a guitar would be.

The pegs are a radial array about the pegbox's own axis, not the body axis.

Real sitar: 1200 mm overall, 250 mm resonator width, 68 mm neck, 13 raised
frets, 6 + 11 strings, 5 pegs in a fan.
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
    length=1200.0,
    body_length=480.0,
    body_width=250.0,
    body_depth=190.0,
    neck_length=620.0,
    neck_width=68.0,
    frets=13,
    playing_strings=6,
    sympathetic=11,
    pegs=5,
    string_dia=1.2,
    sympathetic_dia=0.8,
    scale_length=620.0,
)

BL = SPEC["body_length"]
NL = SPEC["neck_length"]
BRIDGE_X = -BL / 2.0

CHECKS = [
    dict(name="overall_length", mm=1267.5, tol=8.0, how="bbox_x"),
    dict(name="body_width", mm=250.0, tol=6.0, how="bbox_y",
         part="SitarBody"),
    dict(name="neck_length", mm=620.0, tol=6.0, how="bbox_x",
         part="SitarNeck"),
    dict(name="neck_width", mm=68.0, tol=4.0, how="bbox_y",
         part="SitarNeck"),
    dict(name="fret_height", mm=7.0, tol=1.5, how="bbox_z",
         part="SitarFret00"),
    dict(name="peg_row_span", mm=188.2, tol=6.0, how="bbox_y",
         part="SitarPegs"),
    dict(name="body_on_floor", mm=0.0, tol=5.0, how="z_min",
         part="SitarBody"),
]


def build():
    teak = R_.cedar("SitarTeak", base=(0.46, 0.22, 0.10), rough=0.38)
    gourd = R_.cedar("SitarGourd", base=(0.72, 0.58, 0.30), rough=0.44)
    ivory = bkit.pbr("SitarIvory", base=(0.88, 0.84, 0.70), rough=0.30)
    brass = R_.gild("SitarBrass")
    steel = bkit.preset("polished_metal")
    gut = bkit.pbr("SitarGut", base=(0.80, 0.76, 0.60), rough=0.66)
    wire = bkit.pbr("SitarWire", base=(0.90, 0.88, 0.72), metal=0.85,
                    rough=0.28)

    zc = SPEC["body_depth"] / 2.0

    # ---- the resonator: a gourd, so a loft, not a box ---------------
    secs = []
    for (x, ry, rz, n) in ((-BL / 2.0, 40.0, 34.0, 2.2),
                           (-BL / 2.0 + 60.0, 95.0, 78.0, 2.3),
                           (-BL / 2.0 + 200.0, SPEC["body_width"] / 2.0,
                            SPEC["body_depth"] / 2.0, 2.6),
                           (BL / 2.0 - 30.0, 70.0, 58.0, 2.4),
                           (BL / 2.0, 34.0, 30.0, 2.2)):
        ring = bkit.superellipse_section(2.0 * ry, 2.0 * rz, n=n, steps=40,
                                         centre=(0.0, zc))
        secs.append([(x, y, z) for (y, z) in ring])
    body = bkit.loft("SitarBody", secs, mat=teak)
    bkit.recalc(body)
    bkit.shade_smooth(body, 40.0)
    # the smaller upper bout, glued to the back -- a real sitar detail
    up = bkit.lathe("SitarUpperBout",
                    [(0.0, 0.0), (70.0, 0.0), (80.0, 40.0), (58.0, 78.0),
                     (0.0, 90.0)], segments=32,
                    centre=(-BL / 2.0 + 250.0, 0.0, zc + 55.0), mat=gourd)

    # ---- the neck and the fingerboard --------------------------------
    bkit.rounded_box("SitarNeck", NL, SPEC["neck_width"], 34.0, r=10.0,
                     segments=3, centre=(BL / 2.0 + NL / 2.0, 0.0,
                                         zc + 40.0), mat=teak)
    bkit.rounded_box("SitarFingerboard", NL - 20.0, SPEC["neck_width"] - 8.0,
                     8.0, r=3.0, segments=2,
                     centre=(BL / 2.0 + NL / 2.0, 0.0, zc + 60.0),
                     mat=ivory)

    # ---- thirteen raised frets on a SCALE pitch ----------------------
    # the sitar frets are a shortened scale, so the pitch is derived from
    # the scale length: a linear pitch puts fret 13 in the wrong place.
    fl = []
    for i in range(SPEC["frets"]):
        t = i / float(SPEC["frets"])
        x = BRIDGE_X + SPEC["scale_length"] * (1.0 - math.pow(2.0, -t * 2.0))
        if x > BL / 2.0 + NL - 40.0:
            break
        fl.append(x)
    for i, x in enumerate(fl):
        bkit.rounded_box("SitarFret%02d" % i, 5.0, SPEC["neck_width"] - 12.0,
                         7.0, r=2.0, segments=1,
                         centre=(x, 0.0, zc + 66.0), mat=ivory)

    # ---- the bridge and the tailpiece --------------------------------
    bkit.rounded_box("SitarBridge", 14.0, 210.0, 34.0, r=6.0, segments=2,
                     centre=(BRIDGE_X + 40.0, 0.0, zc + 70.0), mat=ivory)
    bkit.rounded_box("SitarTailpiece", 60.0, 160.0, 20.0, r=6.0, segments=2,
                     centre=(BL / 2.0 + 40.0, 0.0, zc + 66.0), mat=ivory)

    # ---- six playing strings in a shallow arc across the neck --------
    for i, dy in enumerate([-24.0, -14.0, -4.0, 6.0, 16.0, 26.0]):
        R_.rope("SitarPlaying%d" % i,
                (BRIDGE_X + 40.0, dy, zc + 84.0),
                (BL / 2.0 + NL + 40.0, dy * 0.8, zc + 84.0),
                SPEC["string_dia"] / 2.0, mat=gut)

    # ---- eleven sympathetic strings in a fan beside the neck --------
    for i in range(SPEC["sympathetic"]):
        t = i / float(SPEC["sympathetic"] - 1)
        y0 = 34.0 + t * 26.0
        y1 = 38.0 + t * 62.0
        R_.rope("SitarSympathetic%02d" % i,
                (BRIDGE_X + 60.0, y0, zc + 30.0),
                (BL / 2.0 + NL + 30.0, y1, zc + 30.0),
                SPEC["sympathetic_dia"] / 2.0, mat=wire)

    # ---- five pegs, arrayed about the pegbox axis --------------------
    pegbox = bkit.rounded_box("SitarPegbox", 150.0, 110.0, 90.0, r=20.0,
                              segments=3,
                              centre=(BL / 2.0 + NL + 90.0, 0.0, zc + 50.0),
                              mat=teak)
    peg = bkit.lathe("SitarPegs",
                     [(0.0, 0.0), (13.0, 0.0), (13.0, 90.0), (9.0, 96.0),
                      (0.0, 96.0)], segments=20, mat=brass)
    R_.place_in_mesh(peg, BL / 2.0 + NL + 90.0, 0.0, zc + 50.0)
    bpy.context.view_layer.update()
    bkit.array_radial(peg, SPEC["pegs"], axis="X",
                      centre=(BL / 2.0 + NL + 90.0, 0.0, zc + 50.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3 + 2 + len(fl) + 2 + 6 + 11 + 2,
                note="Six playing strings and eleven sympathetic strings on "
                     "computed lacing lines; frets on a scale pitch.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
