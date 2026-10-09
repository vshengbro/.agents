"""
tablet -- 240 x 170 x 8.0 mm 10.2" slate.

Same construction reasoning as the phone, scaled: a 2D rounded-rectangle
outline extruded, because the 18 mm corner radius a tablet shows is again
impossible with a thickness-clamped uniform bevel. Speaker grilles are the
repeated feature here, so both rows come from one `array_linear` cutter and a
single boolean each -- twelve hand-placed holes would be twelve solver
invocations and one shared risk of a destroyed body.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=240.0,
    width=170.0,
    height=8.0,
    corner_radius=18.0,
    grille_holes=6,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
R = SPEC["corner_radius"]
NH = SPEC["grille_holes"]


def build():
    body_mat = bkit.pbr("TabletBody", base=(0.34, 0.35, 0.38), rough=0.26,
                        coat=0.3)
    glass = bkit.pbr("TabletGlass", base=(0.030, 0.033, 0.042), rough=0.06,
                     coat=0.8)
    lens = bkit.pbr("TabletLens", base=(0.045, 0.048, 0.055), rough=0.10,
                    coat=0.9)
    btn_mat = bkit.pbr("TabletButton", base=(0.55, 0.56, 0.58), rough=0.36)

    body = bkit.extrude_profile(
        "TabletBody", bkit.rounded_rect_section(L, W, R),
        H, centre=(0, 0, H / 2.0), mat=body_mat)
    bkit.bevel(body, 0.6, segments=2)

    # ---- 10.2" display in a 1.8 mm recess --------------------------------
    bkit.extrude_profile(
        "TabletScreen", bkit.rounded_rect_section(L - 18.0, W - 18.0, R - 4.0),
        1.4, centre=(0, 0, 7.1), mat=glass)
    cut = bkit.extrude_profile(
        "_scr", bkit.rounded_rect_section(L - 17.0, W - 17.0, R - 4.0),
        3.0, centre=(0, 0, 7.8))
    bkit.boolean(body, cut, "DIFFERENCE")

    # ---- front camera: a dark disc proud of the glass --------------------
    bkit.cylinder("TabletCamera", 2.4, 0.5, segments=32,
                  centre=(0.0, W / 2.0 - 24.0, 7.9), mat=lens)

    # ---- two speaker grilles, one arrayed cutter per side ----------------
    for side in (1, -1):
        hole = bkit.cylinder("_g", 0.95, 6.0, segments=20,
                             centre=(-L / 2.0 + 9.0, side * 58.0, 4.0))
        bkit.array_linear(hole, count=NH, offset_mm=(2.4, 0, 0))
        bkit.boolean(body, hole, "DIFFERENCE")

    # ---- volume rocker + power key, one computed row ---------------------
    keys = []
    for i, (x, w) in enumerate(bkit.lay_out([14.0, 22.0], gap=8.0)):
        keys.append(bkit.rounded_box(
            "_k%d" % i, w, 2.4, 3.2, r=0.8,
            centre=(x, W / 2.0 - 0.3, 4.6), mat=btn_mat))
    bkit.join(keys, name="TabletButtons")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="length", mm=240.0, tol=0.6, how="bbox_x", part="TabletBody"),
    dict(name="width", mm=170.0, tol=0.6, how="bbox_y", part="TabletBody"),
    dict(name="height", mm=8.0, tol=0.4, how="bbox_z", part="TabletBody"),
]
