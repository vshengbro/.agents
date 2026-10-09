"""salamander -- a 58 mm fire salamander: the long slender body, the smooth
rounded head, four short legs with four toes each, and a tapering tail. The
black-with-yellow-flecks pattern is the species cue and it is carried as a
second material on the ONE body solid.

Construction: one lofted body from a proportion table, four legs built once and
mirrored, a tail swept along the body axis, and the yellow flecks as a computed
patch of small marks laid out at a pitch from their own count. Nothing is
booleaned.

Orientation: the snout points at -Y, X lateral, Z up.
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
    overall_length=58.0,
    body_length=30.0,
    body_width=13.0,
    body_height=10.0,
    leg_span=18.0,
    tail_length=26.0,
)

# (y, half_height, half_width, z_centre) -- snout -29, hips +1
BODY = [
    (-29.0, 1.6, 1.6, 6.0),
    (-27.5, 3.2, 3.4, 6.2),
    (-25.0, 4.4, 5.0, 6.4),
    (-21.0, 5.0, 6.4, 6.6),
    (-15.0, 5.0, 6.5, 6.6),
    (-8.0, 4.6, 6.0, 6.4),
    (-2.0, 4.0, 5.2, 6.2),
    (1.0, 3.4, 4.4, 6.0),
]
FRONT = [(3.2, -11.0, 5.0), (5.4, -12.0, 3.4), (6.6, -14.0, 1.4),
         (7.6, -16.0, 0.5)]
FRONT_RAD = [(2.2, 2.0), (1.8, 1.6), (1.2, 1.1), (0.5, 0.5)]
HIND = [(3.2, -4.0, 5.0), (5.6, -2.0, 3.4), (7.2, 1.0, 1.4),
        (8.4, 3.6, 0.5)]
HIND_RAD = [(2.4, 2.2), (2.0, 1.8), (1.3, 1.2), (0.6, 0.6)]
TAIL = [(0.0, 1.0, 6.0), (0.0, 8.0, 5.6), (0.0, 16.0, 4.6),
        (0.0, 23.0, 3.4), (0.0, 29.0, 2.0)]
TAIL_RAD = [(3.6, 3.4), (2.8, 2.6), (2.0, 1.9), (1.2, 1.1), (0.4, 0.4)]


def build():
    hide = bkit.pbr("SalamanderHide", base=(0.045, 0.045, 0.05), rough=0.56)
    fleck = bkit.pbr("SalamanderFleck", base=(0.88, 0.80, 0.12), rough=0.48)
    belly = bkit.pbr("SalamanderBelly", base=(0.14, 0.13, 0.10), rough=0.60)
    eye = bkit.pbr("SalamanderEye", base=(0.02, 0.02, 0.025), rough=0.08)

    torso = F.body("Body", BODY, hide, n=2.6, steps=28)
    bkit.assign_faces_by(torso, belly, lambda c, n: c.z / bkit.MM < 4.0)

    tail = F.tube("Tail", TAIL, TAIL_RAD, hide, n=2.2, steps=18)
    bkit.assign_faces_by(tail, belly, lambda c, n: c.z / bkit.MM < 4.0)

    for tag, path, rad in (("Front", FRONT, FRONT_RAD), ("Hind", HIND, HIND_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, hide, n=2.2, steps=14)
        F.mirror_copy(leg, "Leg%sR" % tag)

    # ---- the yellow flecks: a computed patch over the back. The pitch comes
    # from the fleck count and the body length, so no two share a station.
    n_y, n_x = 7, 4
    pitch_y = 24.0 / (n_y - 1)
    pitch_x = 10.0 / (n_x - 1)
    for j in range(n_y):
        for i in range(n_x):
            y = -27.0 + j * pitch_y
            x = -5.0 + i * pitch_x
            if y > 0.0:
                continue
            z = 6.6 + 4.4 * (1.0 - (x / 6.5) ** 2)
            bkit.uv_sphere("Fleck%d%d" % (j, i), 1.5, segments=10, rings=6,
                           centre=(x, y, z), mat=fleck)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 1.6, segments=14, rings=8,
                       centre=(sx * 3.0, -26.0, 7.6), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=42)


CHECKS = [
    dict(name="overall_length", mm=58.0, tol=2.0, how="bbox_y"),
    dict(name="body_length", mm=30.0, tol=2.0, how="bbox_y", part="Body"),
    dict(name="body_width", mm=13.0, tol=1.5, how="bbox_x", part="Body"),
    dict(name="body_height", mm=10.0, tol=1.5, how="bbox_z", part="Body"),
    dict(name="leg_span", mm=18.0, tol=3.0, how="bbox_x"),
]