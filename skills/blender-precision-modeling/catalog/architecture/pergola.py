"""
pergola -- a 4.8 x 3.6 m timber pergola: six posts on a computed grid, two
long beams, eleven joists from a computed pitch, and corner braces.

Large size class (600..3000 mm). A pergola is a frame, so every member counts:
6 posts, 2 beams, 11 joists, 4 braces. The joist pitch is derived from the
span rather than typed in, so the array cannot come out with a gap at one end.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=4800.0,        # along X
    width=3600.0,         # along Y
    post_height=2600.0,
    post_section=180.0,
    post_rows=2,          # posts along Y
    post_cols=3,          # posts along X
    beam_section=150.0,
    beam_depth=280.0,
    joist_section=110.0,
    joist_depth=220.0,
    joist_count=11,
    joist_overhang=420.0,
    brace_section=90.0,
)

L = SPEC["length"]
Wd = SPEC["width"]
PH = SPEC["post_height"]
PS = SPEC["post_section"]
RC, RR = SPEC["post_cols"], SPEC["post_rows"]


def build():
    timber = bkit.pbr("PergolaTimber", base=(0.40, 0.27, 0.15), rough=0.60)
    dark = bkit.pbr("PergolaDark", base=(0.30, 0.20, 0.11), rough=0.64)

    # ---- six posts on a computed grid -------------------------------------
    # grid_positions owns the layout, so the post centres are derived from the
    # span and the row/column counts rather than written out by hand.
    for (x, y) in bkit.grid_positions(RC, RR, (L - PS) / (RC - 1.0),
                                      (Wd - PS) / (RR - 1.0)):
        bkit.rounded_box("PergolaPost", PS, PS, PH, r=12.0, segments=2,
                         centre=(x, y, PH / 2.0), mat=timber)

    # ---- two beams running along X, on top of the posts ------------------
    bd = SPEC["beam_depth"]
    for i, y in enumerate((-1, 1)):
        by = y * (Wd - PS) / 2.0
        bkit.rounded_box("PergolaBeam%d" % (i + 1), L + 240.0,
                         SPEC["beam_section"], bd, r=10.0, segments=2,
                         centre=(0.0, by, PH + bd / 2.0), mat=dark)

    # ---- joists across the beams: pitch derived from the count -----------
    # count and span together fix the pitch, so the outermost joists land
    # symmetrically past the beams by construction.
    jn = SPEC["joist_count"]
    pitch = (L + 2.0 * SPEC["joist_overhang"]) / (jn + 1)
    joist = bkit.rounded_box("PergolaJoists", SPEC["joist_section"],
                             Wd + 480.0, SPEC["joist_depth"], r=8.0,
                             segments=2, centre=(0.0, 0.0, 0.0), mat=timber)
    bkit.array_linear(joist, jn, (pitch, 0.0, 0.0), apply=False)
    # the sweep above needs the seed on the Z axis; move the whole run after
    bkit.move(joist, -(jn - 1) * pitch / 2.0, 0.0,
              PH + bd + SPEC["joist_depth"] / 2.0)

    # ---- corner braces: a 45 degree knee at each post -------------------
    for i, x in enumerate((-1, 1)):
        for j, y in enumerate((-1, 1)):
            bkit.rounded_box("PergolaBrace%d%d" % (i, j), 620.0,
                             SPEC["brace_section"], SPEC["brace_section"],
                             r=8.0, segments=1,
                             centre=(x * ((L - PS) / 2.0 - 200.0),
                                     y * ((Wd - PS) / 2.0 - 200.0),
                                     PH - 200.0), mat=dark)
            br = bpy_objects()[-1]
            br.rotation_euler = (math.radians(45.0 * y),
                                 math.radians(-45.0 * x), 0.0)
            bpy_update()

    return dict(spec=SPEC, parts=RC * RR + 2 + 1 + 4,
                posts=RC * RR, joists=jn)


def bpy_objects():
    import bpy
    return [o for o in bpy.data.objects if o.type == "MESH"]


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="overall_length", mm=5040.0, tol=15.0, how="bbox_x"),
    dict(name="post_height", mm=2600.0, tol=8.0, how="bbox_z", part="PergolaPost"),
    dict(name="beam_length", mm=5040.0, tol=15.0, how="bbox_x", part="PergolaBeam1"),
    dict(name="beam_depth", mm=280.0, tol=6.0, how="bbox_z", part="PergolaBeam1"),
    dict(name="joist_depth", mm=220.0, tol=6.0, how="bbox_z", part="PergolaJoists"),
]
