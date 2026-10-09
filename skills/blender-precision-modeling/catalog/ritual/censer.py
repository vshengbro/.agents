"""
censer -- hanging temple censer: a pierced bronze ball on a three-link chain.

A censer differs from an incense burner in one decisive way: it is PERFORATED
all over, because smoke has to escape through the shell rather than through a
lid.  So the body is three pierced bands stacked on the vertical axis, each one
a real `perforated_panel` rolled onto a cylinder, capped by a turned cap and a
finial, and hung from a three-link chain on a radial array.

The chain's bottom link touches z = 0, which is where the censer hangs from.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R

SPEC = dict(
    body_diameter=120.0,
    body_height=132.0,
    hole_diameter=10.0,
    band_count=3,
    link_count=3,
    link_length=54.0,
    cap_diameter=64.0,
    finial_height=30.0,
    overall_height=336.0,
)

CHECKS = [
    dict(name="body_diameter", mm=120.0, tol=1.5, how="diameter",
         part="CenserBody0"),
    dict(name="body_height", mm=132.0, tol=2.0, how="z_max",
         part="CenserBody2"),
    dict(name="link_length", mm=54.0, tol=2.0, how="bbox_z",
         part="CenserLink0"),
    dict(name="cap_diameter", mm=64.0, tol=1.0, how="diameter",
         part="CenserCap"),
    dict(name="finial_height", mm=30.0, tol=1.5, how="bbox_z",
         part="CenserFinial"),
    dict(name="overall_height", mm=336.0, tol=3.0, how="top_z", part=None),
]

R_OUT = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]
CH = SPEC["link_length"]


def build():
    bronze = R.patina("CenserBronze", base=(0.26, 0.31, 0.25), rough=0.40)
    gold = R.gild("CenserGold", base=(0.86, 0.68, 0.30))
    cord = bkit.pbr("CenserCord", base=(0.52, 0.44, 0.30), rough=0.86)

    # ---- chain: three links, each on its own turn -----------------------
    for i in range(SPEC["link_count"]):
        z = i * CH
        link = bkit.arc_torus("CenserLink%d" % i, CH * 0.30, 5.0, 0.0, 360.0,
                              centre=(0.0, 0.0, z + CH * 0.5), plane="XY",
                              seg_major=28, mat=gold)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = link
        link.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                       scale=True)
        link.select_set(False)
        link.location = bkit.v(0.0, 0.0, 0.0)
        bpy.context.view_layer.update()
        link.rotation_euler = (math.radians(90.0), 0.0,
                               0.0 if i % 2 == 0 else math.radians(90.0))

    # ---- the pierced body: three rolled perforated bands ----------------
    band_h = BH / SPEC["band_count"]
    for i in range(SPEC["band_count"]):
        z0 = SPEC["link_count"] * CH + i * band_h
        b = bkit.perforated_panel("CenserBody%d" % i, 14, 2, 26.0, 26.0,
                                  SPEC["hole_diameter"] / 2.0,
                                  26.0 * 1.02, band_h * 0.92, 6.0, mat=bronze)
        b.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        b.location = bkit.v(0.0, 0.0, z0 + band_h / 2.0)
        bpy.context.view_layer.update()

    # ---- caps ------------------------------------------------------------
    zbody = SPEC["link_count"] * CH
    bkit.lathe("CenserTopCap",
               [(0.0, 0.0), (R_OUT * 0.46, 0.0), (R_OUT * 0.48, 14.0),
                (R_OUT * 0.86, 26.0), (R_OUT * 0.86, 32.0), (0.0, 32.0)],
               segments=48, centre=(0.0, 0.0, zbody - 34.0), mat=gold)
    bkit.lathe("CenserBottomCap",
               [(0.0, 0.0), (R_OUT * 0.86, 0.0), (R_OUT * 0.86, 10.0),
                (R_OUT * 0.48, 24.0), (R_OUT * 0.46, 38.0), (0.0, 38.0)],
               segments=48, centre=(0.0, 0.0, zbody + BH), mat=gold)
    R.finial("CenserFinial", SPEC["finial_height"], 15.0, segments=24,
             mat=gold)
    bkit.move(bpy.data.objects["CenserFinial"], 0.0, 0.0, zbody + BH + 36.0)

    # ---- suspension ring -------------------------------------------------
    bkit.torus("CenserRing", 16.0, 4.0, seg_major=32, seg_minor=12,
               centre=(0.0, 0.0, SPEC["link_count"] * CH), mat=gold)
    R.rope("CenserTail", (0.0, 0.0, SPEC["link_count"] * CH + 16.0),
           (0.0, 0.0, SPEC["link_count"] * CH - 30.0), 3.0, mat=cord)

    return dict(spec=SPEC, parts=11)