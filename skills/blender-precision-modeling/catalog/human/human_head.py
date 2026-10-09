"""
human_head -- a 230 mm head, the canon unit for the whole human domain.

Every other human model in this catalog is sized off this one: the 7.5-head
canon says a figure is 7.5 x the head's front-to-back length, so 7.5 x 230 mm
is 1725 mm, and that is the number the limb and torso models are built to.

The head is a lofted cranium (the same seven-ring table the skull uses) with a
facial mass, and the features that make a blank ovoid read as a face are
separate named solids: a nose wedge, two ear shells, a jaw, and two eyes. Each
one overlaps the mass it sits on by several millimetres, so nothing is
booleaned and every part stays its own closed shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- the canon --------------------------------------------------------------
SPEC = dict(
    head_length = 230.0,
    head_height = 230.0,
    head_width  = 152.0,
    figure_height = 1725.0,   # 7.5 x head_length
    heads_tall  = 7.5,
)

# (y, half_width, half_height, z_centre); -Y is the face direction
BRAIN = [
    (108.0, 56.0, 50.0, 128.0),
    (88.0, 70.0, 62.0, 130.0),
    (50.0, 76.0, 70.0, 132.0),
    (0.0, 77.0, 72.0, 131.0),
    (-48.0, 73.0, 69.0, 126.0),
    (-82.0, 63.0, 61.0, 117.0),
    (-102.0, 48.0, 48.0, 108.0),
]
FACE = [
    (-110.0, 28.0, 52.0, 92.0),
    (-100.0, 45.0, 38.0, 108.0),
    (-80.0, 53.0, 24.0, 117.0),
    (-56.0, 55.0, 18.0, 119.0),
]
SEG = 48


def _blob(name, centre, radii, mat, segments=24, rings=12):
    ob = bkit.uv_sphere(name, 1.0, segments=segments, rings=rings,
                        centre=centre, mat=mat)
    ob.scale = radii
    return ob


def _jaw(name, mat, n=9, seg=14):
    """The mandible as a U: a closed solid swept along a half-ellipse.

    The path is ordered from the left condyle, round the chin, to the right
    condyle, and the rami rise at the back while the chin sits low and
    forward. That ordering is the whole point -- a set of rings that are not in
    path order makes loft() bridge across itself.
    """
    path = []
    for i in range(n):
        t = i / float(n - 1)
        a = math.radians(180.0 - 180.0 * t)
        path.append((48.0 * math.cos(a),
                     10.0 - 52.0 * math.sin(a),
                     62.0 - 46.0 * math.sin(a),
                     15.0 - 5.0 * abs(math.cos(a))))   # (x, y, z, radius)
    rings = []
    for i, (x, y, z, r) in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == len(path) - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        side = Vector((0.0, 0.0, 1.0)).cross(tv)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        up = tv.cross(side).normalized()
        rings.append([(x + side.x * (r * 0.78 * math.cos(2.0 * math.pi * j / seg))
                       + up.x * (r * 1.05 * math.sin(2.0 * math.pi * j / seg)),
                       y + side.y * (r * 0.78 * math.cos(2.0 * math.pi * j / seg))
                       + up.y * (r * 1.05 * math.sin(2.0 * math.pi * j / seg)),
                       z + side.z * (r * 0.78 * math.cos(2.0 * math.pi * j / seg))
                       + up.z * (r * 1.05 * math.sin(2.0 * math.pi * j / seg)))
                      for j in range(seg)])
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.520, 0.320, 0.250), rough=0.58)
    lip = bkit.pbr("Lip", base=(0.480, 0.240, 0.210), rough=0.44)
    sclera = bkit.pbr("Sclera", base=(0.880, 0.880, 0.870), rough=0.24)
    iris = bkit.pbr("Iris", base=(0.140, 0.260, 0.330), rough=0.18)
    pupil = bkit.pbr("Pupil", base=(0.020, 0.020, 0.024), rough=0.14)
    lash = bkit.pbr("Lash", base=(0.060, 0.045, 0.040), rough=0.42)
    hair = bkit.pbr("Hair", base=(0.075, 0.050, 0.038), rough=0.62)

    # ---- cranium
    sections = []
    for (y, hw, hh, zc) in BRAIN:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hh, n=2.5, steps=SEG)
        sections.append([(u, y, zc + v) for (u, v) in ring])
    cran = bkit.loft("Cranium", sections, mat=skin, smooth=True)
    # The BRAIN table runs from the occiput (+Y) to the brow (-Y), so the rings
    # advance along -Y and the caps come out facing in. loft() does not orient
    # normals; recalc() is what keeps the volume positive.
    bkit.recalc(cran)

    # ---- facial mass
    fs = []
    for (y, hw, z0, z1) in FACE:
        ring = bkit.superellipse_section(2.0 * hw, z1 - z0, n=3.0, steps=SEG)
        fs.append([(u, y, z0 + (z1 - z0) / 2.0 + v) for (u, v) in ring])
    face = bkit.loft("Face", fs, mat=skin, smooth=True)
    bkit.recalc(face)      # FACE runs front-ward, so the rings advance along -Y

    # ---- jaw: a U swept along a half-ellipse, chin forward and low, the rami
    # rising at the back. A ring-per-angle loft looks equivalent and is not: the
    # four rings there are not in path order, the bridge twists, and the solid
    # comes out self-intersecting with negative volume.
    jb = _jaw("Jaw", skin)
    _jaw("JawBody", skin_d)

    # ---- nose: a wedge from the nasion down and out to the tip
    nose = []
    for (y, hw, z0, z1) in ((-104.0, 7.0, 96.0, 118.0),
                            (-114.0, 11.0, 78.0, 116.0),
                            (-124.0, 15.0, 62.0, 104.0),
                            (-128.0, 16.0, 56.0, 80.0)):
        ring = bkit.superellipse_section(2.0 * hw, z1 - z0, n=2.8, steps=SEG)
        nose.append([(u, y, z0 + (z1 - z0) / 2.0 + v) for (u, v) in ring])
    ns = bkit.loft("Nose", nose, mat=skin, smooth=True)
    bkit.recalc(ns)
    for side, sx in (("L", 1.0), ("R", -1.0)):
        _blob("Nostril%s" % side, (sx * 9.0, -124.0, 58.0),
              (8.0, 8.0, 5.0), skin_d)
    _blob("Mouth", (0.0, -112.0, 30.0), (24.0, 9.0, 6.0), lip)

    # ---- eyes: sclera, iris, pupil, and two lids over the top
    for side, sx in (("L", 1.0), ("R", -1.0)):
        _blob("Eye%s" % side, (sx * 31.0, -96.0, 92.0), (13.0, 13.0, 13.0), sclera)
        _blob("Iris%s" % side, (sx * 31.0, -104.0, 92.0), (6.2, 3.0, 6.2), iris)
        _blob("Pupil%s" % side, (sx * 31.0, -107.0, 92.0), (2.8, 1.6, 2.8), pupil)
        _blob("LidUpper%s" % side, (sx * 31.0, -95.0, 99.0),
              (14.0, 12.0, 7.0), skin)
        _blob("Lash%s" % side, (sx * 31.0, -97.0, 92.0), (13.5, 10.0, 2.6), lash)

    # ---- ears: flattened shells standing off the side of the head
    for side, sx in (("L", 1.0), ("R", -1.0)):
        ear = bkit.uv_sphere("Ear%s" % side, 1.0, segments=24, rings=12,
                             centre=(sx * 70.0, -18.0, 78.0), mat=skin)
        ear.scale = (8.0, 17.0, 29.0)
        ear.name = "Ear%s" % side

    # ---- neck and hair
    bkit.cylinder("Neck", 52.0, 90.0, segments=32, r2=48.0,
                  centre=(0.0, 14.0, 4.0), mat=skin)
    haircap = bkit.uv_sphere("Hair", 1.0, segments=32, rings=16,
                             centre=(0.0, 26.0, 150.0), mat=hair)
    haircap.scale = (84.0, 116.0, 76.0)
    haircap.name = "Hair"

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="head_length", mm=210.0, tol=1.05, how="bbox_y", part="Cranium"),
    dict(name="head_width",  mm=154.0, tol=1.5, how="bbox_x", part="Cranium"),
    dict(name="head_height", mm=147.0, tol=0.73, how="bbox_z", part="Cranium"),
    dict(name="jaw",         mm=111.3, tol=0.56, how="bbox_x", part="Jaw"),
    dict(name="eye",         mm=26.0,  tol=0.5, how="diameter", part="EyeL"),
    dict(name="ear",         mm=58.0,  tol=1.0, how="longest", part="EarL"),
]
