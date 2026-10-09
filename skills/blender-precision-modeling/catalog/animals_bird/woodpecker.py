"""
woodpecker -- a 280 mm great spotted woodpecker perched

A woodpecker is a stiff, upright bird: a straight chisel bill longer than the head is deep, a wedge tail that tapers to a hard point and is used as a prop, short strong feet, and a swept red crest off the nape. Nothing about the posture is soft, which is why the silhouette has to be built from tapered tubes rather than spheres.

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
    body_length             = 147,
    body_width              = 114,
    body_depth              = 116,
    head_length             = 40,
    bill_length             = 38,
    crest_length            = 30,
    tail_length             = 43,
    stand_height            = 153)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-64, 24, 24.9, 90),
    (-30, 47, 48.9, 89),
    (4, 57, 58.1, 90),
    (38, 50, 48.9, 93),
    (66, 30, 29.5, 96),
    (83, 15, 13.8, 98),
]
NECK_PATH = [
    (0, -60, 92), (0, -79, 107), (0, -93, 120)]
NECK_RAD = [
 (33, 35),
 (27, 29),
 (22, 24)
]
HEAD_PATH = [
    (0, -89, 120), (0, -111, 125), (0, -129, 120)]
HEAD_RAD = [
 (23, 23),
 (20, 20),
 (12, 12)
]
BEAK_PATH = [
    (0, -125, 120), (0, -143, 118), (0, -160, 117)]
BEAK_RAD = [
 (10, 10),
 (7.5, 7.5),
 (2.5, 2.5)
]
LEG_PATH = [
    (21, 6, 53), (21, 3, 26), (21, 1.5, 11)]
LEG_RAD = [
 (8, 9),
 (7, 8),
 (8, 8)
]
FOOT_PATH = [
    (21, 1.5, 11), (21, -12, 5.5), (21, -18, 2.6)]
FOOT_RAD = [
 (8, 7),
 (9, 3.5),
 (5, 2)
]
WING_PATH = [
    (35, -29, 98), (47, 8, 99), (48, 44, 102), (38, 75, 105)]
WING_RAD = [
 (23, 17),
 (32, 14),
 (29, 11),
 (15, 7)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 75, 90), (0, 97.3, 74), (0, 110.5, 58)]
TAIL_RAD = [
 (26, 17),
 (18, 11),
 (6, 4)
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
        "body": bkit.pbr("WoodpeckerBody", base=(0.055, 0.05, 0.048), rough=0.56),
        "head": bkit.pbr("WoodpeckerHead", base=(0.07, 0.062, 0.058), rough=0.54),
        "beak": bkit.pbr("WoodpeckerBill", base=(0.115, 0.11, 0.105), rough=0.32),
        "wing": bkit.pbr("WoodpeckerWing", base=(0.045, 0.042, 0.04), rough=0.58),
        "leg": bkit.pbr("WoodpeckerFoot", base=(0.13, 0.12, 0.108), rough=0.48),
        "eye": bkit.pbr("EyeDark", base=(0.02, 0.016, 0.014), rough=0.16),
        "crest": bkit.pbr("WoodpeckerCrest", base=(0.52, 0.045, 0.035), rough=0.5),
    }
    S = 28

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 4.0, segments=20, rings=10,
                       centre=(sx * 13, -114, 129), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- red nape crest: a flat plate swept back off the crown
    _tube("Crest", [(0.0, -113.0, 134.0), (0.0, -101.0, 147.0),
                    (0.0, -87.0, 153.0)],
          [(14, 5), (10, 4.5), (4.5, 2.5)], M["crest"], n=2.6, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="total_length", mm=280, tol=14, how="bbox_y", part=None),
    dict(name="body_length", mm=147, tol=8, how="bbox_y", part='Body'),
    dict(name="body_width", mm=114, tol=8, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=116, tol=8, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=38, tol=6, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=43, tol=8, how="bbox_y", part='Tail')]
