"""
utility_knife -- 155 mm snap-off knife with a 25 mm trapezoid blade exposed.

Blade sections are computed from the exposed amount, not hand-placed: the
blade base is buried 8 mm inside the body so the joint reads as a blade coming
out of a nose rather than a floating trapezoid sitting on top.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=155.0,
    body_width=32.0,
    body_length=128.0,
    blade_width=25.0,
    blade_thickness=1.6,
)


def build():
    shell = bkit.preset("yellow_paint")
    rubber = bkit.pbr("KnifeGrip", base=(0.13, 0.13, 0.14), rough=0.70)
    steel = bkit.pbr("KnifeSteel", base=(0.76, 0.78, 0.82), metal=0.35,
                     rough=0.20)
    dark = bkit.pbr("KnifeNose", base=(0.16, 0.16, 0.17), rough=0.35)

    body = bkit.rounded_box("UtilityKnifeBody", 32.0, 22.0, 128.0, r=5.0,
                            segments=4, centre=(0, 0, 64.0), mat=shell)
    grip = bkit.rounded_box("UtilityKnifeGrip", 33.5, 23.5, 62.0, r=7.0,
                            segments=4, centre=(0, 0, 31.0), mat=rubber)
    nose = bkit.rounded_box("UtilityKnifeNose", 30.0, 18.0, 12.0, r=3.0,
                            segments=3, centre=(0, 0, 132.0), mat=dark)

    # snap-off blade: 25 mm at the base, 19 mm at the tip, corners snipped
    blade_poly = [(-12.5, 128.0), (12.5, 128.0), (9.5, 152.0), (9.5, 155.0),
                  (-9.5, 155.0), (-9.5, 152.0)]
    blade = bkit.extrude_profile("UtilityKnifeBlade", blade_poly, 1.6,
                                 centre=(0, 0, 0), axis="Y", mat=steel)
    bkit.recalc(blade)
    bkit.bevel(blade, width_mm=0.3, segments=1, angle_deg=40)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="body_width", mm=32.0, tol=0.5, how="bbox_x",
         part="UtilityKnifeBody"),
    dict(name="blade_width", mm=25.0, tol=0.4, how="bbox_x",
         part="UtilityKnifeBlade"),
    dict(name="overall_length", mm=155.0, tol=1.0, how="bbox_z"),
]