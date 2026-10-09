"""
human_eye -- a 24 mm eyeball with cornea, iris, pupil and both lids.

The eye is the one object in this domain where the sclera cannot be a plain
sphere: an eyeball is a sphere with a flatter front, and that flat front is what
carries the cornea. So the globe is a lathe of the real cross-section -- 12 mm
radius everywhere, then 11.4 mm over the corneal bulge -- and the cornea is a
second closed solid seated in that recess, overlapping it by a millimetre
rather than meeting it flush (flush is the tangency trap).

The lids are flattened spheroids that overlap the globe, plus a lash arc. Three
named solids, all closed, no booleans.
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
    globe_diameter = 24.0,
    cornea_diameter = 11.6,
    iris_diameter  = 11.6,
    pupil_diameter = 4.8,
    aperture       = 29.0,     # palpebral fissure, lid to lid
)

R = SPEC["globe_diameter"] / 2.0
SEG = 48

# (radius, y) -- the globe in section: 12 mm sphere with a 0.6 mm corneal
# flattening, the front of the eye at -Y.
GLOBE = [
    (0.0, -11.4),
    (4.0, -11.3),
    (7.5, -10.8),
    (9.6, -9.6),
    (11.1, -6.0),
    (11.8, -1.0),
    (12.0, 5.0),
    (11.2, 9.0),
    (8.0, 11.4),
    (0.0, 12.0),
]


def build():
    sclera = bkit.pbr("Sclera", base=(0.880, 0.875, 0.865), rough=0.20)
    cornea = bkit.pbr("Cornea", base=(0.860, 0.890, 0.910), rough=0.04,
                      transmission=0.30, ior=1.376)
    iris = bkit.pbr("Iris", base=(0.115, 0.235, 0.310), rough=0.16)
    iris_r = bkit.pbr("IrisStroma", base=(0.180, 0.330, 0.400), rough=0.28)
    pupil = bkit.pbr("Pupil", base=(0.016, 0.016, 0.020), rough=0.10)
    lid = bkit.pbr("Eyelid", base=(0.700, 0.500, 0.400), rough=0.54)
    lash = bkit.pbr("Lash", base=(0.055, 0.040, 0.036), rough=0.40)

    # ---- globe: one lathe of the real cross-section. The profile is written
    # front-to-back (front at -11.4) and therefore descends in z; lathe() does
    # not orient normals, so the recalc is what keeps the volume positive.
    globe = bkit.lathe("Globe", GLOBE, segments=SEG, mat=sclera)
    bkit.recalc(globe)

    # ---- cornea: seated in the recess, overlapping 1 mm
    bkit.uv_sphere("Cornea", 1.0, segments=SEG, rings=SEG // 2,
                   centre=(0.0, -8.6, 0.0), mat=cornea).scale = \
        (5.8, 4.4, 5.8)

    # ---- iris and pupil, both facing the front of the eye. lathe() always
    # revolves about Z, so each disc is built along Z and then rotated about
    # its own origin to face -Y.
    iris_ob = bkit.lathe("Iris", [(0.0, 0.0), (4.4, 0.0), (5.4, 0.5),
                                  (5.6, 1.4), (4.0, 1.8), (0.0, 1.8)],
                         segments=40, centre=(0.0, -11.2, 0.0), mat=iris)
    bkit.recalc(iris_ob)
    iris_ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    stro = bkit.lathe("IrisStroma", [(0.0, 0.0), (2.0, 0.0), (2.4, 0.7),
                                      (0.0, 0.9)],
                      segments=32, centre=(0.0, -12.6, 0.0), mat=iris_r)
    bkit.recalc(stro)
    stro.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.uv_sphere("Pupil", 1.0, segments=32, rings=16,
                   centre=(0.0, -12.9, 0.0), mat=pupil).scale = \
        (2.4, 0.9, 2.4)

    # ---- lids: the palpebral fissure is 29 mm, so the lids overlap the
    # globe's 24 mm from above and below and leave the cornea showing
    bkit.uv_sphere("LidUpper", 1.0, segments=32, rings=16,
                   centre=(0.0, -1.0, 9.4), mat=lid).scale = (14.5, 12.5, 8.2)
    bkit.uv_sphere("LidLower", 1.0, segments=32, rings=16,
                   centre=(0.0, 0.5, -9.0), mat=lid).scale = (14.0, 12.0, 7.4)

    # ---- lash lines at the lid margins
    bkit.arc_torus("LashUpper", 13.6, 1.1, 24.0, 156.0, plane="XZ",
                   centre=(0.0, -1.0, 2.0), seg_minor=8, mat=lash)
    bkit.arc_torus("LashLower", 13.0, 0.8, 206.0, 334.0, plane="XZ",
                   centre=(0.0, 0.5, 1.0), seg_minor=8, mat=lash)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="globe_diameter", mm=24.0,  tol=0.5, how="diameter", part="Globe"),
    dict(name="cornea_diameter", mm=11.6, tol=0.4, how="bbox_x",   part="Cornea"),
    dict(name="pupil_diameter", mm=4.8,  tol=0.3, how="bbox_x",   part="Pupil"),
    dict(name="aperture", mm=29.0, tol=1.0, how="bbox_x", part="LidUpper"),
]
