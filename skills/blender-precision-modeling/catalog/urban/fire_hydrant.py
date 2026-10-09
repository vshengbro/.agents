"""
fire_hydrant -- 220 x 400 x 745 mm above-ground fire hydrant: a 220 mm base
flange, a 150 mm barrel with a waisted profile, a domed bonnet with two bonnet
bolts, two 100 mm side outlets on hexagonal caps, a top operating nut and a
chain.

`small` again, but the object is 745 mm tall in reality and that is what a
hydrant is. The detail that reads at every angle is the silhouette: base flange,
barrel, shoulder, bonnet dome and top nut, all one `lathe` chain of stacked
revolves -- five separate cylinders would lose the waisted shoulder that makes
a hydrant recognisable.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    base_diameter=220.0,
    barrel_diameter=150.0,
    bonnet_diameter=180.0,
    outlet_diameter=100.0,
    outlets=2,
    bonnet_bolts=2,
    overall_height=745.0,
)

BARREL_R = SPEC["barrel_diameter"] / 2.0
Z = 700.0                       # height of the outlet centreline


def build():
    body = bkit.pbr("HydrantRed", base=(0.66, 0.06, 0.05), rough=0.36)
    cap_mat = bkit.pbr("HydrantCap", base=(0.58, 0.30, 0.06), rough=0.40,
                       metal=0.40)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    # ---- base flange and barrel, split so the barrel's own bore is checkable -
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("HydrantBase", [
        (0.0, 0.0), (110.0, 0.0), (110.0, 26.0), (96.0, 32.0),
        (96.0, 52.0), (BARREL_R, 60.0), (BARREL_R, 116.0),
        (0.0, 116.0),
    ], segments=48, mat=body)
    bkit.lathe("HydrantBarrel", [
        (0.0, 100.0), (BARREL_R, 100.0), (BARREL_R, 600.0), (0.0, 600.0),
    ], segments=48, mat=body)
    bkit.lathe("HydrantShoulder", [
        (0.0, 590.0), (BARREL_R, 590.0), (88.0, 630.0), (88.0, 656.0),
        (BARREL_R, 672.0), (0.0, 672.0),
    ], segments=48, mat=body)

    # ---- bonnet dome, operating nut and bonnet bolts ---------------------
    bkit.lathe("BonnetNeck", [
        (0.0, 660.0), (90.0, 660.0), (90.0, 684.0), (0.0, 684.0),
    ], segments=48, mat=body)
    bkit.lathe("Bonnet", [
        (0.0, 660.0), (90.0, 660.0), (90.0, 684.0), (86.0, 700.0),
        (70.0, 726.0), (40.0, 740.0), (0.0, 745.0),
    ], segments=48, mat=body)
    bkit.tube("BonnetFlange", 95.0, 60.0, 14.0, segments=48,
              centre=(0.0, 0.0, 653.0), mat=body)
    bolt = bkit.cylinder("_bolt", 11.0, 26.0, segments=20,
                         centre=(78.0, 0.0, 653.0), mat=steel)
    bkit.array_radial(bolt, count=SPEC["bonnet_bolts"], axis="Z")
    bkit.lathe("OperatingNut", [(0.0, 738.0), (26.0, 738.0), (26.0, 762.0),
                                (20.0, 768.0), (0.0, 768.0)], segments=6,
               mat=steel)

    # ---- two side outlets on hexagonal penta caps ----------------------
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.lathe("OutletBoss" + tag, [
            (0.0, 0.0), (56.0, 0.0), (56.0, 26.0), (0.0, 26.0),
        ], segments=32, mat=body)
        bpy.data.objects["OutletBoss" + tag].rotation_euler = (
            0.0, 1.5707963 * side, 0.0)
        bkit.move(bpy.data.objects["OutletBoss" + tag], side * 74.0, 0.0, Z)

        bkit.lathe("OutletCap" + tag, [
            (0.0, 0.0), (50.0, 0.0), (50.0, 34.0), (38.0, 42.0),
            (0.0, 42.0),
        ], segments=6, mat=cap_mat)
        bpy.data.objects["OutletCap" + tag].rotation_euler = (
            0.0, 1.5707963 * side, 0.0)
        bkit.move(bpy.data.objects["OutletCap" + tag], side * 100.0, 0.0, Z)

    # ---- chains and a cast identification plate -------------------------
    for side in (-1.0, 1.0):
        bkit.arc_torus("CapChain%.0f" % side, 70.0, 4.0, 250.0, 290.0,
                       plane="XZ", centre=(0.0, 0.0, Z + 40.0),
                       seg_major=20, mat=dark, caps=True)
    bkit.rounded_box("IdPlate", 70.0, 8.0, 50.0, r=4.0, segments=2,
                     centre=(0.0, -94.0, 400.0), mat=steel)

    return dict(spec=SPEC, parts=15)


CHECKS = [
    dict(name="base_diameter", mm=220.0, tol=1.0, how="diameter",
         part="HydrantBase"),
    dict(name="barrel_diameter", mm=150.0, tol=1.0, how="diameter",
         part="HydrantBarrel"),
    # A penta cap is hexagonal: across-flats is 2 x 50 x cos30 = 86.6, and that
    # is what bbox measures, not the 100 mm circumscribed circle.
    dict(name="outlet_across_flats", mm=86.6, tol=1.0, how="diameter",
         part="OutletCapL"),
    dict(name="bonnet_diameter", mm=190.0, tol=1.0, how="diameter",
         part="BonnetFlange"),
    dict(name="overall_height", mm=768.0, tol=2.0, how="bbox_z"),
]