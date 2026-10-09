"""
icicle -- a 110 mm icicle hanging from a rock lip: a 12-segment tapered
surface of revolution with 11 internal growth rings.

An icicle is a lathe, and the profile is the model: nearly cylindrical for the
top third, then a slow taper, then a fast one to a rounded point. The internal
rings are the same lathe at 96% scale, placed on a station ladder from
`bkit.lay_out` and stepped in radius by a fixed amount per ring -- which is why
they read as growth bands rather than as a stack of washers, because each is a
slightly different diameter on a slightly different station.

The tip is closed at r = 0, so the whole thing is one watertight solid of
revolution with no seam and no boolean.
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
    length    = 110.0,
    root_radius = 6.4,
    rings     = 11,
    segments  = 12,
)

R0 = SPEC["root_radius"]
L = SPEC["length"]
SEG = SPEC["segments"]

# (z, radius). The profile is the icicle: a slow taper for the top half, then
# a fast one into the point. A straight cone reads as a carrot.
def _radius(z):
    u = min(1.0, max(0.0, z / L))
    return R0 * (1.0 - 0.30 * u - 0.70 * u ** 3.2)


# lathe() revolves a (RADIUS, z) profile. Building the table the other way
# round transposes the solid: the icicle comes out 220 mm across and 13 mm
# tall, which is a washer rather than a spike.
ICE = [(_radius(L * t / 12.0), L * t / 12.0) for t in range(13)]
ICE[0] = (R0, 0.0)
ICE[-1] = (0.0, L)


def build():
    ice = bkit.pbr("IcicleIce", base=(0.600, 0.740, 0.800), rough=0.12,
                   transmission=0.68, ior=1.31)
    ice_c = bkit.pbr("IcicleCore", base=(0.780, 0.870, 0.910), rough=0.20,
                     transmission=0.45, ior=1.31)

    body = bkit.lathe("Icicle", ICE, segments=40, mat=ice)
    bkit.recalc(body)

    # ---- the internal growth rings: each a lathe at 94% of the local radius,
    # so it sits INSIDE the body and shows through the transmissive shell.
    # z/L is clamped before the power: lay_out centres its stations, so the
    # first ones are NEGATIVE, and a negative base with a fractional exponent
    # is a complex number in Python -- the comparison against 0.8 then raises
    # TypeError instead of quietly giving a wrong radius.
    stations = [x for (x, w) in bkit.lay_out([7.0] * SPEC["rings"], gap=2.4)]
    for i, s in enumerate(stations):
        z = max(2.0, s + 7.0)
        u = min(1.0, z / L)
        r = R0 * (1.0 - 0.30 * u - 0.70 * u ** 3.2) * 0.94
        if r < 0.8:
            continue
        ring = bkit.lathe("GrowthRing%02d" % i,
                          [(0.0, 0.0), (r, 0.0), (r, 0.5), (r * 0.86, 0.9),
                           (0.0, 0.9)],
                          segments=32, centre=(0.0, 0.0, z), mat=ice_c)
        bkit.recalc(ring)

    # ---- the frozen drip collar where the icicle meets the rock lip
    bkit.lathe("DripCollar", [(0.0, -9.0), (R0 * 1.5, -8.0), (R0 * 1.7, -3.0),
                              (R0 * 1.1, 0.5), (0.0, 1.0)],
               segments=36, mat=ice)

    # ---- the rock lip it hangs from
    bkit.uv_sphere("RockLip", 1.0, segments=28, rings=14,
                   centre=(0.0, 26.0, L + 6.0),
                   mat=bkit.pbr("WetRock", base=(0.290, 0.275, 0.255),
                                rough=0.86)).scale = (86.0, 62.0, 34.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=SPEC["rings"] + 3)


CHECKS = [
    dict(name="length", mm=110.0, tol=1.0, how="bbox_z", part="Icicle"),
    dict(name="root_radius", mm=12.8, tol=0.4, how="diameter", part="Icicle"),
    dict(name="rings", mm=0.9, tol=0.1, how="bbox_z", part="GrowthRing00"),
    dict(name="collar", mm=21.8, tol=0.8, how="diameter", part="DripCollar"),
]
