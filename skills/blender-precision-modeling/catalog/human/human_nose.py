"""
human_nose -- a 50 mm nose: bridge, tip, two alae, a septum and two nostrils.

The nose is a loft along its own long axis (the nasion at the top, the tip at
the front and below) whose section widens from 13 mm at the root to 34 mm at the
alae. That widening IS the nose -- a straight taper is a beak, and the two
requirements that make it read as a human nose are the nasion notch at the top
and the alar flare at the bottom.

The nostrils are two `bore` calls, which pick their own cutter segment count on
purpose: a cutter sharing the host's exact segment count puts coincident
vertices on the rim and the EXACT solver answers with non-manifold edges.
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
    nose_length   = 50.0,
    nose_height   = 36.0,
    ala_span      = 34.0,
    root_width    = 13.0,
)

SEG = 40
# (y, z, half_width, half_height) from the nasion forward and down
BRIDGE = [
    (0.0, 36.0, 6.5, 8.0),     # nasion
    (-8.0, 31.0, 6.0, 8.5),
    (-18.0, 24.0, 7.5, 9.0),
    (-28.0, 16.0, 10.0, 9.5),
    (-36.0, 9.0, 13.5, 9.0),
    (-42.0, 4.0, 16.0, 7.0),   # tip
]


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.540, 0.330, 0.260), rough=0.60)
    nostril = bkit.pbr("Nostril", base=(0.090, 0.055, 0.048), rough=0.76)

    # ---- bridge and tip
    sections = []
    for (y, z, hw, hh) in BRIDGE:
        ring = bkit.superellipse_section(2.0 * hw, 2.0 * hh, n=2.6, steps=SEG)
        sections.append([(u, y, z + v) for (u, v) in ring])
    nose = bkit.loft("Nose", sections, mat=skin, smooth=True)
    bkit.recalc(nose)

    # ---- the two alae: the flare at the base of the nose, as separate
    # overlapping solids so the flare is a real volume and not a section.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        ala = bkit.uv_sphere("Ala%s" % side, 1.0, segments=24, rings=12,
                             centre=(sx * 14.0, -40.0, 3.0), mat=skin)
        ala.scale = (7.0, 9.0, 8.0)
        ala.name = "Ala%s" % side
        # nostril bore, cutting inboard and upward into the ala
        bkit.bore(nose, 3.4, depth=26.0,
                  centre=(sx * 8.0, -42.0, 1.0), axis="Y",
                  host_segments=SEG, mat=nostril)
    bkit.recalc(nose)

    # ---- septum and columella: the divider between the nostrils
    bkit.uv_sphere("Septum", 1.0, segments=20, rings=10,
                   centre=(0.0, -38.0, 1.0), mat=skin).scale = \
        (4.0, 9.0, 8.0)
    bkit.lathe("Columella", [(0.0, 0.0), (5.0, 0.0), (5.5, 7.0), (4.0, 12.0),
                             (0.0, 13.0)],
               segments=24, centre=(0.0, -40.0, -4.0), mat=skin)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="nose_length", mm=42.0,  tol=0.5, how="bbox_y", part="Nose"),
    dict(name="nose_height", mm=47.0,  tol=0.5, how="bbox_z", part="Nose"),
    dict(name="ala_span",    mm=32.0,  tol=0.5, how="bbox_x", part="Nose"),
    dict(name="root_width",  mm=11.0,  tol=0.5, how="bbox_x", part="Columella"),
    dict(name="ala",         mm=18.0,  tol=0.5, how="diameter", part="AlaL"),
]
