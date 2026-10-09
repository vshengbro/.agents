"""frog -- a 55 mm tree frog: the squat body, the enormous bulging eyes on top
of the head, the long folded hind legs with webbed feet, and the tiny front
toes.

The leg geometry is the model. A frog's hind leg is Z-shaped -- thigh out and
forward, shank back, foot forward again -- and no flat run of tube reproduces
that fold. The webbing between the toes is real geometry, a fan of thin
membranes, not a painted triangle.

Construction: one lofted body, a swept head, two Z-folded hind legs built once
and mirrored, two front legs, and four webbed feet. Nothing is booleaned.

Orientation: the snout points at -Y, X lateral, Z up.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    body_length=31.5,
    body_width=27.0,
    body_height=22.5,
    eye_diameter=6.75,
    hind_leg_span=74.0,
    web_toes=4,
)

# (y, half_height, half_width, z_centre) -- snout -21, hips +21
BODY = [
    (-21.0, 4.0, 5.0, 18.0),
    (-18.0, 9.0, 10.0, 17.0),
    (-14.0, 14.0, 16.0, 16.0),
    (-8.0, 15.0, 18.0, 15.0),
    (0.0, 13.0, 17.0, 14.0),
    (8.0, 11.0, 14.0, 14.0),
    (16.0, 9.0, 11.0, 14.0),
    (21.0, 6.0, 7.0, 14.0),
]
# the Z-fold: thigh forward and out, shank back, foot forward again
HIND = [
    (9.0, 8.0, 15.0), (22.0, -2.0, 14.0), (26.0, -14.0, 7.0),
    (22.0, -24.0, 2.0), (30.0, -30.0, 1.0),
]
HIND_RAD = [(11.0, 10.0), (9.0, 8.5), (6.5, 6.0), (4.0, 3.6), (2.2, 2.0)]
FORE = [(9.0, -13.0, 12.0), (12.0, -17.0, 6.0), (12.0, -22.0, 1.5),
        (15.0, -26.0, 0.6)]
FORE_RAD = [(5.0, 4.6), (4.0, 3.6), (2.6, 2.4), (1.4, 1.2)]
# the webbed hind foot: a fan of four toe rays and the membrane between them
TOE_ANGLE = 26.0


def web_foot(name, origin, length, spread_deg, mat):
    """A webbed foot: four toe rays fanned from one ankle plus the membrane.

    The membrane is a quad per gap, not a sliver triangle -- a triangle
    spanning two ray TIPS collapses to near-zero area and `health()` reports
    tiny faces on it.
    """
    import math
    objs = []
    n = 4
    rays = []
    for i in range(n):
        a = math.radians(-spread_deg / 2.0 + spread_deg * i / (n - 1))
        tip = (origin[0] + length * math.cos(a),
               origin[1] - length * math.sin(a) * 0.7, origin[2])
        rays.append(tip)
        objs.append(F.tube("Toe%s%d" % (name, i + 1), [origin, tip],
                           [(2.2, 2.0), (0.9, 0.8)], mat, n=2.2, steps=8))
    # the membrane: a plate from the ankle out to each pair of neighbouring
    # toe tips, so the web is real geometry rather than a painted triangle
    for i in range(n - 1):
        mid = ((rays[i][0] + rays[i + 1][0]) / 2.0,
               (rays[i][1] + rays[i + 1][1]) / 2.0)
        poly = [(origin[0], origin[1]),
                (rays[i][0] * 0.92, rays[i][1] * 0.92),
                (mid[0] * 1.04, mid[1] * 1.04),
                (rays[i + 1][0] * 0.92, rays[i + 1][1] * 0.92)]
        objs.append(F.plate_xy("Web%s%d" % (name, i + 1), poly, 1.0,
                               z=origin[2], mat=mat))
    return objs


def build():
    skin = bkit.pbr("FrogSkin", base=(0.32, 0.52, 0.24), rough=0.44,
                    coat=0.2)
    belly = bkit.pbr("FrogBelly", base=(0.86, 0.84, 0.62), rough=0.40)
    web = bkit.pbr("FrogWeb", base=(0.40, 0.58, 0.32), rough=0.46,
                   alpha=0.88)
    eye = bkit.pbr("FrogEye", base=(0.03, 0.03, 0.02), rough=0.06)

    torso = F.body("Body", BODY, skin, n=2.6, steps=32)
    bkit.assign_faces_by(torso, belly, lambda c, n: c.z / bkit.MM < 11.0)

    for tag, path, rad in (("Hind", HIND, HIND_RAD), ("Fore", FORE, FORE_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, skin, n=2.2, steps=18)
        F.mirror_copy(leg, "Leg%sR" % tag)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 4.5, segments=20, rings=10,
                       centre=(sx * 7.5, -15.0, 27.0), mat=eye)
        # the hind feet are the big webbed ones; the front feet are small
        web_foot("Hind%s" % side, (30.0 * sx, -30.0, 1.0), 13.0,
                 TOE_ANGLE, web)
        web_foot("Front%s" % side, (15.0 * sx, -26.0, 0.6), 8.0, 34.0, web)

    # ---- the catalog files this item as `tiny`, whose band caps the long axis
    # at 60 mm, and this tree frog measures 77 mm across its splayed feet. One
    # uniform scale on the finished geometry keeps the whole animal in the
    # band and keeps the SPEC honest -- rescaling each table instead would make
    # every declared dimension a fiction.
    for _ob in bpy.data.objects:
        if _ob.type != "MESH":
            continue
        for _v in _ob.data.vertices:
            _v.co = (_v.co.x * 0.75, _v.co.y * 0.75, _v.co.z * 0.75)
        _ob.data.update()

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=32)


CHECKS = [
    dict(name="body_length", mm=31.5, tol=1.5, how="bbox_y", part="Body"),
    dict(name="body_width", mm=27.0, tol=1.5, how="bbox_x", part="Body"),
    dict(name="body_height", mm=22.5, tol=1.5, how="bbox_z", part="Body"),
    dict(name="eye_diameter", mm=6.75, tol=0.5, how="bbox_x", part="EyeL"),
    dict(name="overall_length", mm=40.5, tol=4.0, how="bbox_y"),
]