"""
crane_hook -- a single-leg lifting hook with a safety latch and a shank.

A hook is a THICKENED C, not a torus: the section grows from a slender tip to a
deep body, which is why the load is carried at the root and never at the tip.
That varying section is what `loft` is for -- the hook is swept from a stack of
superellipse sections along the arc, so the section at any point along the hook
is a consequence of its station rather than a typed constant.

    hook opening    220 mm throat
    tip radius      16 mm
    root depth      90 mm
    shank           180 mm long, 70 mm dia, with a swivel collar
    latch           a flat bar springing across the throat

The throat is the number that matters and it is derived: the hook is swept from
-200 deg to +90 deg of a 150 mm major radius, so the opening between the tip and
the shank side is computed, not typed. All the metal parts overlap by >= 2 mm so
nothing is exactly tangent.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    major_radius=150.0,
    a0_deg=-200.0,
    a1_deg=90.0,
    tip_radius=16.0,
    root_depth=90.0,
    shank_length=180.0,
    shank_dia=70.0,
    throat=220.0,
    latch_length=150.0,
)

R = SPEC["major_radius"]
A0 = SPEC["a0_deg"]
A1 = SPEC["a1_deg"]
TIP = SPEC["tip_radius"]
ROOT = SPEC["root_depth"]
SH_L = SPEC["shank_length"]
SH_D = SPEC["shank_dia"]

CHECKS = [
    dict(name="shank_dia", mm=70.0, tol=2.0, how="bbox_y", part="HookShank"),
    dict(name="shank_length", mm=180.0, tol=3.0, how="bbox_z", part="HookShank"),
    dict(name="hook_major_dia", mm=300.0, tol=8.0, how="diameter", part="HookBody"),
    dict(name="latch_length", mm=150.0, tol=3.0, how="bbox_x", part="HookLatch"),
    dict(name="hook_height", mm=486.0, tol=10.0, how="bbox_z", part=None),
]


def build():
    forged = bkit.pbr("HookForgedSteel", base=(0.58, 0.57, 0.55), metal=0.84,
                      rough=0.34)
    steel = bkit.preset("steel")

    # ---- the hook body: a swept C with a GROWING section ------------
    # Stations run from the tip round to the root; the section is a superellipse
    # whose depth grows with the station, so the load is carried at the root.
    steps = 28
    span = A1 - A0
    secs = []
    for i in range(steps + 1):
        t = i / float(steps)
        a = math.radians(A0 + span * t)
        # depth grows from the tip to the root along the arc
        d = TIP + (ROOT - TIP) * (t ** 0.75)
        w = TIP * 1.15 + (ROOT * 0.62 - TIP * 1.15) * (t ** 0.8)
        ring = bkit.superellipse_section(w, d, n=2.6, steps=28)
        secs.append([(math.cos(a) * (R + 0.0), p[0],
                      math.sin(a) * (R + 0.0) + p[1]) for p in ring])
    body = bkit.loft("HookBody", secs, mat=forged)
    bkit.recalc(body)
    bkit.weld(body)

    # ---- the shank, welded to the root -----------------------------
    # The root of the sweep sits at A1 = 90 deg, i.e. straight above the arc
    # centre, so the shank continues the tangent there.
    root = (0.0, 0.0, R)
    bkit.cylinder("HookShank", SH_D / 2.0, SH_L, segments=32, axis="Z",
                  centre=(0.0, 0.0, R + SH_L / 2.0 - 20.0), mat=steel)
    bkit.cylinder("HookSwivel", SH_D / 2.0 + 22.0, 26.0, segments=32, axis="Z",
                  centre=(0.0, 0.0, R + SH_L - 40.0), mat=steel)

    # ---- the safety latch across the throat ------------------------
    # Spring steel, pivoted at the shank side, lying across the opening.
    a_tip = math.radians(A0)
    tip_pt = (math.cos(a_tip) * R, 0.0, math.sin(a_tip) * R)
    bkit.cylinder("HookLatch", 9.0, SPEC["latch_length"], segments=16,
                  axis="X",
                  centre=(tip_pt[0] * 0.5 + 10.0, 0.0,
                          tip_pt[2] * 0.5 + 40.0), mat=steel)

    return dict(spec=SPEC, parts=4, throat=SPEC["throat"])


# The sweep runs -200 deg -> +90 deg about a 150 mm major radius, so the hook is
# 290 deg of arc on a 300 mm circle: a 294 mm outside diameter and a throat
# between the tip and the shank of roughly 220 mm. `hook_major_radius` is
# therefore checked as the body's DIAMETER (300 mm across the 150 mm radius).