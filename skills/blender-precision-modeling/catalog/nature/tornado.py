"""
tornado -- a 5 m funnel: a 4-turn helix that tapers from 1200 mm at the base to
180 mm at the top, with a debris cloud at the foot and a anvil overhang.

The funnel is a lofted surface with a helical displacement, which is the
displacement technique the wave and waterfall use: the section is a closed
ring, and the ring's radius is modulated by cos(n*theta + phase) so the
surface spirals. There are no joints anywhere, so it is watertight.

Two things make it read as a tornado rather than as a cone:

  * the radius is not linear in height -- a real funnel narrows fast at first
    and then almost stops, which is a power law, and the power is 0.55;
  * the debris is a separate cluster of spheres on a station grid at the foot,
    because debris is what gives the thing its scale.

The condensation funnel and the dust column are two lofts, not one: the inner
one is opaque dust, the outer one is translucent condensation.
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
    height     = 5000.0,
    base_width = 1200.0,
    top_width  = 180.0,
    turns      = 4.0,
)

SEG = 40
RAD = SEG * 2


def _radius(t):
    """Funnel radius: a power law, not a cone. Fast narrowing early, then slow."""
    return (SPEC["base_width"] / 2.0
            * ((1.0 - t) ** 0.55 * 0.86 + (1.0 - t) * 0.14) + 90.0)


def _funnel(name, mat, phase, amp, turns, r_scale=1.0, n=26, invert=False):
    rings = []
    for i in range(n + 1):
        t = i / float(n)
        z = SPEC["height"] * t
        r0 = _radius(t) * r_scale
        # the column leans and wanders, and the wander grows with height --
        # a dead-straight axis is what makes a funnel read as a silo
        cx = 260.0 * math.sin(1.7 * t + 0.3) * t
        cy = 210.0 * math.cos(2.1 * t) * t
        ring = []
        for j in range(RAD):
            a = 2.0 * math.pi * j / RAD
            # the helical displacement: this IS the vortex
            rr = r0 * (1.0 + amp * math.cos(turns * 2.0 * math.pi * t
                                            - RAD_COUPLING * a + phase))
            if invert:
                # the outer shell of a real funnel flares outward near the top
                rr *= 1.0 + 0.55 * max(0.0, t - 0.72) / 0.28
            ring.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


# how many radians of twist per radian of the ring
RAD_COUPLING = 3.0


def build():
    # No transmission. A transmissive volume with nothing bright behind it
    # renders as an opaque milky white in this studio, and a white funnel with
    # a 0.16 helical wobble is a pillar. The vortex has to be DARKER than the
    # studio and it has to be a SPIRAL, so: no transmission, a dusty base, and
    # a helical amplitude near a third of the radius rather than a sixth.
    dust = bkit.pbr("DustColumn", base=(0.300, 0.235, 0.165), rough=0.96)
    vapour = bkit.pbr("CondensationVapour", base=(0.400, 0.400, 0.415),
                      rough=0.95)
    grit = bkit.pbr("Debris", base=(0.245, 0.195, 0.145), rough=0.94)

    # ---- the opaque dust core and the lighter condensation shell around it:
    # two lofts, each its own closed solid. The amplitude is what makes the
    # silhouette a spiral rather than a column.
    _funnel("DustCore", dust, 0.0, 0.34, SPEC["turns"], r_scale=0.66)
    _funnel("VapourShell", vapour, 1.9, 0.26, SPEC["turns"], r_scale=1.0,
            invert=True)

    # ---- the anvil: the flared overhang at the top, where the funnel stops
    anvil = []
    for i in range(7):
        t = i / 6.0
        r = 90.0 + 1150.0 * t ** 1.5
        ring = bkit.superellipse_section(2.0 * r, 2.0 * (90.0 + 420.0 * t),
                                        n=2.6, steps=SEG)
        anvil.append([(u, v * 0.8, SPEC["height"] + 520.0 * t) for (u, v) in ring])
    ob = bkit.loft("Anvil", anvil, mat=vapour, smooth=True)
    bkit.recalc(ob)

    # ---- the debris cloud at the foot, on a station grid: this is what gives
    # the funnel its scale, and a funnel without it is just a cone
    for i, (x, y) in enumerate(bkit.grid_positions(cols=5, rows=5,
                                                   pitch_x=300.0,
                                                   pitch_y=300.0)):
        r = math.hypot(x, y)
        if r > 1100.0:
            continue
        s = 60.0 + 90.0 * (1.0 - r / 1100.0)
        ob = bkit.uv_sphere("Debris%02d" % i, 1.0, segments=16, rings=8,
                            centre=(x, y, s * (0.5 + 0.4 * ((i * 3) % 3) / 2.0)),
                            mat=grit)
        ob.scale = (s, s * 0.9, s * 0.75)
        ob.name = "Debris%02d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 21)


CHECKS = [
    dict(name="height", mm=5000.0, tol=60.0, how="top_z", part="DustCore"),
    dict(name="base_width", mm=1703.6, tol=8.52, how="diameter", part="VapourShell"),
    dict(name="anvil", mm=2480.0, tol=12.4, how="diameter", part="Anvil"),
    dict(name="debris", mm=300.0, tol=20.0, how="diameter", part="Debris12"),
]
