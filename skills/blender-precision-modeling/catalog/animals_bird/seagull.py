"""
seagull -- a 690 mm herring gull standing, wings folded

Gull proportions: a long neck carried forward at a slight S, a long straight bill with a small hook at the tip, and above all a wing that is far longer than the body -- the primary fan reaches well past the tail. Webbed feet on medium legs put the body high, which is why a gull reads taller than a duck.

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
    total_length            = 690,
    body_length             = 382,
    body_width              = 188,
    body_depth              = 198,
    neck_length             = 72,
    head_length             = 68,
    bill_length             = 82,
    leg_length              = 128,
    wing_length             = 370,
    tail_length             = 70,
    stand_height            = 338)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-190, 32, 36, 250),
    (-124, 68, 78, 244),
    (-42, 90, 96, 239),
    (42, 94, 99, 239),
    (116, 76, 78, 244),
    (166, 44, 44, 250),
    (192, 21, 21, 253),
]
NECK_PATH = [
    (0, -178, 248), (0, -214, 266), (0, -250, 288)]
NECK_RAD = [
 (56, 62),
 (46, 52),
 (38, 42)
]
HEAD_PATH = [
    (0, -242, 286), (0, -280, 292), (0, -310, 288)]
HEAD_RAD = [
 (38, 40),
 (35, 35),
 (21, 21)
]
BEAK_PATH = [
    (0, -302, 288), (0, -340, 284), (0, -374, 277), (0, -384, 269)]
BEAK_RAD = [
 (21, 19),
 (17, 16),
 (10, 10),
 (4, 4)
]
LEG_PATH = [
    (44, 16, 164), (44, 8, 104), (44, 3, 52), (44, 0, 36)]
LEG_RAD = [
 (12, 13),
 (10, 11),
 (9, 10),
 (10, 10)
]
FOOT_PATH = [
    (44, 0, 36), (44, -30, 17), (44, -50, 4)]
FOOT_RAD = [
 (10, 12),
 (18, 7),
 (11, 4)
]
WING_PATH = [
    (82, -124, 274), (104, -32, 264), (110, 58, 256), (100, 148, 246),
    (78, 246, 238)]
WING_RAD = [
 (48, 36),
 (74, 28),
 (78, 23),
 (58, 16),
 (21, 9)
]
PRIM_PATH = [
    (98, 190, 240), (86, 250, 234), (66, 300, 228)]
PRIM_RAD = [
 (18, 14),
 (11, 9),
 (4, 4)
]
TAIL_PATH = [
    (0, 172, 251), (0, 210, 249), (0, 242, 247)]
TAIL_RAD = [
 (45, 27),
 (37, 21),
 (24, 13)
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
        "body": bkit.pbr("GullBody", base=(0.64, 0.64, 0.625), rough=0.66),
        "head": bkit.pbr("GullHead", base=(0.735, 0.735, 0.72), rough=0.62),
        "beak": bkit.pbr("GullBill", base=(0.64, 0.22, 0.055), rough=0.38),
        "wing": bkit.pbr("GullWing", base=(0.43, 0.445, 0.47), rough=0.66),
        "leg": bkit.pbr("GullLeg", base=(0.54, 0.29, 0.115), rough=0.48),
        "eye": bkit.pbr("EyePale", base=(0.78, 0.7, 0.4), rough=0.2),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 7.0, segments=20, rings=10,
                       centre=(sx * 24, -288, 300), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)
        # ---- primary feathers: 5 evenly spaced copies of one plate, rotated about
        # the wing tip, then mirrored -- a fan computed, not placed
        for i, fp in enumerate(_fan_paths(PRIM_PATH, 5, 8, (100, 180, 238), "X")):
            _tube("PrimaryL%d" % (i + 1), fp, PRIM_RAD, M["wing"], n=2.4, steps=S)
            _tube("PrimaryR%d" % (i + 1), _flip(fp), PRIM_RAD, M["wing"], n=2.4, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)


    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=20)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=382, tol=14, how="bbox_y", part='Body'),
    dict(name="body_width", mm=188, tol=10, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=198, tol=10, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=82, tol=10, how="bbox_y", part='Beak'),
    dict(name="leg_length", mm=128, tol=10, how="bbox_z", part='LegL'),
    dict(name="tail_length", mm=70, tol=10, how="bbox_y", part='Tail'),
    dict(name="total_length", mm=690, tol=20, how="bbox_y", part=None)]
