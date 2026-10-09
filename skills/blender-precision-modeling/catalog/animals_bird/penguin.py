"""
penguin -- a 585 mm emperor penguin standing upright

A penguin is an upright bird: no visible neck, a small head merging into the shoulders, narrow flipper-like wings instead of flight feathers, a long slender bill, and feet set well back so the body leans forward over them. The wings are the trap -- they must be thin blades edge-on, not broad plates.

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
    stand_height            = 585,
    body_length             = 410,
    body_width              = 250,
    body_depth              = 250,
    head_length             = 84,
    bill_length             = 84,
    flipper_length          = 240,
    foot_length             = 72,
    tail_length             = 105)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (40, 90, 85, 111.9),
    (45, 115, 110, 207.4),
    (30, 125, 120, 331.5),
    (5, 105, 100, 436.6),
    (-10, 72, 68, 503.4),
]
NECK_PATH = None
NECK_RAD = None
HEAD_PATH = [
    (0, -8, 495.4), (0, -14, 543.4), (0, -16, 578.4)]
HEAD_RAD = [
 (72, 70),
 (66, 64),
 (42, 40)
]
BEAK_PATH = [
    (0, -40, 525.4), (0, -84, 517.4), (0, -124, 509.4)]
BEAK_RAD = [
 (22, 20),
 (12, 12),
 (4, 4)
]
LEG_PATH = [
    (58, 10, 112), (58, 0, 60), (58, -8, 14)]
LEG_RAD = [
 (26, 28),
 (24, 26),
 (24, 24)
]
FOOT_PATH = [
    (58, -8, 14), (58, -48, 8), (58, -72, 5)]
FOOT_RAD = [
 (24, 18),
 (34, 9),
 (20, 5)
]
WING_PATH = [
    (112, 0, 433.4), (128, 60, 363.4), (136, 120, 303.4), (130, 170, 268.4)]
WING_RAD = [
 (8, 34),
 (8, 36),
 (6, 28),
 (4, 16)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 95, 111.9), (0, 150, 93.9), (0, 195, 81.9)]
TAIL_RAD = [
 (50, 30),
 (30, 18),
 (10, 6)
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
        "body": bkit.pbr("PenguinBody", base=(0.045, 0.05, 0.062), rough=0.52),
        "head": bkit.pbr("PenguinHead", base=(0.055, 0.06, 0.072), rough=0.5),
        "beak": bkit.pbr("PenguinBill", base=(0.045, 0.042, 0.04), rough=0.3),
        "wing": bkit.pbr("PenguinFlipper", base=(0.035, 0.04, 0.05), rough=0.5),
        "leg": bkit.pbr("PenguinFoot", base=(0.075, 0.072, 0.07), rough=0.44),
        "eye": bkit.pbr("EyeDark", base=(0.015, 0.013, 0.012), rough=0.14),
        "pale": bkit.pbr("PenguinBelly", base=(0.78, 0.79, 0.79), rough=0.58),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 8.0, segments=20, rings=10,
                       centre=(sx * 30, -60, 549.4), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.4, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- pale belly on the one body solid: a second shell shaped like the
    # belly would z-fight with the real surface and double the non-manifold count
    bkit.assign_faces_by(bpy.data.objects["Body"], M["pale"],
                         lambda c, n: c.z / bkit.MM < 255.0)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=10)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="stand_height", mm=585, tol=18, how="bbox_z", part=None),
    dict(name="body_length", mm=410, tol=18, how="bbox_z", part='Body'),
    dict(name="body_width", mm=250, tol=14, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=250, tol=14, how="bbox_y", part='Body'),
    dict(name="bill_length", mm=84, tol=10, how="bbox_y", part='Beak'),
    dict(name="tail_length", mm=100, tol=14, how="bbox_y", part='Tail')]
