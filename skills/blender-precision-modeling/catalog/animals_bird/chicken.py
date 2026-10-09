"""
chicken -- a 52 mm hen standing

A hen at 52 mm: a plump 14 mm-deep body on two thin legs, a small head with a low serrated comb, a short stubby bill and a short square tail. The scale is the read -- the same table at duck size is a turkey.

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
    total_length            = 52,
    body_length             = 32,
    body_width              = 25.6,
    body_depth              = 27.2,
    head_length             = 6.8,
    bill_length             = 3.8,
    comb_height             = 6,
    leg_length              = 8,
    tail_length             = 7.7)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-13.6, 4.3, 4.7, 18.7),
    (-6.8, 9.4, 10.2, 18.3),
    (1.7, 12.8, 13.6, 17.9),
    (9.4, 11.5, 11.5, 18.3),
    (15.3, 6, 6, 18.7),
    (18.7, 3, 3, 18.7),
]
NECK_PATH = [
    (0, -11.9, 19.6), (0, -15.3, 23), (0, -17.9, 25.5)]
NECK_RAD = [
 (6.8, 6.8),
 (5.5, 5.5),
 (4.7, 4.7)
]
HEAD_PATH = [
    (0, -17, 25.5), (0, -20.8, 25.9), (0, -23.8, 25.1)]
HEAD_RAD = [
 (3.8, 3.8),
 (3.6, 3.6),
 (2.2, 2.2)
]
BEAK_PATH = [
    (0, -23, 25.1), (0, -25.5, 24.7), (0, -26.8, 24.2)]
BEAK_RAD = [
 (1.7, 1.7),
 (1, 1),
 (0.42, 0.42)
]
LEG_PATH = [
    (4.3, 2.6, 8.5), (4.3, 1.7, 4.3), (4.3, 1.2, 1.2)]
LEG_RAD = [
 (0.95, 0.95),
 (0.78, 0.78),
 (0.78, 0.78)
]
FOOT_PATH = [
    (4.3, 1.2, 1.2), (4.3, -2, 0.7), (4.3, -3.7, 0.26)]
FOOT_RAD = [
 (0.85, 0.68),
 (1.28, 0.34),
 (0.77, 0.21)
]
WING_PATH = [
    (6, -6.8, 22.1), (9.4, 1.7, 22.1), (10.2, 8.5, 22.5), (7.7, 14.5, 23)]
WING_RAD = [
 (3.8, 2.6),
 (6, 2.2),
 (5.5, 1.9),
 (2.6, 1)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 17, 20.4), (0, 20.24, 22.5), (0, 22.96, 23.8)]
TAIL_RAD = [
 (5.1, 3.4),
 (3.4, 2.4),
 (1.2, 0.85)
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
        "body": bkit.pbr("HenBody", base=(0.33, 0.2, 0.13), rough=0.7),
        "head": bkit.pbr("HenHead", base=(0.36, 0.225, 0.145), rough=0.66),
        "beak": bkit.pbr("HenBill", base=(0.52, 0.41, 0.14), rough=0.38),
        "wing": bkit.pbr("HenWing", base=(0.255, 0.155, 0.105), rough=0.72),
        "leg": bkit.pbr("HenLeg", base=(0.48, 0.33, 0.11), rough=0.44),
        "eye": bkit.pbr("EyeDark", base=(0.02, 0.016, 0.014), rough=0.16),
        "comb": bkit.pbr("HenComb", base=(0.56, 0.055, 0.048), rough=0.44),
    }
    S = 16

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 0.95, segments=20, rings=10,
                       centre=(sx * 2.4, -20.8, 26.3), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.6, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- low serrated comb: a flat blade along the top of the skull
    _tube("Comb", [(0.0, -17.9, 28.5), (0.0, -19.9, 30.6), (0.0, -21.7, 31.0)],
          [(1.9, 0.85), (2.0, 0.94), (0.85, 0.51)], M["comb"], n=2.6, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="total_length", mm=52, tol=3, how="bbox_y", part=None),
    dict(name="body_length", mm=32, tol=2, how="bbox_y", part='Body'),
    dict(name="body_width", mm=25.6, tol=1.6, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=27.2, tol=1.6, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=3.8, tol=0.8, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=7.7, tol=1.2, how="bbox_y", part='Tail')]
