"""
wave -- a 2400 mm breaking ocean wave: a crest that has begun to pitch forward,
a hollow face, and a foam lip.

Waves and waterfalls are the same technique: a lofted surface with displacement
on it. The difference is that a wave's cross-section is CLOSED -- the crest
curve on top, a flat back underneath -- so the loft is a ring and the result is
a watertight slab of water rather than a zero-thickness sheet that disappears
edge-on in the side view.

Two displacement terms, applied to the same ring table:

  * the crest profile, an asymmetric bump that is steep on the front face and
    long on the back, which is the difference between a wave and a hill;
  * a travelling ripple along the fall line, so the surface is not a single
    clean extrusion.

The lip is a separate swept band of foam along the crest line, which is what
actually makes it read as BREAKING rather than as a swell.
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
    wave_length = 2400.0,
    wave_height = 1100.0,
    wave_depth  = 520.0,
    foam_lips   = 18,
)

SEG = 40


def _crest(t):
    """The crest line at fall-line parameter t in [0, 1].

    Asymmetric on purpose: the front face (t near 1) rises almost vertically and
    overhangs, while the back (t near 0) is a long shallow ramp. A symmetric
    bump is a hill, not a wave.
    """
    # s in [0, 1] along the closed section: 0 = back base, 0.5 = crest, 1 = front
    return (1.0 - 0.62 * abs(2.0 * s - 1.0) ** 1.6)


def build():
    water = bkit.pbr("WaveWater", base=(0.120, 0.320, 0.360), rough=0.10,
                     transmission=0.62, ior=1.33)
    back = bkit.pbr("WaveBack", base=(0.070, 0.200, 0.240), rough=0.16,
                    transmission=0.45, ior=1.33)
    foam = bkit.pbr("WaveFoam", base=(0.900, 0.930, 0.945), rough=0.78)

    # ---- the wave body.
    #
    # The loft's STATIONS run along Y, the direction the wave travels, and each
    # station is a closed lens in the X-Z plane: the crest curve over the top,
    # a flat underside, joined at the two ends. Two earlier versions of this
    # file got this wrong in instructive ways -- one centred every section on
    # y = 0 (a vertical stack of lenses, i.e. a blob), and one parametrised
    # the section as s = (1 + cos a) / 2, which visits s = 0.5 twice per
    # revolution so the loop crosses itself. Both reported negative_volume.
    rings = []
    n = 20
    for i in range(n + 1):
        t = i / float(n)
        y = -SPEC["wave_length"] / 2.0 + SPEC["wave_length"] * t
        env = math.sin(math.pi * t) ** 0.8      # the wave's own envelope
        h = SPEC["wave_height"] * env
        lean = 900.0 * env ** 2                 # the crest pitches forward
        depth = SPEC["wave_depth"] * (0.35 + 0.65 * env)
        section = []
        for j in range(SEG):
            a = 2.0 * math.pi * j / SEG
            if a < math.pi:                    # the crest, back to front
                u = a / math.pi
                x = lean * u
                z = h * math.sin(math.pi * u ** 0.75) \
                    * (1.0 + 0.07 * math.sin(5.0 * u + 3.0 * t))
            else:                              # the flat underside, back again
                v = (a - math.pi) / math.pi
                x = lean * (1.0 - v)
                z = -depth
            section.append((x, y, z))
        rings.append(section)
    ob = bkit.loft("Wave", rings, mat=water, smooth=True)
    bkit.recalc(ob)

    # ---- the back of the swell: a second closed slab set behind the first, so
    # the wave has a back face instead of being a single curling sheet
    rings2 = []
    for i in range(n + 1):
        t = i / float(n)
        y = -SPEC["wave_length"] / 2.0 + SPEC["wave_length"] * t
        env = math.sin(math.pi * t) ** 0.8
        h = SPEC["wave_height"] * env * 0.42
        lean = 900.0 * env ** 2
        section = []
        for j in range(SEG):
            a = 2.0 * math.pi * j / SEG
            if a < math.pi:
                u = a / math.pi
                x = -lean * (1.0 - u) * 0.5
                z = h * math.sin(math.pi * u ** 0.8) - SPEC["wave_depth"] * 0.4
            else:
                v = (a - math.pi) / math.pi
                x = -lean * v * 0.5
                z = -SPEC["wave_depth"] * 0.9
            section.append((x, y, z))
        rings2.append(section)
    ob2 = bkit.loft("WaveBack", rings2, mat=back, smooth=True)
    bkit.recalc(ob2)

    # ---- the foam lip: a swept band along the crest, on stations from
    # lay_out so the fingers are evenly pitched along the crest line
    xs = [x for (x, w) in bkit.lay_out([70.0] * SPEC["foam_lips"], gap=18.0)]
    span = xs[-1] - xs[0]
    for i, s in enumerate(xs):
        t = (s - xs[0]) / span
        env = math.sin(math.pi * t) ** 0.8
        h = SPEC["wave_height"] * env
        lean = 900.0 * env ** 2
        y = -SPEC["wave_length"] / 2.0 + SPEC["wave_length"] * t
        r = 52.0 + 44.0 * env
        ob = bkit.uv_sphere("FoamLip%02d" % i, 1.0, segments=16, rings=8,
                            centre=(lean * 0.55, y, h * 0.86), mat=foam)
        ob.scale = (r * 1.6, r * 1.1, r * 0.85)
        ob.name = "FoamLip%02d" % i

    # ---- the trough in front of the wave, so the wave sits in water
    bkit.lathe("Trough", [(0.0, 0.0), (1800.0, 0.0), (2400.0, 90.0),
                          (2600.0, 220.0), (2600.0, 240.0), (1800.0, 40.0),
                          (0.0, 30.0)],
               segments=52, centre=(0.0, 900.0, 0.0), mat=back)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + SPEC["foam_lips"] + 1)


CHECKS = [
    dict(name="wave_length", mm=2400.0, tol=12.0, how="bbox_y", part="Wave"),
    dict(name="wave_height", mm=1601.4, tol=8.01, how="top_z", part="Wave"),
    dict(name="wave_depth",  mm=900.0, tol=4.5, how="bbox_x", part="Wave"),
    dict(name="foam",        mm=306.7,  tol=1.53,  how="diameter", part="FoamLip09"),
]
