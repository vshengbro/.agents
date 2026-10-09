"""
rock -- a hand-sized weathered rock: a faceted lump, never a smooth ball.

Recipe note: a subdivided sphere with smooth shading reads as a ball, so this
model perturbs an explicit low-segment lattice and builds it with
`mesh_from(..., smooth=False)`. Every quad then stays planar-ish and the flat
facets are what make it read as broken stone. The perturbation is a fixed-seed
`random.Random`, so the rock is byte-identical on every run.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=196.0,          # longest axis of the specimen
    width=142.0,
    height=118.0,
)

SEGS = 9                    # facets around
RINGS = 6                   # facets top to bottom
SQUASH = 0.62               # rocks are wider than they are tall


def _lattice(seed, jitter, radius):
    """Watertight perturbed sphere: pole, interior rings, pole; fans + quads."""
    rnd = random.Random(seed)
    pts = [(0.0, 0.0, radius)]
    for j in range(1, RINGS):
        phi = math.pi * j / RINGS
        for i in range(SEGS):
            a = 2.0 * math.pi * i / SEGS
            r = radius * (1.0 + rnd.uniform(-jitter, jitter))
            pts.append((r * math.sin(phi) * math.cos(a),
                        r * math.sin(phi) * math.sin(a),
                        r * math.cos(phi)))
    bottom = len(pts)
    pts.append((0.0, 0.0, -radius))
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

    Jitter is asymmetric, so multiplying by half the target size overshoots --
    the measured bbox came out 5% long on the first pass. Measuring the
    lattice's own extents and dividing by them is what makes the declared
    envelope and the rendered envelope the same number.
    """
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    fx = size[0] / max(1e-6, max(xs) - min(xs))
    fy = size[1] / max(1e-6, max(ys) - min(ys))
    fz = size[2] / max(1e-6, max(zs) - min(zs))
    cx = (max(xs) + min(xs)) / 2.0
    cy = (max(ys) + min(ys)) / 2.0
    cz = (max(zs) + min(zs)) / 2.0
    return [((p[0] - cx) * fx, (p[1] - cy) * fy, (p[2] - cz) * fz) for p in pts]


def build():
    granite = bkit.pbr("RockGranite", base=(0.40, 0.385, 0.365), rough=0.86)
    lichen = bkit.pbr("RockLichen", base=(0.30, 0.38, 0.24), rough=0.92)

    # Radius is scaled per-axis afterwards, so the declared envelope is hit
    # exactly: SPEC / 2 on each axis, jitter scaled with it.
    pts, faces = _lattice(7, 0.20, 1.0)
    verts = _fit(pts, (SPEC["length"], SPEC["width"], SPEC["height"]))
    rock = bkit.mesh_from("Rock", verts, faces, mat=granite, smooth=False)
    bkit.recalc(rock)

    # A second lump fused to the base reads as a broken-off corner and stops
    # the silhouette being a bare ellipsoid. Overlapping solids, not a boolean:
    # each shell stays independently watertight.
    cpts, cfaces = _lattice(11, 0.24, 1.0)
    cverts = _fit(cpts, (108.0, 84.0, 64.0))
    cverts = [(x + 44.0, y - 14.0, z - 22.0) for (x, y, z) in cverts]
    chip = bkit.mesh_from("RockChip", cverts, cfaces, mat=granite, smooth=False)
    bkit.recalc(chip)

    bkit.assign_faces_by(rock, lichen, lambda c, n: n.z > 0.45)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="length", mm=196.0, tol=1.2, how="bbox_x", part="Rock"),
    dict(name="width", mm=142.0, tol=1.2, how="bbox_y", part="Rock"),
    dict(name="height", mm=118.0, tol=1.2, how="bbox_z", part="Rock"),
]