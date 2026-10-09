"""rolling_pin -- 412 mm French rolling pin: 240 mm barrel, turned handles.

Every turned part is a lathe about its own Z, then rotated a quarter turn about
X and positioned, so the assembly is one straight line along Y -- the axis a
rolling pin is always photographed on. The handles overlap the barrel ends by
4 mm: butting them flush would put two coplanar discs against each other.
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
    length=412.0,          # handle tip to handle tip
    barrel_diameter=56.0,
    barrel_length=240.0,
    handle_diameter=24.0,
    handle_length=90.0,
    barrel_height=28.0,    # barrel axis above the table
)

Z = SPEC["barrel_height"]

BARREL = [
    (0.0, -120.0),
    (9.0, -120.0),
    (12.0, -117.0),
    (12.0, -110.0),
    (26.0, -106.0),        # shoulder out to full barrel diameter
    (28.0, -102.0),
    (28.0, 102.0),
    (26.0, 106.0),
    (12.0, 110.0),
    (12.0, 117.0),
    (9.0, 120.0),
    (0.0, 120.0),
]

HANDLE = [
    (0.0, 0.0),
    (11.0, 0.0),
    (12.0, 4.0),
    (11.5, 60.0),          # slight waist
    (9.0, 84.0),
    (6.0, 89.0),
    (3.0, 90.0),
    (0.0, 90.0),
]


def _to_y(obj, pos):
    """Stand a Z-built lathe on the Y axis, then place it. Millimetres in."""
    obj.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.move(obj, *pos)
    return obj


def build():
    wood = bkit.pbr("PinBeech", base=(0.55, 0.36, 0.18), metal=0.0, rough=0.44)
    dark = bkit.preset("dark_metal")

    barrel = _to_y(bkit.lathe("PinBarrel", BARREL, segments=80, mat=wood),
                   (0.0, 0.0, Z))

    root = SPEC["barrel_length"] / 2.0 - 4.0        # 4 mm of overlap
    left = _to_y(bkit.lathe("PinHandleL", HANDLE, segments=56, mat=wood),
                 (0.0, -(root + SPEC["handle_length"]), Z))
    right = _to_y(bkit.lathe("PinHandleR", HANDLE, segments=56, mat=wood),
                  (0.0, root, Z))

    # the two rings a French pin turns on
    ring_l = bkit.tube("PinRingL", 30.0, 27.5, 5.0, segments=64,
                       centre=(0.0, -100.0, Z), axis="Y", mat=dark)
    ring_r = bkit.tube("PinRingR", 30.0, 27.5, 5.0, segments=64,
                       centre=(0.0, 100.0, Z), axis="Y", mat=dark)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="pin_length", mm=412.0, tol=0.3, how="bbox_y"),
    dict(name="barrel_diameter", mm=56.0, tol=0.3, how="bbox_x",
         part="PinBarrel"),
    dict(name="handle_diameter", mm=24.0, tol=0.3, how="bbox_z",
         part="PinHandleR"),
]
