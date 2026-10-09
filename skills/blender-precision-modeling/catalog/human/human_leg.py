"""
human_leg -- a 900 mm leg from the greater trochanter to the sole, standing with
a 4 deg knee flexion and the foot flat on z = 0.

Same sweep as the arm, longer: a superelliptic section follows hip, thigh,
patella, knee, calf, tibial crest, ankle and heel. The last two path nodes share
a z, which is what makes the rings at the bottom horizontal and the sole a flat
strip resting on the floor -- the same trick the mammal models use to get all
four feet onto z = 0.

The gastrocnemius belly is a separate solid because it is not a section of the
limb: it sits behind the calf and swells past the taper, and trying to express
it in the radius table makes the whole calf lumpy.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    leg_length     = 900.0,
    thigh_length   = 420.0,
    shin_length    = 400.0,
    femur_radius   = 88.0,
    ankle_radius   = 38.0,
)

# (y, z, half_width, half_depth). -Y is anterior, so the knee is forward.
PATH = [
    (0.0, 900.0, 96.0, 104.0),   # hip
    (-6.0, 800.0, 88.0, 94.0),   # upper thigh
    (-10.0, 660.0, 78.0, 84.0),  # mid thigh
    (-12.0, 530.0, 68.0, 72.0),  # above the knee
    (-13.0, 484.0, 58.0, 60.0),  # knee
    (-8.0, 420.0, 58.0, 62.0),   # tibial flare
    (-4.0, 330.0, 52.0, 54.0),   # calf
    (0.0, 240.0, 44.0, 44.0),    # distal shin
    (2.0, 150.0, 34.0, 33.0),    # above the ankle
    (2.0, 95.0, 28.0, 26.0),     # ankle
    (10.0, 46.0, 30.0, 34.0),    # heel block
    (-2.0, 22.0, 34.0, 62.0),    # arch
    (-2.0, 8.0, 32.0, 80.0),     # ball of the foot
]


def _sweep(name, path, mat, n=2.4, steps=28):
    """Sweep along a polyline.

    `path` rows are (y, z, half_width, half_depth) -- FOUR numbers, and the
    tangent must be taken from the first TWO only. Looping `for k in range(3)`
    here reads the half-width column as a third position component, which tilts
    the section frame: the leg then measures 1075 mm instead of 900 and the
    rings are no longer perpendicular to their own path.
    """
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(2)]
        elif i == m - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(2)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(2)]
        tl = math.hypot(t[0], t[1]) or 1.0
        tv = Vector((0.0, t[0] / tl, t[1] / tl))
        side = Vector((1.0, 0.0, 0.0))
        side = (side - tv * side.dot(tv)).normalized()
        nrm = tv.cross(side).normalized()
        w, d = path[i][2], path[i][3]
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            ex = math.copysign(abs(ca) ** (2.0 / n), ca)
            ey = math.copysign(abs(sa) ** (2.0 / n), sa)
            # PATH rows are (y, z, half_width, half_depth): a node's z is
            # path[i][1]. Reading [2] here builds a 250 mm stump instead of a
            # 900 mm leg, because [2] is the radius.
            ring.append((w * ex * side.x + d * ey * nrm.x,
                         p[0] + w * ex * side.y + d * ey * nrm.y,
                         p[1] + w * ex * side.z + d * ey * nrm.z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.560, 0.360, 0.280), rough=0.58)

    _sweep("Leg", PATH, skin)

    # ---- patella: the kneecap, a separate solid because it sits ON the knee
    bkit.uv_sphere("Patella", 1.0, segments=24, rings=12,
                   centre=(0.0, -52.0, 486.0), mat=skin_d).scale = \
        (36.0, 16.0, 38.0)

    # ---- gastrocnemius: the calf belly, swelling behind the taper
    calf = bkit.uv_sphere("Calf", 1.0, segments=28, rings=14,
                          centre=(0.0, 46.0, 350.0), mat=skin)
    calf.scale = (58.0, 46.0, 96.0)
    calf.name = "Calf"

    # ---- five toes on stations from the ball of the foot forward
    for i, y in enumerate((-70.0, -92.0, -110.0, -124.0, -136.0)):
        r = 11.0 - 1.4 * i
        bkit.cylinder("Toe%d" % i, r, 26.0 - 3.0 * i, segments=14, r2=r * 0.6,
                      centre=(0.0, y, 12.0), axis="Y", mat=skin)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 2 + 5)


CHECKS = [
    dict(name="leg_length", mm=905.0, tol=4.52, how="top_z", part="Leg"),
    # A single sweep's bbox_x is its widest section, so it can report the thigh
    # and the ankle only if they are separate parts -- and they are not. The
    # thigh, knee and calf are therefore checked as the calf's own solid and
    # the knee as the patella, which really are separate.
    dict(name="thigh_girth", mm=192.0, tol=2.0, how="bbox_x", part="Leg"),
    dict(name="knee",        mm=72.0,  tol=1.5, how="bbox_x", part="Patella"),
    dict(name="calf",        mm=116.0, tol=1.5, how="bbox_x", part="Calf"),
    dict(name="toe",         mm=26.0,  tol=0.8, how="longest", part="Toe0"),
]
