"""
doll -- a 150 mm standing cloth doll: lathed dress, moulded head, jointed arms.

A doll is a lathe plus a sphere, and the lathe is the whole trick. A child's
dress is a surface of REVOLUTION: it flares from the waist to the hem in a
smooth bell, it is rotationally symmetric about the body axis, and it is the
single largest mass in the model. Building it as a cone or a stack of
cylinders gives a lampshade; building it as one lathed profile from the waist
line out over the hem and back up the inside gives a real dress with a real
thickness at the hem.

The head is a separate moulded mass with painted hair as a second material on
the same solid, the eyes as a third, and the arms as swept capsules with a
visible shoulder ball -- the jointed arm is what separates a doll from a
mannequin. Nothing is booleaned: every part is its own closed solid and they
overlap freely, which is why a sixteen-part assembly is still watertight.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    overall_height=150.0,
    head_diameter=34.0,
    head_height=38.0,
    neck_diameter=13.0,
    torso_height=42.0,
    waist_diameter=30.0,
    hip_diameter=40.0,
    dress_waist_diameter=32.0,
    dress_hem_diameter=64.0,
    dress_height=62.0,
    arm_diameter=11.0,
    arm_length=38.0,
    leg_diameter=13.0,
    leg_length=26.0,
    eye_diameter=5.0,
)

H = SPEC["overall_height"]
HD = SPEC["head_diameter"] / 2.0
HH = SPEC["head_height"]
ND = SPEC["neck_diameter"] / 2.0
TORS = SPEC["torso_height"]
WA = SPEC["waist_diameter"] / 2.0
HIP = SPEC["hip_diameter"] / 2.0
DW = SPEC["dress_waist_diameter"] / 2.0
DH = SPEC["dress_hem_diameter"] / 2.0
DRE_H = SPEC["dress_height"]
AD = SPEC["arm_diameter"] / 2.0
AL = SPEC["arm_length"]
LD = SPEC["leg_diameter"] / 2.0
LL = SPEC["leg_length"]
EYE_R = SPEC["eye_diameter"] / 2.0


def build():
    skin = bkit.pbr("DollSkin", base=(0.88, 0.72, 0.60), rough=0.42, coat=0.3)
    hair = bkit.pbr("DollHair", base=(0.30, 0.14, 0.06), rough=0.34, coat=0.5)
    dress = bkit.preset("red_paint")
    petticoat = bkit.pbr("DollPetticoat", base=(0.93, 0.90, 0.84), rough=0.55)
    socks = bkit.preset("white_plastic")
    shoes = bkit.preset("blue_paint")
    eye = bkit.pbr("DollEye", base=(0.05, 0.06, 0.10), rough=0.18, coat=0.8)

    # ---- dress: one lathe. Walk out along the waist, down and out along the
    # bell to the hem, back up the inside, and close across the hem thickness.
    # That last return is what gives the hem a real 2 mm edge instead of a
    # zero-thickness cone.
    hem_z = 1.0
    waist_z = hem_z + DRE_H
    prof = [
        (0.0, waist_z),              # waist centre, capped
        (DW * 0.52, waist_z),
        (DW, waist_z - 2.0),         # waistband
        (DW + 3.0, waist_z - 9.0),
        (HIP * 0.86, waist_z - 22.0),
        (HIP * 1.18, waist_z - 34.0),
        (DH - 3.0, hem_z + 4.5),
        (DH, hem_z + 2.0),           # outer hem
        (DH - 2.0, hem_z),           # hem thickness
        (DH - 5.0, hem_z + 1.2),     # back up the inside
        (HIP * 1.10, waist_z - 33.0),
        (HIP * 0.80, waist_z - 20.0),
        (DW - 1.0, waist_z - 6.0),
        (0.0, waist_z - 6.0),        # inner waist, capped
    ]
    body = bkit.lathe("Dress", prof, segments=64, mat=dress)
    bkit.recalc(body)
    bkit.shade_smooth(body, 36)
    # a white petticoat shows below the hem line on a real doll's dress
    bkit.assign_faces_by(
        body, petticoat,
        lambda c, n: c.z / bkit.MM < hem_z + 7.0)

    # ---- torso: the bodice above the waist, a lathed barrel
    bodice_prof = [
        (0.0, waist_z - 4.0),
        (DW - 0.6, waist_z - 4.0),
        (DW + 1.4, waist_z + 6.0),
        (DW + 2.6, waist_z + 18.0),
        (ND + 1.0, waist_z + TORS - 2.0),
        (ND, waist_z + TORS),
        (0.0, waist_z + TORS),
    ]
    bodice = bkit.lathe("Bodice", bodice_prof, segments=56, mat=dress)
    bkit.recalc(bodice)
    bkit.shade_smooth(bodice, 36)

    # ---- neck and head
    neck = bkit.cylinder("Neck", ND, 10.0, segments=28,
                         centre=(0.0, 0.0, waist_z + TORS + 3.0), mat=skin)
    bkit.shade_smooth(neck, 40)

    head_z = waist_z + TORS + 8.0 + HH / 2.0
    head = bkit.uv_sphere("Head", HD, segments=48, rings=28,
                          centre=(0.0, 0.0, head_z), mat=skin)
    # hair: a second material on the head, selected by height, so it follows
    # the moulded surface exactly. A separate hair shell would z-fight.
    bkit.assign_faces_by(
        head, hair,
        lambda c, n: c.z / bkit.MM > head_z + HD * 0.10
        or (c.y / bkit.MM) > HD * 0.45)
    # eyes: painted on, lying in the surface
    eyes = [(sx * HD * 0.38, -HD * 0.80, head_z + HD * 0.12)
            for sx in (1.0, -1.0)]

    def _eye_pred(centre, normal):
        p = (centre.x / bkit.MM, centre.y / bkit.MM, centre.z / bkit.MM)
        for e in eyes:
            if math.sqrt(sum((p[i] - e[i]) ** 2 for i in range(3))) < EYE_R * 1.5:
                return True
        return False
    bkit.assign_faces_by(head, eye, _eye_pred)

    # ---- arms: a shoulder ball, an upper arm and a forearm, so the joint is
    # visible. The jointed arm is the cue that says "doll" and not "figure".
    sh_z = waist_z + TORS - 8.0
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Shoulder%s" % side, AD * 1.15, segments=24, rings=14,
                       centre=(sx * (DW + 1.0), 0.0, sh_z), mat=dress)
        upper = bkit.cylinder("ArmUpper%s" % side, AD, AL * 0.52, segments=24,
                              centre=(sx * (DW + 2.6), 0.0, sh_z - AL * 0.30),
                              mat=skin)
        bkit.shade_smooth(upper, 40)
        bkit.uv_sphere("Elbow%s" % side, AD * 0.96, segments=24, rings=14,
                       centre=(sx * (DW + 2.6), 0.0, sh_z - AL * 0.55),
                       mat=skin)
        fore = bkit.cylinder("ArmLower%s" % side, AD * 0.86, AL * 0.44,
                             segments=24,
                             centre=(sx * (DW + 2.2), -1.6,
                                     sh_z - AL * 0.80), mat=skin)
        fore.rotation_euler = (math.radians(9.0), 0.0, 0.0)
        bpy.context.view_layer.update()
        bkit.shade_smooth(fore, 40)
        bkit.uv_sphere("Hand%s" % side, AD * 0.92, segments=20, rings=12,
                       centre=(sx * (DW + 2.0), -2.6, sh_z - AL * 1.04),
                       mat=skin)

    # ---- legs: short, mostly hidden by the hem, with a shoe that reads
    for side, sx in (("L", 1.0), ("R", -1.0)):
        leg = bkit.cylinder("Leg%s" % side, LD, LL, segments=24,
                            centre=(sx * 9.0, 0.0, hem_z + LL / 2.0 + 0.6),
                            mat=socks)
        bkit.shade_smooth(leg, 40)
        bkit.uv_sphere("Shoe%s" % side, 7.0, segments=24, rings=14,
                       centre=(sx * 9.0, -3.2, 5.4), mat=shoes)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="overall_height", mm=150.6, tol=1.5, how="bbox_z"),
    dict(name="head_diameter", mm=34.0, tol=0.5, how="diameter", part="Head"),
    dict(name="dress_hem_diameter", mm=64.0, tol=0.8, how="diameter",
         part="Dress"),
    dict(name="dress_height", mm=62.0, tol=0.8, how="bbox_z", part="Dress"),
    dict(name="upper_arm_length", mm=19.8, tol=0.6, how="bbox_z",
         part="ArmUpperL"),
    dict(name="leg_length", mm=26.0, tol=0.6, how="bbox_z", part="LegL"),
]
