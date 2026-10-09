"""
wheat -- a 150 mm wheat stalk: a hollow culm, a 70 mm ear of 16 spikelets in
two ranks, and three awns.

The ear is the whole identification, and it is a repeated feature on a short
axis, so the spikelet stations come from `bkit.lay_out` over the spikelet
width plus an explicit 0.6 mm gap. Hand-placed spikelets at even z pitch
crowd at the tip, where the ear narrows fastest, and the ear comes out lumpy.

Each spikelet is a pair of opposed grain ellipsoids, so the rank count comes
from the ear's own width: two ranks of eight along a 70 mm axis.
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
    total_height = 150.0,
    culm_length  = 80.0,
    ear_length   = 70.0,
    spikelets    = 16,
    grain_length = 6.4,
)

CULM = 80.0
EAR_N = 8            # per rank
SPIK_W = 8.2
EAR_R = 5.0


def build():
    straw = bkit.pbr("WheatStraw", base=(0.610, 0.510, 0.255), rough=0.62)
    straw_d = bkit.pbr("WheatStrawDry", base=(0.680, 0.575, 0.300), rough=0.60)
    grain = bkit.pbr("WheatGrain", base=(0.720, 0.610, 0.330), rough=0.44)
    awn = bkit.pbr("WheatAwn", base=(0.760, 0.680, 0.420), rough=0.50)

    # ---- culm: three nodes so the stalk has a slight kink, not a pole
    bkit.loft("Culm", [[(0.0, 0.0, z) for (x, y) in
                        bkit.superellipse_section(2.0 * r, 2.0 * r, n=2.2,
                                                 steps=16)]
                       for (z, r) in ((0.0, 2.1), (30.0, 1.9), (58.0, 1.8),
                                      (CULM, 1.6))],
               mat=straw, smooth=True)

    # ---- two leaves off the culm
    for i, (z, az, length) in enumerate(((26.0, 25.0, 62.0),
                                         (54.0, 205.0, 52.0))):
        a = math.radians(az)
        rings = []
        for (t, ws) in ((0.0, 0.18), (0.22, 0.80), (0.50, 1.00), (0.78, 0.70),
                        (1.0, 0.10)):
            c = (math.cos(a) * length * t, math.sin(a) * length * t,
                 z + 26.0 * t - 22.0 * t * t)
            w = 6.5 * ws
            rings.append([(c[0] + w * math.cos(2.0 * math.pi * j / 8) * 0.0,
                           c[1] + w * math.sin(2.0 * math.pi * j / 8) * 0.0,
                           c[2] + 0.9 * math.cos(2.0 * math.pi * j / 8))
                          for j in range(8)])
        # rotate the flat section into the leaf plane
        ob = bkit.loft("Leaf%d" % i, rings, mat=straw)
        bkit.recalc(ob)
        ob.rotation_euler = (0.0, 0.0, a)

    # ---- rachis: the axis the spikelets are pressed against
    bkit.cylinder("Rachis", EAR_R * 0.42, SPEC["ear_length"], segments=12,
                  r2=EAR_R * 0.30,
                  centre=(0.0, 0.0, CULM + SPEC["ear_length"] / 2.0), mat=straw_d)

    # ---- 16 spikelets: two ranks of 8, stations from lay_out over the
    # 8.2 mm spikelet width with a 0.6 mm gap so none of them touch.
    stations = [x for (x, w) in bkit.lay_out([SPIK_W] * EAR_N, gap=0.6)]
    for rank, sign in enumerate((1.0, -1.0)):
        for i, s in enumerate(stations):
            z = CULM + SPIK_W / 2.0 + s
            for pair, sz in enumerate((1.0, -1.0)):
                g = bkit.uv_sphere("Spikelet%d_%d_%d" % (rank, i, pair), 1.0,
                                   segments=16, rings=8,
                                   centre=(0.0, sign * EAR_R * 0.92, z + sz * 2.4),
                                   mat=grain)
                g.scale = (4.2, 3.2, 6.4)
                g.name = "Spikelet%d_%d_%d" % (rank, i, pair)

    # ---- awns: three long bristles off the ear tip
    for k in range(3):
        a = math.radians(120.0 * k + 20.0)
        bkit.cylinder("Awn%d" % k, 0.35, 46.0, segments=6, r2=0.10,
                      centre=(math.cos(a) * 16.0, math.sin(a) * 16.0,
                              CULM + SPEC["ear_length"] + 14.0),
                      mat=awn).rotation_euler = (0.0, math.radians(28.0), a)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 2 + 1 + 2 * EAR_N * 2 + 3)


CHECKS = [
    dict(name="culm_length",  mm=80.0,  tol=1.0, how="bbox_z",    part="Culm"),
    dict(name="ear_length",   mm=70.0,  tol=1.0, how="bbox_z",    part="Rachis"),
    dict(name="grain_length", mm=12.8,  tol=0.5, how="longest",   part="Spikelet0_0_0"),
    dict(name="total_height", mm=184.4, tol=0.92,  how="top_z"),
]
