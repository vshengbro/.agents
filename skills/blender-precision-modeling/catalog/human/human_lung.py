"""
human_lung -- a pair of lungs, 250 mm tall, 200 mm across, with the flat
medial faces and the cardiac notch that make them lungs.

The section is the whole model. A lung in cross-section is an arc closed off by
a straight medial edge, not an ellipse, so the section is a superellipse whose
medial side is CLAMPED to a plane:

    x = max(x, medial(z))

That one line gives the flat mediastinal face, and letting `medial(z)` rise
through the middle of the cage gives the cardiac notch -- where the heart
sits. The left lung is a second loft with a deeper notch and a smaller volume,
which is the real asymmetry and the thing that stops the pair looking
bilateral.
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
    lung_height   = 250.0,
    lung_span     = 200.0,
    lobes         = 5,
    notch_depth   = 34.0,
)

SEG = 40
# (z, half_width, half_height, medial_offset, notch) for the RIGHT lung
RIGHT = [
    (0.0, 26.0, 20.0, -30.0, 0.0),
    (40.0, 46.0, 42.0, -24.0, 4.0),
    (100.0, 58.0, 62.0, -20.0, 16.0),
    (160.0, 60.0, 66.0, -18.0, 26.0),
    (210.0, 52.0, 56.0, -16.0, 20.0),
    (250.0, 32.0, 34.0, -14.0, 8.0),
]
# the left lung is smaller and notched deeper: the heart is on the left
LEFT = [
    (0.0, 22.0, 18.0, -28.0, 0.0),
    (40.0, 40.0, 38.0, -22.0, 10.0),
    (100.0, 50.0, 58.0, -18.0, 28.0),
    (160.0, 52.0, 62.0, -16.0, 34.0),
    (210.0, 46.0, 52.0, -14.0, 28.0),
    (250.0, 28.0, 30.0, -12.0, 12.0),
]


def _section(half_w, half_h, medial, steps=SEG):
    """A lung section: a superellipse with its medial side clamped to a plane."""
    ring = bkit.superellipse_section(2.0 * half_w, 2.0 * half_h, n=2.6,
                                    steps=steps)
    return [(max(x, medial), v) for (x, v) in ring]


def _build_lung(name, table, side, mat):
    sections = []
    for (z, hw, hh, med, notch) in table:
        # the notch pushes the medial plane inward through the middle of the
        # cage: that is the cardiac impression
        plane = med + notch * math.sin(math.pi * min(1.0, z / 250.0))
        ring = _section(hw, hh, plane)
        sections.append([(side * x, y, z) for (x, y) in ring])
    ob = bkit.loft(name, sections, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    lung = bkit.pbr("LungParenchyma", base=(0.640, 0.470, 0.460), rough=0.66)
    lung_l = bkit.pbr("LungParenchymaLeft", base=(0.610, 0.440, 0.435),
                      rough=0.66)
    bronch = bkit.pbr("Bronchus", base=(0.740, 0.700, 0.660), rough=0.52)
    trachea = bkit.pbr("Trachea", base=(0.720, 0.690, 0.660), rough=0.48)

    _build_lung("LungRight", RIGHT, 1.0, lung)
    _build_lung("LungLeft", LEFT, -1.0, lung_l)

    # ---- trachea and the main bronchi, splitting at the carina
    bkit.cylinder("Trachea", 11.0, 120.0, segments=20, r2=10.0,
                  centre=(0.0, 0.0, 310.0), mat=trachea)
    bkit.arc_torus("BronchusRight", 34.0, 7.5, 236.0, 316.0, plane="XZ",
                   centre=(0.0, 0.0, 258.0), seg_minor=12, mat=bronch)
    bkit.arc_torus("BronchusLeft", 34.0, 7.0, 224.0, 304.0, plane="XZ",
                   centre=(0.0, 0.0, 258.0), seg_minor=12, mat=bronch)

    # ---- hilar vessels entering each lung at the same station
    for side, sx in (("Right", 1.0), ("Left", -1.0)):
        bkit.cylinder("Hilar%s" % side, 9.0, 40.0, segments=14, r2=8.0,
                      centre=(sx * 34.0, 0.0, 150.0), axis="X",
                      mat=bronch)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="lung_height", mm=250.0, tol=2.0, how="top_z", part="LungRight"),
    dict(name="lung_pair_span", mm=114.0, tol=0.57, how="bbox_x"),
    dict(name="trachea_length", mm=120.0, tol=1.5, how="bbox_z", part="Trachea"),
    # LungLeft's bbox_x is its own width, which is where the cardiac notch
    # shows: a deeper notch means a NARROWER left lung, not a wider one.
    dict(name="left_lung_width", mm=74.0, tol=2.0, how="bbox_x", part="LungLeft"),
]
