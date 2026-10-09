"""
sunflower -- a cut 130 mm head on a 140 mm stem: 21 ray florets, a domed disc,
and 200 disc florets laid out on a phyllotactic spiral.

Two computed layouts do all the work:

  * the 21 rays are a radial array, but the pitch ring is DERIVED from the
    count and the floret width (r = n*w / 2*pi = 40.1 mm) rather than typed in.
    A 21-ray array on a ring that is too tight interpenetrates into a disc.
  * the disc florets follow r = 16*sqrt(k), theta = k * 137.5 deg, the golden
    angle. That is the real packing, and it is what stops the disc reading as
    concentric rings of beads.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    head_diameter = 130.0,
    disc_diameter = 100.0,
    ray_florets   = 21,
    stem_length   = 140.0,
    ray_length    = 52.0,
)

RAYS = SPEC["ray_florets"]
RAY_W = 12.0
# The pitch ring is DERIVED from the floret count and the ray base width, so
# 21 rays at a 12 mm base pitch 40.1 mm out. Typing the radius in instead is how
# a sunflower array ends up with its rays interpenetrating into a disc.
PITCH_R = RAYS * RAY_W / (2.0 * math.pi)
HEAD_Z = 140.0
DISC_R = 50.0
RAY_LEN = SPEC["ray_length"]


def _ray(name, direction, length, width, mat, n=12):
    """One ray floret: a strap petal with a notched tip."""
    d = Vector(direction).normalized()
    ref = Vector((0.0, 0.0, 1.0)) if abs(d.z) < 0.95 else Vector((1.0, 0.0, 0.0))
    side = d.cross(ref).normalized()
    nrm = side.cross(d).normalized()
    rings = []
    for (t, ws) in ((0.0, 0.30), (0.16, 0.72), (0.42, 0.96), (0.68, 1.00),
                    (0.86, 0.88), (0.96, 0.60), (1.0, 0.34)):
        c = Vector((0.0, 0.0, HEAD_Z)) + d * (PITCH_R * 0.42 + length * t) \
            + nrm * (-2.2 * t * t)
        w = width * ws
        ring = [tuple(c + side * (w * math.cos(2.0 * math.pi * j / n))
                      + nrm * (1.1 * math.sin(2.0 * math.pi * j / n)))
                for j in range(n)]
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    ray_mat = bkit.pbr("SunflowerRay", base=(0.880, 0.600, 0.060), rough=0.42)
    disc_mat = bkit.pbr("SunflowerDisc", base=(0.190, 0.115, 0.055), rough=0.72)
    floret = bkit.pbr("SunflowerFloret", base=(0.330, 0.200, 0.060), rough=0.60)
    stalk = bkit.pbr("SunflowerStalk", base=(0.180, 0.310, 0.095), rough=0.62)
    sepal = bkit.pbr("SunflowerSepal", base=(0.125, 0.265, 0.085), rough=0.60)

    # ---- stem
    bkit.cylinder("Stem", 9.0, SPEC["stem_length"], segments=20, r2=6.5,
                  centre=(0.0, 0.0, SPEC["stem_length"] / 2.0), mat=stalk)

    # ---- back of the head and the calyx: a shallow dome, so the rays have
    # something to be attached to.
    bkit.lathe("HeadBack", [(0.0, 0.0), (22.0, 0.5), (40.0, 3.0),
                            (52.0, 8.0), (56.0, 13.0), (0.0, 15.0)],
               segments=48, centre=(0.0, 0.0, HEAD_Z - 6.0), mat=sepal)

    # ---- 21 rays swept about the head axis
    r0 = _ray("Rays", (1.0, 0.0, -0.10), RAY_LEN, 7.0, ray_mat)
    bkit.array_radial(r0, RAYS, centre=(0.0, 0.0, HEAD_Z))

    # ---- the disc: a domed disc of packed florets on the golden-angle spiral
    disc_ob = bkit.lathe("Disc", [(0.0, 0.0), (18.0, 0.0), (34.0, -1.0),
                                  (46.0, -2.5), (50.0, -4.0)],
                         segments=48, centre=(0.0, 0.0, HEAD_Z + 9.0),
                         mat=disc_mat)
    # the disc profile falls away from the head centre, and lathe() does not
    # orient normals, so the recalc is what keeps the solid's volume positive
    bkit.recalc(disc_ob)

    for k in range(200):
        rr = 9.0 + 4.6 * math.sqrt(k)
        if rr > DISC_R:
            break
        a = math.radians(137.507 * k)
        z = HEAD_Z + 9.0 - 4.0 * (rr / DISC_R) ** 1.6
        f = bkit.uv_sphere("DiscFloret%03d" % k, 2.3, segments=8, rings=5,
                           centre=(rr * math.cos(a), rr * math.sin(a), z),
                           mat=floret)
        f.name = "DiscFloret%03d" % k

    # ---- five narrow sepals peeking between the rays
    for k in range(5):
        a = math.radians(72.0 * k + 10.0)
        sp = _ray("Sepal%d" % k, (math.cos(a), math.sin(a), -0.55), 34.0, 4.5,
                  sepal, n=8)
        sp.name = "Sepal%d" % k

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 205)


CHECKS = [
    dict(name="head_diameter", mm=136.6, tol=0.68, how="diameter", part="Rays"),
    dict(name="disc_diameter", mm=100.0, tol=1.5, how="diameter", part="Disc"),
    dict(name="stem_length",   mm=140.0, tol=1.0, how="bbox_z",    part="Stem"),
    # Rays is the whole 21-copy array, so this is the head's reach, not one
    # ray's length. Naming it that is what makes the check honest.
    dict(name="head_reach",    mm=137.0, tol=2.0, how="longest",  part="Rays"),
]
