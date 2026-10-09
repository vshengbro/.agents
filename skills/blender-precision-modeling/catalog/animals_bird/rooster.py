"""
rooster -- a 280 mm rooster with sickle tail feathers

Three cues separate a rooster from a chicken: a large serrated comb and wattles on the head, a longer thicker neck with pointed hackles, and above all a tail of five sickle feathers sweeping up and back. The tail fan rotates about the tail base in the Y-Z plane -- the plane a sickle actually fans across -- so it is symmetric by construction.

Construction: `_tube` sweeps a superellipse ring along a polyline and caps it,
so every part is a separate closed solid and nothing has to be booleaned. Any
fan of feathers is a computed rotation (`_fan_paths`), never hand-placed, and
every paired part is the exact mirror of its partner (`_flip`).

Orientation: the nose points at -Y, world X is lateral, Z is up. The catalog's
fixed shot list puts the camera on +X for the SIDE view and on -Y for the FRONT
view, so a bird has to be built along Y for side.png to show a silhouette rather
than a face. Both feet rest on z=0.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --------------------------------------------------------------------------
# camera near-clip workaround, local to this model file
# --------------------------------------------------------------------------
# bkit.camera() builds its camera with Blender's default clip_start of 0.1 m.
# frame() then dollies the camera to fit the subject, and for a small subject
# that distance can be under 100 mm -- at which point the whole bird is nearer
# than the near plane and every render comes back as an empty backdrop. A
# 15 mm hummingbird frames at 60 mm, so it disappears completely.
#
# Wrapping the constructor is the fix that stays inside this file: bkit's own
# sources are shared with every other agent working on this skill right now.
_camera_ctor = bkit.camera


def _camera(*args, **kwargs):
    cam = _camera_ctor(*args, **kwargs)
    cam.data.clip_start = 0.0002
    cam.data.clip_end = 1000.0
    return cam


bkit.camera = _camera

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    total_length            = 280,
    body_length             = 162,
    body_width              = 128,
    body_depth              = 130,
    head_length             = 45,
    bill_length             = 26,
    comb_height             = 33,
    tail_length             = 52,
    stand_height            = 171)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-62, 28, 28.5, 100),
    (-26, 52, 54.2, 98),
    (12, 64, 65.3, 100),
    (49, 55, 54.2, 105),
    (80, 34, 33.1, 110),
    (100, 17, 15.6, 112),
]
NECK_PATH = [
    (0, -58, 104), (0, -77, 128), (0, -90, 150)]
NECK_RAD = [
 (36, 38),
 (29, 31),
 (24, 26)
]
HEAD_PATH = [
    (0, -85, 152), (0, -110, 157), (0, -130, 152)]
HEAD_RAD = [
 (24, 24),
 (21, 21),
 (13, 13)
]
BEAK_PATH = [
    (0, -125, 152), (0, -139, 149), (0, -146, 146)]
BEAK_RAD = [
 (9.5, 9),
 (7, 7),
 (2.5, 2.5)
]
LEG_PATH = [
    (24, 8, 60), (24, 5, 30), (24, 3.5, 13)]
LEG_RAD = [
 (10, 11),
 (8, 9),
 (9, 9)
]
FOOT_PATH = [
    (24, 3.5, 13), (24, -13, 6), (24, -20, 3)]
FOOT_RAD = [
 (9, 8),
 (11, 4),
 (6.5, 2.2)
]
WING_PATH = [
    (39, -24, 111), (52, 8, 113), (54, 49, 116), (42, 85, 119)]
WING_RAD = [
 (25, 19),
 (35, 15),
 (32, 13),
 (17, 8)
]
PRIM_PATH = [
    (0, -100, 167), (0, -107, 190), (0, -114, 200)]
PRIM_RAD = [
 (7, 2.7),
 (5.2, 2.2),
 (2.6, 1.3)
]
TAIL_PATH = [
    (0, 84, 118), (0, 115.4, 159.8), (0, 128.8, 201.6)]
TAIL_RAD = [
 (12, 7),
 (7.5, 4.2),
 (2.5, 1.7)
]


def _tube(name, path, rad, mat, n=2.4, steps=28):
    """Sweep a superellipse ring along a 3D polyline and cap both ends.

    One helper builds every organic part of a bird. The ring frame follows the
    tangent, so a bend never twists the profile: `s` is the previous node's side
    axis re-projected perpendicular to the tangent (Gram-Schmidt), and `v` is
    `t x s`. `rad` is one (along_s, along_v) pair per path node. Where the
    tangent is parallel to the chosen world axis the axis list is walked in
    order, so a vertical leg still gets a horizontal ring.

    Every result is one closed solid, so no part of the bird has to be
    booleaned -- which is what keeps `health()` at zero non-manifold edges.
    """
    rings = []
    prev = None
    m = len(path)
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, m - 1)]
        t = [b[k] - a[k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        t = [c / tl for c in t]
        s = None
        if prev is not None:
            d = sum(prev[k] * t[k] for k in range(3))
            cand = [prev[k] - d * t[k] for k in range(3)]
            if sum(c * c for c in cand) > 1e-9:
                s = cand
        if s is None:
            for up in ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)):
                cand = [up[1] * t[2] - up[2] * t[1],
                        up[2] * t[0] - up[0] * t[2],
                        up[0] * t[1] - up[1] * t[0]]
                if sum(c * c for c in cand) > 1e-9:
                    s = cand
                    break
        sl = math.sqrt(sum(c * c for c in s))
        s = [c / sl for c in s]
        v = [t[1] * s[2] - t[2] * s[1], t[2] * s[0] - t[0] * s[2],
             t[0] * s[1] - t[1] * s[0]]
        prev = s
        w, h = rad[i]
        ring = []
        for j in range(steps):
            ang = 2.0 * math.pi * j / steps
            ca, sa = math.cos(ang), math.sin(ang)
            cx = math.copysign(abs(ca) ** (2.0 / n), ca)
            cy = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((p[0] + s[0] * w * cy + v[0] * h * cx,
                         p[1] + s[1] * w * cy + v[1] * h * cx,
                         p[2] + s[2] * w * cy + v[2] * h * cx))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def _flip(path):
    """Mirror a path across X, which is how every paired part stays symmetric."""
    return [(-p[0], p[1], p[2]) for p in path]


def _rotpt(p, deg, pivot, axis):
    """Rotate one path point about an axis through `pivot`."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    d = [p[k] - pivot[k] for k in range(3)]
    if axis == "X":
        return (pivot[0] + d[0],
                pivot[1] + d[1] * ca - d[2] * sa,
                pivot[2] + d[1] * sa + d[2] * ca)
    if axis == "Y":
        return (pivot[0] + d[0] * ca + d[2] * sa,
                pivot[1],
                pivot[2] - d[0] * sa + d[2] * ca)
    return (pivot[0] + d[0] * ca - d[1] * sa,
            pivot[1] + d[0] * sa + d[1] * ca,
            pivot[2])


def _fan_paths(path, count, step_deg, pivot, axis):
    """`count` copies of `path`, each turned a further equal step about `pivot`.

    A feather fan is a rotation, not a set of hand-placed constants, so it is
    symmetric by construction. axis="Y" spreads a fan sideways in the X-Z plane
    (tail coverts, crests); axis="X" spreads one in the Y-Z plane, which is the
    plane a folded wing's primaries actually fan across.
    """
    return [[_rotpt(q, i * step_deg, pivot, axis) for q in path]
            for i in range(count)]

def build():
    M = {
        "body": bkit.pbr("RoosterBody", base=(0.36, 0.2, 0.11), rough=0.66),
        "head": bkit.pbr("RoosterHead", base=(0.42, 0.23, 0.12), rough=0.62),
        "beak": bkit.pbr("RoosterBill", base=(0.54, 0.42, 0.13), rough=0.38),
        "wing": bkit.pbr("RoosterWing", base=(0.23, 0.14, 0.085), rough=0.7),
        "leg": bkit.pbr("RoosterLeg", base=(0.5, 0.35, 0.12), rough=0.42),
        "eye": bkit.pbr("EyeAmber", base=(0.48, 0.32, 0.06), rough=0.18),
        "comb": bkit.pbr("RoosterComb", base=(0.58, 0.06, 0.05), rough=0.42),
    }
    S = 28

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 3.5, segments=20, rings=10,
                       centre=(sx * 13, -108, 162), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.4, steps=S)
    # ---- tail fan: 5 copies of one tapered plate, each turned a
    # further equal step about the tail base
    for i, fp in enumerate(_fan_paths(TAIL_PATH, 5, 13, (0, 84, 118), "X")):
        _tube("Tail%d" % (i + 1), fp, TAIL_RAD, M["wing"], n=2.2, steps=S)

    # ---- comb: five lobes turned an equal 14 degrees about the crown, so the
    # broad blade is a rotation rather than five placed plates
    for i, cp in enumerate(_fan_paths(PRIM_PATH, 5, 14, (0.0, -100.0, 167.0), "Y")):
        _tube("CombLobe%d" % (i + 1), cp, PRIM_RAD, M["comb"], n=2.4, steps=S)

    # ---- wattles: the two fleshy lobes under the bill
    for side, sx in (("L", 1.0), ("R", -1.0)):
        _tube("Wattle%s" % side,
              [(sx * 10.0, -128.0, 140.0), (sx * 10.0, -133.0, 131.0)],
              [(4.5, 3.5), (1.8, 1.8)], M["comb"], n=2.4, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="total_length", mm=280, tol=14, how="bbox_y", part=None),
    dict(name="body_length", mm=162, tol=10, how="bbox_y", part='Body'),
    dict(name="body_width", mm=128, tol=10, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=130, tol=10, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=26, tol=5, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=52, tol=10, how="bbox_y", part='Tail1')]
