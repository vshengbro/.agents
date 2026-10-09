"""
mobius_strip -- a 33 mm-radius band, 30 mm wide, 4 mm thick, with one half twist.

WHY THIS IS NOT A SOLIDIFY
--------------------------
The obvious construction -- generate the twisted sheet, weld the seam,
Solidify it -- cannot work here, and fails in a way that looks fine in the
numbers. A Moebius band is NON-ORIENTABLE: there is no consistent choice of
outward normal over the whole surface. Solidify offsets along those normals, so
half the band thickens outward and half inward. The result is a self-
intersecting shell whose signed volume comes out NEGATIVE even though
non-manifold edges are zero, and `recalc_face_normals` cannot repair it because
it also needs a globally consistent orientation.

So the SOLID is built directly. Its boundary is parametrised twice over:
`u` runs once around the band, and `s` runs once around the perimeter of the
cross-section rectangle (v, t). Under the Moebius identification
(u, v, t) -> (u + 2pi, -v, -t), and (v, t) -> (-v, -t) is exactly half a lap
around that rectangle -- which is why the closing band runs from column j to
column j + M/2 instead of to column j+1. The result is one closed,
orientable, watertight shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    centre_radius=33.0,   # radius of the band centreline
    band_width=30.0,      # 2 x half_width
    thickness=4.0,
    half_twist=1,         # one half twist: the Moebius condition
    width=83.80,
    depth=30.25,
    height=90.32,
)

R = SPEC["centre_radius"]
HALF_W = SPEC["band_width"] / 2.0
T = SPEC["thickness"]

CHECKS = [
    dict(name="width", mm=83.80, tol=0.4, how="bbox_x", part="MobiusStrip"),
    dict(name="depth", mm=30.25, tol=0.4, how="bbox_y", part="MobiusStrip"),
    dict(name="height", mm=90.32, tol=0.4, how="bbox_z", part="MobiusStrip"),
]


def _mid(u, v):
    """Point on the Moebius mid-surface, standing upright in the XZ plane."""
    ch, sh = math.cos(u / 2.0), math.sin(u / 2.0)
    rad = R + v * ch
    return (rad * math.cos(u), v * sh, rad * math.sin(u))


def _normal(u, v):
    """Unit surface normal of the mid-surface, by central differences."""
    e = 1e-4
    du = tuple(_mid(u + e, v)[i] - _mid(u - e, v)[i] for i in range(3))
    dv = tuple(_mid(u, v + e)[i] - _mid(u, v - e)[i] for i in range(3))
    n = (du[1] * dv[2] - du[2] * dv[1],
         du[2] * dv[0] - du[0] * dv[2],
         du[0] * dv[1] - du[1] * dv[0])
    L = math.sqrt(sum(c * c for c in n)) or 1.0
    return (n[0] / L, n[1] / L, n[2] / L)


def _section_point(s):
    """Walk the perimeter of the (v, t) cross-section rectangle.

    Returns (v, t) at perimeter parameter s in [0, 1).
    """
    a = 2.0 * HALF_W          # top edge length
    b = T                      # side edge length
    total = 2.0 * (a + b)
    q = (s % 1.0) * total
    if q < a:                                  # along the top, -w -> +w
        return -HALF_W + q, T / 2.0
    q -= a
    if q < b:                                  # down the +w end
        return HALF_W, T / 2.0 - q
    q -= b
    if q < a:                                  # back along the bottom
        return HALF_W - q, -T / 2.0
    q -= a
    return -HALF_W, -T / 2.0 + q                # up the -w end


def build():
    steps = 288          # samples around the band (u)
    across = 64          # samples around the cross-section (s), must be even
    verts, faces = [], []

    for i in range(steps):
        u = 2.0 * math.pi * i / steps
        for j in range(across):
            v, t = _section_point(float(j) / across)
            p = _mid(u, v)
            n = _normal(u, v)
            verts.append((p[0] + t * n[0], p[1] + t * n[1], p[2] + t * n[2]))

    half = across // 2
    for i in range(steps):
        i2 = (i + 1) % steps
        for j in range(across):
            j2 = (j + 1) % across
            # The closing band (i2 -> 0) is the one place the half-twist shows
            # up as index arithmetic: column j meets column j + across/2.
            jj = (j + half) % across if i2 == 0 else j
            jj2 = (j2 + half) % across if i2 == 0 else j2
            faces.append((i * across + j, i * across + j2,
                          i2 * across + jj2, i2 * across + jj))

    mat = bkit.pbr("MoebiusBand", base=(0.82, 0.32, 0.30), metal=0.15, rough=0.28)
    band = bkit.mesh_from("MobiusStrip", verts, faces, mat=mat)

    # Closed, connected and orientable now, so recalc() really does orient it
    # outward and the signed volume comes back positive.
    bkit.recalc(band)
    bkit.shade_smooth(band, 50)

    return dict(spec=SPEC, parts=1)