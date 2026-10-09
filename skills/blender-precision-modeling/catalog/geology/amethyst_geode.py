"""
amethyst_geode -- a geode: an irregular basalt shell cracked open, lined with a
druse of amethyst crystal points.

Real object: a 132 mm amethyst geode from a Brazilian basalt flow -- an outer
weathered shell ~11 mm thick and an inner cavity packed with terminated quartz
points, biggest at the centre. Both halves matter: the druse alone reads as a
crystal pile, the shell alone reads as a pebble.

Two things had to be right to make the druse visible at all:

1. The cavity is SHALLOW (24 mm deep in a 132 mm shell). A geode with a deep
   bowl hides its own contents from any camera above 30 deg elevation -- the
   rim occludes everything. Real geodes are cut open and shallow for the same
   reason.
2. The crystals splay outward and stand tall enough to clear the rim, so the
   read from a three-quarter view is druse-on-a-shell.

The shell is an open bowl (`lathe` over a closed profile that walks out along
the base, up the outside, over the broken rim and back down the inside), so it
has a real wall thickness instead of being a zero-thickness dome.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    outer_diameter=132.0,
    shell_thickness=11.0,
    cavity_depth=24.0,        # shallow: a deep bowl hides its own druse
    rim_height=24.0,
    crystal_height=34.0,      # the tallest, central point
    crystal_diameter=9.0,
    crystal_count=34,
)

R_OUT = SPEC["outer_diameter"] / 2.0
WALL = SPEC["shell_thickness"]
RIM_Z = SPEC["rim_height"]
FLOOR_Z = 9.0


def _crystal(name, r, length, mat, tip_frac=0.32):
    """Hexagonal prism + hexagonal termination, as one watertight solid.

    The tip root is 0.4 mm wider than the barrel and starts 1.2 mm inside it:
    same segment count would put coincident facets on both surfaces and the
    union of the two solids would come back non-manifold.
    """
    prism_h = length * (1.0 - tip_frac)
    hexa = [(r * math.cos(math.radians(60 * i)),
             r * math.sin(math.radians(60 * i))) for i in range(6)]
    prism = bkit.extrude_profile(name + "Prism", hexa, prism_h,
                                 centre=(0.0, 0.0, prism_h / 2.0), mat=mat)
    tip_h = length - prism_h + 1.2      # the extra 1.2 mm is buried in the barrel
    bkit.boolean(prism, bkit.cylinder(name + "Tip", r + 0.4, tip_h,
                                      r2=0.0, segments=6, centre=(0.0, 0.0,
                                      prism_h - 1.2 + tip_h / 2.0),
                                      smooth=False), "UNION")
    bkit.recalc(prism)
    prism.name = name
    return prism


def build():
    basalt = bkit.pbr("GeodeBasalt", base=(0.155, 0.15, 0.155), rough=0.80)
    amethyst = bkit.pbr("Amethyst", base=(0.42, 0.24, 0.56), rough=0.09,
                        transmission=0.30, ior=1.55)
    amethyst_pale = bkit.pbr("AmethystPale", base=(0.66, 0.54, 0.78), rough=0.12,
                             transmission=0.24, ior=1.55)

    # ---- shell: outer wall up, over the rim, inner wall down, across floor -
    prof = [
        (0.0, 0.0),
        (R_OUT - 9.0, 0.0),
        (R_OUT, 5.0),
        (R_OUT, RIM_Z - 4.0),
        (R_OUT - 4.0, RIM_Z + 2.0),        # broken, rounded-over rim
        (R_OUT - WALL - 2.0, RIM_Z + 1.0),
        (R_OUT - WALL, RIM_Z - 6.0),        # down the inside
        (R_OUT - WALL - 8.0, FLOOR_Z + 3.0),
        (12.0, FLOOR_Z),
        (0.0, FLOOR_Z),                     # across the cavity floor
    ]
    shell = bkit.lathe("GeodeShell", prof, segments=40, mat=basalt, smooth=False)

    # ---- druse: crystals on computed concentric rings --------------------
    # Radius per ring and an outward tilt per ring: a flat druse of equal
    # points reads as a hedgehog, a tilted one reads as a geode lining. Ring
    # radii are staggered by a half-step so no two crystals are coaxial.
    rings = [(0.0, 1, 0.0), (17.0, 6, 12.0), (33.0, 10, 25.0), (47.0, 17, 38.0)]
    count = sum(n for _r, n, _t in rings)
    for ri, (rad, n, tilt) in enumerate(rings):
        for i in range(n):
            a = 2.0 * math.pi * i / n + ri * 0.7
            t = max(0.0, 1.0 - rad / 54.0)     # biggest crystals in the middle
            length = SPEC["crystal_height"] * (0.42 + 0.58 * t)
            dia = SPEC["crystal_diameter"] * (0.55 + 0.45 * t)
            mat = amethyst if (i + ri) % 3 else amethyst_pale
            c = _crystal("Crystal_r%d_i%d" % (ri, i), dia / 2.0, length, mat)
            c.rotation_euler = (math.radians(tilt), 0.0,
                                math.radians(90 + i * 360.0 / n))
            # Foot on the cavity floor: outer rings ride up the wall so their
            # tips clear the rim instead of hiding under it.
            bkit.move(c, rad * math.cos(a), rad * math.sin(a),
                      FLOOR_Z - 2.0 + 0.30 * rad)

    return dict(spec=SPEC, parts=1 + count)


CHECKS = [
    dict(name="outer_diameter", mm=132.0, tol=1.0, how="diameter", part="GeodeShell"),
    dict(name="shell_height", mm=26.0, tol=1.0, how="bbox_z", part="GeodeShell"),
    dict(name="central_crystal_height", mm=34.0, tol=1.5,
         how="bbox_z", part="Crystal_r0_i0"),
    # The shell rim is the widest thing on a geode; the druse stays inside it.
    dict(name="overall_diameter", mm=132.0, tol=2.0, how="diameter"),
]