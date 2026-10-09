"""
ostrich -- a 1750 mm ostrich standing

An ostrich inverts every bird ratio: a 1.4 m barrel of a body on legs almost as long again, a bare neck that is over a third of total height, a tiny head with a short flat bill, and wings so reduced they are plumes on the flank. The two-toed foot and the plume tail finish it -- nothing about this shape could be mistaken for an emu or a rhea.

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
    stand_height            = 1747,
    body_length             = 610,
    body_width              = 536,
    body_depth              = 576,
    neck_length             = 400,
    head_length             = 58,
    bill_length             = 46,
    leg_length              = 1056,
    foot_length             = 82,
    tail_length             = 90)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-200, 110, 120, 1300),
    (-70, 230, 250, 1290),
    (90, 268, 288, 1290),
    (240, 200, 208, 1298),
    (350, 110, 112, 1310),
    (410, 50, 52, 1316),
]
NECK_PATH = [
    (0, -180, 1310), (0, -215, 1425), (0, -228, 1540), (0, -216, 1645),
    (0, -205, 1705)]
NECK_RAD = [
 (96, 98),
 (70, 72),
 (54, 55),
 (42, 43),
 (34, 34)
]
HEAD_PATH = [
    (0, -202, 1707), (0, -232, 1711), (0, -260, 1703)]
HEAD_RAD = [
 (36, 36),
 (32, 32),
 (18, 18)
]
BEAK_PATH = [
    (0, -254, 1703), (0, -284, 1695), (0, -300, 1689)]
BEAK_RAD = [
 (18, 16),
 (13, 10),
 (5, 4)
]
LEG_PATH = [
    (130, 60, 1080), (130, 30, 830), (130, 10, 545), (130, 0, 270),
    (130, -14, 95), (130, -24, 24)]
LEG_RAD = [
 (48, 48),
 (38, 38),
 (30, 30),
 (26, 26),
 (24, 24),
 (24, 24)
]
FOOT_PATH = [
    (130, -24, 24), (130, -70, 12), (130, -104, 6)]
FOOT_RAD = [
 (24, 20),
 (34, 8),
 (20, 4)
]
WING_PATH = [
    (246, -60, 1330), (270, 40, 1326), (254, 150, 1336)]
WING_RAD = [
 (58, 42),
 (54, 38),
 (26, 18)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 390, 1310), (0, 440, 1326), (0, 480, 1338)]
TAIL_RAD = [
 (90, 60),
 (70, 44),
 (34, 22)
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
        "body": bkit.pbr("OstrichBody", base=(0.115, 0.105, 0.098), rough=0.7),
        "head": bkit.pbr("OstrichHead", base=(0.135, 0.122, 0.112), rough=0.66),
        "beak": bkit.pbr("OstrichBill", base=(0.33, 0.235, 0.15), rough=0.42),
        "wing": bkit.pbr("OstrichPlume", base=(0.165, 0.152, 0.142), rough=0.76),
        "leg": bkit.pbr("OstrichLeg", base=(0.4, 0.31, 0.245), rough=0.48),
        "eye": bkit.pbr("EyeDark", base=(0.02, 0.016, 0.014), rough=0.16),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 10.0, segments=20, rings=10,
                       centre=(sx * 24, -244, 1725), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.6, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)
    # ---- tail fan: 5 copies of one tapered plate, each turned a
    # further equal step about the tail base
    for i, fp in enumerate(_fan_paths(TAIL_PATH, 5, 14, (0, 390, 1310), "Y")):
        _tube("Tail%d" % (i + 1), fp, TAIL_RAD, M["wing"], n=2.4, steps=S)


    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="stand_height", mm=1747, tol=30, how="bbox_z", part=None),
    dict(name="body_length", mm=610, tol=26, how="bbox_y", part='Body'),
    dict(name="body_width", mm=536, tol=24, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=576, tol=24, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=46, tol=10, how="bbox_y", part='Beak'),
    dict(name="leg_length", mm=1056, tol=30, how="bbox_z", part='LegL')]
