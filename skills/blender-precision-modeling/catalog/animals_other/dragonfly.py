"""dragonfly -- a 110 mm dragonfly: a long segmented abdomen, a huge pair of
compound eyes, a short thorax, two pairs of LONG narrow wings held out at the
sides, and six spiny legs.

Two pairs of wings, each a long narrow blade, is the dragonfly cue -- a
damselfly holds its wings together over the back, a dragonfly holds them out.
Wing span here is 110 mm and the abdomen is over half the animal's length.

Construction: a swept thorax and a segmented abdomen whose segment count and
per-segment length come from the table, four wing blades (two mirrored pairs),
six arrayed legs, and two faceted compound eyes. Nothing is booleaned.

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
    wing_span=110.0,
    body_length=85.0,
    abdomen_segments=9,
    abdomen_pitch=6.6,
    eye_diameter=9.0,
    wing_count=4,
)

THORAX = [(0.0, -9.0, 12.0), (0.0, -5.0, 12.4), (0.0, -1.0, 12.2),
          (0.0, 2.0, 12.0)]
THORAX_RAD = [(3.2, 2.8), (4.6, 4.0), (4.4, 3.8), (3.2, 2.8)]
N_SEG = 9
SEG_PITCH = 6.6
SEG_R = [3.4, 3.2, 3.0, 2.8, 2.6, 2.4, 2.1, 1.8, 1.4]
SEG_W = [3.6, 3.4, 3.2, 3.0, 2.7, 2.4, 2.0, 1.6, 1.1]
# a long narrow blade with the real dragonfly's leading-edge vein bulge
FORE = [(0.0, 0.0), (18.0, 3.0), (38.0, 5.4), (52.0, 5.0), (52.0, 1.6),
        (34.0, -1.0), (16.0, -2.2)]
HIND = [(0.0, 0.0), (16.0, 2.6), (34.0, 4.6), (46.0, 4.2), (46.0, 1.2),
        (30.0, -1.2), (14.0, -2.0)]
LEG = [(0.0, 0.0, 0.0), (4.4, 1.6, -3.4), (8.0, 3.4, -7.6),
       (10.0, 5.6, -10.4)]
LEG_RAD = [(1.1, 1.0), (0.8, 0.7), (0.6, 0.55), (0.3, 0.28)]


def build():
    body = bkit.pbr("DragonflyBody", base=(0.20, 0.34, 0.20), rough=0.38,
                    coat=0.3)
    band = bkit.pbr("DragonflyBand", base=(0.05, 0.09, 0.06), rough=0.42)
    wing = bkit.pbr("DragonflyWing", base=(0.80, 0.86, 0.92), rough=0.08,
                    transmission=0.6, ior=1.38)
    eye = bkit.pbr("DragonflyEye", base=(0.10, 0.22, 0.06), rough=0.16,
                   coat=0.4)

    F.tube("Thorax", THORAX, THORAX_RAD, body, n=2.4, steps=18)

    # ---- the abdomen: nine segments at a derived pitch. The per-segment
    # length is what makes it read as segmented rather than as one tube.
    for i in range(N_SEG):
        y0 = 3.0 + i * SEG_PITCH
        r0 = SEG_R[i]
        r1 = SEG_R[i + 1] if i + 1 < N_SEG else r0 * 0.55
        F.tube("Abdomen%d" % (i + 1),
               [(0.0, y0, 12.0 - 0.06 * i), (0.0, y0 + SEG_PITCH * 0.5,
                                             12.0 - 0.06 * i),
                (0.0, y0 + SEG_PITCH + 0.4, 12.0 - 0.06 * (i + 1))],
               [(SEG_W[i], r0), ((SEG_W[i] + SEG_W[i + 1]
                                  if i + 1 < N_SEG else SEG_W[i] * 0.7) / 2.0,
                                 (r0 + r1) / 2.0),
                (SEG_W[i + 1] if i + 1 < N_SEG else SEG_W[i] * 0.7, r1)],
               body if i % 2 == 0 else band, n=2.4, steps=14)
    # the terminal appendages
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("Cerci%s" % side,
                       (0.0, 3.0 + N_SEG * SEG_PITCH, 11.5),
                       (sx * 1.6, 3.0 + N_SEG * SEG_PITCH + 7.0, 11.0),
                       0.8, 0.15, seg=8, mat=band)

    # ---- four wings, two pairs, each authored once and mirrored
    fore = F.plate_xy("WingForeL", FORE, 0.9, z=0.0, mat=wing)
    bkit.move(fore, 3.4, -6.0, 14.0)
    F.bake_rot(fore, "X", -6.0)
    F.mirror_copy(fore, "WingForeR")
    hind = F.plate_xy("WingHindL", HIND, 0.9, z=0.0, mat=wing)
    bkit.move(hind, 3.2, -3.0, 13.4)
    F.bake_rot(hind, "X", 4.0)
    F.mirror_copy(hind, "WingHindR")

    leg = F.tube("Leg0", [(p[0], p[1] - 4.0, p[2] + 12.0) for p in LEG],
                 LEG_RAD, band, n=2.2, steps=12)
    bkit.array_radial(leg, 6, centre=(0.0, -4.0, 12.0))

    # ---- the huge compound eyes: faceted spheres, one per side of the head
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.sphere("Eye%s" % side, 4.5, (sx * 2.6, -8.6, 15.2), eye,
                 segments=20, rings=10)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=24)


CHECKS = [
    dict(name="wing_span", mm=110.0, tol=6.0, how="bbox_x"),
    dict(name="body_length", mm=85.0, tol=4.0, how="bbox_y"),
    dict(name="eye_diameter", mm=9.0, tol=0.8, how="bbox_x", part="EyeL"),
    dict(name="thorax_width", mm=9.2, tol=1.0, how="bbox_x", part="Thorax"),
    dict(name="abdomen_segments", mm=6.6, tol=1.0, how="bbox_y",
         part="Abdomen1"),
]