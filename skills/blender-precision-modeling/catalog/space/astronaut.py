"""
astronaut -- an EMU spacesuit figure on the surface: 1.88 m tall in a suit,
standing with a slight A-stance.

Size class `large` (600..3000 mm). The real object is an Extravehicular
Mobility Unit: a person inside a pressure garment, a life-support backpack
and a gold-visored helmet. What carries the read is the SILHOUETTE, so this is
built as proportions rather than as an anatomy:

- the helmet is a sphere with a real neck ring, not a ball on a stick,
- the PLSS backpack is wider than the torso and stands off the back,
- the joints have real bulk (bearings, ELBOW rings) because a slim
  mannequin reads as a mannequin,
- the boots are square, wide and heavy: Apollo EVA boots are unmistakable.

Limbs are lofted tapered tubes, which keeps them single watertight solids
with no seam, and every segment overlaps its neighbour by a joint's worth.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=1880.0,
    helmet_diameter=340.0,
    torso_width=560.0,
    backpack_width=620.0,
    backpack_depth=300.0,
    boot_length=400.0,
)

HT = SPEC["overall_height"]
HD = SPEC["helmet_diameter"]
TW = SPEC["torso_width"]
BKW = SPEC["backpack_width"]
BKD = SPEC["backpack_depth"]


def _limb(name, sections, mat):
    """Tapered tube from a list of (x, y, z, radius) keypoints -> one solid."""
    rings = []
    for (x, y, z, r) in sections:
        ring = bkit.superellipse_section(r * 2.0, r * 2.0, n=2.6, steps=20)
        rings.append([(px + x, py + y, z) for (px, py) in ring])
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    white = bkit.pbr("SuitWhite", base=(0.88, 0.87, 0.84), rough=0.44)
    beta = bkit.pbr("SuitBetaCloth", base=(0.78, 0.77, 0.74), rough=0.62)
    joint = bkit.pbr("SuitJoint", base=(0.52, 0.52, 0.51), rough=0.48)
    gold = bkit.pbr("VisorGold", base=(0.92, 0.74, 0.24), metal=0.85, rough=0.10)
    dark = bkit.pbr("SuitDark", base=(0.16, 0.16, 0.17), rough=0.55)

    # ---- legs: the mass of the figure, and the widest part of it ---------
    for (side, sign) in (("L", 1.0), ("R", -1.0)):
        x = sign * TW * 0.19
        hip_z, knee_z, ankle_z = HT * 0.50, HT * 0.27, HT * 0.075
        _limb("Thigh" + side, [
            (x, 0.0, hip_z + 40.0, TW * 0.215),
            (x, 0.0, hip_z - 60.0, TW * 0.190),
            (x * 1.06, 0.0, knee_z + 90.0, TW * 0.155),
            (x * 1.10, 0.0, knee_z, TW * 0.140),
        ], beta)
        # knee bearing: the visible joint hardware
        bkit.cylinder("Knee" + side, TW * 0.145, 190.0, segments=20,
                      centre=(x * 1.10, 0.0, knee_z), axis="X",
                      smooth=True, mat=joint)
        _limb("Shin" + side, [
            (x * 1.10, 0.0, knee_z - 10.0, TW * 0.135),
            (x * 1.12, 0.0, knee_z - 150.0, TW * 0.120),
            (x * 1.10, 0.0, ankle_z + 30.0, TW * 0.112),
        ], beta)

        # ---- boot: square, heavy, unmistakable -------------------------
        bkit.rounded_box("Boot" + side, 190.0, SPEC["boot_length"], 160.0,
                         r=30.0,
                         centre=(x * 1.10, 60.0, 82.0), mat=white)
        sole = bkit.rounded_box("BootSole" + side, 200.0, SPEC["boot_length"] + 20.0,
                                40.0, r=14.0,
                                centre=(x * 1.10, 60.0, 20.0), mat=dark)

    # ---- torso: wider than a person, because it is a pressure garment ---
    # TW wide, not TW*0.78: the limbs stand off at TW*0.44 on each side, so a
    # narrower torso makes the declared shoulder width unmeasurable on the
    # torso part itself.
    torso = bkit.rounded_box("Torso", TW, 360.0, HT * 0.30, r=90.0,
                             centre=(0.0, 0.0, HT * 0.645), mat=white)
    # suit waist bearing
    bkit.cylinder("WaistBearing", TW * 0.36, 120.0, segments=24,
                  centre=(0.0, 0.0, HT * 0.505), axis="Z", smooth=True,
                  mat=joint)

    # ---- PLSS backpack: stands off the back, wider than the torso -------
    pack = bkit.rounded_box("PLSS", BKW, BKD, HT * 0.34, r=50.0,
                            centre=(0.0, -(180.0 + BKD / 2.0), HT * 0.66),
                            mat=white)
    # consumables tanks on the pack face
    for i, dx in enumerate((-190.0, 190.0)):
        bkit.cylinder("PLSS_Tank%d" % (i + 1), 95.0, HT * 0.28, segments=20,
                      centre=(dx, -(180.0 + BKD + 30.0), HT * 0.66),
                      smooth=True, mat=beta)

    # ---- arms: upper arm, elbow, forearm, glove -------------------------
    for (side, sign) in (("L", 1.0), ("R", -1.0)):
        x = sign * TW * 0.44
        sh_z, el_z = HT * 0.775, HT * 0.585
        bkit.rounded_box("Shoulder" + side, 130.0, 260.0, 190.0, r=50.0,
                         centre=(x * 0.94, 0.0, sh_z + 20.0), mat=white)
        _limb("UpperArm" + side, [
            (x * 0.92, 0.0, sh_z + 20.0, TW * 0.150),
            (x * 1.06, 0.0, sh_z - 90.0, TW * 0.135),
            (x * 1.12, 0.0, el_z + 90.0, TW * 0.122),
        ], white)
        bkit.cylinder("Elbow" + side, TW * 0.122, 150.0, segments=20,
                      centre=(x * 1.12, 0.0, el_z), axis="X", smooth=True,
                      mat=joint)
        _limb("Forearm" + side, [
            (x * 1.12, 0.0, el_z - 10.0, TW * 0.118),
            (x * 1.10, 20.0, el_z - 170.0, TW * 0.104),
            (x * 1.06, 40.0, el_z - 260.0, TW * 0.098),
        ], white)
        bkit.rounded_box("Glove" + side, 110.0, 150.0, 190.0, r=40.0,
                         centre=(x * 1.06, 55.0, el_z - 350.0), mat=dark)

    # ---- neck ring, helmet, gold visor --------------------------------
    # The helmet's CENTRE is placed so its crown lands exactly on HT. Placing
    # it at a fraction of HT and hoping the sphere adds the rest left the
    # figure 76 mm under its declared height.
    HELMET_Z = HT - HD / 2.0
    ring = bkit.tube("NeckRing", HD * 0.36, HD * 0.26, 90.0, segments=32,
                     centre=(0.0, 0.0, HELMET_Z - HD * 0.34), mat=joint)
    helmet = bkit.uv_sphere("Helmet", HD / 2.0, segments=40, rings=24,
                            centre=(0.0, 0.0, HELMET_Z))
    bkit.assign(helmet, white)
    # visor: a flattened cap over the front of the same solid, gold-coated
    # Large and pushed well FORWARD: at HD*0.44 centred 0.30 HD back, the gold
    # only showed as a sliver past the shell and the figure read as a
    # featureless white snowman.
    visor = bkit.uv_sphere("Visor", HD * 0.50, segments=36, rings=20,
                           centre=(0.0, -HD * 0.40, HELMET_Z - HD * 0.02))
    visor.scale = (0.98, 0.72, 0.80)
    bkit.apply_mods(visor)
    bkit.assign(visor, gold)
    # sunshade: the visor peak
    bkit.rounded_box("Sunshade", HD * 0.92, 100.0, 44.0, r=16.0,
                     centre=(0.0, -HD * 0.42, HELMET_Z + HD * 0.24),
                     mat=white)

    # ---- chest control module ------------------------------------------
    ccm = bkit.rounded_box("ChestModule", 240.0, 130.0, 170.0, r=26.0,
                           centre=(0.0, -190.0, HT * 0.70), mat=dark)

    return dict(spec=SPEC, parts=6 + 2 + 2 + 1 + 1 + 2 + 8 + 4 + 1)


CHECKS = [
    dict(name="overall_height", mm=1880.0, tol=8.0, how="bbox_z"),
    dict(name="helmet_diameter", mm=340.0, tol=4.0, how="diameter", part="Helmet"),
    dict(name="torso_width", mm=560.0, tol=30.0, how="bbox_x", part="Torso"),
    dict(name="backpack_width", mm=620.0, tol=2.0, how="bbox_x", part="PLSS"),
    dict(name="boot_length", mm=400.0, tol=4.0, how="bbox_y", part="BootL"),
    dict(name="overall_width", mm=700.0, tol=20.0, how="bbox_x"),
]