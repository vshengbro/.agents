"""
vase_modes -- a 132 mm fluted vessel whose wall is a sum of angular modes.

The radius is not a function of height alone. Each ring is

    r(z, theta) = base(z) * (1 + fade(z) * SUM_m a_m * cos(m*(theta - phi_m)))

i.e. the vessel's silhouette (the axial mode) plus five angular modes
(m = 3, 5, 6, 7, 9) beating against each other. That interference is the
decoration: no two flutes are identical, which is exactly what makes a
lathe-turned vase look machined and this one look grown.

It is a loft of rings, so the rim is closed by capping start and end. The
inner wall runs back down to a small flat floor of radius 2 mm rather than to
r = 0 -- a ring at r = 0 would cap to an n-gon of coincident vertices, which
`validate()` deletes and which leaves a hole in the base.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height=132.0,
    max_diameter=88.0,
    wall=3.0,
    modes=(3, 5, 6, 7, 9),      # angular wavenumbers summed on the wall
    mode_amplitudes=(0.030, 0.020, 0.024, 0.014, 0.010),
    foot_diameter=44.0,
    rim_diameter=52.0,
    width=91.02,
    depth=87.66,
)

H = SPEC["height"]
WALL = SPEC["wall"]
SEG = 128
FLOOR_R = 2.0

CHECKS = [
    dict(name="height", mm=132.0, tol=0.6, how="bbox_z", part="VaseModes"),
    dict(name="width", mm=91.02, tol=1.0, how="bbox_x", part="VaseModes"),
    dict(name="depth", mm=87.66, tol=1.0, how="bbox_y", part="VaseModes"),
]


def _silhouette(z):
    """The axisymmetric profile r(z): foot, belly, waist, flared rim."""
    t = z / H
    r = 22.0 + 22.0 * math.sin(math.pi * min(1.0, t * 1.06) ** 0.85)
    if t > 0.74:                       # pull the neck in above the belly
        r -= 12.0 * (t - 0.74) / 0.26
    if t > 0.93:                       # then flare the lip back out
        r += 5.0 * (t - 0.93) / 0.07
    return r


def _fade(z):
    """Flutes fade in above the foot and out again below the lip."""
    t = z / H
    return min(1.0, max(0.0, (t - 0.06) / 0.10)) * min(1.0, max(0.0, (0.99 - t) / 0.06))


def _ring(r, z, fade):
    """One cross-section: the silhouette modulated by the angular modes."""
    pts = []
    for j in range(SEG):
        th = 2.0 * math.pi * j / SEG
        wob = 0.0
        for m, a in zip(SPEC["modes"], SPEC["mode_amplitudes"]):
            # each mode carries its own drifting phase
            wob += a * math.cos(m * (th - 0.35 * z / H))
        rr = r * (1.0 + fade * wob)
        pts.append((rr * math.cos(th), rr * math.sin(th), z))
    return pts


def build():
    sections = []

    # --- up the outside -----------------------------------------------------
    steps = 56
    for k in range(steps + 1):
        z = H * k / steps
        sections.append(_ring(_silhouette(z), z, _fade(z)))

    # --- over the rim and back down the inside ------------------------------
    # The inner rings reuse the OUTER modulation at the same height, so the rim
    # band is a clean flat annulus instead of a sheared, twisted collar.
    inner_top = _silhouette(H) - WALL
    rim_inner = _ring(inner_top, H, _fade(H))
    # ONE section, not one section per angle: loft() takes a list of equal-
    # length rings, so appending SEG single-point rings fails its own check.
    sections.append(rim_inner)

    wall_steps = 40
    for k in range(1, wall_steps + 1):
        z = H * (1.0 - k / wall_steps)
        r = max(FLOOR_R, _silhouette(z) - WALL * (0.6 + 0.4 * z / H))
        sections.append(_ring(r, z, _fade(z)))

    mat = bkit.pbr("VaseGlaze", base=(0.30, 0.50, 0.62), metal=0.10, rough=0.20,
                   coat=0.5)
    vase = bkit.loft("VaseModes", sections, closed_loop=True,
                     cap_start=True, cap_end=True, mat=mat)
    bkit.recalc(vase)
    bkit.shade_smooth(vase, 42)

    return dict(spec=SPEC, parts=1)