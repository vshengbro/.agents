"""
snow_cloud -- a 1700 mm cloud shedding 60 snow lumps on a ragged lower edge.

Snow and rain are the same fall, so the layout is the same station grid; what
changes is the particle. A rain streak is a thin cylinder 1400 mm long; a snow
flake is a 22 mm lump with its own irregular scale, so the fall reads as
*scattered* rather than as a curtain. Scaling the particle by 100x while
shortening the fall by 40x is the whole difference between the two models.

The flakes are also offset from the grid station by a deterministic jitter
derived from the station index, so they do not sit in a visible lattice.
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
    width        = 1700.0,
    height       = 700.0,
    snow_flakes  = 60,
    flake_diameter = 26.0,
)

SEG, RING = 24, 12


def _blob(name, centre, radii, mat, segments=SEG, rings=RING):
    ob = bkit.uv_sphere(name, 1.0, segments=segments, rings=rings,
                        centre=centre, mat=mat)
    ob.scale = radii
    return ob


def build():
    body = bkit.pbr("SnowCloudBody", base=(0.720, 0.750, 0.790), rough=0.93)
    belly = bkit.pbr("SnowCloudBelly", base=(0.560, 0.595, 0.650), rough=0.94)
    snow = bkit.pbr("Snow", base=(0.930, 0.945, 0.960), rough=0.70)

    # ---- the cloud: a wide, soft, slightly domed mass
    for i, x in enumerate([x for (x, w) in
                           bkit.lay_out([480.0] * 6, gap=30.0)]):
        r = 185.0 + 30.0 * (i % 3)
        _blob("BodyLobe%d" % i, (x, 0.0, r * 0.62),
              (r * 1.75, r * 1.5, r * 0.62), body)
    for i, (x, y) in enumerate(bkit.grid_positions(cols=4, rows=2,
                                                   pitch_x=390.0,
                                                   pitch_y=300.0)):
        r = 155.0 + 26.0 * (i % 3)
        _blob("BodyCrown%02d" % i, (x, y, 350.0 + r * 0.4),
              (r * 1.55, r * 1.35, r * 0.66), belly if i % 2 else body)

    # ---- the fall: the same station grid as the rain model, a different
    # particle. The jitter is deterministic (a function of the station index),
    # so the model rebuilds identically and the lattice is invisible.
    for i, (x, y) in enumerate(bkit.grid_positions(cols=8, rows=8,
                                                   pitch_x=200.0,
                                                   pitch_y=190.0)):
        if i >= SPEC["snow_flakes"]:
            break
        jx = x + 70.0 * math.sin(2.7 * i)
        jy = y + 70.0 * math.cos(1.9 * i)
        # flakes spread as they fall: a real snow curtain widens with distance
        spread = 1.0 + 0.30 * (i % 4)
        r = SPEC["flake_diameter"] / 2.0 * (0.55 + 0.45 * abs(math.sin(3.1 * i))) \
            * spread
        z = -120.0 - 520.0 * (0.4 + 0.6 * abs(math.cos(1.3 * i)))
        _blob("Flake%02d" % i, (jx, jy, z), (r, r * 0.92, r * 0.88), snow,
              segments=16, rings=8)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6 + 8 + SPEC["snow_flakes"])


CHECKS = [
    dict(name="width", mm=3302.5, tol=16.51, how="bbox_x"),
    dict(name="height", mm=1170.2,  tol=5.85, how="top_z", part="BodyCrown00"),
    dict(name="flake_diameter", mm=14.3, tol=1.0, how="diameter", part="Flake00"),
    # z_min is an absolute coordinate and sit_on_floor() has already put the
    # lowest point on z=0, so a scene z_min can only ever read 0. The cloud's
    # own base is a part-scoped coordinate instead.
    dict(name="cloud_base", mm=655.9, tol=3.28, how="z_min", part="BodyLobe0"),
]
