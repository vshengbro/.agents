"""
handsaw -- 680 mm panel saw with a closed wooden grip.

The tooth line is part of the blade polygon, not a separate strip: a zigzag
edge with 104 teeth closes into the same watertight solid, and nothing can
z-fight with the blade face. The teeth sit BELOW a straight base line, so the
polygon still travels left-to-right along the bottom without self-crossing.

Size class is "large", which is what the 680 mm envelope needs; a handsaw is
the one tool in this domain that is genuinely not small.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BLADE_T = 1.6
TEETH = 104
TOOTH_DEPTH = 4.2

SPEC = dict(
    overall_length=687.0,
    overall_height=176.0,
    blade_length=523.0,
    blade_height=146.0,
    handle_length=168.0,
)


def _base(x):
    """Straight tooth base line, heel at (-35, 8) rising to (462, 64)."""
    return 8.0 + (x + 35.0) / 497.0 * 56.0


def blade_poly():
    pts = [(-35.0, 128.0), (100.0, 150.0), (340.0, 138.0), (480.0, 112.0),
           (488.0, 94.0), (480.0, 72.0), (462.0, _base(462.0))]
    pitch = 497.0 / TEETH
    x = 462.0
    for _ in range(TEETH):
        pts.append((x, _base(x) - TOOTH_DEPTH))       # tooth tip
        x -= pitch
        pts.append((x + pitch * 0.45, _base(x + pitch * 0.45)))
    return pts


def build():
    steel = bkit.pbr("SawBlade", base=(0.76, 0.78, 0.82), metal=0.30,
                     rough=0.20)
    wood = bkit.pbr("SawHandle", base=(0.30, 0.15, 0.06), rough=0.42)

    blade = bkit.extrude_profile("HandsawBlade", blade_poly(), BLADE_T,
                                 axis="Y", mat=steel)
    bkit.recalc(blade)

    # Closed grip loop. scale() is applied in the object's LOCAL frame, and the
    # torus is laid into the world XZ plane by axis="Y", so local X -> world X,
    # local Y -> world Z and local Z -> world Y: squashing local Z flattens
    # the handle across its thickness, which is what a turned grip looks like.
    handle = bkit.torus("HandsawHandle", 68.0, 16.0, seg_major=72,
                        seg_minor=28, centre=(-115.0, 0, 78.0), axis="Y",
                        mat=wood)
    handle.scale = (1.00, 1.05, 0.50)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="blade_length", mm=523.0, tol=1.0, how="bbox_x",
         part="HandsawBlade"),
    dict(name="handle_length", mm=168.0, tol=1.0, how="bbox_x",
         part="HandsawHandle"),
    dict(name="handle_height", mm=176.4, tol=1.5, how="bbox_z",
         part="HandsawHandle"),
    dict(name="overall_length", mm=687.0, tol=3.0, how="bbox_x"),
]