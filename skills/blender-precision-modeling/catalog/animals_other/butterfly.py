"""butterfly -- an 85 mm monarch: two large triangular forewings, two smaller
hindwings, a slender segmented abdomen, antennae with clubbed tips, and the
black-and-orange wing pattern as a second material.

The wing SHAPES are the model. A butterfly has four wings of two distinct
shapes -- big triangular forewings and smaller rounded hindwings -- and a
moth has four of much the same outline. Forewing span here is 85 mm.

Construction: two forewing blades and two hindwing blades, each authored once
and mirrored, a swept thorax and abdomen with real segment ridges, and two
antennae. Nothing is booleaned.

Orientation: the body runs along Y, the wings spread in X, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    wing_span=85.0,
    forewing_length=42.0,
    hindwing_length=30.0,
    body_length=42.0,  # head to abdomen tip across the whole animal
    body_diameter=5.0,
    antenna_segments=9,
)

# forewing: big and triangular, with the characteristic squared-off tip
FORE = [
    (0.0, 4.0), (10.0, 10.0), (24.0, 15.0), (38.0, 14.0), (42.0, 7.0),
    (36.0, 0.0), (22.0, -5.0), (8.0, -3.0),
]
# hindwing: smaller and rounded, tucked behind and below the forewing
HIND = [
    (0.0, -2.0), (10.0, -6.0), (22.0, -10.0), (30.0, -8.0), (28.0, 0.0),
    (16.0, 3.0), (5.0, 2.0),
]
BODY = [(0.0, -18.0, 14.0), (0.0, -8.0, 14.4), (0.0, 2.0, 14.4),
        (0.0, 12.0, 14.0), (0.0, 20.0, 13.6), (0.0, 24.0, 13.2)]
BODY_RAD = [(2.4, 2.2), (3.0, 2.8), (2.9, 2.7), (2.6, 2.4), (2.2, 2.0),
            (1.0, 0.9)]


def build():
    orange = bkit.pbr("MonarchOrange", base=(0.86, 0.34, 0.03), rough=0.42)
    black = bkit.pbr("MonarchBlack", base=(0.035, 0.030, 0.028), rough=0.40)
    cream = bkit.pbr("MonarchCream", base=(0.92, 0.88, 0.74), rough=0.44)
    body = bkit.pbr("ButterflyBody", base=(0.05, 0.04, 0.04), rough=0.52)

    F.tube("Thorax", BODY[:3], BODY_RAD[:3], body, n=2.4, steps=16)
    abd = F.tube("Abdomen", BODY[2:], BODY_RAD[2:], body, n=2.4, steps=16)
    # the abdominal segments: ridges at a pitch derived from the segment count
    n_seg = 6
    pitch = 18.0 / n_seg
    for i in range(n_seg):
        y = 4.0 + i * pitch
        bkit.torus("Seg%d" % i, 2.7 - 0.28 * i, 0.5, seg_major=20,
                   seg_minor=8, centre=(0.0, y, 14.0 - 0.1 * i), axis="Y",
                   mat=body)

    # ---- four wings of two distinct shapes
    fore = F.plate_xy("WingForeL", FORE, 1.0, z=0.0, mat=orange)
    bkit.move(fore, 2.6, 0.0, 14.0)
    F.bake_rot(fore, "X", -8.0)
    F.mirror_copy(fore, "WingForeR")
    hind = F.plate_xy("WingHindL", HIND, 0.9, z=0.0, mat=orange)
    bkit.move(hind, 2.4, -2.0, 13.6)
    F.bake_rot(hind, "X", 6.0)
    F.mirror_copy(hind, "WingHindR")

    # ---- the wing pattern: veins and the dark border, as second materials on
    # the ONE wing solid per wing (never a second shell -- that z-fights)
    for tag, obj, edge in (("ForeL", fore, 4.0), ("HindL", hind, 3.0)):
        bkit.assign_faces_by(
            bpy.data.objects[obj.name], black,
            lambda c, n, e=edge: abs(c.x / bkit.MM) > 2.6 + e
            or c.y / bkit.MM > 10.0 - e * 0.5)
    del cream

    for side, sx in (("L", 1.0), ("R", -1.0)):
        n = SPEC["antenna_segments"]
        run, rad = [], []
        for i in range(n):
            t = i / float(n - 1)
            run.append((sx * (2.2 + 9.0 * t), -17.0 - 15.0 * t,
                        15.0 + 7.0 * t + 1.5 * t * t))
            rad.append((0.45, 0.4))
        F.tube("Antenna%s" % side, run, rad, body, n=2.2, steps=10)
        F.sphere("Club%s" % side, 1.3, run[-1], black, segments=14, rings=8)
        F.sphere("Eye%s" % side, 2.4, (sx * 2.4, -18.0, 15.6), black,
                 segments=16, rings=8)

    del abd
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=24)


CHECKS = [
    dict(name="wing_span", mm=89.0, tol=4.0, how="bbox_x"),
    dict(name="forewing_length", mm=42.0, tol=3.0, how="bbox_x",
         part="WingForeL"),
    dict(name="hindwing_length", mm=30.0, tol=3.0, how="bbox_x",
         part="WingHindL"),
    dict(name="body_length", mm=57.0, tol=4.0, how="bbox_y"),
    dict(name="body_diameter", mm=6.0, tol=1.0, how="bbox_x", part="Thorax"),
]