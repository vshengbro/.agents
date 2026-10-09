"""
ceremonial_mask -- carved cedar mask, 180 mm across with a feather crown.

A mask is a SHELL with a rim, not a solid: it is a `lathe` cut to a half-sphere
and hollowed, so the concave inside is a real cavity and the rim has a real
edge.  The ornament is then built on that shell: a brow band, two inset eyes, a
pierced cheek panel on each side (`perforated_panel`, the right recipe for a
pierced surface), a row of teeth, and a feather crown on a radial array.

The shell's lowest point is z = 0, so the mask stands on its own chin.
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
    height=115.2,
    width=180.0,
    shell_thickness=10.0,
    rim_diameter=190.0,
    eye_diameter=26.0,
    tooth_count=7,
    tooth_width=12.0,
    crown_ray_count=9,
    crown_ray_length=96.0,
    overall_height=123.2,
)

CHECKS = [
    dict(name="height", mm=115.2, tol=1.5, how="bbox_z", part="MaskShell"),
    dict(name="width", mm=180.0, tol=1.5, how="bbox_x", part="MaskShell"),
    dict(name="rim_diameter", mm=190.0, tol=1.5, how="diameter",
         part="MaskRim"),
    dict(name="eye_diameter", mm=26.0, tol=0.8, how="bbox_x", part="MaskEye0"),
    dict(name="tooth_count_width", mm=12.0, tol=0.6, how="bbox_x",
         part="MaskTooth0"),
    dict(name="crown_ray_length", mm=96.0, tol=2.0, how="bbox_z",
         part="MaskCrown"),
    dict(name="overall_height", mm=123.2, tol=2.0, how="top_z", part=None),
]

R_OUT = 90.0
WALL = SPEC["shell_thickness"]
R_IN = R_OUT - WALL


def build():
    wood = R.cedar("MaskCedar", base=(0.46, 0.24, 0.10), rough=0.44)
    paint = bkit.pbr("MaskPaint", base=(0.66, 0.14, 0.08), rough=0.38)
    shell_col = bkit.pbr("MaskShellCol", base=(0.86, 0.78, 0.52), rough=0.42)
    gold = R.gild("MaskGold")
    dark = bkit.pbr("MaskDark", base=(0.05, 0.04, 0.03), rough=0.32)

    # ---- the shell: a closed revolved profile with a real cavity ---------
    H_OUT = R_OUT * 1.28
    prof = [(0.0, 0.0), (R_OUT * 0.42, 0.0), (R_OUT, R_OUT * 0.55),
            (R_OUT, H_OUT), (R_IN, H_OUT),
            (R_IN, R_IN * 0.72), (R_IN * 0.46, R_IN * 0.30), (0.0, 0.0)]
    sh = bkit.lathe("MaskShell", prof, segments=48, cap_ends=False, mat=wood)
    bkit.recalc(sh)

    # ---- rim: a real band around the opening, so the shell has thickness -
    bkit.tube("MaskRim", R_OUT + 5.0, R_OUT - 3.0, 16.0, segments=48,
              centre=(0.0, 0.0, H_OUT), mat=paint)

    # ---- brow, eyes, nose, mouth ----------------------------------------
    bkit.rounded_box("MaskBrow", 176.0, 34.0, 30.0, r=12.0, segments=3,
                     centre=(0.0, R_OUT * 0.72, H_OUT * 0.80), mat=paint)
    for i, x in enumerate((-38.0, 38.0)):
        eye = bkit.lathe("MaskEye%d" % i,
                         [(0.0, 0.0), (13.0, 0.0), (13.0, 10.0), (0.0, 10.0)],
                         segments=28, centre=(0, 0, 0), mat=gold)
        bkit.place(eye, (x, R_OUT * 0.70, H_OUT * 0.70), "Y")
        bkit.uv_sphere("MaskPupil%d" % i, 8.0, segments=16, rings=10,
                       centre=(x, R_OUT * 0.80, H_OUT * 0.70), mat=dark)
    bkit.rounded_box("MaskNose", 26.0, 70.0, 66.0, r=10.0, segments=3,
                     centre=(0.0, R_OUT * 0.86, H_OUT * 0.52), mat=wood)
    bkit.rounded_box("MaskMouth", 96.0, 30.0, 46.0, r=10.0, segments=3,
                     centre=(0.0, R_OUT * 0.78, H_OUT * 0.30), mat=dark)

    # ---- teeth: counted layout, never hand-placed ------------------------
    for i, (x, w) in enumerate(bkit.lay_out([SPEC["tooth_width"]] * 7,
                                            gap=8.0)):
        bkit.rounded_box("MaskTooth%d" % i, w, 20.0, 34.0, r=4.0, segments=2,
                         centre=(x, R_OUT * 0.82, H_OUT * 0.30), mat=shell_col)

    # ---- pierced cheek panels: one real perforated mesh per side ---------
    for i, s in enumerate((1, -1)):
        p = bkit.perforated_panel("MaskCheek%d" % i, 3, 4, 13.0, 13.0, 3.6,
                                  39.0, 52.0, 5.0, mat=paint)
        p.rotation_euler = (0.0, math.radians(72.0 * s), 0.0)
        p.location = bkit.v(s * R_OUT * 0.72, R_OUT * 0.22, H_OUT * 0.46)
        bpy.context.view_layer.update()

    # ---- feather crown on a radial array about the crown centre ----------
    R.ray_crown("MaskCrown", 96.0, SPEC["crown_ray_count"],
                SPEC["crown_ray_length"], 26.0, mat=gold,
                centre=(0.0, 0.0, H_OUT - 6.0))

    return dict(spec=SPEC, parts=23)