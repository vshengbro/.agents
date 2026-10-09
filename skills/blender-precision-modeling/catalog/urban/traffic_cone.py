"""
traffic_cone -- 250 x 250 x 300 mm miniature parking cone: chamfered base, a
220 mm-to-60 mm tapered body and a 70 mm reflective collar.

The catalog asks for `small`, and a 300 mm mini cone is a real, sold product --
so unlike the full-height cones this one is modelled at its genuine size rather
than scaled up. The collar is a lathed truncated cone standing just proud of
the body, not a `tube`: the body tapers, so a straight ring would only touch
it at one edge and read as a floating hoop.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=250.0,
    base_depth=250.0,
    base_thickness=25.0,
    overall_height=300.0,
    body_base_diameter=220.0,
    tip_diameter=60.0,
    collar_height=70.0,
)


def build():
    orange = bkit.pbr("ConeOrange", base=(0.82, 0.24, 0.03), rough=0.52)
    collar = bkit.pbr("ConeCollar", base=(0.90, 0.90, 0.88), rough=0.22,
                      emission=(0.90, 0.90, 0.88), emission_strength=0.6)
    base_mat = bkit.preset("rubber")

    # ---- chamfered base ----------------------------------------------------
    bkit.rounded_box("ConeBase", SPEC["base_width"], SPEC["base_depth"],
                     SPEC["base_thickness"], r=10.0, segments=2,
                     centre=(0.0, 0.0, SPEC["base_thickness"] / 2.0),
                     mat=base_mat)

    # ---- tapered body, 220 mm at the base to 60 mm at the tip -----------
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("ConeBody", [
        (0.0, 18.0), (110.0, 18.0), (110.0, 25.0), (88.0, 110.0),
        (58.0, 200.0), (42.0, 270.0), (30.0, 296.0), (0.0, 300.0),
    ], segments=48, mat=orange)

    # ---- reflective collar: a lathed truncated cone just proud of the body
    bkit.lathe("ReflectiveCollar", [(0.0, 175.0), (62.0, 175.0), (56.0, 245.0),
                                    (0.0, 245.0)], segments=48, mat=collar)

    # ---- moulded stiffening ribs and a recessed base pad --------------------
    rib = bkit.box("_rib", 4.0, 4.0, 90.0, centre=(0.0, 104.0, 70.0),
                   mat=orange)
    bkit.array_radial(rib, count=4, axis="Z")
    bkit.rounded_box("BasePad", 190.0, 190.0, 6.0, r=6.0, segments=2,
                     centre=(0.0, 0.0, 22.0), mat=orange)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="base_width", mm=250.0, tol=0.5, how="bbox_x", part="ConeBase"),
    dict(name="base_depth", mm=250.0, tol=0.5, how="bbox_y", part="ConeBase"),
    dict(name="base_thickness", mm=25.0, tol=0.5, how="bbox_z", part="ConeBase"),
    dict(name="overall_height", mm=300.0, tol=0.8, how="bbox_z"),
    dict(name="collar_height", mm=70.0, tol=0.5, how="bbox_z",
         part="ReflectiveCollar"),
]