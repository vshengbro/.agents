"""
beaker -- 250 ml Griffin low-form glass beaker: 70 mm outside diameter,
95 mm tall, 1.8 mm wall.

Every graduation is a real groove cut into the revolve profile rather than a
printed-looking decal: the mark heights are computed from the real inner bore
area (V = pi*r^2*h), so the scale is calibrated rather than eyeballed, and the
groove floor takes the ink material as a second face material on the same
watertight solid.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=70.0,      # outside diameter
    body_height=95.0,        # rim height above the table
    wall=1.8,                # soda-lime glass
    base_thickness=2.2,
    volume_ml=250.0,
    major_graduations=5,     # 50 ... 250 ml
    minor_step_ml=25.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]
WALL = SPEC["wall"]
RI = R - WALL
FLOOR = SPEC["base_thickness"]
AREA = math.pi * RI ** 2          # mm^2 of bore


def fill_height(vol_ml):
    """Height of the bore surface at `vol_ml`, from the real bore area."""
    return vol_ml * 1000.0 / AREA


def build():
    glass = bkit.pbr("BeakerGlass", base=(0.86, 0.90, 0.90), rough=0.05,
                     transmission=0.72, ior=1.52, coat=0.5)
    ink = bkit.pbr("BeakerInk", base=(0.07, 0.07, 0.08), rough=0.45)

    # ---- revolve: base -> outer wall (with graduations) -> rim -> bore -----
    prof = [(0.0, 0.0), (R - 4.0, 0.0), (R - 0.8, 1.1), (R, 3.2)]

    majors = list(range(50, int(SPEC["volume_ml"]) + 1, 50))
    minors = []
    for vol in sorted(set(minors) | set(majors)):
        z = FLOOR + 3.0 + fill_height(vol)
        if z > H - 8.0:
            continue
        depth = 0.30 if vol in majors else 0.20
        prof += [(R, z), (R - depth, z), (R - depth, z + 0.7), (R, z + 0.7)]

    prof += [
        (R, H - 4.0),
        (R - 0.5, H),                   # rolled outer rim
        (RI, H),                        # across the rim
        (RI, FLOOR + 1.4),              # down the bore
        (RI - 3.0, FLOOR),
        (0.0, FLOOR),                   # across the bore floor
    ]
    beaker = bkit.lathe("BeakerBody", prof, segments=128, mat=glass)

    # the groove floors are the only faces at R-depth: give them the ink
    bkit.assign_faces_by(beaker, ink,
                         lambda c, n: R - 0.36 < _rad(c) / bkit.MM < R - 0.14)

    return dict(spec=SPEC, parts=1)


def _rad(c):
    return (c.x ** 2 + c.y ** 2) ** 0.5


CHECKS = [
    dict(name="body_diameter", mm=70.0, tol=0.2, how="diameter", part="BeakerBody"),
    dict(name="body_height", mm=95.0, tol=0.2, how="bbox_z", part="BeakerBody"),
    dict(name="overall_height", mm=95.0, tol=0.2, how="bbox_z"),
]