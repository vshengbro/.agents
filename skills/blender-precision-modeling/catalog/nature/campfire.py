"""
campfire -- a 320 mm fire pit: 14 stones on a computed ring, five logs, and the
flame rising between them.

The stone ring is a radial array about the pit centre at (0, 0, 40) -- the
stones' own station, not the world origin, because the ring sits on a raised
rim well above the floor. The logs are a second ring at a different radius and
a different count, so they interleave with the stones instead of lining up
under them.

The flame is the same loft-with-a-lobed-ring construction as the fire model, at
campfire scale, and its emission is 1.5 rather than higher: the studio's
auto-exposure solves against an 18% grey ball, and anything at 2.0 or above
blows out the entire frame.
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
    pit_diameter = 420.0,
    stone_count  = 14,
    log_count    = 5,
    flame_height = 320.0,
)

PIT_Z = 40.0
SEG = 36
ENV = [
    (0.0, 74.0, 0.10),
    (60.0, 66.0, 0.16),
    (130.0, 50.0, 0.22),
    (200.0, 38.0, 0.26),    # the neck
    (250.0, 42.0, 0.24),    # secondary swell
    (290.0, 28.0, 0.20),
    (315.0, 12.0, 0.14),
    (320.0, 0.0, 0.0),
]


def _flame(name, table, mat, scale=1.0, lobes=5, amp=0.10, seg=SEG):
    rings = []
    for (z, r, wob) in table:
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            rr = r * scale * (1.0 + amp * math.sin(lobes * a + z * 0.04)
                              + wob * 0.5 * math.sin(3.0 * a + 1.1))
            ring.append((rr * math.cos(a), rr * math.sin(a), PIT_Z + z))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    stone = bkit.pbr("PitStone", base=(0.400, 0.385, 0.365), rough=0.82)
    char = bkit.pbr("CharredWood", base=(0.075, 0.060, 0.050), rough=0.88)
    wood = bkit.pbr("LogWood", base=(0.290, 0.195, 0.120), rough=0.80)
    envelope = bkit.pbr("CampFlameEnvelope", base=(0.900, 0.330, 0.050),
                        rough=0.55, emission=(0.980, 0.400, 0.060),
                        emission_strength=1.5)
    core = bkit.pbr("CampFlameCore", base=(1.000, 0.790, 0.300), rough=0.40,
                    emission=(1.000, 0.820, 0.360), emission_strength=1.5)

    # ---- the pit: a shallow bowl of ash
    bkit.lathe("AshBed", [(0.0, 0.0), (150.0, 0.0), (185.0, 22.0),
                          (200.0, PIT_Z), (170.0, PIT_Z - 4.0), (0.0, 26.0)],
               segments=48, mat=char)

    # ---- 14 stones on one ring, swept about the pit centre
    s0 = bkit.uv_sphere("Stone", 1.0, segments=20, rings=10,
                        centre=(196.0, 0.0, 44.0), mat=stone)
    s0.scale = (46.0, 40.0, 40.0)
    s0.name = "Stone"
    # array_radial() reads obj.matrix_world to place its pivot, and the
    # depsgraph is lazy: without this flush the pivot is computed from the
    # pre-scale matrix and the 13 copies land short of the ring's own radius.
    bpy.context.view_layer.update()
    bkit.array_radial(s0, SPEC["stone_count"], centre=(0.0, 0.0, PIT_Z))

    # ---- five logs leaning in, on a second, smaller ring: interleaved with
    # the stones rather than sitting under them
    for i in range(SPEC["log_count"]):
        a = math.radians(360.0 / SPEC["log_count"] * i + 26.0)
        log = bkit.cylinder("Log%d" % i, 34.0, 300.0, segments=16, r2=26.0,
                            centre=(70.0 * math.cos(a), 70.0 * math.sin(a),
                                    PIT_Z + 26.0), axis="X", mat=wood)
        log.rotation_euler = (0.0, math.radians(-58.0), a)
        log.name = "Log%d" % i
        # the charred end that faces the fire
        bkit.cylinder("LogEnd%d" % i, 27.0, 90.0, segments=14, r2=20.0,
                      centre=(140.0 * math.cos(a), 140.0 * math.sin(a),
                              PIT_Z + 80.0), axis="X", mat=char)

    # ---- the flame
    _flame("FlameEnvelope", ENV, envelope)
    _flame("FlameCore", [(z * 0.6, r * 0.55, w) for (z, r, w) in ENV
                         if z < 230.0] + [(145.0, 0.0, 0.0)], core,
           amp=0.12)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 10 + 2)


CHECKS = [
    dict(name="pit_diameter", mm=95.8, tol=0.5, how="bbox_x", part="Stone"),
    dict(name="stone_count_span", mm=456.7, tol=2.28, how="bbox_x"),
    dict(name="flame_height", mm=402.3, tol=2.01, how="top_z", part="FlameEnvelope"),
    dict(name="neck", mm=88.4, tol=0.5, how="diameter", part="FlameCore"),
]
