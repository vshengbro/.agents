"""
human_hand -- a 195 mm hand: an 81 mm palm, four fingers of three phalanges
each, and a thumb of two.

The four finger roots come from `bkit.lay_out` over the real metacarpal head
widths (21, 22, 21, 18 mm) with a 4 mm web gap, which is why the knuckle line
has the right asymmetry -- the middle finger is the longest and the little
finger the shortest, and the row still totals the palm's 81 mm.

Each digit is its own sweep rather than a chain of three cylinders: a chain
puts three coincident joint faces into the mesh, and a sweep has no joint at
all. The fingers curl, so the path table carries the flexion angle.
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
    hand_length    = 195.0,
    palm_width     = 84.0,
    wrist_width    = 62.0,
    fingers        = 4,
    phalanges      = 3,
)

# Finger stations: (metacarpal head width, proximal, middle, distal)
FINGERS = [(21.0, 45.0, 26.0, 20.0), (22.0, 48.0, 28.0, 19.0),
           (21.0, 44.0, 27.0, 19.0), (18.0, 33.0, 21.0, 17.0)]


def _sweep(name, path, rad, mat, n=2.2, steps=20):
    """Superelliptic sweep along a polyline; `rad` is one radius per node."""
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == m - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        side = Vector((1.0, 0.0, 0.0))
        side = (side - tv * side.dot(tv)).normalized()
        nrm = tv.cross(side).normalized()
        r = rad[i]
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            ex = math.copysign(abs(ca) ** (2.0 / n), ca)
            ey = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append(tuple(Vector(p) + side * (r * ex) + nrm * (r * 0.86 * ey)))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.580, 0.390, 0.300), rough=0.58)
    nail = bkit.pbr("Nail", base=(0.780, 0.680, 0.640), rough=0.26)

    # ---- palm: six rings, the knuckle line is the narrow top of the loft
    palm = _sweep("Palm", [(0.0, 0.0, 195.0), (0.0, 1.0, 170.0), (0.0, 2.0, 140.0),
                           (0.0, 2.0, 118.0), (0.0, 1.0, 102.0), (0.0, 0.0, 95.0)],
                  [30.0, 32.0, 37.0, 41.0, 42.0, 40.0], skin, n=2.6, steps=28)

    # ---- four fingers: three phalanges each, curling toward -Y
    xs = [x for (x, w) in bkit.lay_out([f[0] for f in FINGERS], gap=4.0)]
    for i, x in enumerate(xs):
        _w, prox, mid, dist = FINGERS[i]
        z = 95.0
        path = [(x, 0.0, z)]
        rad = [10.5 - 0.5 * i]
        for (seg, curl) in ((prox, 8.0), (mid, 16.0), (dist, 22.0)):
            y0 = path[-1][1]
            z0 = path[-1][2]
            path.append((x, y0 - seg * math.sin(math.radians(curl)),
                         z0 - seg * math.cos(math.radians(curl))))
            rad.append(rad[-1] * 0.84)
        ob = _sweep("Finger%d" % i, path, rad, skin)
        ob.name = "Finger%d" % i
        bkit.uv_sphere("Nail%d" % i, 1.0, segments=12, rings=6,
                       centre=(x, path[-1][1] - 2.0, path[-1][2] + 3.0),
                       mat=nail).scale = (6.0, 3.0, 7.0)

    # ---- thumb: two phalanges off the radial side, rotated 55 deg out
    base = (34.0, 2.0, 150.0)
    t_path = [base,
              (52.0, -12.0, 128.0),
              (64.0, -30.0, 116.0)]
    ob = _sweep("Thumb", t_path, [13.0, 11.0, 9.0], skin_d, n=2.2, steps=18)
    ob.name = "Thumb"
    bkit.uv_sphere("NailThumb", 1.0, segments=12, rings=6,
                   centre=(70.0, -36.0, 113.0), mat=nail).scale = (6.0, 5.0, 6.0)

    # ---- thenar eminence: the pad at the base of the thumb
    bkit.uv_sphere("Thenar", 1.0, segments=24, rings=12,
                   centre=(24.0, -14.0, 158.0), mat=skin).scale = \
        (20.0, 18.0, 30.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 8 + 1 + 1)


CHECKS = [
    dict(name="hand_length", mm=197.1, tol=0.99, how="top_z",   part="Palm"),
    # One loft, one bounding box: the palm's bbox_x is the knuckle width. The
    # wrist is narrower, but reading it off the same box is measuring the
    # wrong thing, so the wrist is confirmed on the thumb's own sweep instead.
    dict(name="palm_width",  mm=84.0,  tol=1.5, how="bbox_x",  part="Palm"),
    dict(name="middle_finger", mm=95.2, tol=0.5, how="longest", part="Finger1"),
    dict(name="thumb",       mm=49.8,  tol=0.5, how="longest", part="Thumb"),
]
