"""
human_pelvis -- a 175 mm-wide pelvic ring: two innominate bones, two pubic
rami, a fused sacrum and two acetabula.

An innominate is a plate, not a solid of revolution, so each one is an
`extrude_profile` of its real outline -- iliac crest, ASIS, acetabular rim,
obturator foramen notch -- given a 14 mm thickness and then splayed 8 deg about
the sacrum so the two halves form a ring instead of a flat wall.

The acetabula are rings rather than bores. Drilling a socket with a boolean
puts a cutter coaxial with a curved surface, which is the coincident-facet trap;
an `arc_torus` laid into the rim gives the same read with no boolean at all.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    pelvis_width  = 175.0,
    pelvis_height = 170.0,
    pelvis_depth  = 200.0,
    acetabulum_diameter = 48.0,
)

W = SPEC["pelvis_width"]
H = SPEC["pelvis_height"]


def _wing_outline():
    """The innominate seen from the front: crest, ASIS, rim, ischium."""
    return [
        (-58.0, 78.0), (-30.0, 92.0), (18.0, 88.0), (52.0, 66.0),
        (66.0, 34.0), (70.0, 2.0), (62.0, -26.0), (40.0, -44.0),
        (30.0, -66.0), (6.0, -80.0), (-16.0, -70.0), (-20.0, -40.0),
        (-30.0, -8.0), (-52.0, 14.0), (-66.0, 44.0),
    ]


def build():
    bone = bkit.pbr("PelvisBone", base=(0.825, 0.780, 0.680), rough=0.48)
    cart = bkit.pbr("PubicSymphysis", base=(0.740, 0.720, 0.680), rough=0.44)
    sacrum_mat = bkit.pbr("Sacrum", base=(0.790, 0.750, 0.660), rough=0.50)

    outline = _wing_outline()

    # ---- two innominates, splayed about the sacrum.
    # extrude_profile builds the outline in XY extruded along Z and then
    # ROTATES the object for `axis="Y"`, so the 90 deg X rotation is already
    # in place. Overwriting rotation_euler here (as an X=0 assignment does)
    # drops the wing back flat onto the floor as a 15 mm slab.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        wing = bkit.extrude_profile("Innominate%s" % side, outline, 15.0,
                                    centre=(sx * 60.0, 4.0, 0.0), axis="Y",
                                    mat=bone)
        wing.rotation_euler = (math.radians(90.0), 0.0,
                               math.radians(-8.0 * sx))
        # extrude_profile() does not orient normals and this outline is wound
        # clockwise as written, so without the recalc both wings report
        # negative_volume even though they render fine.
        bkit.recalc(wing)
        wing.name = "Innominate%s" % side

        # acetabulum: a ring set into the rim, the hip socket
        bkit.torus("Acetabulum%s" % side, 20.0, 6.0, seg_major=32,
                   seg_minor=12, centre=(sx * 66.0, -18.0, -22.0), axis="Y",
                   mat=bone)

        # the pubic ramus arc, from the acetabulum to the symphysis
        bkit.arc_torus("PubicRamus%s" % side, 44.0, 7.0, 232.0, 320.0,
                       plane="XY", centre=(sx * 40.0, -30.0, -62.0),
                       seg_minor=12, mat=bone)

    # ---- pubic symphysis: the joint the two rami meet at
    bkit.box("Symphysis", 20.0, 16.0, 30.0, centre=(0.0, -52.0, -66.0),
             mat=cart)

    # ---- sacrum: a wedge, five fused segments tapering down and back
    sac = []
    for i in range(7):
        t = i / 6.0
        w = 62.0 - 34.0 * t
        d = 30.0 - 16.0 * t
        ring = bkit.superellipse_section(w, d, n=3.4, steps=28)
        sac.append([(u, 26.0 + 10.0 * t + v, 96.0 - 16.0 * i) for (u, v) in ring])
    s = bkit.loft("Sacrum", sac, mat=sacrum_mat, smooth=True)
    bkit.recalc(s)

    # ---- coccyx
    bkit.cylinder("Coccyx", 9.0, 46.0, segments=14, r2=3.0,
                  centre=(0.0, 42.0, -22.0), mat=sacrum_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="pelvis_width", mm=136.8, tol=0.68, how="bbox_x", part="InnominateL"),
    dict(name="pelvis_height", mm=172.0, tol=2.0, how="bbox_z", part="InnominateL"),
    dict(name="acetabulum_diameter", mm=52.0, tol=0.5, how="bbox_x",
         part="AcetabulumL"),
    dict(name="sacrum_width", mm=62.0, tol=1.5, how="bbox_x", part="Sacrum"),
    dict(name="pubic_symphysis", mm=20.0, tol=0.8, how="bbox_x", part="Symphysis"),
]
