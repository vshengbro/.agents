"""
football -- size 5 American football: pointed at both ends, a real panel seam
that wraps over both tips, and a laced panel.

The silhouette is a surface of revolution whose radius table is NOT a circle:
a gridiron ball is widest at the waist and drawn out into two points. A plain
uv_sphere reads as a beach ball, so the radius comes from a measured taper
table and the tip radius is a real spherical cap, which is what lets the seam
wrap over the nose instead of collapsing to a point.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# Size 5: 220 mm long, 162 mm across the waist, 112 mm tall.
SPEC = dict(
    length=220.0,
    width=162.0,
    height=112.0,
    body_half_length=101.0,   # + 9 mm spherical caps = 220
    tip_radius=9.0,
    seam_groove=1.3,
    cross_laces=8,
    lace_pitch=10.7,
)

HW = SPEC["width"] / 2.0        # 81  half width  (y)
HH = SPEC["height"] / 2.0       # 56  half height (z)
XT = SPEC["body_half_length"]   # 101
TR = SPEC["tip_radius"]         # 9

# Measured taper, waist -> tip, as a fraction of the waist half-extent.
TAPER_Y = [(0.00, 1.000), (0.25, 0.990), (0.50, 0.930),
           (0.72, 0.780), (0.88, 0.480), (1.00, TR / HW)]
TAPER_Z = [(0.00, 1.000), (0.25, 0.975), (0.50, 0.900),
           (0.72, 0.710), (0.88, 0.410), (1.00, TR / HH)]


# --------------------------------------------------------------------------
# plain-tuple vector helpers (mm) -- kept local so the model file stands alone
# --------------------------------------------------------------------------
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


def _tube(name, path, r, seg=10, closed=False, mat=None):
    """Sweep a circle of radius r (mm) along a 3D polyline (mm).

    Parallel transport keeps the ring from spinning; for a planar path the
    holonomy is zero, so a closed loop comes back on itself exactly.
    """
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


def _interp(table, u):
    # smoothstep, not linear: a linear blend between two taper rows leaves a
    # slope discontinuity at every row, and shade_smooth turns each of those
    # into a visible band running around the ball
    for i in range(len(table) - 1):
        u0, f0 = table[i]
        u1, f1 = table[i + 1]
        if u <= u1 or i == len(table) - 2:
            t = 0.0 if u1 == u0 else (u - u0) / (u1 - u0)
            t = min(1.0, max(0.0, t))
            t = t * t * (3.0 - 2.0 * t)
            return f0 + (f1 - f0) * t
    return table[-1][1]


def _halfs(x):
    """(half width, half height, superellipse exponent) at station x."""
    ax = abs(x)
    if ax <= XT:
        u = ax / XT
        return (HW * _interp(TAPER_Y, u), HH * _interp(TAPER_Z, u),
                2.3 - 0.3 * (ax / XT))
    d = ax - XT
    r = math.sqrt(max(0.0, TR * TR - d * d))
    return (r, r, 2.0)


def _top_z(x, y=0.0):
    """Height of the surface at (x, y) -- where the laces sit."""
    hy, hz, n = _halfs(x)
    if hy <= 0.0:
        return 0.0
    t = min(0.999, abs(y) / hy)
    return hz * (1.0 - t ** n) ** (1.0 / n)


CHECKS = [
    dict(name="length", mm=220.0, tol=0.5, how="bbox_x", part="Football"),
    dict(name="width", mm=162.0, tol=0.6, how="bbox_y", part="Football"),
    dict(name="height", mm=112.0, tol=0.6, how="bbox_z", part="Football"),
]


def build():
    leather = bkit.pbr("BallLeather", base=(0.86, 0.84, 0.80), rough=0.44)
    stripe = bkit.pbr("BallStripe", base=(0.16, 0.20, 0.38), rough=0.46)
    seam_mat = bkit.pbr("SeamHide", base=(0.55, 0.53, 0.50), rough=0.52)
    lace_mat = bkit.pbr("LaceWhite", base=(0.92, 0.90, 0.86), rough=0.58)

    # ---- stations: spherical cap, body, spherical cap (ascending x) --------
    # 65 body stations, not 13: shade_smooth averages the normals, so a coarse
    # loft shows its own rings as terracing across a ball this smooth.
    xs = []
    for i in range(8, 0, -1):
        th = math.radians(88.0) * i / 8
        xs.append(-XT - TR * math.sin(th))
    for i in range(65):
        xs.append(-XT + 2.0 * XT * i / 64.0)
    for i in range(1, 9):
        th = math.radians(88.0) * i / 8
        xs.append(XT + TR * math.sin(th))

    sections = []
    for x in xs:
        hy, hz, n = _halfs(x)
        ring = bkit.superellipse_section(2.0 * hy, 2.0 * hz, n=n, steps=48)
        sections.append([(x, u, w) for (u, w) in ring])
    body = bkit.loft("Football", sections, mat=leather, smooth=True)
    bkit.recalc(body)
    # two-tone panels: the single seam loop in the XZ plane splits the ball
    # into its two side panels, exactly as the stripe on a real one does
    bkit.assign_faces_by(body, stripe, lambda c, n: c.y / bkit.MM > 0.0)

    # ---- one seam loop, in the vertical plane: over the nose, along the
    # ---- bottom, round the tail, and back. Offset outward so the 1.3 mm
    # ---- cord stands 2.2 mm proud and 0.4 mm buried.
    off = 0.9
    path = []
    steps = 56
    for i in range(steps + 1):                       # top run, -x -> +x
        x = -XT + 2.0 * XT * i / steps
        path.append((x, 0.0, _top_z(x) + off))
    rt = TR + off
    for i in range(1, 25):                            # over the nose
        t = math.pi / 2.0 - math.pi * i / 24.0
        path.append((XT + rt * math.cos(t), 0.0, rt * math.sin(t)))
    for i in range(1, steps + 1):                     # bottom run, +x -> -x
        x = XT - 2.0 * XT * i / steps
        path.append((x, 0.0, -(_top_z(x) + off)))
    for i in range(1, 24):                            # round the tail
        t = -math.pi / 2.0 + math.pi * i / 24.0
        path.append((-XT + rt * math.cos(t), 0.0, rt * math.sin(t)))
    seam = _tube("PanelSeam", path, SPEC["seam_groove"], seg=10, closed=True,
                 mat=seam_mat)

    # ---- laces: one long lace along the seam, 8 cross laces over it -------
    long_path = []
    for i in range(25):
        x = 16.0 + 64.0 * i / 24.0
        long_path.append((x, 0.0, _top_z(x) + 0.5))
    long_lace = _tube("LaceLong", long_path, 1.0, seg=8, mat=lace_mat)

    cross = []
    for (x, _y) in bkit.grid_positions(cols=SPEC["cross_laces"], rows=1,
                                      pitch_x=SPEC["lace_pitch"], pitch_y=1.0):
        cross.append(bkit.rounded_box(
            "LaceCross", 2.6, 23.0, 2.4, r=0.9, segments=2,
            centre=(x, 0.0, _top_z(x) + 0.35), mat=lace_mat))
    laces = bkit.join([long_lace] + cross, name="Laces")

    return dict(spec=SPEC, parts=3)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
