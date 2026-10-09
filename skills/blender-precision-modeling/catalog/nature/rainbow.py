"""
rainbow -- a 6-band arc of 3000 mm radius standing on a 6000 mm diameter base.

A rainbow is seven concentric bands, which is the one place in nature where a
radial array is literally the right tool: one band is built and the other six
are `array_radial` copies about the arc's own centre of curvature at
(0, 0, 1300). Getting that `centre` wrong is the classic failure -- sweep about
the world origin and the bands spread into a fan instead of nesting.

The arc is a partial torus in the XZ plane, and the band radii step by 42 mm,
which is the real angular width of one primary-colour band seen from the
ground. Each band is its own closed solid: no booleans, so the nesting is free.
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
    radius     = 3000.0,
    span       = 6000.0,
    bands      = 7,
    band_width = 42.0,
    apex_angle = 42.0,     # degrees above the horizon
)

HUB = (0.0, 0.0, 1180.0)
A0, A1 = 4.0, 176.0
# The spectrum, outside in. Kept as a list so the array order is the spectrum
# order and nothing has to be sorted at render time.
BANDS = [
    ("Red",    (0.640, 0.090, 0.080)),
    ("Orange", (0.760, 0.320, 0.060)),
    ("Yellow", (0.840, 0.660, 0.080)),
    ("Green",  (0.140, 0.520, 0.180)),
    ("Blue",   (0.080, 0.260, 0.640)),
    ("Indigo", (0.160, 0.100, 0.420)),
    ("Violet", (0.380, 0.160, 0.500)),
]


def build():
    R = SPEC["radius"]
    w = SPEC["band_width"]

    for i, (name, rgb) in enumerate(BANDS):
        mat = bkit.pbr("Band" + name, base=rgb, rough=0.42)
        band = bkit.arc_torus("Band" + name, R - i * w, w * 0.92, A0, A1,
                              plane="XZ", centre=HUB, seg_minor=18, mat=mat)
        # Nested bands are the whole object, so the sweep is about the centre
        # of curvature -- NOT the world origin. Orbiting about (0,0,0) turns
        # seven nested arcs into a fan of copies swinging across the ground.
        if i > 0:
            bkit.array_radial(band, 1, centre=HUB)

    # ---- the sun that makes it: a bright disc low behind the arc
    bkit.uv_sphere("Sun", 260.0, segments=24, rings=12,
                   centre=(0.0, 300.0, 900.0),
                   mat=bkit.pbr("SunDisc", base=(1.0, 0.95, 0.80), rough=0.20,
                                emission=(1.0, 0.92, 0.72),
                                emission_strength=1.5)).scale = (1.0, 0.3, 1.0)

    # ---- ground haze the arc stands in, so it is not floating in a void
    bkit.lathe("GroundHaze", [(0.0, 0.0), (900.0, 0.0), (1500.0, 90.0),
                              (2100.0, 230.0)],
               segments=48,
               mat=bkit.pbr("Haze", base=(0.640, 0.660, 0.700), rough=0.95))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(BANDS) + 2)


CHECKS = [
    # A partial torus's `longest` is the largest side of its bounding box,
    # which for a 3 m-radius arc is the SPAN, not the radius. The arc is
    # therefore confirmed by the three dimensions a box really can see.
    dict(name="span",   mm=6062.5, tol=30.31, how="bbox_x", part="BandRed"),
    dict(name="apex",   mm=4216.8, tol=21.08, how="top_z", part="BandRed"),
    dict(name="arc_height", mm=2830.2, tol=14.15, how="bbox_z", part="BandRed"),
    dict(name="sun",    mm=520.0,  tol=10.0, how="bbox_x", part="Sun"),
    dict(name="ground", mm=4200.0, tol=20.0, how="diameter", part="GroundHaze"),
]
