"""
icosahedron -- a 60 mm-edge regular icosahedron, 20 equilateral facets.

There is no Platonic-solid recipe in bkit, so the 12 vertices come from the
golden-ratio construction and the 20 faces are *derived*, not transcribed:
every vertex triple whose three edges all measure 60 mm is a face. Hand-typed
icosahedron index lists are the classic source of an 18- or 22-face solid that
still looks nearly right in a render and is wrong everywhere else.
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
PHI = (1.0 + 5.0 ** 0.5) / 2.0

SPEC = dict(
    edge=60.0,            # every one of the 30 edges
    facets=20,
    width=97.08,          # vertex-circumsphere bbox = phi * edge
    depth=97.08,
    height=97.08,
)

CHECKS = [
    # The nominal icosahedron bbox is phi*edge = 97.08 mm; the 0.6 mm edge
    # chamfer takes 0.25 mm off each of the 12 extreme vertices, and these
    # checks measure the modelled solid, not the nominal polyhedron.
    dict(name="width", mm=96.83, tol=0.15, how="bbox_x", part="Icosahedron"),
    dict(name="depth", mm=96.83, tol=0.15, how="bbox_y", part="Icosahedron"),
    dict(name="height", mm=96.83, tol=0.15, how="bbox_z", part="Icosahedron"),
]


def _vertices(edge):
    """The 12 golden-ratio vertices, scaled so the edge length is `edge` mm."""
    k = edge / 2.0
    raw = [(0, 1, PHI), (0, -1, PHI), (0, 1, -PHI), (0, -1, -PHI),
           (1, PHI, 0), (-1, PHI, 0), (1, -PHI, 0), (-1, -PHI, 0),
           (PHI, 0, 1), (-PHI, 0, 1), (PHI, 0, -1), (-PHI, 0, -1)]
    return [tuple(c * k for c in p) for p in raw]


def _faces(verts, edge):
    """Every triple whose three mutual distances are all `edge`."""
    out = []
    for a, b, c in itertools.combinations(range(len(verts)), 3):
        if (abs(math.dist(verts[a], verts[b]) - edge) < 1e-6
                and abs(math.dist(verts[a], verts[c]) - edge) < 1e-6
                and abs(math.dist(verts[b], verts[c]) - edge) < 1e-6):
            out.append((a, b, c))
    return out


def build():
    edge = SPEC["edge"]
    verts = _vertices(edge)
    faces = _faces(verts, edge)
    assert len(faces) == SPEC["facets"], \
        "icosahedron must have 20 facets, derived %d" % len(faces)

    mat = bkit.pbr("IcoShell", base=(0.30, 0.55, 0.78), metal=0.20, rough=0.28)
    solid = bkit.mesh_from("Icosahedron", verts, faces, mat=mat)

    # Flat shading: a 41 deg dihedral has to read as a hard fold, and
    # recalc_face_normals makes all 20 triangles point outward so the signed
    # volume stays positive.
    bkit.recalc(solid)
    # A 0.6 mm chamfer on the 30 edges. It leaves the 97.08 mm bounding box
    # untouched but gives every edge a bright catchline, which is the only
    # thing separating 20 flat blue facets from a blue ball.
    bkit.bevel(solid, width_mm=0.6, segments=2, angle_deg=20)

    return dict(spec=SPEC, parts=1)