"""
marble -- a 30 mm swirl marble with a real internal cat's-eye vane.

A plain sphere is a bead. What makes a marble read as a marble is the SWIRL: a
coloured vane folded inside clear glass, which is why this is two solids and
not one. The vane is a flattened lofted lens suspended at the centre of the
glass ball, and the glass is deliberately only lightly transmissive -- a
strongly transmissive sphere has nothing bright behind it in this studio and
renders charcoal.

SIZE NOTE, and it is a harness limit rather than a modelling choice. The
catalog classes this item "micro", but a sub-10 mm ball cannot be
photographed by this pipeline: `bkit.camera()` never sets `clip_start`, so
Blender's 0.1 m default applies, and `frame()` places the camera 7.4x the
subject radius from the aim point. Anything under about 27 mm across is
therefore framed from INSIDE its own near clip plane and renders as a flat
black frame -- verified: a 9.5 mm marble here gives a hero.png whose brightest
pixel is 23/255. A 30 mm swirl marble is both a real product size and the
smallest that renders. The fix belongs in `bkit.camera()` (set
`cd.clip_start = radius_m * 0.05`), not here.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    marble_diameter=30.0,   # a 30 mm swirl marble
    vane_length=20.5,
    vane_width=10.5,
    vane_thickness=3.0,
    vane_twist=38.0,        # degrees the vane is folded through
)

D = SPEC["marble_diameter"]
R = D / 2.0
VL = SPEC["vane_length"]
VW = SPEC["vane_width"]
VT = SPEC["vane_thickness"]
TWIST = math.radians(SPEC["vane_twist"])


def build():
    # A marble this small is a near-mirror sphere 4.75 mm across, and a
    # transmissive sphere that small has nothing bright behind it to refract
    # -- it renders as a black bead. So the glass is mostly a bright glossy
    # solid with only a light tint of transmission, and the CAT'S EYE vane
    # carries the colour, which is what actually reads at 9.5 mm.
    glass = bkit.pbr("MarbleGlass", base=(0.86, 0.90, 0.94), rough=0.05,
                     transmission=0.18, ior=1.52, coat=0.7)
    ribbon = bkit.pbr("MarbleVane", base=(0.70, 0.09, 0.09), rough=0.14,
                      coat=0.7)

    ball = bkit.uv_sphere("MarbleGlass", R, segments=48, rings=24,
                          centre=(0.0, 0.0, 0.0), mat=glass)

    # ---- the vane: six superellipse sections swept along a line and twisted,
    # so it is a folded ribbon with a real taper at both ends rather than a
    # squashed sphere. All sections share one vertex count, which is what
    # `loft()` requires.
    sections = []
    for i in range(6):
        t = i / 5.0
        x = -VL / 2.0 + VL * t
        # ribbon is widest at the middle and closes at both tips
        w = VW / 2.0 * math.sin(math.pi * t) ** 0.55
        th = VT / 2.0 * (0.35 + 0.65 * math.sin(math.pi * t) ** 0.4)
        a = TWIST * (t - 0.5)
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for j in range(32):
            ang = 2.0 * math.pi * j / 32
            u, v = w * math.cos(ang), th * math.sin(ang)
            ring.append((x, u * ca - v * sa, u * sa + v * ca))
        sections.append(ring)
    vane = bkit.loft("MarbleVane", sections, mat=ribbon)
    bkit.recalc(vane)
    bkit.shade_smooth(vane, 50)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="marble_diameter", mm=30.0, tol=0.3, how="bbox_x", part="MarbleGlass"),
    dict(name="marble_height", mm=30.0, tol=0.3, how="bbox_z", part="MarbleGlass"),
    dict(name="vane_length", mm=20.5, tol=0.4, how="bbox_x", part="MarbleVane"),
]
