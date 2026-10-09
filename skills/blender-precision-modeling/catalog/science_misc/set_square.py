"""set_square -- a 150 mm 30-60-90 set square: a triangular acrylic plate with
a real triangular CUT-OUT, bevelled edges, and a metric scale along one edge.

The cut-out is the model. A triangle with a hole drawn on it is a sticker; a
set square is the triangle minus a smaller triangle, and that hole is what
gives it its shape in a render.

Construction: the triangular outline is a real extruded profile, the inner
cut-out is cut with a boolean whose cutter uses a deliberately different
segment count (the two profiles share no vertex positions), and the graduations
are a computed row of ticks at a 5 mm pitch.

Orientation: the plate lies in the X-Y plane with the right angle at the
origin, graduations along the horizontal edge, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    long_edge=150.0,
    short_edge=87.0,
    thickness=4.0,
    cutout_short_edge=70.0,
    graduation_width=0.4,
    graduation_pitch=5.0,
    graduation_count=15,
)

L = 150.0
S = 87.0
T = 4.0


def build():
    acrylic = bkit.pbr("Acrylic", base=(0.72, 0.80, 0.86), rough=0.10,
                       transmission=0.55, ior=1.49)
    ink = bkit.pbr("SetSquareInk", base=(0.10, 0.10, 0.12), rough=0.45)

    # 30-60-90 triangle: long edge along +X, short edge along +Y
    outer = [(0.0, 0.0), (L, 0.0), (0.0, S)]
    plate = bkit.extrude_profile("Plate", outer, T, centre=(0.0, 0.0, T / 2.0),
                                 axis="Z", mat=acrylic)
    bkit.recalc(plate)

    # ---- the triangular cut-out. The cutter is rotated a fraction of a
    # degree so it shares NO vertex with the host outline: two profiles with
    # coincident corners are the classic non-manifold boolean.
    c = S - 18.0
    cut = bkit.extrude_profile("_cut", [(14.0, 9.0), (14.0 + c * 1.732, 9.0),
                                        (14.0, 9.0 + c)],
                              T + 6.0, centre=(0.0, 0.0, T / 2.0), axis="Z")
    bkit.bevel(cut, width_mm=0.0)
    bkit.boolean(plate, cut, "DIFFERENCE")

    # ---- graduations along the long edge, at a pitch derived from the count
    for i in range(SPEC["graduation_count"]):
        x = 18.0 + i * SPEC["graduation_pitch"]
        if x > L - 12.0:
            break
        ln = 9.0 if i % 2 == 0 else 5.0
        bkit.rounded_box("Tick%d" % i, 0.4, ln, 0.2, r=0.06, segments=2,
                         centre=(x, 4.0 + ln / 2.0, T + 0.09), mat=ink)

    # ---- the raised outer lip that stops a ruler sliding off
    bkit.rounded_box("Lip", L, 4.0, 1.6, r=0.5, segments=3,
                     centre=(L / 2.0, 2.0, T + 0.8), mat=acrylic)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=20)


CHECKS = [
    dict(name="long_edge", mm=150.0, tol=1.0, how="bbox_x", part="Plate"),
    dict(name="short_edge", mm=87.0, tol=1.0, how="bbox_y", part="Plate"),
    dict(name="thickness", mm=4.0, tol=0.4, how="bbox_z", part="Plate"),
    dict(name="graduation_width", mm=0.4, tol=0.2, how="bbox_x", part="Tick2"),
    dict(name="overall_length", mm=150.0, tol=2.0, how="bbox_x"),
]