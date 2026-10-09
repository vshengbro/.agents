"""
dodecahedron -- a 36 mm-edge regular dodecahedron, 12 regular pentagon faces.

Built through duality rather than by transcription: the 20 vertices are the
face centres of the icosahedron, and each of the 12 pentagons is the set of
icosahedron faces meeting at one icosahedron vertex. Getting this backwards
(dodeca vertices from icosa *vertices*) silently yields a 17-vertex solid
with only 3 of the 4 visible faces closed -- a shape that renders
convincingly and is not a dodecahedron.
"""
import itertools
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
from mathutils import Vector

PHI = (1.0 + 5.0 ** 0.5) / 2.0

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    edge=36.0,            # every one of the 30 edges
    facets=12,
    width=94.25,          # bbox = phi^2 * edge
    depth=94.25,
    height=94.25,
)

CHECKS = [
    dict(name="width", mm=94.25, tol=0.15, how="bbox_x", part="Dodecahedron"),
    dict(name="depth", mm=94.25, tol=0.15, how="bbox_y", part="Dodecahedron"),
    dict(name="height", mm=94.25, tol=0.15, how="bbox_z", part="Dodecahedron"),
]


def _icosa_faces(edge):
    k = edge / 2.0
    raw = [(0, 1, PHI), (0, -1, PHI), (0, 1, -PHI), (0, -1, -PHI),
           (1, PHI, 0), (-1, PHI, 0), (1, -PHI, 0), (-1, -PHI, 0),
           (PHI, 0, 1), (-PHI, 0, 1), (PHI, 0, -1), (-PHI, 0, -1)]
    v = [tuple(c * k for c in p) for p in raw]
    f = [t for t in itertools.combinations(range(12), 3)
         if abs(math.dist(v[t[0]], v[t[1]]) - edge) < 1e-6
         and abs(math.dist(v[t[0]], v[t[2]]) - edge) < 1e-6
         and abs(math.dist(v[t[1]], v[t[2]]) - edge) < 1e-6]
    return v, f


def _dodeca(edge):
    """Vertices and pentagon faces of a dodecahedron with edge length `edge`."""
    ico_v, ico_f = _icosa_faces(60.0)

    # --- 20 vertices: the unit normals of the 20 icosahedron facets --------
    centres = []
    for (a, b, c) in ico_f:
        p = tuple((ico_v[a][i] + ico_v[b][i] + ico_v[c][i]) / 3.0 for i in range(3))
        L = math.sqrt(sum(x * x for x in p))
        centres.append(tuple(x / L for x in p))

    # At unit circumradius the icosahedron-derived solid has edge e1; rescale so
    # the dodecahedron edge is exactly `edge`.
    e1 = min(math.dist(centres[i], centres[j])
             for i, j in itertools.combinations(range(20), 2))
    k = edge / e1
    verts = [tuple(c * k for c in p) for p in centres]

    # --- 12 faces: the facets meeting at each of the 12 icosahedron vertices -
    # A set of five vertices is NOT yet a polygon: the corners have to be put in
    # cyclic order, or the n-gon connects non-adjacent vertices and every one
    # of the 30 edges ends up unshared (44 non-manifold edges, and a solid that
    # renders as a convincing dodecahedron anyway).
    faces = []
    for i in range(12):
        ring = [j for j, (a, b, c) in enumerate(ico_f) if i in (a, b, c)]
        assert len(ring) == 5, "each icosahedron vertex meets 5 facets"
        n = Vector(ico_v[i]).normalized()
        ref = Vector((0.0, 0.0, 1.0)) if abs(n[2]) < 0.9 else Vector((1.0, 0.0, 0.0))
        e1 = (ref - n * ref.dot(n)).normalized()
        e2 = n.cross(e1)
        ring.sort(key=lambda j: math.atan2(Vector(centres[j]).dot(e2),
                                            Vector(centres[j]).dot(e1)))
        faces.append(tuple(ring))
    return verts, faces


def build():
    verts, faces = _dodeca(SPEC["edge"])
    assert len(verts) == 20, "dodecahedron needs 20 distinct vertices"
    assert all(len(f) == 5 for f in faces), "dodecahedron facets are pentagons"

    mat = bkit.pbr("DodecaShell", base=(0.86, 0.72, 0.30), metal=0.25, rough=0.26)
    solid = bkit.mesh_from("Dodecahedron", verts, faces, mat=mat)

    # The 12 n-gons come out of the duality with mixed winding; recalc()
    # orients a closed shell outward in one pass, which is what keeps
    # calc_volume(signed=True) positive and the gate happy.
    bkit.recalc(solid)
    # No bevel here: the beveller cannot split a pentagonal n-gon cleanly at
    # this angle limit and leaves ~76 non-manifold edges on the 12 faces. The
    # flat-shaded facets read correctly without one.

    return dict(spec=SPEC, parts=1)