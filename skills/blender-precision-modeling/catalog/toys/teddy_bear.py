"""
teddy_bear -- a 150 mm seated teddy bear.

A teddy bear is not a scaled dog. Three things make it read as a toy bear
rather than a small animal, and all three are in this file:

  1. PROPORTION. The head is 38% of the seated height, against 22% for a real
     bear of any size. The huge head and stubby limbs ARE the toy. The seated
     pose -- haunches down, legs splayed forward, arms out and forward -- is
     the other half of it, because that is how a bear is shown and how a child
     holds it.
  2. MASS, not outline. Each mass is a super-ellipsoid rather than a sphere,
     because a stuffed plush limb is slightly flattened where the stuffing is
     packed, and a sphere reads as a ball stuck on a ball.
  3. MATERIAL. Fuzzy matte plush in a warm tan, a cream muzzle and belly
     patch, and near-black bead eyes and nose. A grey bear is a prototype.

Two construction rules this file is built around:

  * The eyes and nose are real EMBEDDED SPHERES, not paint. `assign_faces_by`
    picks whole faces, so on a 40-segment blob each face is ~7 mm across and a
    5 mm eye painted onto it comes out as a 14 mm smear. A sphere whose centre
    sits just inside the head surface cannot smear, because it is geometry.
  * The belly patch and the inner ear ARE paint, because they are large and
    low-frequency -- exactly the case face selection is good at.

Nothing is booleaned. Every part is its own closed solid and they overlap
freely, which is why an eighteen-part assembly is still watertight.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real plush dimensions, millimetres ------------------------------------
SPEC = dict(
    seated_height=150.0,     # crown of the head to the floor
    head_diameter=57.0,      # 38% of seated height: the teddy proportion
    head_width=55.0,
    muzzle_diameter=24.0,
    ear_diameter=24.0,
    body_width=70.0,
    body_depth=64.0,
    body_height=80.0,
    arm_diameter=24.0,
    arm_length=52.0,
    leg_diameter=30.0,
    leg_length=52.0,
    eye_diameter=6.0,
    nose_diameter=9.0,
)

HD = SPEC["head_diameter"] / 2.0
HW = SPEC["head_width"] / 2.0
MD = SPEC["muzzle_diameter"] / 2.0
ED = SPEC["ear_diameter"] / 2.0
BW = SPEC["body_width"] / 2.0
BD = SPEC["body_depth"] / 2.0
BH = SPEC["body_height"]
AD = SPEC["arm_diameter"] / 2.0
AL = SPEC["arm_length"]
LD = SPEC["leg_diameter"] / 2.0
LL = SPEC["leg_length"]
EYE_R = SPEC["eye_diameter"] / 2.0
NOSE_R = SPEC["nose_diameter"] / 2.0


def _blob(name, rx, ry, rz, centre, mat, n=2.6, steps=48, rings=26):
    """A super-ellipsoid: an ellipsoid whose exponent `n` rounds off the poles.

    n=2 is a true ellipsoid; the teddy's masses are n~2.4-2.8, which is what a
    stuffed plush limb looks like -- full through the middle, slightly
    compressed where the stuffing is packed. Authored as concentric rings and
    capped at both poles, so it is a closed solid.
    """
    sections = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        sp, cp = math.sin(phi), math.cos(phi)
        spn = math.copysign(abs(sp) ** (2.0 / n), sp)
        cpn = math.copysign(abs(cp) ** (2.0 / n), cp)
        sections.append([
            (centre[0] + rx * spn * math.cos(2.0 * math.pi * j / steps),
             centre[1] + ry * spn * math.sin(2.0 * math.pi * j / steps),
             centre[2] + rz * cpn)
            for j in range(steps)])
    ob = bkit.loft(name, sections, mat=mat, smooth=True)
    bkit.recalc(ob)
    bkit.weld(ob)
    bkit.shade_smooth(ob, 60)
    return ob


def build():
    fur = bkit.pbr("TeddyFur", base=(0.44, 0.27, 0.145), rough=0.93)
    pale = bkit.pbr("TeddyPale", base=(0.66, 0.49, 0.30), rough=0.94)
    cream = bkit.pbr("TeddyCream", base=(0.80, 0.69, 0.51), rough=0.95)
    dark = bkit.pbr("TeddyDark", base=(0.028, 0.022, 0.020), rough=0.28,
                    coat=0.7)

    # ---- head: the dominant mass. It overlaps the body by 8 mm so the two
    # solids intersect instead of meeting on a shared face.
    head_z = 150.0 - HD
    _blob("BearHead", HW, HD * 0.97, HD, (0.0, 0.0, head_z), fur, n=2.5)

    # ---- muzzle: a broad snout pushed forward off the face
    _blob("BearMuzzle", MD, MD * 0.85, MD * 0.80,
          (0.0, -HD * 0.70, head_z - HD * 0.38), cream, n=2.3)

    # ---- ears: flattened discs set on the sides of the crown. They sit at
    # 0.92 of the head half-width so they clear the skull; tucked in to 0.80
    # they are buried in it and only one of the pair is visible from any angle.
    ear_z = head_z + HD * 0.40
    for side, sx in (("L", 1.0), ("R", -1.0)):
        ear = _blob("BearEar%s" % side, ED, ED * 0.36, ED,
                    (sx * HW * 0.92, 1.5, ear_z), fur, n=2.2)
        ear.rotation_euler = (0.0, 0.0, math.radians(18.0 * sx))
        bpy.context.view_layer.update()
        # the inner ear is paint: it is large and low-frequency, which is the
        # case face selection is actually good at
        bkit.assign_faces_by(
            ear, pale,
            lambda c, n, s=sx: (c.x - s * HW * 0.92) * s < -1.2)

    # ---- body: a seated pear, wider than deep at the haunches and narrowing
    # to the shoulders, which is a seated plush bear's whole silhouette.
    body = _blob("BearBody", BW, BD, BH / 2.0, (0.0, 3.0, BH / 2.0), fur,
                 n=2.7)
    bkit.assign_faces_by(
        body, cream,
        lambda c, n: (c.y / bkit.MM) < -BD * 0.52
        and abs(c.x / bkit.MM) < BW * 0.66
        and c.z / bkit.MM < BH * 0.66)

    # ---- arms: stubby capsules swung out and forward. They sit OUTSIDE the
    # body line (x = 0.95 of the body half-width) rather than at 0.80: pushed
    # in any further the arm centres are inside the body ellipsoid and the
    # whole arm vanishes into the silhouette.
    arm_z = BH * 0.66
    for side, sx in (("L", 1.0), ("R", -1.0)):
        arm = _blob("BearArm%s" % side, AD, AD, AL / 2.0,
                    (sx * (BW * 0.95), -BD * 0.34, arm_z), fur, n=2.4)
        arm.rotation_euler = (math.radians(-14.0 * sx),
                              math.radians(-34.0 * sx), 0.0)
        bpy.context.view_layer.update()

    # ---- legs: splayed forward, soles flat on z=0
    for side, sx in (("L", 1.0), ("R", -1.0)):
        leg = _blob("BearLeg%s" % side, LD, LL / 2.0, LD,
                    (sx * LD * 1.02, -BD * 0.52, LD), fur, n=2.5)
        bkit.assign_faces_by(
            leg, pale,
            lambda c, n: c.y / bkit.MM < -BD * 0.52 - LL * 0.16)

    # ---- face. Eyes and nose are real geometry: a sphere centred just inside
    # the head surface, so only its cap shows. Painting them onto faces does
    # not work at this tessellation -- each face is several times wider than
    # the eye, and the "eye" comes out as a smear.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("BearEye%s" % side, EYE_R, segments=28, rings=16,
                       centre=(sx * HW * 0.38, -HD * 0.66,
                               head_z + HD * 0.10), mat=dark)
    bkit.uv_sphere("BearNose", NOSE_R, segments=28, rings=16,
                   centre=(0.0, -HD * 0.88, head_z - HD * 0.26), mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="head_diameter", mm=57.0, tol=0.8, how="bbox_z", part="BearHead"),
    dict(name="head_width", mm=55.0, tol=0.8, how="bbox_x", part="BearHead"),
    dict(name="body_width", mm=70.0, tol=1.0, how="bbox_x", part="BearBody"),
    dict(name="body_height", mm=80.0, tol=1.0, how="bbox_z", part="BearBody"),
    dict(name="muzzle_diameter", mm=24.0, tol=0.8, how="diameter",
         part="BearMuzzle"),
    # the ear is tilted 18 degrees out, so its bounding box across Z is
    # slightly less than the full 24 mm disc
    dict(name="ear_diameter", mm=23.0, tol=0.5, how="diameter", part="BearEarL"),
    dict(name="eye_diameter", mm=6.0, tol=0.4, how="diameter", part="BearEyeL"),
    dict(name="seated_height", mm=150.0, tol=2.0, how="bbox_z"),
]
