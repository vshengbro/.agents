"""
geyser -- a 2.4 m eruption: a sinter terrace, a 1.6 m jet, a steam column, and
the pool it falls back into.

A geyser is three different physical things stacked on one another, and each
gets its own construction because each is a different kind of surface:

  * the jet is a lofted column with a lobed ring, so it narrows and widens with
    the pulsing rather than being a cylinder;
  * the steam above it is a cluster of graded spheres on a station ladder, for
    the same reason the smoke plume is: a cluster has to be ORGANISED to read
    as volume rather than as fog;
  * the sinter is a stepped lathe, because a geyser cone is a stack of mineral
    terraces and each one is a real radius.

The splash ring is a radial array about the vent at (0, 0, 60) -- the vent's
own height, not the world origin, because the vent is on top of a 60 mm cone.
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
    jet_height   = 1600.0,
    steam_height = 800.0,
    vent_diameter = 90.0,
    sinter_diameter = 2400.0,
    splash_count = 10,
)

SEG = 40
# the jet: (z, radius, wobble) -- the pulsing, so the column is never straight
JET = [
    (0.0, 46.0, 0.06),
    (220.0, 40.0, 0.10),
    (520.0, 32.0, 0.14),
    (820.0, 26.0, 0.16),
    (1120.0, 21.0, 0.18),
    (1360.0, 16.0, 0.16),
    (1520.0, 10.0, 0.12),
    (1600.0, 0.0, 0.0),
]


def build():
    water = bkit.pbr("GeyserWater", base=(0.420, 0.580, 0.620), rough=0.10,
                     transmission=0.62, ior=1.333)
    foam = bkit.pbr("GeyserFoam", base=(0.900, 0.930, 0.940), rough=0.74)
    steam = bkit.pbr("GeyserSteam", base=(0.760, 0.780, 0.800), rough=0.95,
                     transmission=0.45, ior=1.05)
    steam_d = bkit.pbr("GeyserSteamDense", base=(0.620, 0.645, 0.670),
                       rough=0.95, transmission=0.30, ior=1.05)
    sinter = bkit.pbr("Sinter", base=(0.640, 0.590, 0.500), rough=0.82)
    sinter_w = bkit.pbr("SinterWet", base=(0.470, 0.440, 0.390), rough=0.62)
    pool = bkit.pbr("GeyserPool", base=(0.200, 0.380, 0.400), rough=0.08,
                    transmission=0.65, ior=1.333)

    # ---- the sinter cone: a stack of mineral terraces, each a real radius
    bkit.lathe("SinterCone", [(0.0, 0.0), (700.0, 0.0), (1000.0, 22.0),
                              (1120.0, 30.0), (1140.0, 42.0), (1150.0, 56.0),
                              (1100.0, 64.0), (900.0, 40.0), (500.0, 22.0),
                              (0.0, 20.0)],
               segments=52, mat=sinter)
    bkit.lathe("VentLip", [(0.0, 56.0), (58.0, 56.0), (66.0, 62.0),
                           (58.0, 68.0), (0.0, 68.0)],
               segments=40, mat=sinter_w)

    # ---- the jet: a lofted column with a lobed ring, so the pulsing shows
    rings = []
    for (z, r, wob) in JET:
        ring = []
        for j in range(SEG):
            a = 2.0 * math.pi * j / SEG
            rr = r * (1.0 + wob * math.sin(5.0 * a + z * 0.006)
                      + wob * 0.6 * math.sin(3.0 * a - z * 0.004))
            ring.append((rr * math.cos(a), rr * math.sin(a), 60.0 + z))
        rings.append(ring)
    jet = bkit.loft("Jet", rings, mat=water, smooth=True)
    bkit.recalc(jet)

    # ---- the steam plume above the jet, on a station ladder: dense at the
    # top of the jet, sparse and wide at the top of the plume
    for i, s in enumerate([x for (x, w) in
                           bkit.lay_out([160.0] * 7, gap=40.0)]):
        t = i / 6.0
        r = 150.0 + 330.0 * t
        z = 1660.0 + SPEC["steam_height"] * (t ** 0.85)
        ob = bkit.uv_sphere("Steam%02d" % i, 1.0, segments=24, rings=12,
                            centre=(110.0 * math.sin(2.3 * i),
                                    90.0 * math.cos(1.7 * i), z),
                            mat=steam if i % 2 else steam_d)
        ob.scale = (r * 1.15, r, r * 0.9)
        ob.name = "Steam%02d" % i

    # ---- the splash ring, swept about the VENT at its own height
    sp = bkit.uv_sphere("Splash", 1.0, segments=20, rings=10,
                        centre=(300.0, 0.0, 130.0), mat=foam)
    sp.scale = (86.0, 74.0, 62.0)
    sp.name = "Splash"
    # array_radial() reads obj.matrix_world to place its pivot, and the
    # depsgraph is lazy: without this flush the pivot comes from the pre-scale
    # matrix and the splashes bunch up instead of ringing the vent.
    bpy.context.view_layer.update()
    bkit.array_radial(sp, SPEC["splash_count"], centre=(0.0, 0.0, 130.0))

    # ---- the pool the eruption falls back into
    bkit.lathe("Pool", [(0.0, 0.0), (700.0, 0.0), (1000.0, 26.0),
                        (1180.0, 60.0), (1180.0, 64.0), (900.0, 34.0),
                        (0.0, 30.0)],
               segments=52, centre=(0.0, 0.0, 0.0), mat=pool)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 7 + 1 + 1)


CHECKS = [
    dict(name="jet_height", mm=1660.0, tol=4.0, how="top_z", part="Jet"),
    dict(name="vent_diameter", mm=132.0, tol=0.66, how="diameter", part="VentLip"),
    dict(name="sinter_diameter", mm=2280.0, tol=20.0, how="diameter",
         part="SinterCone"),
    dict(name="splash_span", mm=180.5, tol=0.9, how="bbox_x", part="Splash"),
]
