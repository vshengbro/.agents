"""
meteorite -- an ordinary chondrite, 180 mm, with a fusion crust.

Real object: a fell NWA 869 ordinary chondrite, 180 mm across, dark grey
fusion crust over chondrules. Two features do the work: the crusted face is
matte and slightly pitted (regmaglypts), and the broken face exposes the
pale grey interior. A single-material lump cannot show both, so the interior
is a `assign_faces_by` region on one watertight solid -- never a second shell,
which would z-fight with the crust.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=180.0,
    width=142.0,
    height=104.0,
    pits=9,               # regmaglypts: thumbprint depressions
    pit_depth=6.0,
)

SEGS = 13
RINGS = 8


def _lattice(seed, jitter):
    """Perturbed low-segment sphere: faceted rock, not a ball."""
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
    """Scale so the ACTUAL extent equals `size` exactly (jitter is asymmetric)."""
    xs, ys, zs = ([p[i] for p in pts] for i in range(3))
    fx = size[0] / (max(xs) - min(xs))
    fy = size[1] / (max(ys) - min(ys))
    fz = size[2] / (max(zs) - min(zs))
    cx, cy, cz = ((max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0,
                  (max(zs) + min(zs)) / 2.0)
    return [((p[0] - cx) * fx, (p[1] - cy) * fy, (p[2] - cz) * fz) for p in pts]


def build():
    crust = bkit.pbr("FusionCrust", base=(0.085, 0.082, 0.080), rough=0.72)
    interior = bkit.pbr("ChondriteInterior", base=(0.46, 0.44, 0.41), rough=0.55)
    fusion = bkit.pbr("FusionCrustFresher", base=(0.16, 0.15, 0.145), rough=0.34,
                      metal=0.85)

    pts, faces = _lattice(41, 0.16)
    verts = _fit(pts, (SPEC["length"], SPEC["width"], SPEC["height"]))
    meteor = bkit.mesh_from("Meteorite", verts, faces, mat=crust, smooth=False)
    bkit.recalc(meteor)

    # ---- broken face: the pale interior, as a face region on the same solid
    # A second shell here would z-fight with the crust and double the
    # non-manifold count; selecting faces by normal keeps one watertight body.
    bkit.assign_faces_by(meteor, interior, lambda c, n: n.x < -0.72 and n.z > -0.3)

    # ---- regmaglypts: shallow thumbprint depressions on the crusted face --
    # Placed on a computed grid inside the projected outline, each a separate
    # overlapping solid rather than a difference: a difference of 9 shallow
    # bowls is 9 chances to make the mesh non-manifold, and these read as
    # texture at this scale.
    rnd = random.Random(5)
    pit_r = SPEC["pit_depth"] * 2.6
    for i, (px, py) in enumerate(bkit.grid_positions(cols=3, rows=3,
                                                     pitch_x=52.0, pitch_y=48.0)):
        d = SPEC["pit_depth"] * rnd.uniform(0.7, 1.0)
        pit = bkit.rounded_box("Regmaglypt%d" % (i + 1), pit_r, pit_r, d, r=pit_r / 2.6,
                               centre=(px, py, d / 2.0 + 6.0), mat=fusion)
        pit.rotation_euler = (0.0, 0.0, math.radians(rnd.uniform(0.0, 90.0)))

    return dict(spec=SPEC, parts=1 + SPEC["pits"])


CHECKS = [
    dict(name="length", mm=180.0, tol=1.5, how="bbox_x", part="Meteorite"),
    dict(name="width", mm=142.0, tol=1.5, how="bbox_y", part="Meteorite"),
    dict(name="height", mm=104.0, tol=1.5, how="bbox_z", part="Meteorite"),
]