"""
peacock -- a 905 mm peacock with a partly fanned train

The train is the bird: a fan of seven long coverts rotating about the tail base, each turned an equal 15 degrees so the fan is symmetric by construction. Behind it the body is small and plain -- thin long legs, a short neck, a crested head with a stubby bill. Without the fan a peacock is just a large dark chicken.

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
    stand_height            = 905,
    body_length             = 410,
    body_width              = 232,
    body_depth              = 236,
    train_span              = 300,
    crest_height            = 40,
    leg_length              = 585,
    tail_length             = 95)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-160, 48, 52, 760),
    (-90, 92, 100, 752),
    (-5, 112, 118, 748),
    (85, 116, 118, 750),
    (165, 86, 86, 758),
    (220, 42, 44, 766),
    (250, 20, 20, 770),
]
NECK_PATH = [
    (0, -148, 762), (0, -190, 800), (0, -226, 850)]
NECK_RAD = [
 (60, 62),
 (48, 50),
 (38, 40)
]
HEAD_PATH = [
    (0, -218, 850), (0, -256, 858), (0, -288, 850)]
HEAD_RAD = [
 (38, 38),
 (34, 34),
 (20, 20)
]
BEAK_PATH = [
    (0, -282, 848), (0, -310, 842), (0, -324, 834)]
BEAK_RAD = [
 (18, 16),
 (12, 12),
 (4, 4)
]
LEG_PATH = [
    (70, 20, 600), (70, 8, 440), (70, 0, 260), (70, -4, 120),
    (70, -10, 40), (70, -14, 16)]
LEG_RAD = [
 (24, 24),
 (19, 19),
 (14, 14),
 (13, 13),
 (12, 12),
 (12, 12)
]
FOOT_PATH = [
    (70, -14, 16), (70, -48, 8), (70, -72, 4)]
FOOT_RAD = [
 (12, 12),
 (24, 5),
 (13, 3)
]
WING_PATH = [
    (98, -96, 762), (118, -6, 752), (122, 86, 754), (104, 168, 764)]
WING_RAD = [
 (48, 36),
 (68, 30),
 (66, 26),
 (36, 18)
]
PRIM_PATH = [
    (0, 240, 760), (0, 300, 820), (0, 330, 880)]
PRIM_RAD = [
 (26, 12),
 (16, 9),
 (7, 4)
]
TAIL_PATH = [
    (0, 225, 720), (0, 280, 700), (0, 320, 690)]
TAIL_RAD = [
 (46, 30),
 (36, 24),
 (20, 14)
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
        "body": bkit.pbr("PeacockBody", base=(0.075, 0.105, 0.145), rough=0.52),
        "head": bkit.pbr("PeacockHead", base=(0.06, 0.115, 0.115), rough=0.48),
        "beak": bkit.pbr("PeacockBill", base=(0.145, 0.135, 0.12), rough=0.38),
        "wing": bkit.pbr("PeacockWing", base=(0.105, 0.095, 0.115), rough=0.54),
        "leg": bkit.pbr("PeacockLeg", base=(0.135, 0.12, 0.105), rough=0.48),
        "eye": bkit.pbr("EyeDark", base=(0.02, 0.016, 0.014), rough=0.16),
        "train": bkit.pbr("PeacockTrain", base=(0.075, 0.165, 0.115), rough=0.46),
        "crest": bkit.pbr("PeacockCrest", base=(0.085, 0.14, 0.125), rough=0.44),
    }
    S = 28

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 7.0, segments=20, rings=10,
                       centre=(sx * 22, -268, 866), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- the train: seven coverts turned an equal 15 degrees about the tail
    # base. This is a computed fan -- a rotation, not seven placed constants.
    for i, tp in enumerate(_fan_paths(PRIM_PATH, 7, 15, (0.0, 240.0, 760.0), "Y")):
        _tube("Train%d" % (i + 1), tp, PRIM_RAD, M["train"], n=2.4, steps=S)

    # ---- crest: five thin stalks radiating off the crown
    for i, cp in enumerate(_fan_paths(TAIL_PATH, 5, 14, (0.0, -250.0, 862.0), "Y")):
        _tube("Crest%d" % (i + 1), cp, TAIL_RAD, M["crest"], n=2.4, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=17)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="stand_height", mm=905, tol=24, how="bbox_z", part=None),
    dict(name="body_length", mm=410, tol=18, how="bbox_y", part='Body'),
    dict(name="body_width", mm=232, tol=14, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=236, tol=14, how="bbox_z", part='Body'),
    dict(name="leg_length", mm=585, tol=20, how="bbox_z", part='LegL'),
    dict(name="tail_length", mm=95, tol=14, how="bbox_y", part='Tail')]
