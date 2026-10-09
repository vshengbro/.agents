"""
smoke -- a 2000 mm plume from a campfire: 26 spheres whose radius grows and
whose spacing stretches as the plume rises, on a drifting S-curve.

Smoke is a cluster, and the cluster has to be ORGANISED or it reads as fog.
Three laws do that:

  * radius(t) grows roughly linearly with height -- smoke expands as it cools;
  * the plume's centre drifts sideways on a slow S, because a perfectly vertical
    plume reads as a steam jet;
  * the vertical spacing between puffs grows with height too, so the top of the
    plume is sparse and the bottom is dense, which is what real smoke does.

The puffs are on a `bkit.grid_positions`-derived ladder rather than random, so
the model rebuilds identically every time.
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
    height    = 2000.0,
    puffs     = 26,
    base_radius = 90.0,
    top_radius  = 260.0,
    drift     = 520.0,
)

PUFFS = SPEC["puffs"]
SEG, RING = 24, 12


def _drift(t):
    """Plume centre: a slow S in X and a slower one in Y."""
    return (SPEC["drift"] * math.sin(2.1 * t + 0.4),
            0.55 * SPEC["drift"] * math.sin(1.3 * t))


def build():
    # Transmission rather than plain white: smoke that is opaque grey reads as
    # a rock. A tinted partial transmission keeps the silhouette and still lets
    # the puffs behind show through, which is what makes it read as volume.
    body = bkit.pbr("SmokeBody", base=(0.480, 0.470, 0.460), rough=0.96,
                    transmission=0.30, ior=1.05)
    pale = bkit.pbr("SmokePale", base=(0.660, 0.655, 0.650), rough=0.96,
                    transmission=0.42, ior=1.05)
    dark = bkit.pbr("SmokeDark", base=(0.260, 0.255, 0.250), rough=0.97,
                    transmission=0.18, ior=1.05)

    # ---- puffs on a station ladder. The spacing is not uniform: stations
    # come from lay_out and are then RE-MAPPED through t**1.45, so the puffs
    # are dense at the source and sparse at the top.
    stations = [x for (x, w) in bkit.lay_out([70.0] * PUFFS, gap=26.0)]
    span = stations[-1] - stations[0]
    for i, s in enumerate(stations):
        t = ((s - stations[0]) / span) ** 1.45
        z = SPEC["height"] * t
        dx, dy = _drift(t)
        r = SPEC["base_radius"] + (SPEC["top_radius"] - SPEC["base_radius"]) * t
        # a deterministic per-puff offset so the puffs are not a perfect ladder
        ox = 70.0 * math.sin(2.7 * i) * (0.3 + 0.7 * t)
        oy = 70.0 * math.cos(1.9 * i) * (0.3 + 0.7 * t)
        mat = dark if i < 4 else (body if i % 3 else pale)
        ob = bkit.uv_sphere("Puff%02d" % i, 1.0, segments=SEG, rings=RING,
                            centre=(dx + ox, dy + oy, z), mat=mat)
        ob.scale = (r * 1.12, r, r * 0.86)
        ob.name = "Puff%02d" % i

    # ---- the source: a dense dark knot where the smoke leaves the fire
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=2,
                                                   pitch_x=52.0,
                                                   pitch_y=52.0)):
        ob = bkit.uv_sphere("Source%d" % i, 1.0, segments=16, rings=8,
                            centre=(x, y, 40.0 + 26.0 * (i % 2)), mat=dark)
        ob.scale = (78.0, 74.0, 66.0)
        ob.name = "Source%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=PUFFS + 6)


CHECKS = [
    dict(name="height", mm=2301.0, tol=11.51, how="top_z"),
    dict(name="drift",   mm=910.2,  tol=4.55, how="bbox_x"),
    dict(name="base_radius", mm=201.6, tol=1.01, how="diameter", part="Puff00"),
    dict(name="source",  mm=156.0,  tol=4.0, how="diameter", part="Source4"),
]
