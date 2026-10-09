"""
human_torso -- a 650 mm trunk from the iliac crest to the base of the neck,
built to the 7.5-head canon (650 / 0.414 = 1.57 heads, so the figure it belongs
to is 1725 mm).

A torso is one changing cross-section, which is exactly what `loft` is for.
Seven superellipse rings carry the whole silhouette: the section is a squircle
(n = 3.2) at the ribcage, a flatter rounded rectangle (n = 4.0) at the lumbar
region where the back flattens, and it narrows sharply into the neck.

The ring table is the model. Changing the waist is editing one row of numbers,
not hunting for a vertex.
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
    shoulder_width = 400.0,
    chest_depth    = 240.0,
    waist_width    = 310.0,
    trunk_height   = 650.0,
    neck_diameter  = 112.0,
)

# (z, width, depth, z_centre_offset, n) -- z = 0 at the top of the pelvis.
# The waist is the narrowest ring and the chest the deepest: that contrast is
# the whole silhouette, and a table that tapers evenly reads as a barrel.
RINGS = [
    (0.0,  300.0, 210.0, 105.0, 3.6),
    (120.0, 286.0, 198.0, 108.0, 4.0),   # waist / lumbar
    (300.0, 330.0, 216.0, 120.0, 3.6),   # lower ribs
    (450.0, 372.0, 244.0, 128.0, 3.2),   # chest, deepest
    (545.0, 400.0, 210.0, 130.0, 3.0),   # shoulder girdle, widest
    (600.0, 318.0, 168.0, 134.0, 2.8),   # trapezius slope
    (650.0, 132.0, 128.0, 142.0, 2.2),   # neck
]
SEG = 48


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.540, 0.340, 0.265), rough=0.58)

    sections = []
    for (z, w, d, zc, n) in RINGS:
        ring = bkit.superellipse_section(w, d, n=n, steps=SEG)
        sections.append([(u, v, z) for (u, v) in ring])
    torso = bkit.loft("Torso", sections, mat=skin, smooth=True)
    bkit.recalc(torso)

    # ---- shoulder caps. The deltoid heads have to sit OUTSIDE the
    # shoulder-girdle ring's half-width (200 mm) or they disappear inside the
    # torso and the shoulders come out square.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Deltoid%s" % side, 1.0, segments=28, rings=14,
                       centre=(sx * 192.0, 0.0, 528.0), mat=skin).scale = \
            (60.0, 64.0, 70.0)

    # ---- pectorals: the chest is not a smooth curve, it has two masses on it
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Pectoral%s" % side, 1.0, segments=28, rings=14,
                       centre=(sx * 76.0, -96.0, 432.0), mat=skin).scale = \
            (88.0, 38.0, 66.0)

    # ---- the scapulae, standing off the back of the ribcage
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Scapula%s" % side, 1.0, segments=20, rings=10,
                       centre=(sx * 78.0, 92.0, 470.0), mat=skin_d).scale = \
            (64.0, 26.0, 84.0)

    # ---- the acromion ridge: a thin skin-coloured arc over each shoulder.
    # In cloth it reads as a foreign tube laid on the model.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.arc_torus("Acromion%s" % side, 72.0, 8.0, 200.0, 340.0,
                       plane="XY", centre=(sx * 52.0, -18.0, 556.0),
                       seg_minor=12, mat=skin)

    # ---- the sternal furrow, as a second material on the one solid rather
    # than as a shell that would z-fight with the wall
    bkit.assign_faces_by(torso, skin_d,
                         lambda c, n: (c.y / bkit.MM < -60.0
                                       and abs(c.x / bkit.MM) < 34.0
                                       and c.z / bkit.MM > 330.0))

    # ---- iliac crests: the top of the pelvis the trunk sits on
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("IliacCrest%s" % side, 1.0, segments=24, rings=12,
                       centre=(sx * 122.0, 4.0, 6.0), mat=skin_d).scale = \
            (58.0, 84.0, 30.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="shoulder_span", mm=120.0, tol=0.6, how="bbox_x", part="DeltoidL"),
    dict(name="shoulder_width", mm=400.0, tol=2.0, how="bbox_x", part="Torso"),
    dict(name="chest_depth",    mm=244.0, tol=2.0, how="bbox_y", part="Torso"),
    dict(name="trunk_height",   mm=650.0, tol=2.0, how="bbox_z", part="Torso"),
    dict(name="neck_diameter",  mm=400.0, tol=2.0, how="diameter", part="Torso"),
    dict(name="pectoral",       mm=176.0, tol=2.0, how="bbox_x", part="PectoralL"),
]
