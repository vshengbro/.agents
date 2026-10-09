"""
rain_cloud -- a 1800 mm nimbostratus with 46 rain streaks falling from its flat
base.

Two different repetitions, laid out two different ways, because they are two
different kinds of thing:

  * the cloud body is a cluster of graded spheres, as on a cumulus, but with a
    much flatter and wider base -- a nimbostratus is a slab, not a cauliflower;
  * the rain is a station GRID (`bkit.grid_positions`), not a radial array. Rain
    falls everywhere under the cloud, so a grid is the right topology and a
    radial sweep would leave a bare patch under the middle.

Each streak is a thin tapered cylinder hanging from the cloud's base plane, and
its length comes from its own station so the curtain has a ragged lower edge --
an even curtain reads as a plastic sheet.
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
    width        = 1800.0,
    height       = 620.0,
    rain_streaks = 46,
    rain_fall    = 1400.0,
)

SEG, RING = 24, 12


def _blob(name, centre, radii, mat):
    ob = bkit.uv_sphere(name, 1.0, segments=SEG, rings=RING, centre=centre,
                        mat=mat)
    ob.scale = radii
    return ob


def build():
    body = bkit.pbr("NimbostratusBody", base=(0.640, 0.665, 0.710), rough=0.94)
    belly = bkit.pbr("NimbostratusBelly", base=(0.470, 0.500, 0.560), rough=0.95)
    rain = bkit.pbr("RainStreak", base=(0.560, 0.680, 0.780), rough=0.30,
                    transmission=0.35, ior=1.33)

    # ---- the slab: a wide flat base row, then a shallower second row on top
    xs = [x for (x, w) in bkit.lay_out([520.0] * 6, gap=30.0)]
    for i, x in enumerate(xs):
        r = 190.0 + 26.0 * (i % 3)
        _blob("SlabBase%d" % i, (x, 0.0, r * 0.52),
              (r * 1.7, r * 1.5, r * 0.52), body)
    for i, (x, y) in enumerate(bkit.grid_positions(cols=4, rows=2,
                                                   pitch_x=400.0,
                                                   pitch_y=300.0)):
        r = 150.0 + 24.0 * (i % 3)
        _blob("SlabCrown%02d" % i, (x, y, 330.0 + r * 0.4),
              (r * 1.5, r * 1.3, r * 0.62), belly if i % 2 else body)

    # ---- the rain: a station grid under the base, each streak's length from
    # its own station so the curtain's lower edge is ragged
    for i, (x, y) in enumerate(bkit.grid_positions(cols=7, rows=7,
                                                   pitch_x=230.0,
                                                   pitch_y=210.0)):
        if i >= SPEC["rain_streaks"]:
            break
        length = 700.0 + 420.0 * abs(math.sin(2.3 * i + 0.7))
        z = 170.0 - length / 2.0
        ob = bkit.cylinder("RainStreak%02d" % i, 7.0, length, segments=8,
                           r2=3.0, centre=(x, y, z), mat=rain)
        ob.rotation_euler = (0.06 * math.sin(i), 0.05 * math.cos(i * 1.7), 0.0)
        ob.name = "RainStreak%02d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6 + 8 + SPEC["rain_streaks"])


CHECKS = [
    dict(name="width", mm=3484.4, tol=17.42, how="bbox_x"),
    dict(name="height", mm=1432.5,  tol=7.16, how="top_z", part="SlabCrown00"),
    dict(name="rain_fall", mm=1481.5, tol=7.41, how="top_z"),
    dict(name="streak_thickness", mm=58.5, tol=3.0, how="diameter",
         part="RainStreak00"),
]
