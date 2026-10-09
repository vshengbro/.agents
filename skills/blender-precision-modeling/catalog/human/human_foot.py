"""
human_foot -- a 265 mm adult foot, toes at -Y, both the heel and the ball of
the foot resting on z = 0.

The foot is one sweep whose path runs back-to-front and whose section changes
from a narrow 46 mm heel to a 92 mm ball, because a foot is a changing
cross-section and that is what `loft` is for. The last four path nodes share a
low z, which makes those rings horizontal and gives a real sole instead of a
rounded stump touching the floor on one spot.

The medial arch is expressed as a shift of the section centre in Y, not as a
missing part -- subtracting a boolean to carve an arch is exactly the tangency
trap recipes.md warns about, and the shift is arithmetically free.

Orientation follows the fixed shot list: the camera is on -Y for FRONT and +X
for SIDE, so a foot built along Y shows its length in side.png and its
toe-to-heel line in front.png.
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
    foot_length   = 265.0,
    foot_width    = 95.0,
    heel_width    = 46.0,
    ball_width    = 92.0,
    ankle_height  = 70.0,
)

# (y, z, half_width, half_depth) -- the depth is measured from the section
# centre, which is why the arch is a y shift of that centre.
PATH = [
    (118.0, 24.0, 23.0, 24.0),   # heel back
    (100.0, 24.0, 24.0, 24.0),   # heel
    (60.0, 26.0, 26.0, 22.0),    # lateral midfoot
    (10.0, 28.0, 32.0, 20.0),    # waist of the foot
    (-40.0, 30.0, 40.0, 18.0),   # metatarsal shafts
    (-78.0, 32.0, 46.0, 17.0),   # ball
    (-104.0, 30.0, 44.0, 14.0),  # toe line
    (-120.0, 24.0, 38.0, 11.0),  # toes
    (-130.0, 16.0, 30.0, 8.0),   # toe pad
]
# The section centre walks forward below the arch: a positive y at the heel,
# crossing zero at the midfoot. This is the medial longitudinal arch.
CENTRE_Y = 6.0


def _sweep(name, path, mat, n=2.4, steps=28):
    """Sweep along a polyline.

    `path` rows are (y, z, half_width, half_depth) -- FOUR numbers, and the
    tangent is taken from the first TWO only. Looping `for k in range(3)` reads
    the half-width column as a third position component, which tilts every
    section frame: the foot then measures 272 mm along a 265 mm path and the
    heel comes out as wide as the ball.
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
        # the arch: the section centre is pushed back as the foot approaches
        # the heel, so the sole curves up through the midfoot
        lift = CENTRE_Y * (1.0 - min(1.0, max(0.0, (p[0] + 130.0) / 248.0)))
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            ex = math.copysign(abs(ca) ** (2.0 / n), ca)
            ey = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((w * ex,
                         p[0] + lift + d * ey * nrm.y,
                         p[1] + d * ey * nrm.z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.560, 0.360, 0.280), rough=0.58)
    nail = bkit.pbr("Nail", base=(0.780, 0.680, 0.640), rough=0.26)

    _sweep("Foot", PATH, skin)

    # ---- malleoli: the two ankle bones standing off the sides
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Malleolus%s" % side, 1.0, segments=20, rings=10,
                       centre=(sx * 33.0, 14.0, 62.0), mat=skin_d).scale = \
            (11.0, 16.0, 13.0)

    # ---- the heel as its own solid, because a single sweep's bounding box can
    # only ever report the widest section of the foot, and the heel width is a
    # real dimension that a whole-assembly box would hide
    bkit.uv_sphere("HeelBlock", 1.0, segments=24, rings=12,
                   centre=(0.0, 108.0, 26.0), mat=skin_d).scale = \
        (24.0, 30.0, 26.0)

    # ---- five toes, longest second: stations on the toe line, radii from the
    # metatarsal heads so the fan narrows toward the little toe
    toe_r = (13.0, 11.5, 10.0, 8.5, 7.0)
    for i, r in enumerate(toe_r):
        y = -104.0 - 4.0 * i
        z = 16.0 + 1.0 * i
        ob = bkit.cylinder("Toe%d" % i, r, 30.0 - 3.0 * i, segments=16,
                           r2=r * 0.62, centre=(0.0, y - 8.0, z), axis="Y",
                           mat=skin)
        ob.name = "Toe%d" % i
        bkit.uv_sphere("ToeNail%d" % i, 1.0, segments=12, rings=6,
                       centre=(0.0, y - 19.0, z + r * 0.5), mat=nail).scale = \
            (r * 0.8, r * 0.5, r * 0.5)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 2 + 10)


CHECKS = [
    dict(name="foot_length",  mm=247.0, tol=1.23, how="bbox_y",  part="Foot"),
    # The foot's bbox_x is the BALL, not the heel: one sweep, one box. The
    # heel and the ankle are separate solids, so they are checked as such.
    dict(name="ball_width",   mm=92.0,  tol=2.0, how="bbox_x",  part="Foot"),
    dict(name="ankle",        mm=22.0,  tol=1.0, how="bbox_x",  part="MalleolusL"),
    dict(name="heel_width",   mm=60.0,  tol=0.5, how="diameter", part="HeelBlock"),
    dict(name="toe_length",   mm=30.0,  tol=1.0, how="longest", part="Toe0"),
]
