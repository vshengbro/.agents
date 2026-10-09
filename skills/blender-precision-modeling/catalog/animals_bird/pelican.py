"""
pelican -- a 1090 mm brown pelican standing

A pelican is a big body, a neck folded back on itself in an S so the head sits over the shoulders, and a bill a quarter of total length with a slack gular pouch hanging under it. The pouch is not optional: without the sagging sac the bill reads as a heron's dagger.

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
    total_length            = 1090,
    body_length             = 770,
    body_width              = 392,
    body_depth              = 418,
    neck_length             = 260,
    head_length             = 72,
    bill_length             = 238,
    pouch_drop              = 122,
    leg_length              = 116,
    wing_length             = 610)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-300, 70, 78, 330),
    (-160, 150, 165, 320),
    (20, 195, 210, 316),
    (190, 196, 208, 320),
    (330, 140, 146, 330),
    (420, 70, 72, 340),
    (470, 34, 34, 344),
]
NECK_PATH = [
    (0, -285, 340), (0, -320, 400), (0, -320, 470), (0, -295, 520),
    (0, -270, 545)]
NECK_RAD = [
 (96, 100),
 (76, 80),
 (58, 62),
 (46, 48),
 (38, 38)
]
HEAD_PATH = [
    (0, -268, 547), (0, -306, 552), (0, -340, 544)]
HEAD_RAD = [
 (40, 40),
 (35, 35),
 (20, 20)
]
BEAK_PATH = [
    (0, -334, 546), (0, -420, 536), (0, -520, 524), (0, -572, 516)]
BEAK_RAD = [
 (26, 24),
 (22, 22),
 (13, 15),
 (5, 7)
]
LEG_PATH = [
    (95, 40, 140), (95, 26, 70), (95, 18, 26)]
LEG_RAD = [
 (30, 32),
 (24, 26),
 (26, 26)
]
FOOT_PATH = [
    (95, 18, 26), (95, -52, 14), (95, -96, 7)]
FOOT_RAD = [
 (26, 20),
 (48, 8),
 (26, 4)
]
WING_PATH = [
    (160, -170, 340), (208, 20, 330), (212, 200, 336), (186, 350, 344),
    (140, 440, 352)]
WING_RAD = [
 (96, 66),
 (140, 50),
 (146, 42),
 (108, 28),
 (36, 14)
]
PRIM_PATH = [
    (184, 300, 342), (156, 378, 344), (118, 448, 346)]
PRIM_RAD = [
 (32, 23),
 (18, 14),
 (7, 7)
]
TAIL_PATH = [
    (0, 430, 342), (0, 480, 338), (0, 520, 334)]
TAIL_RAD = [
 (72, 44),
 (56, 32),
 (34, 20)
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
        "body": bkit.pbr("PelicanBody", base=(0.33, 0.255, 0.195), rough=0.68),
        "head": bkit.pbr("PelicanHead", base=(0.78, 0.76, 0.72), rough=0.62),
        "beak": bkit.pbr("PelicanBill", base=(0.48, 0.41, 0.215), rough=0.42),
        "wing": bkit.pbr("PelicanWing", base=(0.245, 0.195, 0.16), rough=0.7),
        "leg": bkit.pbr("PelicanLeg", base=(0.185, 0.17, 0.15), rough=0.48),
        "eye": bkit.pbr("EyePale", base=(0.72, 0.64, 0.38), rough=0.2),
        "pouch": bkit.pbr("PelicanPouch", base=(0.56, 0.48, 0.3), rough=0.52),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 9.0, segments=20, rings=10,
                       centre=(sx * 24, -318, 568), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)
        # ---- primary feathers: 5 evenly spaced copies of one plate, rotated about
        # the wing tip, then mirrored -- a fan computed, not placed
        for i, fp in enumerate(_fan_paths(PRIM_PATH, 5, 8, (196, 280, 340), "X")):
            _tube("PrimaryL%d" % (i + 1), fp, PRIM_RAD, M["wing"], n=2.4, steps=S)
            _tube("PrimaryR%d" % (i + 1), _flip(fp), PRIM_RAD, M["wing"], n=2.4, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- gular pouch: the slack skin sac hanging under the upper mandible.
    # It overlaps the bill rather than meeting it, so no boolean is needed.
    _tube("Pouch", [(0.0, -350.0, 518.0), (0.0, -420.0, 482.0),
                    (0.0, -480.0, 452.0), (0.0, -520.0, 432.0)],
          [(24, 20), (40, 30), (30, 20), (8, 6)], M["pouch"], n=2.6, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=21)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="total_length", mm=1090, tol=26, how="bbox_y", part=None),
    dict(name="body_length", mm=770, tol=30, how="bbox_y", part='Body'),
    dict(name="body_width", mm=392, tol=20, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=418, tol=20, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=238, tol=20, how="bbox_y", part='Beak'),
    dict(name="leg_length", mm=116, tol=14, how="bbox_z", part='LegL')]
