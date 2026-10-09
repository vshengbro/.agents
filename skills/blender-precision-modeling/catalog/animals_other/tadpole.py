"""tadpole -- a 9.5 mm tadpole: the big round head-body mass, the tapering
muscular tail with a FIN MEMBRANE along its top and bottom, and the tiny
external gills behind the head.

The tail fin is the model. A tadpole's tail is a swimming organ with a
translucent fin fringe on both edges; a bare tapered tube reads as a worm. The
fringe is real geometry -- a thin blade on each side of the tail -- and its
depth grows and then falls along the tail exactly as a tadpole's does.

At 9.5 mm the camera frames closer than Blender's default 0.1 m near clip, so
this file wraps `bkit.camera` locally rather than editing a shared script.

Orientation: the head points at -Y, the tail trails to +Y, Z up.
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

_camera_ctor = bkit.camera


def _camera(*args, **kwargs):
    cam = _camera_ctor(*args, **kwargs)
    cam.data.clip_start = 0.0002
    cam.data.clip_end = 1000.0
    return cam


bkit.camera = _camera

SPEC = dict(
    overall_length=9.5,
    head_diameter=3.2,
    body_length=4.6,
    tail_length=4.9,
    fin_depth=1.2,
    gill_count=3,
)

# head-body mass: (y, half_height, half_width, z_centre)
BODY = [
    (-4.6, 1.0, 0.9, 1.6),
    (-4.0, 1.6, 1.4, 1.6),
    (-3.0, 1.8, 1.6, 1.7),
    (-1.6, 1.6, 1.5, 1.7),
    (-0.4, 1.2, 1.1, 1.6),
]
# tail: myomeres stepping back, tapering
TAIL = [(0.0, 0.0, 1.6), (0.0, 1.4, 1.7), (0.0, 2.8, 1.7),
        (0.0, 4.0, 1.7), (0.0, 4.9, 1.7)]
TAIL_RAD = [(1.15, 1.1), (0.95, 0.95), (0.72, 0.72), (0.48, 0.48),
            (0.22, 0.22)]
# the fin membrane: top and bottom outlines that swell then taper to a point
FIN_TOP = [(0.2, 1.9), (1.6, 2.2), (3.2, 2.2), (4.4, 1.9), (5.1, 1.7)]
FIN_BOT = [(0.2, 1.3), (1.6, 0.4), (3.2, 0.5), (4.4, 1.4), (5.1, 1.6)]


def build():
    body = bkit.pbr("TadpoleBody", base=(0.16, 0.14, 0.11), rough=0.40,
                    alpha=0.90)
    dark = bkit.pbr("TadpoleDark", base=(0.07, 0.06, 0.05), rough=0.44)
    fin = bkit.pbr("TadpoleFin", base=(0.72, 0.78, 0.84), rough=0.16,
                   transmission=0.6, ior=1.36)
    gill = bkit.pbr("TadpoleGill", base=(0.55, 0.42, 0.42), rough=0.52,
                    alpha=0.85)

    F.body("Body", BODY, body, n=2.4, steps=24)
    F.tube("Tail", TAIL, TAIL_RAD, body, n=2.2, steps=16)

    F.plate_yz("FinTop", FIN_TOP, 0.10, x=0.0, mat=fin)
    F.plate_yz("FinBottom", FIN_BOT, 0.10, x=0.0, mat=fin)

    # ---- the eyes: dark beads set high on the head
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.sphere("Eye%s" % side, 0.42, (sx * 0.9, -3.8, 2.5), dark,
                 segments=14, rings=8)

    # ---- three pairs of external gills behind the head, fanned at a pitch
    # derived from the gill count
    n_g = SPEC["gill_count"]
    for i in range(n_g):
        t = i / float(n_g)
        y = -2.9 + 1.5 * t
        for side, sx in (("L", 1.0), ("R", -1.0)):
            F.cone_between("Gill%s%d" % (side, i),
                           (sx * 1.2, y, 1.9),
                           (sx * (2.4 + 0.6 * (1.0 - t)), y - 1.4 + 2.8 * t,
                            2.6 + 1.4 * t),
                           0.30, 0.10, seg=8, mat=gill)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="overall_length", mm=9.5, tol=0.8, how="bbox_y"),
    dict(name="body_length", mm=4.2, tol=0.4, how="bbox_y", part="Body"),
    dict(name="head_diameter", mm=3.2, tol=0.4, how="bbox_x", part="Body"),
    dict(name="tail_length", mm=4.9, tol=0.5, how="bbox_y", part="Tail"),
    dict(name="fin_depth", mm=0.5, tol=0.4, how="bbox_z", part="FinTop"),
]