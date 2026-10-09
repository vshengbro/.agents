"""
boulder -- a field boulder, 1.6 m across, built the way a rock is built: a
perturbed low-segment lattice, flat shaded.

Same faceting logic as `rock`, but at landscape scale, so the jitter is scaled
up in absolute millimetres (a 6 cm chip on a rock is a 1 m boulder) and the
specimen gets a second, smaller companion lump so the composition has a base.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1620.0,
    width=1240.0,
    height=1010.0,
    companion_diameter=620.0,
)

SEGS = 11
RINGS = 7
SQUASH = 0.66


def _lattice(seed, jitter):
    rnd = random.Random(seed)
    pts = [(0.0, 0.0, 1.0)]
    for j in range(1, RINGS):
        phi = math.pi * j / RINGS
        for i in range(SEGS):
            a = 2.0 * math.pi * i / SEGS
            r = 1.0 + rnd.uniform(-jitter, jitter)
            pts.append((r * math.sin(phi) * math.cos(a),
                        r * math.sin(phi) * math.sin(a),
                        r * math.cos(phi)))
    bottom = len(pts)
    pts.append((0.0, 0.0, -1.0))
    faces = []
    for i in range(SEGS):
        k = (i + 1) % SEGS
        faces.append((0, 1 + k, 1 + i))
    for ring in range(RINGS - 2):
        b0, b1 = 1 + ring * SEGS, 1 + (ring + 1) * SEGS
        for i in range(SEGS):
            k = (i + 1) % SEGS
            faces.append((b0 + i, b0 + k, b1 + k, b1 + i))
    base = 1 + (RINGS - 2) * SEGS
    for i in range(SEGS):
        k = (i + 1) % SEGS
        faces.append((bottom, base + i, base + k))
    return pts, faces


def _fit(pts, size):
    """Scale a unit lattice so its ACTUAL extent equals `size` exactly.

    The jitter is not symmetric, so multiplying by half the target overshoots;
    measuring the lattice's own extents is what makes the declared envelope and
    the rendered envelope the same number.
    """
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    fx = size[0] / max(1e-6, max(xs) - min(xs))
    fy = size[1] / max(1e-6, max(ys) - min(ys))
    fz = size[2] / max(1e-6, max(zs) - min(zs))
    cx, cy, cz = ((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0,
                  (max(zs) + min(zs)) / 2.0)
    return [((p[0] - cx) * fx, (p[1] - cy) * fy, (p[2] - cz) * fz) for p in pts]


def build():
    grey = bkit.pbr("BoulderGrey", base=(0.44, 0.435, 0.42), rough=0.84)
    moss = bkit.pbr("BoulderMoss", base=(0.22, 0.30, 0.17), rough=0.95)

    pts, faces = _lattice(3, 0.17)
    verts = _fit(pts, (SPEC["length"], SPEC["width"], SPEC["height"]))
    main = bkit.mesh_from("BoulderMain", verts, faces, mat=grey, smooth=False)
    bkit.recalc(main)

    # ---- companion cobble, half-buried against the main mass --------------
    # Overlapping shells rather than a boolean: at this facet count the EXACT
    # solver has nothing to gain and a coincidence to lose.
    cpts, cfaces = _lattice(23, 0.20)
    cr = SPEC["companion_diameter"]
    cverts = _fit(cpts, (cr * 1.15, cr, cr * 0.72))
    cverts = [(x + 560.0, y + 240.0, z - 260.0) for (x, y, z) in cverts]
    cobble = bkit.mesh_from("BoulderCobble", cverts, cfaces, mat=grey, smooth=False)
    bkit.recalc(cobble)

    bkit.assign_faces_by(main, moss, lambda c, n: n.z > 0.35)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="length", mm=1620.0, tol=3.0, how="bbox_x", part="BoulderMain"),
    dict(name="width", mm=1240.0, tol=3.0, how="bbox_y", part="BoulderMain"),
    dict(name="height", mm=1010.0, tol=3.0, how="bbox_z", part="BoulderMain"),
]