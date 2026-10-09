"""carafe -- 1 L glass water carafe: wide body, drawn neck, swung bail handle.

232 mm tall on a 108 mm body. Like the wine glass this is one closed lathe
profile: out along the base, up the outside, over the rim and back down the
inside, so the wall is real instead of a zero-thickness revolve.

The handle is a computed bail, not a hand-placed arc: the two attachment points
define a chord, the outward normal of that chord gives the apex, and the major
radius follows from a circle through both tips and the apex --
rmaj = (rise^2 + half_chord^2) / (2 * rise). Getting that backwards makes the
handle bulge into the body instead of away from it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    body_diameter=108.0,    # widest point of the body
    height=232.0,           # rim above the table
    rim_diameter=68.0,
    neck_diameter=63.0,
    wall=2.5,
    base_thickness=6.5,
    handle_reach=38.0,      # outer protrusion from the body wall
    handle_tube=12.0,
    volume_ml=1000.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["height"]
WALL = SPEC["wall"]

# bail geometry: where it meets the body and how far it stands off
UPPER = (41.0, 165.0)     # (x, z) upper attachment
LOWER = (53.0, 75.0)      # lower attachment, on the belly
REACH = 32.0              # apex distance out from the chord midpoint


def _bail():
    """Major radius, centre and sweep of a handle through two tips and an apex."""
    ux, uz = UPPER
    lx, lz = LOWER
    mx, mz = (ux + lx) / 2.0, (uz + lz) / 2.0
    dx, dz = lx - ux, lz - uz
    chord = math.hypot(dx, dz)
    # outward normal of the chord, on the +x side where the handle belongs
    nx, nz = -dz / chord, dx / chord
    apex = (mx + nx * REACH, mz + nz * REACH)
    half = chord / 2.0
    rmaj = (REACH ** 2 + half ** 2) / (2.0 * REACH)
    centre = (apex[0] - rmaj * nx, apex[1] - rmaj * nz)
    a1 = math.degrees(math.atan2(uz - centre[1], ux - centre[0]))
    a0 = math.degrees(math.atan2(lz - centre[1], lx - centre[0]))
    return rmaj, (centre[0], 0.0, centre[1]), min(a0, a1), max(a0, a1)


def build():
    # See wine_glass: 0.82 transmission goes charcoal against this studio's
    # dark backdrop, so the glass is carried by base colour and a coat.
    glass = bkit.pbr("CrystalBright", base=(0.95, 0.97, 1.0), rough=0.04,
                     transmission=0.22, ior=1.46, coat=0.4)

    prof = [
        (0.0, 0.0),
        (R - 16.0, 0.0),           # flat base
        (R - 6.0, 1.5),
        (R - 2.0, 6.0),
        (R, 16.0),
        (R, 112.0),
        (R - 3.0, 138.0),          # shoulder
        (R - 9.0, 158.0),
        (R - 16.0, 174.0),
        (31.5, 186.0),
        (31.5, 196.0),             # neck
        (31.5, 216.0),
        (33.5, 226.0),             # flare into the pouring rim
        (34.0, H),
        (34.0 - WALL, H),          # across the rim
        (31.0, H - 6.0),
        (31.5 - WALL, 216.0),
        (31.5 - WALL, 198.0),
        (31.0, 188.0),             # down the inside
        (36.0, 176.0),
        (43.0, 160.0),
        (R - 9.0 - WALL, 138.0),
        (R - 1.6 - WALL, 112.0),
        (R - 1.6 - WALL, 18.0),
        (R - 5.0, 9.0),
        (R - 16.0, SPEC["base_thickness"]),
        (0.0, SPEC["base_thickness"]),
    ]
    body = bkit.lathe("CarafeBody", prof, segments=96, mat=glass)
    bkit.recalc(body)

    rmaj, centre, a0, a1 = _bail()
    tube = SPEC["handle_tube"] / 2.0
    handle = bkit.arc_torus("CarafeHandle", rmaj, tube, a0, a1,
                            centre=centre, plane="XZ", seg_major=48,
                            mat=glass, caps=True)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="body_diameter", mm=108.0, tol=0.3, how="diameter",
         part="CarafeBody"),
    dict(name="carafe_height", mm=232.0, tol=0.3, how="bbox_z",
         part="CarafeBody"),
    dict(name="overall_height", mm=232.0, tol=0.3, how="bbox_z"),
]
