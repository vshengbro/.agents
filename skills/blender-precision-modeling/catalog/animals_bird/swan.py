"""
swan -- an 810 mm mute swan on the water stance, wings folded

The swan is the neck. A long S -- forward from the shoulders, up, then the head carried level with the base of the neck -- is the whole silhouette, and it is why a swan cannot be built as a big goose. The bill is straight and orange with a black knob, the body is broad and flat, and the wing carries a very long primary projection past the short square tail.

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
    total_length            = 810,
    body_length             = 520,
    body_width              = 296,
    body_depth              = 316,
    neck_length             = 420,
    head_length             = 50,
    bill_length             = 70,
    wing_length             = 540,
    tail_length             = 68,
    stand_height            = 674)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-230, 55, 60, 260),
    (-140, 110, 122, 252),
    (-30, 145, 158, 248),
    (85, 148, 158, 250),
    (180, 112, 118, 258),
    (250, 60, 62, 266),
    (290, 28, 28, 270),
]
NECK_PATH = [
    (0, -215, 262), (0, -255, 340), (0, -272, 430), (0, -268, 520),
    (0, -252, 590), (0, -244, 630)]
NECK_RAD = [
 (78, 80),
 (64, 66),
 (52, 54),
 (43, 43),
 (34, 34),
 (27, 27)
]
HEAD_PATH = [
    (0, -242, 632), (0, -268, 638), (0, -292, 632)]
HEAD_RAD = [
 (28, 28),
 (25, 25),
 (14, 14)
]
BEAK_PATH = [
    (0, -286, 632), (0, -322, 626), (0, -356, 620)]
BEAK_RAD = [
 (17, 16),
 (14, 14),
 (5, 5)
]
LEG_PATH = [
    (72, 30, 120), (72, 18, 64), (72, 12, 30)]
LEG_RAD = [
 (20, 21),
 (16, 17),
 (18, 18)
]
FOOT_PATH = [
    (72, 12, 30), (72, -34, 16), (72, -62, 8)]
FOOT_RAD = [
 (18, 14),
 (32, 7),
 (16, 4)
]
WING_PATH = [
    (118, -140, 300), (152, -20, 296), (158, 110, 300), (140, 240, 304),
    (96, 400, 308)]
WING_RAD = [
 (70, 48),
 (112, 38),
 (118, 32),
 (88, 22),
 (30, 12)
]
PRIM_PATH = [
    (124, 290, 306), (104, 372, 306), (76, 448, 304)]
PRIM_RAD = [
 (22, 16),
 (13, 11),
 (5, 5)
]
TAIL_PATH = [
    (0, 262, 266), (0, 300, 262), (0, 330, 258)]
TAIL_RAD = [
 (52, 32),
 (42, 24),
 (26, 14)
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
        "body": bkit.pbr("SwanBody", base=(0.72, 0.72, 0.71), rough=0.6),
        "head": bkit.pbr("SwanHead", base=(0.76, 0.76, 0.75), rough=0.58),
        "beak": bkit.pbr("SwanBill", base=(0.76, 0.245, 0.04), rough=0.36),
        "wing": bkit.pbr("SwanWing", base=(0.56, 0.57, 0.585), rough=0.62),
        "leg": bkit.pbr("SwanFoot", base=(0.055, 0.05, 0.048), rough=0.44),
        "eye": bkit.pbr("EyeDark", base=(0.02, 0.016, 0.014), rough=0.16),
        "knob": bkit.pbr("SwanKnob", base=(0.03, 0.026, 0.024), rough=0.34),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 6.0, segments=20, rings=10,
                       centre=(sx * 18, -278, 646), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)
        # ---- primary feathers: 5 evenly spaced copies of one plate, rotated about
        # the wing tip, then mirrored -- a fan computed, not placed
        for i, fp in enumerate(_fan_paths(PRIM_PATH, 5, 7, (128, 270, 304), "X")):
            _tube("PrimaryL%d" % (i + 1), fp, PRIM_RAD, M["wing"], n=2.4, steps=S)
            _tube("PrimaryR%d" % (i + 1), _flip(fp), PRIM_RAD, M["wing"], n=2.4, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- the black knob at the base of the bill, which is the mute swan's
    # giveaway and the reason the bill reads orange rather than yellow
    bkit.uv_sphere("BillKnob", 15.0, segments=20, rings=10,
                   centre=(0.0, -286.0, 640.0), mat=M["knob"])

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=21)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=520, tol=18, how="bbox_y", part='Body'),
    dict(name="body_width", mm=296, tol=14, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=316, tol=14, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=70, tol=10, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=68, tol=12, how="bbox_y", part='Tail'),
    dict(name="stand_height", mm=674, tol=20, how="bbox_z", part=None),
    dict(name="total_length", mm=810, tol=24, how="bbox_y", part=None)]
