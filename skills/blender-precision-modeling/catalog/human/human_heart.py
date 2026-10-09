"""
human_heart -- a 120 mm heart: ventricular mass, two atria, and three great
vessels.

The ventricular mass is a loft along the heart's own long axis, from the base
at the top down to the apex at the bottom-front, with the section narrowing to
almost nothing at the apex. That taper is the entire silhouette -- a heart
without a point is a bag.

The three vessels are what make it a heart and not a pear: the aorta arches
back over the pulmonary trunk, the trunk crosses in front of it, and the vena
cava comes down behind. They are an `arc_torus` and two cylinders, all separate
closed solids overlapping the base, so nothing is booleaned.
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
    heart_length = 120.0,
    heart_width  = 92.0,
    heart_height = 130.0,
    aorta_diameter = 30.0,
)

SEG = 36
# (y, z, half_width, half_depth) from the base down to the apex, which points
# down, forward and to the left.
VENT = [
    (0.0, 118.0, 42.0, 38.0),
    (-2.0, 96.0, 45.0, 40.0),
    (-4.0, 68.0, 42.0, 38.0),
    (-6.0, 40.0, 34.0, 31.0),
    (-7.0, 18.0, 23.0, 21.0),
    (-7.0, 4.0, 12.0, 11.0),
    (-7.0, 0.0, 4.0, 4.0),
]


def build():
    myo = bkit.pbr("Myocardium", base=(0.480, 0.145, 0.155), rough=0.50)
    myo_d = bkit.pbr("MyocardiumDark", base=(0.330, 0.090, 0.100), rough=0.54)
    artery = bkit.pbr("Artery", base=(0.620, 0.180, 0.175), rough=0.46)
    vein = bkit.pbr("Vein", base=(0.180, 0.240, 0.400), rough=0.48)

    # ---- ventricular mass. The section spans both X and Y, so the loft is a
    # real cone down the heart's long axis rather than a flat plate.
    sections = []
    for (y, z, hw, hd) in VENT:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hd, n=2.8, steps=SEG)
        sections.append([(u, y + v, z) for (u, v) in ring])
    vent = bkit.loft("Ventricles", sections, mat=myo, smooth=True)
    bkit.recalc(vent)
    # the anterior interventricular groove, as a second material on the one
    # solid rather than as a shell that would z-fight with the wall
    bkit.assign_faces_by(vent, myo_d, lambda c, n: c.y / bkit.MM < -30.0)

    # ---- atria: the two rounded chambers sitting on the base
    for side, sx in (("Right", -1.0), ("Left", 1.0)):
        ob = bkit.uv_sphere("Atrium%s" % side, 1.0, segments=28, rings=14,
                            centre=(sx * 20.0, 6.0, 138.0), mat=myo)
        ob.scale = (28.0, 26.0, 24.0)
        ob.name = "Atrium%s" % side

    # ---- great vessels
    bkit.arc_torus("Aorta", 26.0, 15.0, 20.0, 200.0, plane="XZ",
                   centre=(0.0, 6.0, 140.0), seg_minor=20, mat=artery)
    bkit.cylinder("PulmonaryTrunk", 17.0, 60.0, segments=24, r2=15.0,
                  centre=(10.0, 10.0, 158.0), mat=artery)
    bkit.cylinder("VenaCava", 13.0, 66.0, segments=20, r2=12.0,
                  centre=(-16.0, 18.0, 158.0), mat=vein)

    # ---- coronary vessels on the anterior surface, on the same pitch as the
    # vessels they arise between
    for i, (z, y) in enumerate(((96.0, -40.0), (68.0, -42.0), (40.0, -34.0))):
        bkit.cylinder("Coronary%d" % i, 3.4, 30.0, segments=10, r2=2.4,
                      centre=(-6.0, y, z), axis="X", mat=artery)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    # Ventricles is the ventricular mass only: the atria and the great
    # vessels are separate solids above it, so its top is not the heart's top.
    dict(name="ventricle_height", mm=118.0, tol=2.0, how="top_z", part="Ventricles"),
    dict(name="heart_width",  mm=90.0, tol=2.0, how="bbox_x", part="Ventricles"),
    dict(name="heart_length", mm=80.0, tol=2.0, how="bbox_y", part="Ventricles"),
    dict(name="atrium",       mm=56.0, tol=1.5, how="bbox_x", part="AtriumLeft"),
    dict(name="aorta_diameter", mm=30.0, tol=1.0, how="bbox_y", part="Aorta"),
]
