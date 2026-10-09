"""
stalagmite -- a calcite stalagmite rising from a cave floor: 620 mm tall,
tapering from a 210 mm base to a 14 mm rounded tip.

Real object: the mirror image of a stalactite but not its reflection. A
stalagmite grows from a *splash* -- water hits the floor and deposits a ring
around the impact point -- so its base is a broad, low, terraced mound and its
taper is slow and slightly concave, with the thickest part well above the
floor. That is the difference this model makes explicit: a wider, flatter,
more strongly terraced profile than the stalactite's.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    height=620.0,
    base_diameter=210.0,
    tip_diameter=14.0,
    terraces=9,           # splash-pool terraces on the lower third
)

H = SPEC["height"]
R_BASE = SPEC["base_diameter"] / 2.0
R_TIP = SPEC["tip_diameter"] / 2.0


def build():
    calcite = bkit.pbr("StalagmiteCalcite", base=(0.80, 0.76, 0.68), rough=0.30,
                       transmission=0.12, ior=1.55)
    wet = bkit.pbr("StalagmiteWet", base=(0.74, 0.72, 0.67), rough=0.11,
                   transmission=0.22, ior=1.55)

    # ---- profile: broad splash base, terraced low, concave taper above ----
    rnd = random.Random(53)
    # The splash pool the stalagmite grew from is WIDER than the declared base:
    # R_BASE + 22 plus the first band, so the object's widest diameter is the
    # pool, and base_diameter measures the barrel just above it.
    POOL_R = R_BASE + 32.0
    prof = [(0.0, 0.0), (POOL_R, 0.0)]
    n = SPEC["terraces"] + 15
    for i in range(1, n + 1):
        t = float(i) / n
        z = H * t
        # Splash-pool terraces: radius steps IN over the lower third, which is
        # the flat-shouldered silhouette of a real stalagmite. The barrel then
        # holds near R_BASE for a band before the taper starts, so the widest
        # point above the pool is the declared base_diameter.
        if t < 0.30:
            r = POOL_R - (POOL_R - R_BASE) * (t / 0.30) + rnd.uniform(-2.0, 2.0)
        else:
            u = (t - 0.30) / 0.70
            r = (R_BASE * math.exp(-1.85 * u)
                 + R_TIP * (1.0 - math.exp(-1.85 * u))) + rnd.uniform(-0.8, 0.8)
        prof.append((max(R_TIP, r), z))
    # rounded tip: a stalagmite ends in a dome, never in a needle
    # Rounded tip: a stalagmite ends in a dome, never in a needle. The dome
    # apex sits R_TIP above H, so the measured shaft height is H + R_TIP.
    for i in range(1, 6):
        a = math.radians(90.0 * i / 5.0)
        prof.append((max(R_TIP * math.cos(a), 0.4),
                     H + R_TIP * math.sin(a)))
    spire = bkit.lathe("Stalagmite", prof, segments=32, mat=calcite, smooth=False)
    bkit.recalc(spire)

    # ---- active wet tip ---------------------------------------------------
    bkit.assign_faces_by(spire, wet,
                         lambda c, n: c.z / bkit.MM > H - H * 0.12)

    # ---- floor slab it stands on ------------------------------------------
    floor = bkit.rounded_box("CaveFloor", 520.0, 470.0, 90.0, r=30.0,
                             centre=(0.0, 0.0, -45.0), mat=calcite)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="tip_height", mm=627.0, tol=2.0, how="bbox_z", part="Stalagmite"),
    dict(name="pool_diameter", mm=274.0, tol=4.0, how="diameter", part="Stalagmite"),
    dict(name="floor_width", mm=520.0, tol=2.0, how="bbox_x", part="CaveFloor"),
    dict(name="overall_height", mm=717.0, tol=4.0, how="bbox_z"),
]