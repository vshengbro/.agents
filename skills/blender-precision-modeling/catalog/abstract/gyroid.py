"""
gyroid -- a triply-periodic minimal surface: a 90 mm specimen block.

The gyroid is the zero set of  cos x cos y + cos y cos z + cos z cos x = 0, so
it is an implicit surface and bkit has no implicit-surface recipe. It is
marched here with TETRAHEDRA rather than cubes: marching cubes needs a 256-case
lookup table, marching tetrahedra only needs the 16 cases, and the Freudenthal
6-tet split of every cube is conforming (every grid edge is shared by exactly
two tetrahedra), which is what makes the result watertight.

Two details decide whether this passes the gate:
  * a shared VERTEX CACHE keyed on the grid edge, so the crossing point an
    edge produces is the same vertex for both tetrahedra that contain it --
    without it every triangle owns private duplicates and every edge has
    exactly one face;
  * every grid point on the block boundary is forced OUTSIDE the surface, so
    the isosurface is pushed clear of the six faces and closes on itself
    instead of being sliced open.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    block=90.0,            # specimen cube edge
    divisions=22,          # cells per axis
    periods=3.0,           # unit cells across the block
    pore_thickness=9.0,    # rule-of-thumb wall between neighbouring sheets
    width=90.0,
    depth=90.0,
    height=90.0,
)

L = SPEC["block"]
N = SPEC["divisions"]
CELL = L / N
SCALE = SPEC["periods"] * 2.0 * math.pi / L

CHECKS = [
    # 85.88, not 90: the lattice faces are forced outside the surface, so the
    # specimen is the gyroid clipped just inside the 90 mm block rather than a
    # solid whose surface runs into the six faces.
    dict(name="width", mm=85.88, tol=0.4, how="bbox_x", part="Gyroid"),
    dict(name="depth", mm=85.88, tol=0.4, how="bbox_y", part="Gyroid"),
    dict(name="height", mm=85.88, tol=0.4, how="bbox_z", part="Gyroid"),
]


def _field(x, y, z):
    return (math.cos(x * SCALE) * math.cos(y * SCALE)
            + math.cos(y * SCALE) * math.cos(z * SCALE)
            + math.cos(z * SCALE) * math.cos(x * SCALE))


def build():
    # --- sample the field on the (N+1)^3 lattice --------------------------
    n1 = N + 1
    field = []
    for k in range(n1):
        z = -L / 2.0 + k * CELL
        for j in range(n1):
            y = -L / 2.0 + j * CELL
            for i in range(n1):
                x = -L / 2.0 + i * CELL
                on_face = (i in (0, N) or j in (0, N) or k in (0, N))
                # Face samples are forced positive (= outside the solid) so the
                # surface is clipped clear of the block boundary and closes.
                field.append(1.0 if on_face else _field(x, y, z))

    def pid(i, j, k):
        return i + n1 * (j + n1 * k)

    verts, faces = [], []
    cache = {}

    def crossing(a, b):
        """The one vertex where the surface cuts grid edge a-b."""
        key = (a, b) if a < b else (b, a)
        hit = cache.get(key)
        if hit is not None:
            return hit
        fa, fb = field[a], field[b]
        t = fa / (fa - fb)
        ia, ja, ka = a % n1, (a // n1) % n1, a // (n1 * n1)
        ib, jb, kb = b % n1, (b // n1) % n1, b // (n1 * n1)
        p = (-L / 2.0 + (ia + t * (ib - ia)) * CELL,
             -L / 2.0 + (ja + t * (jb - ja)) * CELL,
             -L / 2.0 + (ka + t * (kb - ka)) * CELL)
        idx = len(verts)
        verts.append(p)
        cache[key] = idx
        return idx

    # Freudenthal / Kuhn split of one cell into six tetrahedra: conforming, and
    # every cell edge lands in exactly two of them.
    TETS = ((0, 1, 3, 7), (0, 1, 5, 7), (0, 4, 5, 7),
            (0, 4, 6, 7), (0, 2, 6, 7), (0, 2, 3, 7))
    TET_EDGES = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))

    for k in range(N):
        for j in range(N):
            for i in range(N):
                # corner index = (i&1) + 2*(j&1) + 4*(k&1)
                base = [pid(i + (c & 1), j + ((c >> 1) & 1), k + ((c >> 2) & 1))
                        for c in range(8)]
                for tet in TETS:
                    vals = [field[base[c]] for c in tet]
                    inside = [t for t in range(4) if vals[t] < 0.0]
                    if not inside or len(inside) == 4:
                        continue
                    if len(inside) in (1, 3):
                        odd = inside[0] if len(inside) == 1 else \
                            [t for t in range(4) if t not in inside][0]
                        tri = []
                        for (a, b) in TET_EDGES:
                            if a == odd or b == odd:
                                tri.append(crossing(base[tet[a]], base[tet[b]]))
                        faces.append(tuple(tri))
                    else:
                        out = [t for t in range(4) if t not in inside]
                        i0, i1 = inside
                        o0, o1 = out
                        # The four crossings must be walked CYCLICALLY
                        # (i0-o0, i1-o0, i1-o1, i0-o1). Collecting them in
                        # TET_EDGES order gives a bow-tie, and splitting a
                        # bow-tie into two triangles produces two degenerate
                        # faces that validate() silently deletes -- which
                        # reads as ~46 000 non-manifold edges, not as a bug in
                        # the triangulation.
                        quad = [crossing(base[tet[i0]], base[tet[o0]]),
                                crossing(base[tet[i1]], base[tet[o0]]),
                                crossing(base[tet[i1]], base[tet[o1]]),
                                crossing(base[tet[i0]], base[tet[o1]])]
                        faces.append((quad[0], quad[1], quad[2]))
                        faces.append((quad[0], quad[2], quad[3]))

    mat = bkit.pbr("GyroidShell", base=(0.88, 0.72, 0.40), metal=0.30, rough=0.24)
    solid = bkit.mesh_from("Gyroid", verts, faces, mat=mat)
    bkit.recalc(solid)
    bkit.shade_smooth(solid, 60)

    return dict(spec=SPEC, parts=1)