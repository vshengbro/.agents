"""
incense_burner -- tripod bronze censer, 168 mm across and 156 mm tall.

A censer is a turned bowl with THREE feet, two loop handles and a pierced lid.
The turned bowl is one closed lathe profile with a real wall; the pierced lid is
a `perforated_panel` collar under a domed cap; the three feet and the two
handles come off `array_radial` about the bowl's own axis, not the world origin.

The feet's soles are z = 0.
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
    bowl_diameter=168.0,
    bowl_wall=5.0,
    bowl_height=74.0,
    foot_height=58.0,
    foot_count=3,
    handle_height=56.0,
    rim_diameter=178.0,
    lid_hole_diameter=8.0,
    finial_height=26.0,
    overall_height=196.0,
)

CHECKS = [
    dict(name="bowl_diameter", mm=168.0, tol=1.5, how="diameter",
         part="CenserBowl"),
    dict(name="rim_diameter", mm=178.0, tol=1.5, how="diameter",
         part="CenserRim"),
    dict(name="foot_height", mm=58.0, tol=1.5, how="bbox_z", part="CenserFoot0"),
    dict(name="handle_height", mm=56.0, tol=2.0, how="bbox_z",
         part="CenserHandle0"),
    dict(name="finial_height", mm=26.0, tol=1.5, how="bbox_z",
         part="CenserFinial"),
    dict(name="overall_height", mm=196.0, tol=2.5, how="top_z", part=None),
]

R_OUT = SPEC["bowl_diameter"] / 2.0
R_IN = R_OUT - SPEC["bowl_wall"]
BH = SPEC["bowl_height"]
FH = SPEC["foot_height"]
LID_Z = FH + BH


def build():
    bronze = R.patina("CenserBronze", base=(0.28, 0.33, 0.27), rough=0.42)
    gold = R.gild("CenserGold", base=(0.88, 0.70, 0.32))

    # ---- three turned feet, arrayed about the bowl axis -------------------
    foot = R.turned_leg("CenserFoot0", FH, 11.0, 9.0, 6.0, segments=20,
                        mat=bronze)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = foot
    foot.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    foot.select_set(False)
    foot.location = bkit.v(R_OUT * 0.62, 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.array_radial(foot, SPEC["foot_count"], axis="Z",
                      centre=(0.0, 0.0, 0.0))

    # ---- the bowl: one closed profile, real wall, real cavity -------------
    prof = [(0.0, 0.0), (R_OUT * 0.40, 0.0), (R_OUT * 0.44, 12.0),
            (R_OUT * 0.86, BH * 0.42), (R_OUT, BH * 0.88), (R_OUT, BH),
            (R_IN, BH), (R_IN, BH * 0.30), (R_IN * 0.40, 16.0), (0.0, 16.0)]
    bowl = bkit.lathe("CenserBowl", prof, segments=56, cap_ends=True,
                      mat=bronze)
    bkit.move(bowl, 0.0, 0.0, FH)
    bkit.tube("CenserRim", R_OUT + 5.0, R_IN - 2.0, 10.0, segments=56,
              centre=(0.0, 0.0, FH + BH - 3.0), mat=gold)

    # ---- two loop handles on a radial array ------------------------------
    handle = bkit.arc_torus("CenserHandle0", 22.0, 6.0, -70.0, 250.0,
                            centre=(R_OUT - 2.0, 0.0, FH + BH * 0.62),
                            plane="YZ", seg_major=26, mat=gold)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = handle
    handle.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    handle.select_set(False)
    handle.location = bkit.v(0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.array_radial(handle, 2, axis="Z", centre=(0.0, 0.0, 0.0))

    # ---- pierced lid: a real perforated collar ----------------------------
    band = bkit.perforated_panel("CenserLidBand", 12, 2, 22.0, 22.0,
                                 SPEC["lid_hole_diameter"] / 2.0,
                                 22.0 * 12.0 / 12.0 * 1.02, 42.0, 5.0,
                                 mat=gold)
    band.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    band.location = bkit.v(0.0, 0.0, LID_Z + 18.0)
    bpy.context.view_layer.update()
    R.dome("CenserLid", R_OUT * 0.98, 40.0, 6.0, segments=56, mat=gold)
    bkit.move(bpy.data.objects["CenserLid"], 0.0, 0.0, LID_Z - 2.0)
    R.finial("CenserFinial", SPEC["finial_height"], 14.0, segments=24,
             mat=gold)
    bkit.move(bpy.data.objects["CenserFinial"], 0.0, 0.0, LID_Z + 38.0)

    return dict(spec=SPEC, parts=8)