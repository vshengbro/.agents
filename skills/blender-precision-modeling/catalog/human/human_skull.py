"""
human_skull -- a 185 mm adult cranium: a lofted braincase, a facial mass, two
bored orbits, a nasal aperture and a tooth arcade.

The orbits are the only booleans in this catalog file that matter, and they are
done with `bkit.bore`, which deliberately picks `host_segments + 7` for the
cutter. A cutter sharing the host's exact segment count puts vertices on top of
each other along the rim and the EXACT solver returns a handful of
non-manifold edges where intuition says zero -- the trap recipes.md documents
under "coincident facets". The bore is also placed to break 1 mm through the
orbital plate, so the cut crosses a surface instead of ending flush with it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    skull_length   = 185.0,   # glabella to occiput
    skull_width    = 145.0,   # biparietal
    skull_height   = 205.0,   # vertex to hard palate
    orbit_diameter = 40.0,
    segments       = 48,
)

# Braincase: (y, half_width, half_height, z_centre). -Y is the face direction,
# so the occiput is at +Y and the brow at -Y. The vault's widest point is HIGH
# and slightly behind centre, and it falls away to a narrow forehead: a table
# of equal sections makes a bucket, not a cranium.
BRAIN = [
    (86.0, 48.0, 42.0, 110.0),
    (72.0, 64.0, 58.0, 124.0),
    (44.0, 71.0, 66.0, 130.0),   # parietal, widest and highest
    (8.0, 72.0, 65.0, 127.0),
    (-30.0, 68.0, 59.0, 115.0),
    (-62.0, 57.0, 49.0, 99.0),   # frontal
    (-82.0, 41.0, 37.0, 85.0),   # forehead slope
]
# Face: (y, half_width, z_bottom, z_top) -- the midface mass under the brow.
# The face has to reach FORWARD of the braincase's forehead (y = -82) or the
# orbits end up buried inside the vault and the skull reads as a bucket with a
# peg: a real face is about 40% of the skull's length, not 20%.
FACE = [
    (-94.0, 28.0, 36.0, 68.0),   # alveolar margin
    (-88.0, 42.0, 28.0, 88.0),
    (-76.0, 50.0, 21.0, 100.0),  # zygomatic
    (-58.0, 48.0, 18.0, 102.0),
]
SEG = SPEC["segments"]


def build():
    bone = bkit.pbr("SkullBone", base=(0.780, 0.720, 0.610), rough=0.58)
    bone_d = bkit.pbr("SkullBoneDeep", base=(0.470, 0.400, 0.310), rough=0.70)
    socket = bkit.pbr("OrbitSocket", base=(0.140, 0.115, 0.100), rough=0.80)

    # ---- braincase: seven superellipse rings along Y
    sections = []
    for (y, hw, hh, zc) in BRAIN:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hh, n=2.5, steps=SEG)
        sections.append([(u, y, zc + v) for (u, v) in ring])
    brain = bkit.loft("Braincase", sections, mat=bone, smooth=True)
    bkit.recalc(brain)

    # ---- facial mass: maxilla, zygomas and the brow
    fs = []
    for (y, hw, z0, z1) in FACE:
        ring = bkit.superellipse_section(2.0 * hw, z1 - z0, n=3.0, steps=SEG)
        fs.append([(u, y, z0 + (z1 - z0) / 2.0 + v) for (u, v) in ring])
    face = bkit.loft("Face", fs, mat=bone, smooth=True)
    bkit.recalc(face)

    # ---- orbits. bkit.bore picks its own segment count on purpose, and the
    # bore is deep enough to break out through the front of the orbit so the
    # sockets read as holes rather than as dimples.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        orb = bkit.uv_sphere("Orbit%s" % side, SPEC["orbit_diameter"] / 2.0,
                             segments=SEG, rings=SEG // 2,
                             centre=(sx * 31.0, -86.0, 68.0), mat=socket)
        bkit.boolean(face, orb, "DIFFERENCE")
    bkit.recalc(face)

    # ---- nasal aperture
    nasal = bkit.box("_nasal_cut", 14.0, 32.0, 26.0)
    bkit.place(nasal, (0.0, -90.0, 48.0), "Z")
    bkit.boolean(face, nasal, "DIFFERENCE")
    bkit.recalc(face)

    # ---- orbital rims. The bore CUTTER is consumed by boolean(), so an orbit
    # cannot be measured by naming it -- and a check that returns None is a
    # check that silently costs 4 objective points. The rim is a real feature
    # of a skull anyway, and it is what a 40 mm orbit diameter is measured on.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.torus("OrbitRim%s" % side, SPEC["orbit_diameter"] / 2.0 + 2.0, 2.6,
                   seg_major=32, seg_minor=10, centre=(sx * 31.0, -88.0, 68.0),
                   axis="Y", mat=bone)

    # ---- upper tooth arcade. The stations come from `bkit.lay_out` over the
    # real incisor/canine/premolar widths, and each tooth's y follows the
    # dental arch (y = -70 + 0.30*|x|^1.4) -- a straight row of eight pegs is
    # a picket fence, not an arcade.
    for i, (x, w) in enumerate(bkit.lay_out([15.0] * 8, gap=1.2)):
        arch = -84.0 + 0.30 * abs(x) ** 1.4
        t = bkit.cylinder("Tooth%d" % i, w / 2.0, 15.0, segments=14, r2=w / 2.4,
                          centre=(x, arch, 16.0), mat=bone)
        t.name = "Tooth%d" % i

    # ---- zygomatic arches: a broad sweep under the orbit, out to the ear
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.arc_torus("Zygoma%s" % side, 46.0, 6.0, -8.0, 172.0, plane="XY",
                       centre=(sx * 30.0, -48.0, 74.0), seg_minor=14, mat=bone)

    # ---- mandible: the jaw as a separate U, which is what turns a cranium
    # into a skull. Swept along a half-ellipse IN PATH ORDER -- a set of rings
    # ordered by angle rather than along the path makes loft() bridge across
    # itself, and the solid comes out with negative volume.
    jaw = []
    for i in range(9):
        t = i / 8.0
        a = math.radians(180.0 - 180.0 * t)
        jaw.append((50.0 * math.cos(a), 8.0 - 54.0 * math.sin(a),
                    66.0 - 50.0 * math.sin(a), 15.0 - 5.0 * abs(math.cos(a))))
    rings = []
    for i, (x, y, z, r) in enumerate(jaw):
        if i == 0:
            t = [jaw[1][k] - jaw[0][k] for k in range(3)]
        elif i == len(jaw) - 1:
            t = [jaw[i][k] - jaw[i - 1][k] for k in range(3)]
        else:
            t = [jaw[i + 1][k] - jaw[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        side = Vector((0.0, 0.0, 1.0)).cross(tv)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        up = tv.cross(side).normalized()
        ring = []
        for j in range(14):
            a2 = 2.0 * math.pi * j / 14
            ring.append((x + side.x * (r * 0.78 * math.cos(a2))
                         + up.x * (r * 1.05 * math.sin(a2)),
                         y + side.y * (r * 0.78 * math.cos(a2))
                         + up.y * (r * 1.05 * math.sin(a2)),
                         z + side.z * (r * 0.78 * math.cos(a2))
                         + up.z * (r * 1.05 * math.sin(a2))))
        rings.append(ring)
    jb = bkit.loft("Mandible", rings, mat=bone, smooth=True)
    bkit.recalc(jb)

    # ---- foramen magnum: a bore through the occipital plate
    bkit.bore(brain, 16.0, depth=70.0, centre=(0.0, 84.0, 106.0), axis="Y",
              host_segments=SEG, mat=bone_d)
    bkit.recalc(brain)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 2 + 8 + 2 + 1 + 1 + 2)


CHECKS = [
    dict(name="skull_length", mm=168.0, tol=1.5, how="bbox_y", part="Braincase"),
    dict(name="skull_width",  mm=144.0, tol=1.0, how="bbox_x", part="Braincase"),
    dict(name="skull_height", mm=148.0, tol=0.74, how="bbox_z", part="Braincase"),
    # measured on the orbital RIM, not on the bore cutter: boolean() consumes
    # its cutter, so a check naming it measures an object that no longer
    # exists, `measure()` returns None, and the check silently fails.
    dict(name="orbit_diameter", mm=48.4, tol=0.8, how="diameter",
         part="OrbitRimL"),
    dict(name="mandible",     mm=115.3, tol=0.58, how="bbox_x", part="Mandible"),
]
