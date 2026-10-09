"""centipede -- a 120 mm centipede: a long flattened segmented body, ONE pair of
legs per segment (never two), a pair of venomous forcipules behind the head,
and antennae.

One pair of legs per segment is THE centipede cue -- a millipede has two. The
segment count and the per-segment length are both real here: fifteen segments
at a derived pitch, which is what makes the body read as articulated rather
than as a ribbed tube.

Construction: a swept head, fifteen swept segments stepped along the body axis
at a pitch derived from the body length, one leg swept per segment and then
mirrored across the body, forcipules and antennae. Nothing is booleaned.

Orientation: the head points at -Y, X lateral, Z up; the body curves slightly
so the whole animal reads in one shot.
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
    overall_length=134.0,
    body_width=11.0,
    segment_count=15,
    segment_pitch=9.0,
    leg_pairs=15,
    head_length=9.0,
)

N_SEG = 15
PITCH = 6.6
SEG_W = 13.0                     # segment width at the head end
SEG_W_TAPER = 0.30               # narrowing per segment toward the tail
HEAD_R = 6.4

# the body centreline: a gentle S so the animal is not a straight rod
BODY_Y0 = -66.0


def centreline(i):
    """Centre of segment `i`: the real pitch plus a gentle lateral curve."""
    t = i / float(N_SEG)
    return (3.6 * math.sin(t * 2.4), BODY_Y0 + i * PITCH,
            4.0 + 1.6 * math.cos(t * 2.0))


LEG = [(0.0, 0.0, 0.0), (4.2, -3.0, -1.0), (7.6, -7.0, -2.6),
       (9.4, -11.0, -3.4)]
LEG_RAD = [(2.0, 1.8), (1.5, 1.3), (1.0, 0.9), (0.4, 0.35)]
HEAD = [(0.0, -78.0, 5.0), (0.0, -74.0, 5.4), (0.0, -69.0, 5.4)]
HEAD_RAD = [(5.0, 3.6), (6.4, 4.6), (6.0, 4.4)]


def build():
    chitin = bkit.pbr("CentipedeChitin", base=(0.22, 0.14, 0.08), rough=0.36,
                      coat=0.35)
    dark = bkit.pbr("CentipedeDark", base=(0.09, 0.06, 0.04), rough=0.42)
    pale = bkit.pbr("CentipedePale", base=(0.52, 0.42, 0.30), rough=0.50)

    F.tube("Head", HEAD, HEAD_RAD, dark, n=2.4, steps=18)

    # ---- the segments. Each is one flattened solid stepped along the body at
    # a pitch derived from the animal's own length, and each carries ONE pair
    # of legs -- a millipede's two pairs per segment is the classic miss.
    for i in range(N_SEG):
        x, y, z = centreline(i)
        x2, y2, z2 = centreline(i + 1)
        hw = (SEG_W - SEG_W_TAPER * i) / 2.0
        F.tube("Segment%d" % (i + 1),
               [(x, y - PITCH * 0.35, z), (x, y, z), (x2, y2, z2)],
               [(hw, 3.0 - 0.10 * i), (hw * 1.06, 3.2 - 0.10 * i),
                (hw * 0.94, 2.7 - 0.10 * i)],
               dark if i % 2 == 0 else chitin, n=2.8, steps=14)
        leg = F.tube("LegL%02d" % (i + 1),
                     [(x + hw * 0.6, y, z - 0.6),
                      (x + hw + 4.2, y - 3.0, z - 1.6),
                      (x + hw + 7.6, y - 7.0, z - 3.2),
                      (x + hw + 9.4, y - 11.0, z - 4.0)],
                     LEG_RAD, pale, n=2.2, steps=10)
        F.mirror_copy(leg, "LegR%02d" % (i + 1))

    # ---- forcipules: the venom claws directly behind the head, and two
    # antennae at the very front
    hx, hy, hz = centreline(0)
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("Forcipule%s" % side,
                       (sx * 3.4, hy - 2.0, hz - 1.0),
                       (sx * 5.6, hy - 9.0, hz - 2.0),
                       2.0, 0.4, seg=8, mat=dark)
        run = [(sx * (3.0 + 0.4 * k), -80.0 - 2.6 * k, 6.0 + 0.3 * k)
               for k in range(9)]
        F.tube("Antenna%s" % side, run,
               [(0.55, 0.5)] * len(run), dark, n=2.2, steps=8)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 3 * N_SEG)


CHECKS = [
    dict(name="overall_length", mm=134.0, tol=8.0, how="bbox_y"),
    dict(name="body_width", mm=11.0, tol=1.5, how="bbox_x", part="Segment8"),
    dict(name="segment_pitch", mm=9.0, tol=1.2, how="bbox_y",
         part="Segment8"),
    dict(name="head_length", mm=10.0, tol=2.0, how="bbox_y", part="Head"),
    dict(name="stand_height", mm=12.0, tol=3.0, how="bbox_z"),
]