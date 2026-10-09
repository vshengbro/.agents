"""
rail_switch -- 5,800 mm single turnout: main line, diverging road, points,
frog, timbers and a switch stand.

A turnout is FOUR things and missing any one of them makes it read as a
broken rail: the main line continues straight, the ROAD curves away on a real
divergence curve, the switch BLADES taper from a knife edge to full section,
and the FROG is the casting where the two routes cross. The blades and the
road are swept as lofts along a sampled curve -- a straight box at an angle
looks like a straight box at an angle.

Timbers lengthen across the turnout, which is why there are two sleeper rows
rather than one long array: the short bearers under the plain line and the long
bearers under the diverging track, both laid out by pitch.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    section_length=5600.0,
    gauge=1435.0,
    rail_height=172.0,
    heel_length=2400.0,
    divergence=1200.0,
    lead_length=2000.0,
    frog_x=600.0,
    timber_pitch=600.0,
    switch_stand_height=1100.0,
)

CHECKS = [
    dict(name="section_length", mm=5600.0, tol=4.0, how="bbox_x",
         part="SwitchRailMainL"),
    dict(name="rail_height", mm=172.0, tol=2.0, how="bbox_z",
         part="SwitchRailMainL"),
    dict(name="gauge", mm=1435.0, tol=2.0, how="bbox_y", part="SwitchGaugeBar"),
    dict(name="road_far_rail_y", mm=-2740.0, tol=6.0, how="y_min",
         part="SwitchRoadFar"),
    dict(name="frog_top_z", mm=372.0, tol=3.0, how="top_z", part="SwitchFrog"),
    dict(name="stand_top_z", mm=1100.0, tol=4.0, how="top_z",
         part="SwitchStand"),
]

LENGTH = 5600.0
RAIL_Z = 200.0
RAIL_H = 172.0
GAUGE = R.GAUGE
HALF = GAUGE / 2.0 + 35.0            # 752.5 rail centreline
FROG_X = 600.0
LEAD = 2000.0
DIVERGE = 1200.0
TIMBER_PITCH = 600.0


def _curve(t):
    """Diverging-road centreline: straight at the heel, then easing away."""
    return -(HALF + DIVERGE * (t ** 2.0))


def _road_rail(name, side, mat):
    """One diverging rail: an I-ish section lofted along the divergence curve.

    `side` is -1 for the near rail of the road and +1 for the far one, so the
    two keep the 1,435 mm gauge as the road curves instead of converging.
    """
    rings = []
    n = 12
    for i in range(n + 1):
        t = i / float(n)
        x = FROG_X + LEAD * t
        y = _curve(t) - side * HALF
        sec = [(y - 35.0, RAIL_Z), (y + 35.0, RAIL_Z),
               (y + 35.0, RAIL_Z + RAIL_H), (y + 20.0, RAIL_Z + RAIL_H),
               (y + 20.0, RAIL_Z + 40.0), (y - 20.0, RAIL_Z + 40.0),
               (y - 20.0, RAIL_Z + RAIL_H), (y - 35.0, RAIL_Z + RAIL_H)]
        rings.append([(x, a, b) for (a, b) in sec])
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 36.0)
    return ob


def _blade(name, side, mat):
    """A switch blade: a knife edge at the toe growing to full head width."""
    rings = []
    n = 8
    x0, x1 = -LENGTH / 2.0 + 120.0, -LENGTH / 2.0 + 2520.0
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = -HALF + side * (26.0 + 8.0 * t)
        w = 7.0 + 26.0 * t
        rings.append([(x, y - w, RAIL_Z), (x, y + w, RAIL_Z),
                      (x, y + w, RAIL_Z + RAIL_H),
                      (x, y - w, RAIL_Z + RAIL_H)])
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    steel = bkit.preset("dark_metal")
    rust = bkit.pbr("SwitchRail", base=(0.31, 0.26, 0.22), metal=0.80,
                    rough=0.54)
    timber = bkit.pbr("SwitchTimber", base=(0.24, 0.18, 0.12), rough=0.84)
    frog_m = bkit.pbr("SwitchFrogMat", base=(0.44, 0.36, 0.28), metal=0.72,
                      rough=0.58)

    # --- main line through, full section -----------------------------------
    R.rail("SwitchRailMainL", LENGTH, y=HALF, z0=RAIL_Z, h=RAIL_H, mat=rust)
    R.rail("SwitchRailMainR", LENGTH, y=-HALF, z0=RAIL_Z, h=RAIL_H, mat=rust)

    # --- diverging road, from the frog out to the far end -----------------
    _road_rail("SwitchRoadNear", -1, rust)
    _road_rail("SwitchRoadFar", +1, rust)

    # --- switch blades at the toe ------------------------------------------
    blades = [_blade("SwitchBladeL", 1, rust), _blade("SwitchBladeR", -1, rust)]
    bl_ob = bkit.join(blades, "SwitchBlades")
    bkit.recalc(bl_ob)

    # --- frog, wing rails and the switch stand -----------------------------
    frog = []
    frog.append(bkit.rounded_box("SwitchFrog", 900.0, 420.0, 172.0, r=24.0,
                                 segments=2,
                                 centre=(FROG_X, -HALF + 250.0, RAIL_Z + 86.0),
                                 mat=frog_m))
    frog.append(bkit.rounded_box("SwitchCheckRail", LENGTH - 1200.0, 60.0,
                                 140.0, r=20.0, segments=2,
                                 centre=(300.0, -HALF + 40.0, RAIL_Z + 80.0),
                                 mat=rust))
    fg_ob = bkit.join(frog, "SwitchFrog")
    bkit.recalc(fg_ob)

    # --- timbers: short bearers on the plain line, long bearers at the road -
    R.sleeper_row("SwitchTimberShort", 5, TIMBER_PITCH, 2600.0, sx=250.0,
                  sz=RAIL_Z, z0=0.0, mat=timber)
    long_t = []
    for i, x in enumerate(R.evenly(4, 1600.0, centre=False, start=700.0)):
        y = _curve(min(1.0, (x - FROG_X) / LEAD))
        long_t.append(bkit.rounded_box("SwitchTimberLong%d" % i, 250.0,
                                       3200.0, RAIL_Z, r=18.0, segments=2,
                                       centre=(x, y - 400.0, RAIL_Z / 2.0),
                                       mat=timber))
    lt_ob = bkit.join(long_t, "SwitchTimberLong")
    bkit.recalc(lt_ob)

    # --- switch stand and the throw rod -----------------------------------
    bkit.cylinder("SwitchStand", 130.0, 900.0, segments=20, axis="Z",
                  centre=(-1900.0, 1900.0, 650.0), mat=steel)
    bkit.rounded_box("SwitchStandHead", 520.0, 240.0, 300.0, r=60.0,
                     segments=3, centre=(-1900.0, 1900.0, 1000.0), mat=frog_m)
    lever = bkit.rounded_box("SwitchLever", 900.0, 70.0, 60.0, r=25.0,
                             segments=2, centre=(0.0, 0.0, 0.0),
                             mat=steel)
    bkit.mirror(lever, "Y")
    bkit.move(lever, -1900.0, 1780.0, 1150.0)
    R.strut("SwitchThrowRod", (-2650.0, -HALF, RAIL_Z + 90.0),
            (-1150.0, -HALF, RAIL_Z + 90.0), 34.0, steel, seg=12)

    gauge = bkit.rounded_box("SwitchGaugeBar", 150.0, GAUGE, 38.0, r=8.0,
                             segments=2, centre=(-1500.0, 0.0,
                                                 RAIL_Z + RAIL_H - 5.0),
                             mat=steel)

    return dict(spec=SPEC, parts=13)