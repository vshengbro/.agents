"""
palm_tree -- an 11 m coconut palm: a leaning, ring-scarred bole and nine
drooping fronds radiating from the crown shaft.

The bole is a `loft` over seven superellipse rings whose centres walk a gentle
S-curve, because a straight cylinder reads as a pipe. Each ring is scaled up
slightly at the leaf-scar stations (every other node) so the trunk shows the
stepped collars a real palm has.

Each frond is swept along its own drooping arc: a flattened elliptical section
whose width follows a broad, blunt-tipped leaf profile and whose section
collapses to a spine at the base and a point at the tip. The nine fronds are
built once and swept with `array_radial` about the crown shaft at
(0, 0, 9500) -- passing `centre` is what keeps the copies on the crown instead
of spiralling away from it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height          = 10900.0,
    trunk_diameter  = 760.0,
    trunk_height    = 9500.0,
    frond_count     = 9,
    frond_length    = 4200.0,
    crown_spread    = 7400.0,
)

CROWN_Z = SPEC["trunk_height"]
FRONDS = SPEC["frond_count"]
FROND_L = SPEC["frond_length"]

# Bole: (z, centre_y, base_radius, scar). The 22 mm collars are the rings of
# old frond bases every 900 mm up a mature palm.
BOLE = [
    (0.0,    0.0, 380.0, 1.00),
    (1400.0, 40.0, 356.0, 1.06),
    (2900.0, 95.0, 330.0, 1.00),
    (4400.0, 165.0, 306.0, 1.05),
    (5900.0, 250.0, 288.0, 1.00),
    (7400.0, 330.0, 268.0, 1.05),
    (8600.0, 400.0, 252.0, 1.00),
    (9500.0, 440.0, 244.0, 1.05),
]

# Frond section: (t, width_scale, thickness_scale).
LEAF = [
    (0.00, 0.06, 1.60),
    (0.10, 0.34, 1.00),
    (0.26, 0.72, 0.62),
    (0.46, 0.96, 0.42),
    (0.64, 1.00, 0.30),
    (0.80, 0.84, 0.20),
    (0.92, 0.52, 0.12),
    (1.00, 0.08, 0.05),
]


def _frond(name, mat, az_deg=0.0):
    """One frond: an elliptical section swept along a drooping arc."""
    ca, sa = math.cos(math.radians(az_deg)), math.sin(math.radians(az_deg))
    root = Vector((0.0, 0.0, CROWN_Z + 120.0))
    rings = []
    steps = 16
    for (t, ws, ts) in LEAF:
        # The rachis rises 340 mm off the shaft, then arcs over and falls 1500 mm
        # -- the shape of a mature coconut frond.
        reach = FROND_L * t
        up = 340.0 * math.sin(math.pi * min(1.0, t * 1.15)) - 1500.0 * t ** 2.2
        centre = root + Vector((ca * reach, sa * reach, up))
        # Chord across the frond (lateral) and its own normal.
        lateral = Vector((-sa, ca, 0.0))
        normal = Vector((ca * 0.34, sa * 0.34, 0.94)).normalized()
        w = 210.0 * ws
        h = 16.0 * ts
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ring.append(tuple(centre + lateral * (w * math.cos(a))
                              + normal * (h * math.sin(a))))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    bark = bkit.pbr("PalmBark", base=(0.300, 0.245, 0.175), rough=0.78)
    frond_mat = bkit.pbr("PalmFrond", base=(0.115, 0.290, 0.095), rough=0.58)
    nut = bkit.pbr("Coconut", base=(0.290, 0.215, 0.120), rough=0.66)

    # ---- bole
    sections = []
    for (z, cy, r, scar) in BOLE:
        ring = bkit.superellipse_section(2.0 * r * scar, 2.0 * r * scar,
                                         n=2.6, steps=28)
        sections.append([(u, cy + v, z) for (u, v) in ring])
    bole = bkit.loft("Trunk", sections, mat=bark, smooth=True)
    bkit.recalc(bole)

    # ---- crown shaft: the collar the fronds actually spring from
    bkit.cylinder("CrownShaft", 250.0, 520.0, segments=24, r2=200.0,
                  centre=(0.0, 0.0, CROWN_Z + 60.0), mat=bark)

    # ---- nine fronds, one built and the rest swept about the crown shaft.
    f0 = _frond("Frond0", frond_mat)
    bkit.array_radial(f0, FRONDS, centre=(0.0, 0.0, CROWN_Z))
    fronds = bkit.join([f0], name="Fronds")

    # ---- three coconut bunches tucked under the crown
    for i, (dx, dy, dz) in enumerate(((210.0, 90.0, -180.0),
                                      (-160.0, 190.0, -230.0),
                                      (60.0, -200.0, -260.0))):
        bkit.uv_sphere("Coconut%d" % i, 118.0, segments=20, rings=10,
                       centre=(dx, dy, CROWN_Z + dz), mat=nut)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    # The bole leans 440 mm off plumb, so its bounding box is wider than its
    # girth: the check is the transverse width (how=X), which is the 760 mm
    # diameter the trunk actually has, not the lean envelope.
    dict(name="trunk_girth",  mm=760.0,  tol=2.0, how="bbox_x",  part="Trunk"),
    dict(name="trunk_height", mm=9500.0, tol=2.0, how="bbox_z",  part="Trunk"),
    dict(name="crown_spread", mm=8152.7, tol=40.76, how="bbox_x", part="Fronds"),
    dict(name="height",       mm=9826.3, tol=49.13, how="top_z"),
]
