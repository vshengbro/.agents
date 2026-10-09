"""grasshopper -- a 78 mm short-horned grasshopper: the wedge head with big
compound eyes, the elongated angled femur of the hind leg, the folded tibia
and tarsus, two pairs of wings folded along the body, and six legs.

The hind leg is the model. A grasshopper's femur is a thick triangular wedge
angled up and back off the body, and the tibia folds back down against it --
the folded "Z" is the whole silhouette. A straight tube leg does not read.

Construction: a swept head and thorax, a conical wedge femur, a folded tibia
and tarsus built as one path, two forewing and two hindwing blades folded along
the back, and four front/mid legs. Nothing is booleaned.

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
    overall_length=78.0,
    body_length=44.0,
    femur_length=31.5,
    tibia_length=38.0,
    hind_leg_span=74.4,
    antenna_segments=12,
)

# (y, half_height, half_width, z_centre) -- head -22, abdomen tip +22
BODY = [
    (-22.0, 5.0, 4.0, 14.0),
    (-18.0, 7.0, 5.4, 14.0),
    (-13.0, 8.0, 6.4, 13.5),
    (-6.0, 8.4, 6.6, 13.0),
    (2.0, 8.0, 6.2, 12.6),
    (10.0, 6.6, 5.2, 12.4),
    (17.0, 5.0, 4.0, 12.2),
    (22.0, 3.2, 2.6, 12.0),
]
# the hind femur: a thick wedge angled up and back off the body
FEMUR = [(5.0, 8.0, 13.0), (10.0, 18.0, 20.0), (16.0, 26.0, 22.0),
         (20.0, 32.0, 19.0)]
FEMUR_RAD = [(7.0, 6.0), (8.4, 7.6), (7.0, 6.2), (4.4, 4.0)]
# the tibia folds back down and forward, then the tarsus
TIBIA = [(20.0, 32.0, 19.0), (23.0, 38.0, 10.0), (20.0, 33.0, 3.0),
         (26.0, 30.0, 1.2)]
TIBIA_RAD = [(4.0, 3.6), (3.2, 2.8), (2.4, 2.0), (1.0, 0.9)]
MID_LEG = [(0.0, -6.0, 12.0), (16.0, -8.0, 9.0), (24.0, -12.0, 2.0)]
MID_RAD = [(3.0, 2.8), (2.2, 2.0), (0.9, 0.8)]
FORE_LEG = [(0.0, -13.0, 12.0), (14.0, -16.0, 8.0), (20.0, -19.0, 1.2)]
FORE_RAD = [(2.6, 2.4), (1.9, 1.7), (0.8, 0.7)]
# wings folded back over the abdomen
FOREWING = [(0.0, 2.0), (8.0, -6.0), (18.0, -16.0), (30.0, -24.0),
            (30.0, -21.0), (16.0, -11.0), (4.0, 0.0)]
HINDWING = [(0.0, -2.0), (8.0, -10.0), (20.0, -22.0), (32.0, -30.0),
            (32.0, -26.0), (18.0, -16.0), (4.0, -4.0)]


def build():
    hide = bkit.pbr("GrasshopperHide", base=(0.36, 0.40, 0.16), rough=0.58)
    pale = bkit.pbr("GrasshopperPale", base=(0.62, 0.60, 0.32), rough=0.54)
    wing = bkit.pbr("GrasshopperWing", base=(0.52, 0.40, 0.20), rough=0.36,
                    alpha=0.88)
    eye = bkit.pbr("GrasshopperEye", base=(0.10, 0.16, 0.05), rough=0.18,
                   coat=0.4)

    torso = F.body("Body", BODY, hide, n=2.8, steps=32)
    bkit.assign_faces_by(torso, pale, lambda c, n: c.z / bkit.MM < 10.0)

    # ---- the folded hind leg: the wedge femur plus the Z-folded tibia
    hind = F.tube("HindFemurL", FEMUR, FEMUR_RAD, hide, n=2.6, steps=16)
    F.mirror_copy(hind, "HindFemurR")
    shin = F.tube("HindTibiaL", TIBIA, TIBIA_RAD, pale, n=2.4, steps=16)
    F.mirror_copy(shin, "HindTibiaR")

    for tag, path, rad in (("Mid", MID_LEG, MID_RAD), ("Fore", FORE_LEG,
                                                      FORE_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, hide, n=2.2, steps=14)
        F.mirror_copy(leg, "Leg%sR" % tag)

    # ---- two pairs of wings folded back over the abdomen
    fw = F.plate_xy("WingForeL", FOREWING, 1.6, z=0.0, mat=wing)
    bkit.move(fw, 5.6, 0.0, 17.0)
    F.bake_rot(fw, "X", 4.0)
    F.mirror_copy(fw, "WingForeR")
    hw = F.plate_xy("WingHindL", HINDWING, 1.4, z=0.0, mat=wing)
    bkit.move(hw, 5.2, -1.0, 18.4)
    F.bake_rot(hw, "X", 8.0)
    F.mirror_copy(hw, "WingHindR")

    # ---- short antennae: a chain of segments at a pitch derived from the
    # segment count, so they are even and never share a station
    n = SPEC["antenna_segments"]
    for side, sx in (("L", 1.0), ("R", -1.0)):
        run, rad = [], []
        for i in range(n):
            t = i / float(n - 1)
            run.append((sx * (3.4 + 6.0 * t), -22.0 - 16.0 * t,
                        17.0 + 4.0 * t - 3.0 * t * t))
            rad.append((0.5, 0.45))
        F.tube("Antenna%s" % side, run, rad, hide, n=2.2, steps=10)
        F.sphere("Eye%s" % side, 3.2, (sx * 4.6, -20.0, 17.4), eye,
                 segments=18, rings=9)

    # ---- palps under the mouth
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("Palp%s" % side,
                       (sx * 1.6, -24.0, 12.6), (sx * 1.8, -28.0, 11.6),
                       1.0, 0.3, seg=8, mat=pale)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=24)


CHECKS = [
    dict(name="overall_length", mm=78.0, tol=6.0, how="bbox_y"),
    dict(name="body_length", mm=44.0, tol=3.0, how="bbox_y", part="Body"),
    dict(name="femur_length", mm=31.5, tol=3.0, how="longest",
         part="HindFemurL"),
    dict(name="hind_leg_span", mm=74.4, tol=6.0, how="bbox_x"),
    dict(name="eye_diameter", mm=6.4, tol=0.6, how="bbox_x", part="EyeL"),
]