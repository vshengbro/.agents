"""Shared organic-construction helpers for the wave-10 animal domains.

Every part these helpers return is its own CLOSED SOLID, built from absolute
millimetre coordinates, so nothing has to be booleaned and `bkit.health()`
reports zero non-manifold edges part by part. That is the same approach the
shipped mammals and birds use: overlapping closed solids stay manifold solids.

`bkit.mesh_from()` writes millimetres into the mesh and leaves the object
transform at identity, which is what makes `bkit.array_radial()` orbit a part
that was authored in world coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy          # noqa: E402
import bkit         # noqa: E402
from mathutils import Matrix    # noqa: E402


# ---------------------------------------------------------------------------
# swept bodies
# ---------------------------------------------------------------------------
def orient_outward(ob):
    """Guarantee outward-facing normals on a closed solid.

    `bmesh.ops.recalc_face_normals` alone is not enough: on a nearly DEGENERATE
    profile -- an extruded outline that is almost a straight line, e.g. a
    sea-turtle flipper blade tapering to a point -- its orientation heuristic
    picks inward, and `health()` then reports `negative_volume` on a solid that
    looks correct. So recalc first, then trust the signed volume, and reverse
    the faces if it came out inside-out.
    """
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    try:
        inside = bm.calc_volume(signed=True) < 0.0
    except Exception:
        inside = False
    if inside:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def tube(name, path, rad, mat, n=2.4, steps=28, smooth=True):
    """Sweep a superellipse ring along a 3D polyline and cap both ends.

    `rad` is one (along_s, along_v) pair per path node, where `s` is the ring's
    in-plane side axis and `v = t x s`. The frame follows the tangent with
    Gram-Schmidt, so a bend never twists the profile.
    """
    rings = []
    prev = None
    m = len(path)
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, m - 1)]
        t = [b[k] - a[k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        t = [c / tl for c in t]
        s = None
        if prev is not None:
            d = sum(prev[k] * t[k] for k in range(3))
            cand = [prev[k] - d * t[k] for k in range(3)]
            if sum(c * c for c in cand) > 1e-9:
                s = cand
        if s is None:
            for up in ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)):
                cand = [up[1] * t[2] - up[2] * t[1],
                        up[2] * t[0] - up[0] * t[2],
                        up[0] * t[1] - up[1] * t[0]]
                if sum(c * c for c in cand) > 1e-9:
                    s = cand
                    break
        sl = math.sqrt(sum(c * c for c in s))
        s = [c / sl for c in s]
        v = [t[1] * s[2] - t[2] * s[1], t[2] * s[0] - t[0] * s[2],
             t[0] * s[1] - t[1] * s[0]]
        prev = s
        w, h = rad[i]
        ring = []
        for j in range(steps):
            ang = 2.0 * math.pi * j / steps
            ca, sa = math.cos(ang), math.sin(ang)
            cx = math.copysign(abs(ca) ** (2.0 / n), ca)
            cy = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((p[0] + s[0] * w * cy + v[0] * h * cx,
                         p[1] + s[1] * w * cy + v[1] * h * cx,
                         p[2] + s[2] * w * cy + v[2] * h * cx))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=smooth)
    orient_outward(ob)
    return ob


def body(name, rows, mat, n=2.4, steps=32):
    """Loft an animal torso from a table.

    Every row is (y, half_height, half_width, z_centre) in millimetres, so body
    length, depth and girth are properties of the table rather than a claim
    made afterwards. The nose points at -Y, which is what the catalog's fixed
    side view (camera on +X) needs for a silhouette instead of a face.
    """
    sections = []
    for (y, hh, hw, zc) in rows:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hh, n=n, steps=steps)
        sections.append([(u, y, zc + w) for (u, w) in ring])
    ob = bkit.loft(name, sections, mat=mat)
    orient_outward(ob)
    bkit.shade_smooth(ob, 50.0)
    return ob


def sphere(name, radius, centre, mat, segments=24, rings=12):
    """A closed sphere whose normals are guaranteed outward.

    `bkit.uv_sphere()` recalcs itself, but on a very small radius (a 0.16 mm ant
    eye) the pole weld plus recalc can leave the winding inside-out, and
    `health()` then reports `negative_volume` on a part that renders fine.
    Re-checking the signed volume here costs nothing and keeps micro models
    clean.
    """
    ob = bkit.uv_sphere(name, radius, segments=segments, rings=rings,
                        centre=centre, mat=mat)
    return orient_outward(ob)


def cone_between(name, base, tip, r_base, r_tip, seg=12, mat=None):
    """A closed cone from `base` to `tip` -- spines, antennae, claws, tusks.

    Written straight from two points, so the caller never has to think about
    which Blender axis a part happens to lie along.
    """
    d = [tip[k] - base[k] for k in range(3)]
    dl = math.sqrt(sum(c * c for c in d))
    if dl < 1e-9:
        # degenerate: base == tip would normalise to the zero vector, and then
        # every cross product below is zero too, so `s` stays None
        d = [0.0, 1.0, 0.0]
        dl = 1.0
    d = [c / dl for c in d]
    s = None
    for up in ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)):
        cand = [up[1] * d[2] - up[2] * d[1],
                up[2] * d[0] - up[0] * d[2],
                up[0] * d[1] - up[1] * d[0]]
        if sum(c * c for c in cand) > 1e-9:
            s = cand
            break
    sl = math.sqrt(sum(c * c for c in s))
    s = [c / sl for c in s]
    v = [d[1] * s[2] - d[2] * s[1], d[2] * s[0] - d[0] * s[2],
         d[0] * s[1] - d[1] * s[0]]
    verts = []
    for (c, r) in ((base, r_base), (tip, r_tip)):
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            ca, sa = math.cos(a), math.sin(a)
            verts.append((c[0] + s[0] * r * ca + v[0] * r * sa,
                          c[1] + s[1] * r * ca + v[1] * r * sa,
                          c[2] + s[2] * r * ca + v[2] * r * sa))
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((i, j, seg + j, seg + i))
    faces.append(tuple(range(seg - 1, -1, -1)))
    faces.append(tuple(range(seg, 2 * seg)))
    ob = bkit.mesh_from(name, verts, faces, mat)
    orient_outward(ob)
    return ob


# ---------------------------------------------------------------------------
# flat blades: fins, wings, leaf blades, webbing
# ---------------------------------------------------------------------------
def plate_yz(name, yz, thickness, x=0.0, mat=None):
    """A thin blade lying in the Y-Z plane, `thickness` mm along X.

    `yz` is a closed outline in millimetres, y forward-positive as authored.
    Vertical fins (dorsal, anal, caudal, pectoral when it is edge-on) are all
    this shape at a different x.
    """
    poly = [(-z, y) for (y, z) in yz]
    ob = bkit.extrude_profile(name, poly, thickness, centre=(x, 0.0, 0.0),
                              axis="X", mat=mat)
    orient_outward(ob)
    return ob


def plate_xy(name, xy, thickness, z=0.0, mat=None):
    """A thin blade lying in the X-Y plane, `thickness` mm along Z."""
    ob = bkit.extrude_profile(name, list(xy), thickness,
                              centre=(0.0, 0.0, z), axis="Z", mat=mat)
    orient_outward(ob)
    return ob


def tilt(obj, deg_x=0.0, deg_y=0.0, deg_z=0.0):
    """Rotate a part about the WORLD origin, in degrees.

    Used to swing a horizontal pectoral blade out of the horizontal plane. The
    rotation is about the origin, which is only meaningful for parts authored
    in world coordinates -- true for every helper here.
    """
    obj.rotation_euler = (math.radians(deg_x), math.radians(deg_y),
                          math.radians(deg_z))
    bpy.context.view_layer.update()
    return obj


def bake_rot(obj, axis="Y", deg=0.0):
    """Rotate a part's own vertices about the world origin, keeping the object
    transform at identity.

    Object-level rotation composes badly with a later world-space mirror --
    `mirror()` applied to `matrix_world` flips the translation column too, and
    the copy's silhouette drifts out of the assembly. Baking the rotation into
    the mesh means every part here lives in the same coordinate space with no
    object rotation at all, so `mirror_copy()` is exactly a sign flip on X.
    """
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    me = obj.data
    if axis == "X":
        rot = lambda x, y, z: (x, y * ca - z * sa, y * sa + z * ca)
    elif axis == "Z":
        rot = lambda x, y, z: (x * ca - y * sa, x * sa + y * ca, z)
    else:
        rot = lambda x, y, z: (x * ca + z * sa, y, -x * sa + z * ca)
    for v in me.vertices:
        p = rot(v.co.x, v.co.y, v.co.z)
        v.co = (p[0], p[1], p[2])
    obj.data.update()
    bpy.context.view_layer.update()
    return obj


# ---------------------------------------------------------------------------
# path maths for paired and repeated parts
# ---------------------------------------------------------------------------
def flipx(path):
    """Mirror a path across the sagittal plane X=0."""
    return [(-p[0], p[1], p[2]) for p in path]


def flipy(path):
    return [(p[0], -p[1], p[2]) for p in path]


def rotz(path, deg, pivot=(0.0, 0.0, 0.0)):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in path:
        dx, dy = p[0] - pivot[0], p[1] - pivot[1]
        out.append((pivot[0] + dx * ca - dy * sa,
                    pivot[1] + dx * sa + dy * ca, p[2]))
    return out


def roty(path, deg, pivot=(0.0, 0.0, 0.0)):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in path:
        dx, dz = p[0] - pivot[0], p[2] - pivot[2]
        out.append((pivot[0] + dx * ca + dz * sa, p[1],
                    pivot[2] - dx * sa + dz * ca))
    return out


def rotx(path, deg, pivot=(0.0, 0.0, 0.0)):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in path:
        dy, dz = p[1] - pivot[1], p[2] - pivot[2]
        out.append((p[0], pivot[1] + dy * ca - dz * sa,
                    pivot[2] + dy * sa + dz * ca))
    return out


def mirror_copy(ob, name):
    """Exact world-space mirror of a part across X=0, as its own closed solid.

    The Mirror MODIFIER is the wrong tool here twice over: it mirrors about the
    OBJECT's own origin rather than the world sagittal plane, so a part that had
    been moved off X=0 got its copy back at the same radius instead of the
    opposite side; and it welds the two halves on a shared face, which reads as
    a non-manifold edge. Mirroring the world matrix instead keeps each half a
    separate closed solid and puts it exactly opposite.
    """
    new = ob.copy()
    new.data = ob.data.copy()
    new.name = name
    bpy.context.collection.objects.link(new)
    # mirror across the plane X=0: S @ (R|t) = (S R | S t), i.e. the whole world
    # transform reflected. Getting this diagonal wrong (flipping Y instead)
    # silently reflects the part along the wrong axis and the "pair" ends up
    # overlapping its own original.
    flip = Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0)).to_4x4()
    new.matrix_world = flip @ ob.matrix_world
    # a mirror reverses orientation, so the copy comes out inside-out
    orient_outward(new)
    bpy.context.view_layer.update()
    return new


def mirror_pair(ob, name):
    """Mirror one half-built object across the world sagittal plane.

    Returns (original, mirror); both stay separate named solids.
    """
    return ob, mirror_copy(ob, name)


def pair_tubes(name, path, rad, mat, n=2.4, steps=24):
    """Build one swept part and its exact mirror -- legs, flippers, wings."""
    first = tube(name, path, rad, mat, n=n, steps=steps)
    return mirror_pair(first, name)


def radial(ob, count, centre=(0.0, 0.0, 0.0)):
    """Sweep an already-authored part around `centre` -- arms, legs, spines."""
    bkit.array_radial(ob, count, centre=centre)
    return ob