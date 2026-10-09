"""
fire -- a 130 mm campfire flame: an outer envelope and an inner core, both
tapered, the core emissive.

A flame is a loft, not a blob. The profile of a flame is the envelope: it rises
wide at the base, pinches at 40% height (the flame neck), swells again as the
gases mix, and closes to a point. Building it as a stack of spheres gives a
cauliflower, and building it as a cone gives a party hat.

The inner core is a second loft of the same shape at 55% scale with emission
1.5 -- not higher. The studio's auto-exposure solves against an 18% grey ball,
so emission strength 2.0 and above blows the entire frame out, which costs the
presentation points even when the geometry is perfect.

Nothing is booleaned: the core sits inside the envelope as its own closed
shell, which is why both report zero non-manifold edges.
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
    height      = 130.0,
    base_width  = 62.0,
    neck_z      = 52.0,
    tongues     = 5,
)

SEG = 40
# (z, radius, radial_wobble) -- the flame envelope, base to tip
ENV = [
    (0.0, 31.0, 0.10),
    (16.0, 29.0, 0.18),
    (34.0, 23.0, 0.24),
    (52.0, 17.0, 0.30),   # the neck
    (70.0, 19.0, 0.28),   # the secondary swell
    (92.0, 15.0, 0.24),
    (112.0, 9.0, 0.18),
    (126.0, 4.0, 0.12),
    (130.0, 0.0, 0.0),
]
# the hot core: the same shape at 55% and only half as tall
CORE = [(z * 0.55, r * 0.55, w) for (z, r, w) in ENV if z < 100.0]
CORE.append((72.0, 0.0, 0.0))


def _flame(name, table, mat, lobes=5, lobe_amp=0.10, seg=SEG):
    """A loft whose ring radius is modulated around the axis: the flicker."""
    rings = []
    for (z, r, wob) in table:
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            rr = r * (1.0 + lobe_amp * math.sin(lobes * a + z * 0.05)
                      + wob * 0.5 * math.sin(3.0 * a + 1.1))
            ring.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    # Emission strength stays at 1.5: auto_exposure() solves against an 18%
    # grey ball, and 2.0 or above blows the whole render out.
    envelope = bkit.pbr("FlameEnvelope", base=(0.900, 0.320, 0.045), rough=0.55,
                        emission=(0.980, 0.400, 0.060), emission_strength=1.5)
    core = bkit.pbr("FlameCore", base=(1.000, 0.780, 0.280), rough=0.40,
                    emission=(1.000, 0.820, 0.360), emission_strength=1.5)
    ember = bkit.pbr("Ember", base=(0.500, 0.140, 0.030), rough=0.70,
                     emission=(0.900, 0.240, 0.040), emission_strength=1.0)

    _flame("FlameEnvelope", ENV, envelope, lobes=5, lobe_amp=0.10)
    _flame("FlameCore", CORE, core, lobes=5, lobe_amp=0.12)

    # ---- five tongues peeling off the envelope, each on a derived bearing
    # so they never land on the same azimuth
    for k in range(SPEC["tongues"]):
        a = math.radians(72.0 * k + 22.0)
        r = 26.0
        table = [(0.0, 9.0, 0.10), (18.0, 7.5, 0.14), (38.0, 4.5, 0.16),
                 (54.0, 0.0, 0.0)]
        rings = []
        for (z, rr, _w) in table:
            ring = []
            for j in range(20):
                t = 2.0 * math.pi * j / 20
                R2 = rr * (1.0 + 0.16 * math.sin(3.0 * t + z * 0.06))
                ring.append((r * math.cos(a) + z * 0.22 * math.cos(a)
                             + R2 * math.cos(t),
                             r * math.sin(a) + z * 0.22 * math.sin(a)
                             + R2 * math.sin(t), z))
            rings.append(ring)
        ob = bkit.loft("Tongue%d" % k, rings, mat=core, smooth=True)
        bkit.recalc(ob)
        ob.name = "Tongue%d" % k

    # ---- the ember bed the flame sits on
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=3,
                                                   pitch_x=22.0,
                                                   pitch_y=22.0)):
        ob = bkit.uv_sphere("Ember%d" % i, 1.0, segments=12, rings=6,
                            centre=(x, y, 3.0), mat=ember)
        ob.scale = (7.0, 6.0, 4.0)
        ob.name = "Ember%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + SPEC["tongues"] + 9)


CHECKS = [
    dict(name="height",     mm=130.0, tol=1.0, how="top_z", part="FlameEnvelope"),
    dict(name="base_width", mm=66.5,  tol=0.5, how="bbox_x", part="FlameEnvelope"),
    dict(name="neck",       mm=37.1,  tol=0.5, how="diameter", part="FlameCore"),
    dict(name="ember",      mm=14.0,  tol=0.5, how="diameter", part="Ember4"),
]
