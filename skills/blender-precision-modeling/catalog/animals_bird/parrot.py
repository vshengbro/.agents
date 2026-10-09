"""
parrot -- a 250 mm macaw perched

The parrot silhouette is beak-versus-body: a deep, strongly hooked upper mandible with a matching lower mandible, as long as the head is deep, sitting on a compact stocky body -- plus a long graduated tail that is half the bird's length. A generic cone beak makes a pigeon.

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
    total_length            = 250,
    body_length             = 124,
    body_width              = 104,
    body_depth              = 103,
    head_length             = 33,
    bill_length             = 42,
    leg_length              = 34,
    tail_length             = 43,
    stand_height            = 132)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-50, 22, 23.0, 76),
    (-21, 43, 43.3, 75),
    (11, 52, 51.6, 76),
    (38, 45, 44.2, 78),
    (61, 27, 24.9, 81),
    (74, 12, 11.1, 82),
]
NECK_PATH = [
    (0, -47, 77), (0, -63, 85), (0, -75, 92)]
NECK_RAD = [
 (31, 32),
 (27, 28),
 (23, 25)
]
HEAD_PATH = [
    (0, -71, 92), (0, -89, 96), (0, -104, 92)]
HEAD_RAD = [
 (23, 23),
 (21, 21),
 (13, 13)
]
BEAK_PATH = [
    (0, -100, 93), (0, -121, 90), (0, -136, 78), (0, -139, 63)]
BEAK_RAD = [
 (17, 16),
 (15, 14),
 (10, 10),
 (3.5, 3.5)
]
LEG_PATH = [
    (20, 5, 44), (20, 2, 22), (20, 0, 9)]
LEG_RAD = [
 (8, 8.5),
 (7, 7.5),
 (7.5, 7.5)
]
FOOT_PATH = [
    (20, 0, 9), (20, -11, 5), (20, -17, 2)]
FOOT_RAD = [
 (7.5, 6.5),
 (9, 3.5),
 (5.5, 2)
]
WING_PATH = [
    (43, -25, 81), (54, 5, 80), (56, 38, 82), (46, 69, 85)]
WING_RAD = [
 (25, 18),
 (33, 15),
 (30, 12),
 (15, 7)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 67, 81), (0, 89, 75), (0, 110, 70)]
TAIL_RAD = [
 (12, 9),
 (9, 6),
 (4.5, 3.5)
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
        "body": bkit.pbr("MacawBody", base=(0.64, 0.18, 0.075), rough=0.62),
        "head": bkit.pbr("MacawHead", base=(0.7, 0.215, 0.085), rough=0.58),
        "beak": bkit.pbr("MacawBill", base=(0.115, 0.105, 0.098), rough=0.34),
        "wing": bkit.pbr("MacawWing", base=(0.56, 0.15, 0.065), rough=0.64),
        "leg": bkit.pbr("MacawFoot", base=(0.145, 0.135, 0.125), rough=0.48),
        "eye": bkit.pbr("EyePale", base=(0.78, 0.7, 0.4), rough=0.2),
    }
    S = 28

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=2.6, steps=S)
    _tube("BeakLower", [
    (0, -101, 82), (0, -118, 76), (0, -128, 68)], [
 (12, 9),
 (10, 7),
 (3.5, 2.5)
], M["beak"], n=3, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 5.0, segments=20, rings=10,
                       centre=(sx * 16, -95, 103), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)
    # ---- tail fan: 5 copies of one tapered plate, each turned a
    # further equal step about the tail base
    for i, fp in enumerate(_fan_paths(TAIL_PATH, 5, 10, (0, 67, 81), "Y")):
        _tube("Tail%d" % (i + 1), fp, TAIL_RAD, M["wing"], n=2.4, steps=S)


    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="total_length", mm=250, tol=14, how="bbox_y", part=None),
    dict(name="body_length", mm=124, tol=8, how="bbox_y", part='Body'),
    dict(name="body_width", mm=104, tol=8, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=103, tol=8, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=42, tol=6, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=43, tol=8, how="bbox_y", part='Tail')]
