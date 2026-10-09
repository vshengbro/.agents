"""mantis -- a 90 mm praying mantis: the triangular head with enormous eyes on
lateral cones, the long prothorax with its folded raptorial forelegs held in
the praying position, and two pairs of wings over the abdomen.

The raptorial forelegs are the model. A mantis holds its front legs folded in
front of the face with the femur against the tibia and the spines visible --
a straight front leg reads as a grasshopper, not a mantis.

Construction: a swept prothorax, a triangular head with two cone-mounted eyes,
two folded forelegs built as femur + tibia + tarsus, four walking legs, and
four wing blades over the abdomen. Nothing is booleaned.

Orientation: the head points at -Y, X lateral, Z up.
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
    overall_length=83.0,
    body_length=60.0,
    head_width=14.0,  # head alone; the eye cones sit outside it
    femur_length=19.1,
    foreleg_span=30.0,
)

# (y, half_height, half_width, z_centre) -- prothorax -34 to 0
BODY = [
    (-34.0, 4.0, 4.0, 30.0),
    (-28.0, 5.4, 5.0, 30.0),
    (-20.0, 6.0, 5.4, 30.0),
    (-12.0, 5.6, 5.0, 29.0),
    (-4.0, 5.0, 4.4, 28.0),
    (4.0, 5.6, 5.0, 26.0),
    (12.0, 6.0, 5.4, 25.0),
    (20.0, 5.4, 4.6, 24.5),
    (26.0, 3.6, 3.0, 24.0),
]
HEAD = [(0.0, -38.0, 30.0), (0.0, -44.0, 30.4), (0.0, -49.0, 29.6)]
HEAD_RAD = [(6.4, 6.0), (7.0, 6.4), (4.0, 3.6)]
# the raptorial foreleg: femur up and forward, tibia folded back down
FEMUR = [(0.0, -30.0, 28.0), (7.0, -36.0, 34.0), (12.0, -41.0, 38.0)]
FEMUR_RAD = [(4.6, 4.2), (5.2, 4.8), (4.4, 4.0)]
TIBIA = [(12.0, -41.0, 38.0), (8.0, -48.0, 32.0), (6.0, -52.0, 26.0)]
TIBIA_RAD = [(4.0, 3.6), (2.8, 2.4), (1.4, 1.2)]
WALK = [(0.0, -8.0, 28.0), (20.0, -10.0, 16.0), (28.0, -14.0, 2.0)]
WALK_RAD = [(3.4, 3.0), (2.4, 2.0), (1.0, 0.9)]
HIND_LEG = [(0.0, 16.0, 24.0), (20.0, 20.0, 12.0), (28.0, 26.0, 2.0)]
HIND_RAD = [(3.6, 3.2), (2.6, 2.2), (1.1, 1.0)]
TEGMINA = [(0.0, 6.0), (8.0, -6.0), (16.0, -18.0), (22.0, -26.0),
           (22.0, -22.0), (14.0, -12.0), (4.0, 4.0)]
WING = [(0.0, 2.0), (8.0, -8.0), (16.0, -22.0), (24.0, -32.0),
        (24.0, -27.0), (15.0, -14.0), (4.0, 2.0)]


def build():
    hide = bkit.pbr("MantisHide", base=(0.34, 0.46, 0.18), rough=0.52)
    pale = bkit.pbr("MantisPale", base=(0.62, 0.66, 0.36), rough=0.54)
    wing = bkit.pbr("MantisWing", base=(0.44, 0.52, 0.26), rough=0.36,
                    alpha=0.82)
    eye = bkit.pbr("MantisEye", base=(0.28, 0.44, 0.12), rough=0.14,
                   coat=0.5)
    spine = bkit.pbr("MantisSpine", base=(0.12, 0.16, 0.06), rough=0.40)

    torso = F.body("Body", BODY, hide, n=2.6, steps=32)
    bkit.assign_faces_by(torso, pale, lambda c, n: c.z / bkit.MM < 24.0)

    F.tube("Head", HEAD, HEAD_RAD, hide, n=3.0, steps=18)

    # ---- the raptorial forelegs, folded in the praying position
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.tube("ForelegFemur%s" % side,
               [(sx * p[0], p[1], p[2]) for p in FEMUR], FEMUR_RAD, hide,
               n=2.4, steps=14)
        F.tube("ForelegTibia%s" % side,
               [(sx * p[0], p[1], p[2]) for p in TIBIA], TIBIA_RAD, pale,
               n=2.4, steps=14)
        # the femur's gripping spines, spaced at a pitch from their own count
        n_sp = 7
        for i in range(n_sp):
            t = 0.2 + 0.6 * i / float(n_sp - 1)
            px = sx * (0.0 + 12.0 * t)
            py = -30.0 - 11.0 * t
            pz = 28.0 + 10.0 * t
            F.cone_between("Spine%s%d" % (side, i),
                           (px, py, pz), (px + sx * 2.6, py - 0.6, pz - 0.6),
                           1.0, 0.15, seg=6, mat=spine)

    for tag, path, rad in (("Mid", WALK, WALK_RAD),
                              ("Hind", HIND_LEG, HIND_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, hide, n=2.2, steps=14)
        F.mirror_copy(leg, "Leg%sR" % tag)

    # ---- two pairs of wings folded over the abdomen
    teg = F.plate_xy("WingTegminaL", TEGMINA, 1.8, z=0.0, mat=wing)
    bkit.move(teg, 4.4, 0.0, 30.0)
    F.bake_rot(teg, "X", 8.0)
    F.mirror_copy(teg, "WingTegminaR")
    hind = F.plate_xy("WingHindL", WING, 1.6, z=0.0, mat=pale)
    bkit.move(hind, 4.0, 1.0, 29.0)
    F.bake_rot(hind, "X", 12.0)
    F.mirror_copy(hind, "WingHindR")

    # ---- the big eyes sit on lateral CONES: the mantis's head silhouette
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("EyeCone%s" % side,
                       (sx * 5.4, -42.0, 31.0), (sx * 8.2, -43.4, 31.6),
                       3.4, 5.0, seg=14, mat=hide)
        F.sphere("Eye%s" % side, 4.4,
                 (sx * 9.0, -43.6, 31.8), eye, segments=20, rings=10)
        F.cone_between("Antenna%s" % side,
                       (sx * 4.6, -47.0, 32.0), (sx * 7.0, -56.0, 35.0),
                       0.7, 0.25, seg=8, mat=hide)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=34)


CHECKS = [
    dict(name="overall_length", mm=83.0, tol=8.0, how="bbox_y"),
    dict(name="body_length", mm=60.0, tol=5.0, how="bbox_y", part="Body"),
    dict(name="head_width", mm=14.0, tol=2.0, how="bbox_x", part="Head"),
    dict(name="femur_length", mm=19.1, tol=2.5, how="longest",
         part="ForelegFemurL"),
    dict(name="stand_height", mm=40.0, tol=5.0, how="bbox_z"),
]