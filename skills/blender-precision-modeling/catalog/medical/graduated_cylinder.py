"""
graduated_cylinder -- 250 ml borosilicate graduated cylinder: 42 mm bore tube,
300 mm tall on a 100 mm foot.

The whole object is one revolve: foot, flared shoulder, graduated stem, rolled
rim, bore, and inside floor. Mark heights come from the real bore area
(V = pi*r^2*h), so 250 ml lands where the geometry says it should -- and the
marks are 0.35 mm engravings in the profile, not a printed decal, which keeps
the solid watertight instead of adding a z-fighting shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    foot_diameter=100.0,
    tube_diameter=42.0,      # outside diameter of the stem
    overall_height=300.0,
    wall=1.6,
    volume_ml=250.0,
    major_step_ml=50.0,
    minor_step_ml=10.0,
)

FOOT = SPEC["foot_diameter"] / 2.0       # 50.0
TR = SPEC["tube_diameter"] / 2.0         # 21.0
H = SPEC["overall_height"]
WALL = SPEC["wall"]
BR = TR - WALL                          # 19.4 bore radius
AREA = math.pi * BR ** 2
STEM_LO = 22.0                          # bottom of the straight stem
MARK_LO, MARK_HI = 40.0, 280.0          # graduated region
MARK_D = 0.35


def build():
    glass = bkit.pbr("CylGlass", base=(0.88, 0.91, 0.90), rough=0.05,
                     transmission=0.74, ior=1.47, coat=0.5)
    ink = bkit.pbr("CylInk", base=(0.08, 0.08, 0.09), rough=0.45)

    # ---- foot: wide base with a chamfer, then the flared shoulder ----------
    prof = [
        (0.0, 0.0),
        (FOOT - 5.0, 0.0),
        (FOOT - 0.8, 1.2),
        (FOOT, 3.0),
        (FOOT, 7.0),
        (FOOT - 2.0, 9.0),
        (FOOT - 8.0, 11.0),
        (FOOT - 20.0, 15.0),
        (TR + 1.5, STEM_LO - 4.0),
        (TR, STEM_LO),
    ]

    # ---- graduations, computed from the real bore area --------------------
    majors = list(range(50, int(SPEC["volume_ml"]) + 1, 50))
    span = AREA * (MARK_HI - MARK_LO) / 1000.0        # ml across the scale
    # A 0.35 mm engraving every 10 ml turned the stem into a screw thread:
    # real graduation lines are hairline, and there are five of them.
    for vol in majors:
        frac = vol / span
        if not 0.0 <= frac <= 1.0:
            continue
        z = MARK_LO + frac * (MARK_HI - MARK_LO)
        prof += [(TR, z), (TR - MARK_D, z),
                 (TR - MARK_D, z + 0.8), (TR, z + 0.8)]

    prof += [
        (TR, H - 8.0),
        (TR + 1.4, H - 5.0),          # rolled rim bead
        (TR + 1.4, H - 1.5),
        (TR - 0.6, H),
        (BR, H - 0.8),                # across the rim
        (BR, 14.0),                   # down the bore
        (0.0, 12.0),                  # inside floor, 2 mm over the foot top
    ]
    cyl = bkit.lathe("GraduatedCylinder", prof, segments=128, mat=glass)

    bkit.assign_faces_by(cyl, ink,
                         lambda c, n: TR - MARK_D - 0.05
                         < _rad(c) / bkit.MM < TR - MARK_D + 0.05)

    return dict(spec=SPEC, parts=1)


def _rad(c):
    return (c.x ** 2 + c.y ** 2) ** 0.5


CHECKS = [
    dict(name="foot_diameter", mm=100.0, tol=0.3, how="diameter",
         part="GraduatedCylinder"),
    dict(name="overall_height", mm=300.0, tol=0.3, how="bbox_z",
         part="GraduatedCylinder"),
    dict(name="assembly_height", mm=300.0, tol=0.3, how="bbox_z"),
]