"""
owl -- a 550 mm eagle owl standing, ear tufts up

An owl is not a bird with a head on it: the head is a third of the body, the neck is invisible, and both eyes face forward. That is the whole silhouette, so the head is built as one huge near-spherical mass merged into the upright body, the eyes sit forward of the facial disc rather than on the sides, and the bill is short and stubby beneath them. Ear tufts and a faceted facial disc finish it.

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
    stand_height            = 540,
    body_height             = 354,
    head_diameter           = 276,
    beak_length             = 46,
    eye_diameter            = 52,
    tail_length             = 115,
    leg_length              = 62,
    ear_tuft_height         = 50)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (62, 58, 60, 62),
    (66, 102, 108, 123.2),
    (54, 126, 130, 206.6),
    (28, 122, 124, 290.1),
    (2, 88, 90, 355.0),
    (-14, 56, 57, 390.3),
]
NECK_PATH = None
NECK_RAD = None
HEAD_PATH = [
    (0, -4, 378), (0, -26, 432), (0, -34, 482), (0, -32, 508)]
HEAD_RAD = [
 (126, 124),
 (138, 134),
 (122, 118),
 (68, 66)
]
BEAK_PATH = [
    (0, -140, 440), (0, -172, 438), (0, -186, 432)]
BEAK_RAD = [
 (22, 20),
 (14, 13),
 (5, 5)
]
LEG_PATH = [
    (52, 20, 80), (52, 12, 45), (52, 8, 18)]
LEG_RAD = [
 (22, 24),
 (20, 22),
 (22, 22)
]
FOOT_PATH = [
    (52, 8, 18), (52, -18, 9), (52, -34, 4)]
FOOT_RAD = [
 (20, 15),
 (28, 7),
 (16, 4)
]
WING_PATH = [
    (112, -24, 340), (130, 10, 262), (126, 58, 186), (108, 102, 132)]
WING_RAD = [
 (40, 26),
 (46, 28),
 (36, 22),
 (16, 10)
]
PRIM_PATH = None
PRIM_RAD = None
TAIL_PATH = [
    (0, 50, 90), (0, 102.2, 72), (0, 150, 58)]
TAIL_RAD = [
 (60, 40),
 (48, 30),
 (22, 14)
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
        "body": bkit.pbr("OwlBody", base=(0.235, 0.16, 0.1), rough=0.76),
        "head": bkit.pbr("OwlHead", base=(0.29, 0.205, 0.135), rough=0.78),
        "beak": bkit.pbr("OwlBill", base=(0.48, 0.36, 0.11), rough=0.38),
        "wing": bkit.pbr("OwlWing", base=(0.185, 0.125, 0.08), rough=0.78),
        "leg": bkit.pbr("OwlFoot", base=(0.33, 0.225, 0.12), rough=0.5),
        "eye": bkit.pbr("OwlEye", base=(0.62, 0.33, 0.035), rough=0.16),
        "pupil": bkit.pbr("OwlPupil", base=(0.015, 0.012, 0.01), rough=0.14),
        "pale": bkit.pbr("OwlDisc", base=(0.43, 0.32, 0.205), rough=0.8),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=3.0, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 26.0, segments=20, rings=10,
                       centre=(sx * 46, -140, 468), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.6, steps=S)

    if TAIL_PATH:
        _tube("Tail", TAIL_PATH, TAIL_RAD, M["wing"], n=2.6, steps=S)

    # ---- forward-facing eyes: an owl's eyes look out of the front of the
    # facial disc, so the pupil sits on the eye's own axis pushed forward,
    # concentric with it -- offset pupils read as two separate beads
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Pupil%s" % side, 14.0, segments=20, rings=10,
                       centre=(sx * 46.0, -158.0, 468.0), mat=M["pupil"])

    # ---- ear tufts: two cones off the crown
    for side, sx in (("L", 1.0), ("R", -1.0)):
        _tube("EarTuft%s" % side,
              [(sx * 62.0, -4.0, 486.0), (sx * 74.0, -10.0, 536.0)],
              [(24, 24), (3, 3)], M["head"], n=2.4, steps=S)

    # ---- pale facial disc: a shallow dome lying ON the front of the head, not a
    # tube standing proud of it
    _tube("FacialDisc", [(0.0, -108.0, 450.0), (0.0, -142.0, 452.0),
                         (0.0, -152.0, 452.0)],
          [(118, 112), (96, 92), (58, 56)], M["pale"], n=2.8, steps=S)

    # every part above is its own closed solid: nothing was booleaned
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_height", mm=354, tol=20, how="bbox_z", part='Body'),
    dict(name="head_diameter", mm=276, tol=16, how="diameter", part='Head'),
    dict(name="beak_length", mm=46, tol=8, how="bbox_y", part='Beak'),
    dict(name="eye_diameter", mm=52, tol=4, how="diameter", part='EyeL'),
    dict(name="tail_length", mm=115, tol=14, how="bbox_y", part='Tail'),
    dict(name="stand_height", mm=540, tol=24, how="bbox_z", part=None)]
