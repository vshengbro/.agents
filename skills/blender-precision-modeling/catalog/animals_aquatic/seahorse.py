"""seahorse -- a 55 mm longsnout seahorse: the upright S-curved body, the
horse-shaped head with a tubular snout, a ridged coronet, a dorsal fin and a
prehensile tail that coils.

The proportions are the whole animal. A seahorse's head is a third of its body
length without the snout, the trunk is deep and narrow, and the tail tapers into
a coil. A generic fish body with a snout attached does not read as a seahorse.

Construction: one swept body from a table, a swept head, a conical snout, a
flattened dorsal fin, and a coiled tail built from a logarithmic spiral so the
coil is a real curve rather than three hand-placed nodes.

Orientation: the animal is upright, snout pointing at -Y, X lateral, Z up.
A 55 mm seahorse fits the catalog's `tiny` band.
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
    stand_height=54.0,
    body_depth=13.0,
    head_length=18.0,
    snout_length=13.0,
    coronet_height=6.0,
    tail_coils=1.25,
)

# trunk: an upright body leaning slightly forward, deep and narrow
TRUNK = [
    (0.0, 2.0, 5.8, 5.0),
    (0.0, 8.6, 6.2, 13.6),
    (0.0, 14.4, 6.6, 21.2),
    (0.0, 18.2, 6.2, 28.9),
    (0.0, 20.2, 5.3, 36.5),
    (0.0, 20.7, 4.3, 42.2),
]
TRUNK_RAD = [(3.8, 2.9), (6.1, 5.0), (6.6, 5.9), (6.1, 5.3), (5.1, 4.4),
             (4.2, 3.4)]
# neck and head: the horse-shaped head with the coronet on top
HEAD = [
    (0.0, -1.0, 42.2), (0.0, -4.8, 44.6), (0.0, -9.6, 46.1),
    (0.0, -13.9, 45.6), (0.0, -17.3, 44.1),
]
HEAD_RAD = [(5.0, 4.0), (6.0, 5.4), (6.2, 5.8), (5.4, 4.8), (4.2, 3.6)]
# the prehensile tail: a real logarithmic spiral in the Y-Z plane
COIL_R0 = 13.0
COIL_STEPS = 22
COIL_PITCH = 0.42


def coil_path():
    """The tail's coil: a logarithmic spiral in the Y-Z plane.

    Generated from the real pitch and the real turn count rather than typed in
    as points -- a three-node 'coil' is a kink, not a curl.
    """
    pts = []
    for i in range(COIL_STEPS + 1):
        t = i / float(COIL_STEPS)
        a = 2.0 * math.pi * SPEC["tail_coils"] * t
        r = COIL_R0 * math.exp(-COIL_PITCH * a)
        pts.append((0.0, -r * math.sin(a), 36.5 - r + r * math.cos(a)))
    return pts


def build():
    hide = bkit.pbr("SeahorseHide", base=(0.72, 0.52, 0.16), rough=0.62)
    belly = bkit.pbr("SeahorseBelly", base=(0.86, 0.74, 0.42), rough=0.66)
    ridge = bkit.pbr("SeahorseRidge", base=(0.56, 0.36, 0.10), rough=0.60)
    eye = bkit.pbr("SeahorseEye", base=(0.02, 0.02, 0.025), rough=0.08)

    trunk = F.tube("Trunk", TRUNK, TRUNK_RAD, hide, n=2.6, steps=24)
    head = F.tube("Head", HEAD, HEAD_RAD, hide, n=2.6, steps=24)

    # ---- the tubular snout, swept from the muzzle down and slightly forward.
    # Built as a cone between two points rather than an oriented cylinder:
    # `bkit.cylinder(axis="Y")` sets its own rotation, so a later attempt to
    # tilt it OVERWRITES the axis alignment and the "snout" ends up pointing
    # at the ceiling.
    F.cone_between("Snout", (0.0, -18.7, 43.9), (0.0, -30.2, 40.7),
                   3.0, 1.9, seg=20, mat=hide)

    # ---- coronet: the spiny crown on top of the head
    F.cone_between("Coronet", (0.0, -14.4, 49.0), (0.0, -12.5, 54.5),
                   4.5, 1.2, seg=12, mat=ridge)

    # ---- the dorsal fin: a thin blade set on the trunk's back
    F.plate_yz("FinDorsal", [(5.8, 38.4), (13.4, 44.2), (23.0, 42.2),
                          (28.8, 34.6), (15.4, 31.7)], 1.4, x=0.0, mat=belly)

    # ---- the prehensile coil
    path = coil_path()
    rad = [(5.0 - 3.4 * (i / float(len(path) - 1)), 4.6 - 3.2 * (i / float(len(path) - 1)))
           for i in range(len(path))]
    F.tube("Tail", path, rad, hide, n=2.4, steps=16)

    # ---- the bony body rings are the species cue: a row of raised ridges,
    # laid out at a pitch derived from the trunk height rather than typed in
    n_ridge = 9
    pitch = 34.0 / (n_ridge - 1)
    for i in range(n_ridge):
        z = 8.0 + i * pitch
        F.tube("Ridge%d" % (i + 1),
               [(0.0, -8.2, z), (0.0, 0.0, z + 1.2), (0.0, 8.2, z)],
               [(2.2, 2.6), (3.4, 3.0), (2.2, 2.6)], ridge, n=2.4, steps=12)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 2.4, segments=16, rings=8,
                       centre=(sx * 4.4, -13.0, 47.5), mat=eye)

    bkit.assign_faces_by(trunk, belly, lambda c, n: c.x / bkit.MM < -2.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


CHECKS = [
    dict(name="stand_height", mm=54.0, tol=3.0, how="bbox_z"),
    dict(name="body_depth", mm=14.0, tol=1.5, how="bbox_x", part="Trunk"),
    dict(name="head_length", mm=19.0, tol=2.0, how="bbox_y", part="Head"),
    dict(name="snout_length", mm=13.0, tol=2.0, how="bbox_y", part="Snout"),
    dict(name="coronet_height", mm=8.0, tol=2.0, how="bbox_z",
         part="Coronet"),
]