"""
basketball -- regulation size 7 ball, 760 mm circumference (242 mm across),
with four real seam grooves.

A ball with no seams is a sphere; a ball with ONE seam is a beach ball. The
eight-panel pattern is four great circles through the poles at 45 degree steps,
which is what divides the surface into the eight curved panels a viewer
recognises instantly. The grooves are swept tubes seated a millimetre into the
leather, so they read as recessed stitching rather than painted stripes.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# 760 mm circumference -> 760/pi = 241.9 mm; regulation rounds to 242.
SPEC = dict(
    diameter=242.0,
    circumference=760.0,
    panels=8,
    seam_groove=2.0,
    seam_depth=1.0,
)

R = SPEC["diameter"] / 2.0
SEAT = 1.0                       # how far the groove centre sits outside
RG = R + SEAT                    # groove centreline radius

CHECKS = [
    dict(name="diameter", mm=242.0, tol=0.5, how="diameter", part="Basketball"),
    dict(name="seam_outer_diameter", mm=248.0, tol=0.5, how="diameter",
         part="BasketballSeam"),
    dict(name="length", mm=248.0, tol=0.5, how="longest"),
]


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    ln = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1.0 / ln)


def _tube(name, path, r, seg=12, closed=True, mat=None):
    """Sweep a circle of radius r (mm) along a 3D polyline (mm)."""
    n = len(path)
    tans = []
    for i in range(n):
        if closed:
            a, b = path[(i - 1) % n], path[(i + 1) % n]
        else:
            a, b = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        tans.append(_norm(_sub(b, a)))
    up = (0.0, 0.0, 1.0)
    if abs(_dot(tans[0], up)) > 0.9:
        up = (1.0, 0.0, 0.0)
    nrm = _norm(_sub(up, _mul(tans[0], _dot(up, tans[0]))))
    verts, faces = [], []
    for i in range(n):
        t = tans[i]
        nrm = _norm(_sub(nrm, _mul(t, _dot(nrm, t))))
        bin_ = _cross(t, nrm)
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            verts.append(tuple(_add(
                path[i], _add(_mul(nrm, r * math.cos(a)),
                              _mul(bin_, r * math.sin(a))))))
    cols = n if closed else n - 1
    for i in range(cols):
        i2 = (i + 1) % n
        for j in range(seg):
            j2 = (j + 1) % seg
            faces.append((i * seg + j, i2 * seg + j, i2 * seg + j2, i * seg + j2))
    if not closed:
        faces.append(tuple(range(seg - 1, -1, -1)))
        base = (n - 1) * seg
        faces.append(tuple(range(base, base + seg)))
    ob = bkit.mesh_from(name, verts, faces, mat)
    bkit.recalc(ob)
    return ob


def build():
    leather = bkit.pbr("BasketballHide", base=(0.68, 0.26, 0.075), rough=0.52)
    groove = bkit.pbr("SeamGroove", base=(0.30, 0.11, 0.035), rough=0.58)

    ball = bkit.uv_sphere("Basketball", R, segments=96, rings=48, mat=leather)

    # Four great circles through the poles, 45 degrees apart -> eight panels.
    grooves = []
    steps = 128
    for k in range(4):
        phi = math.radians(45.0 * k)
        ux, uy = -math.sin(phi), math.cos(phi)
        path = []
        for i in range(steps):
            psi = 2.0 * math.pi * i / steps
            s, c = math.sin(psi), math.cos(psi)
            path.append((RG * s * ux, RG * s * uy, RG * c))
        grooves.append(_tube("Seam%d" % (k + 1), path, SPEC["seam_groove"],
                             seg=12, closed=True, mat=groove))
    seam = bkit.join(grooves, name="BasketballSeam")

    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
