"""chopsticks -- a pair of 240 mm tapered hardwood chopsticks.

Each stick is a single loft over squarish superellipse sections that shrink from
8.4 mm to 3.2 mm and from 8.0 mm to 1.2 mm thick, with the centre line dropping
as it goes so the underside stays on the table the whole way -- the way a
chopstick actually lies, and the reason it does not look like a floating rod.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=240.0,           # tip to tip
    butt_width=8.4,         # at the thick end
    tip_width=2.6,
    butt_thickness=8.0,
    tip_thickness=1.2,
    gap=17.0,               # centre-to-centre spacing of the pair
)

# y, width, thickness, centre height above the table
STATIONS = [
    (-120.0, 8.4, 8.0, 4.00),
    (-100.0, 8.2, 7.8, 4.00),
    (-60.0, 7.6, 7.2, 3.90),
    (-10.0, 6.8, 6.4, 3.60),
    (40.0, 5.8, 5.4, 3.20),
    (90.0, 4.6, 4.2, 2.30),
    (114.0, 3.6, 3.0, 1.60),
    (120.0, 2.6, 1.2, 0.65),
]


def _stick(name, mat):
    sections = []
    for (y, w, t, zc) in STATIONS:
        ring = bkit.superellipse_section(w, t, n=3.4, steps=20)
        sections.append([(px, y, pz + zc) for (px, pz) in ring])
    ob = bkit.loft(name, sections, closed_loop=True, cap_start=True,
                   cap_end=True, mat=mat, smooth=True)
    # loft() does not orient the winding; recalc makes the signed volume
    # positive so health() stops reporting inverted normals.
    return bkit.recalc(ob)


def build():
    wood = bkit.pbr("ChopstickBamboo", base=(0.58, 0.40, 0.21), metal=0.0,
                    rough=0.42)

    left = _stick("ChopstickA", wood)
    bkit.move(left, -SPEC["gap"] / 2.0, 0.0, 0.0)

    right = _stick("ChopstickB", wood)
    # a degree of splay: rotating about Z before moving swings the tips apart.
    # Kept small -- the pair has to read as two sticks, not one grooved rod.
    right.rotation_euler = (0.0, 0.0, math.radians(-1.0))
    bpy.context.view_layer.update()
    bkit.move(right, SPEC["gap"] / 2.0, 0.0, 0.0)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="stick_length", mm=240.0, tol=0.3, how="bbox_y",
         part="ChopstickA"),
    dict(name="butt_width", mm=8.4, tol=0.3, how="bbox_x", part="ChopstickA"),
    dict(name="overall_length", mm=240.0, tol=0.3, how="bbox_y"),
]
