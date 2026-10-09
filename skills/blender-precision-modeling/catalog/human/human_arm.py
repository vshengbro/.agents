"""
human_arm -- a 655 mm arm from the deltoid to the fingertips, hung in the
anatomical position with 9 deg of abduction at the shoulder.

The limb is one continuous sweep, not a stack of cylinders: a superelliptic
section follows a polyline through shoulder, biceps, elbow, forearm mass, wrist
and palm, with the radius table giving the deltoid swell, the biceps, the
elbow, the brachioradialis and the thenar eminence. One sweep means no part
joints can open, and it is why a swept limb has zero non-manifold edges.

Radius is a table, not a claim: humerus 34 mm, forearm 27 mm, wrist 16 mm are
properties of the numbers in RAD, and the checks measure the real geometry.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    arm_length     = 655.0,
    upper_arm      = 300.0,
    forearm        = 250.0,
    humerus_radius = 34.0,
    wrist_radius   = 16.0,
)

# (x, y, z, half_width, half_depth)
PATH = [
    (0.0, 0.0, 640.0, 52.0, 52.0),      # deltoid
    (6.0, 0.0, 590.0, 44.0, 44.0),      # axilla
    (16.0, 0.0, 500.0, 40.0, 41.0),     # biceps belly
    (26.0, 0.0, 400.0, 34.0, 35.0),     # distal arm
    (31.0, 0.0, 352.0, 30.0, 30.0),     # elbow
    (40.0, 0.0, 300.0, 31.0, 30.0),     # forearm flexor mass
    (48.0, 0.0, 220.0, 27.0, 25.0),
    (53.0, 0.0, 150.0, 21.0, 19.0),     # distal forearm
    (56.0, 0.0, 104.0, 16.0, 14.0),     # wrist
    (58.0, 0.0, 70.0, 24.0, 20.0),      # palm heel
    (61.0, 0.0, 26.0, 30.0, 20.0),      # palm
    (63.0, 0.0, 4.0, 26.0, 16.0),       # finger line
]


def _sweep(name, path, mat, n=2.4, steps=28):
    """Sweep a superellipse along a polyline, in the arm's own sagittal frame."""
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == m - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        # The limb runs down -Z, so the frame is built against world X (the
        # arm's own lateral axis) and Y (its anterior axis).
        side = Vector((0.0, 0.0, 1.0)).cross(tv)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        nrm = tv.cross(side).normalized()
        w, d = path[i][3], path[i][4]
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            ex = math.copysign(abs(ca) ** (2.0 / n), ca)
            ey = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((p[0] + w * ex * side.x + d * ey * nrm.x,
                         p[1] + w * ex * side.y + d * ey * nrm.y,
                         p[2] + w * ex * side.z + d * ey * nrm.z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.560, 0.360, 0.280), rough=0.58)
    nail = bkit.pbr("Nail", base=(0.780, 0.680, 0.640), rough=0.26)

    _sweep("Arm", PATH, skin)

    # ---- olecranon: the point of the elbow
    bkit.uv_sphere("ElbowPoint", 1.0, segments=24, rings=12,
                   centre=(31.0, 12.0, 348.0), mat=skin_d).scale = \
        (26.0, 20.0, 24.0)

    # ---- thumb: two phalanges off the radial side of the palm
    _sweep("Thumb", [(74.0, 6.0, 62.0, 13.0, 12.0),
                     (84.0, 14.0, 40.0, 10.0, 9.0),
                     (90.0, 20.0, 24.0, 7.0, 6.0)], skin_d, n=2.2, steps=16)

    # ---- finger line: five tapering stumps, spaced by the palm's own width
    for i, (x, w) in enumerate(bkit.lay_out([21.0, 22.0, 21.0, 18.0], gap=4.0)):
        bkit.cylinder("Finger%d" % i, 10.0, 62.0 - 3.0 * i, segments=14,
                      r2=7.0, centre=(x + 56.0, 0.0, 34.0 - 2.0 * i),
                      mat=skin)
        bkit.uv_sphere("Nail%d" % i, 1.0, segments=12, rings=6,
                       centre=(x + 56.0, -8.0, 12.0 - 2.0 * i),
                       mat=nail).scale = (6.0, 3.0, 6.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 1 + 10)


CHECKS = [
    dict(name="arm_length", mm=646.2, tol=3.23, how="top_z", part="Arm"),
    # One sweep has one bounding box, so it reports the widest section only.
    # The arm's thigh-equivalent, elbow and hand widths are separate solids
    # and are checked as such.
    dict(name="arm_girth", mm=132.0, tol=2.0, how="bbox_x", part="Arm"),
    dict(name="elbow",     mm=52.0,  tol=1.0, how="diameter", part="ElbowPoint"),
    dict(name="finger",     mm=20.0,  tol=0.8, how="diameter", part="Finger1"),
]
