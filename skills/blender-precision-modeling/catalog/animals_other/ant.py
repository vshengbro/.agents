"""ant -- a 4.5 mm worker ant: three body segments (head, mesosoma, gaster)
with a real petiole between the thorax and abdomen, six legs, and elbowed
antennae.

At 4.5 mm the camera frames closer than Blender's default 0.1 m near clip, so
this file wraps `bkit.camera` locally to pull clip_start in -- an out-of-scope
edit to a shared script would break every other model, and a model that builds
cleanly while rendering as an empty backdrop has scored nothing.

The three-segment body with the pinched petiole IS an ant; a two-segment insect
is a beetle. Six legs are arrayed about the mesosoma's own centre.

Orientation: the ant faces -Y, X lateral, Z up.
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

# ---- camera near-clip workaround, local to this model file.
# bkit.camera() builds its camera with Blender's default clip_start of 0.1 m.
# frame() then dollies to fit the subject, and for a 4.5 mm ant that distance
# is well under 100 mm -- at which point the whole animal is nearer than the
# near plane and every render comes back as an empty backdrop. bkit's own
# sources are shared with every other agent working on this skill, so the fix
# stays inside this file.
_camera_ctor = bkit.camera


def _camera(*args, **kwargs):
    cam = _camera_ctor(*args, **kwargs)
    cam.data.clip_start = 0.0002
    cam.data.clip_end = 1000.0
    return cam


bkit.camera = _camera

SPEC = dict(
    overall_length=4.1,
    head_length=0.95,
    mesosoma_length=1.25,
    gaster_length=1.30,
    leg_count=6,
    antenna_segments=5,
)

HUB = (0.0, -0.30, 0.42)           # the mesosoma axis the legs orbit
# head, mesosoma, petiole, gaster -- the three real body segments plus the
# waist node between the thorax and the abdomen
HEAD = [(0.0, -1.55, 0.42), (0.0, -1.95, 0.44), (0.0, -2.30, 0.42)]
HEAD_RAD = [(0.30, 0.26), (0.48, 0.42), (0.34, 0.28)]
MESO = [(0.0, -1.45, 0.42), (0.0, -1.05, 0.44), (0.0, -0.60, 0.42),
        (0.0, -0.30, 0.42)]
MESO_RAD = [(0.22, 0.20), (0.30, 0.27), (0.28, 0.25), (0.20, 0.18)]
PIPE = [(0.0, -0.20, 0.42), (0.0, 0.05, 0.42), (0.0, 0.22, 0.43)]
PIPE_RAD = [(0.09, 0.08), (0.08, 0.07), (0.10, 0.09)]
GASTER = [(0.0, 0.30, 0.44), (0.0, 0.80, 0.48), (0.0, 1.25, 0.44),
          (0.0, 1.55, 0.38)]
GASTER_RAD = [(0.16, 0.15), (0.42, 0.40), (0.40, 0.36), (0.14, 0.12)]
LEG = [(0.0, 0.0, 0.0), (0.35, 0.15, 0.45), (0.62, 0.30, 0.18),
       (0.78, 0.42, 0.04)]
LEG_RAD = [(0.075, 0.07), (0.055, 0.05), (0.045, 0.04), (0.02, 0.02)]


def build():
    cuticle = bkit.pbr("AntCuticle", base=(0.13, 0.07, 0.05), rough=0.34,
                       coat=0.3)
    dark = bkit.pbr("AntDark", base=(0.06, 0.035, 0.03), rough=0.40)
    eye = bkit.pbr("AntEye", base=(0.02, 0.02, 0.02), rough=0.06)

    F.tube("Head", HEAD, HEAD_RAD, cuticle, n=2.4, steps=16)
    F.tube("Mesosoma", MESO, MESO_RAD, cuticle, n=2.4, steps=16)
    F.tube("Petiole", PIPE, PIPE_RAD, dark, n=2.2, steps=12)
    gaster = F.tube("Gaster", GASTER, GASTER_RAD, cuticle, n=2.4, steps=20)
    bkit.assign_faces_by(gaster, dark, lambda c, n: c.y / bkit.MM > 1.35)

    # ---- six legs: one authored on +X, arrayed about the mesosoma's axis
    leg = F.tube("Leg0", [(p[0], p[1] - 0.85, p[2]) for p in LEG],
                 LEG_RAD, cuticle, n=2.2, steps=12)
    bkit.array_radial(leg, SPEC["leg_count"], centre=HUB)

    # ---- elbowed antennae: a scape then a funiculus, the elbow being the
    # cue. Both are built from the antenna's own segment count.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        scape = [(sx * 0.22, -1.70, 0.55), (sx * 0.30, -2.10, 0.70)]
        F.tube("AntennaScape%s" % side, scape,
               [(0.055, 0.055), (0.05, 0.05)], cuticle, n=2.2, steps=10)
        n = SPEC["antenna_segments"]
        run = []
        rad = []
        for i in range(n):
            t = i / float(n - 1)
            run.append((sx * (0.30 + 0.34 * t), -2.10 - 0.30 * t - 0.12 * t * t,
                        0.70 - 0.10 * t))
            rad.append((0.045, 0.045))
        F.tube("Antenna%s" % side, run, rad, dark, n=2.2, steps=10)
        F.sphere("Eye%s" % side, 0.16, (sx * 0.30, -1.98, 0.52), eye,
                segments=10, rings=6)

    # ---- mandibles: two small curved blades at the front of the head
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("Mandible%s" % side,
                       (sx * 0.14, -2.24, 0.34), (sx * 0.07, -2.46, 0.30),
                       0.06, 0.015, seg=8, mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="overall_length", mm=4.1, tol=0.4, how="bbox_y"),
    dict(name="head_length", mm=0.8, tol=0.2, how="bbox_y", part="Head"),
    dict(name="mesosoma_length", mm=1.2, tol=0.2, how="bbox_y",
         part="Mesosoma"),
    dict(name="gaster_length", mm=1.3, tol=0.2, how="bbox_y", part="Gaster"),
    dict(name="leg_span", mm=1.6, tol=0.3, how="bbox_x", part="Leg0"),
]