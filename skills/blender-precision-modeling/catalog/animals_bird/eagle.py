"""
eagle -- a 880 mm bald eagle perched, wings folded

Proportions are eagle, not generic bird: a heavy deep body on short powerful tarsi, a small head for the body mass, and above all a short thick bill whose tip folds back into a deep hook. The folded wing is long -- it runs from the shoulder to a primary fan level with the tail -- and that wing-to-body ratio is the raptor silhouette.

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
    total_length            = 880,
    body_length             = 460,
    body_width              = 256,
    body_depth              = 264,
    head_length             = 86,
    bill_length             = 88,
    leg_length              = 140,
    wing_length             = 495,
    tail_length             = 215,
    stand_height            = 412)

# --- construction tables, millimetres ---------------------------------------
# body rows are (y, half_width, half_depth, z_centre): width and depth are
# properties of the table, so body shape is never asserted after the fact
BODY = [
    (-230, 40, 45, 300),
    (-160, 85, 95, 290),
    (-70, 118, 122, 282),
    (20, 128, 132, 280),
    (110, 112, 112, 286),
    (185, 72, 68, 296),
    (230, 34, 34, 300),
]
NECK_PATH = [
    (0, -215, 300), (0, -260, 318), (0, -300, 338)]
NECK_RAD = [
 (96, 100),
 (80, 84),
 (64, 66)
]
HEAD_PATH = [
    (0, -292, 338), (0, -338, 346), (0, -378, 344)]
HEAD_RAD = [
 (62, 62),
 (58, 56),
 (38, 36)
]
BEAK_PATH = [
    (0, -368, 344), (0, -410, 342), (0, -444, 330), (0, -456, 312)]
BEAK_RAD = [
 (40, 38),
 (32, 30),
 (18, 18),
 (7, 7)
]
LEG_PATH = [
    (62, 10, 180), (62, 4, 120), (62, -2, 70), (62, -4, 44)]
LEG_RAD = [
 (26, 26),
 (22, 22),
 (19, 20),
 (20, 20)
]
FOOT_PATH = [
    (62, -4, 44), (62, -32, 18), (62, -52, 5)]
FOOT_RAD = [
 (20, 15),
 (26, 9),
 (14, 5)
]
WING_PATH = [
    (88, -165, 336), (132, -60, 322), (138, 60, 308), (126, 190, 294),
    (92, 330, 286)]
WING_RAD = [
 (56, 42),
 (86, 32),
 (92, 26),
 (70, 18),
 (26, 10)
]
PRIM_PATH = [
    (128, 240, 294), (116, 320, 286), (100, 384, 278)]
PRIM_RAD = [
 (22, 17),
 (13, 10),
 (5, 5)
]
TAIL_PATH = [
    (0, 205, 300), (0, 300, 296), (0, 420, 286)]
TAIL_RAD = [
 (70, 50),
 (58, 38),
 (30, 18)
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
        "body": bkit.pbr("EagleBody", base=(0.115, 0.085, 0.062), rough=0.62),
        "head": bkit.pbr("EagleHead", base=(0.215, 0.13, 0.055), rough=0.58),
        "beak": bkit.pbr("EagleBill", base=(0.56, 0.4, 0.055), rough=0.34),
        "wing": bkit.pbr("EagleWing", base=(0.085, 0.068, 0.055), rough=0.6),
        "leg": bkit.pbr("EagleTarsus", base=(0.48, 0.29, 0.07), rough=0.46),
        "eye": bkit.pbr("EyeAmber", base=(0.4, 0.26, 0.055), rough=0.18),
    }
    S = 32

    _tube("Body", [(0.0, y, z) for (y, _w, _h, z) in BODY],
          [(w, h) for (_y, w, h, _z) in BODY], M["body"], n=2.6, steps=S)

    if NECK_PATH:
        _tube("Neck", NECK_PATH, NECK_RAD, M["head"], n=2.6, steps=S)
    _tube("Head", HEAD_PATH, HEAD_RAD, M["head"], n=2.6, steps=S)
    _tube("Beak", BEAK_PATH, BEAK_RAD, M["beak"], n=2.6, steps=S)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 10.0, segments=20, rings=10,
                       centre=(sx * 48, -340, 356), mat=M["eye"])
        _tube("Leg%s" % side, [(sx * x, y, z) for (x, y, z) in LEG_PATH],
              LEG_RAD, M["leg"], n=2.2, steps=S)
        _tube("Foot%s" % side, [(sx * x, y, z) for (x, y, z) in FOOT_PATH],
              FOOT_RAD, M["leg"], n=2.4, steps=S)
        _tube("Wing%s" % side, [(sx * x, y, z) for (x, y, z) in WING_PATH],
              WING_RAD, M["wing"], n=2.8, steps=S)
        # ---- primary feathers: 5 evenly spaced copies of one plate, rotated about
        # the wing tip, then mirrored -- a fan computed, not placed
        for i, fp in enumerate(_fan_paths(PRIM_PATH, 5, 8, (126, 230, 290), "X")):
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
    dict(name="body_length", mm=460, tol=14, how="bbox_y", part='Body'),
    dict(name="body_width", mm=256, tol=10, how="bbox_x", part='Body'),
    dict(name="body_depth", mm=264, tol=10, how="bbox_z", part='Body'),
    dict(name="bill_length", mm=88, tol=10, how="bbox_y", part='Beak'),
    dict(name="leg_length", mm=140, tol=10, how="bbox_z", part='LegL'),
    dict(name="tail_length", mm=215, tol=14, how="bbox_y", part='Tail'),
    dict(name="total_length", mm=880, tol=20, how="bbox_y", part=None)]
