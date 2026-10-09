"""
tripod -- 1372 x 714 mm photographic tripod: 76 mm leg hub, three splayed
1106 mm legs, centre column, pan head and quick-release plate.

The legs are the interesting part and the reason this file exists. A splayed
leg cannot be a `cylinder` (no angled axis) and cannot be built as a primitive
then rotated either: `array_radial` sweeps copies about the WORLD ORIGIN, so a
leg rotated into place first just gets its copies fanned around the middle of
the tripod instead of around the hub.

The fix is to bake the splay into the MESH. `loft` writes absolute millimetre
vertices and leaves `location` at zero, so a leg whose sections already walk
from (0, 0, 1030) at the hub out to (402, 0, 0) at the foot is a three-way
`array_radial` that lands three legs on the floor at 120 degrees. Verified:
array_radial leaves the source at the world origin and rotates copies about it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=1383.0,
    leg_hub_diameter=76.0,
    centre_column_diameter=28.0,
    leg_length=1106.0,
    leg_splay_radius=402.0,
    legs=3,
    leg_top_diameter=30.0,
)

HUB_R = SPEC["leg_hub_diameter"] / 2.0
HUB_Z = 1030.0                     # height of the leg hub
LEG_L = SPEC["leg_length"]
SPREAD = SPEC["leg_splay_radius"]


def _ring(r, cx, cz, n=16):
    """One circular loft section, centred on the leg axis at (cx, 0, cz)."""
    return [(cx + r * math.cos(2 * math.pi * i / n),
             r * math.sin(2 * math.pi * i / n),
             cz) for i in range(n)]


def _leg():
    """One straight tapered leg: hub end at the axis, foot out on the floor."""
    # (t along the leg, radius) -- the drop in the upper section is what reads
    # as a two-part leg with a slide lock between the two tubes.
    steps = [(0.0, 15.0), (0.05, 14.0), (0.44, 13.0), (0.47, 13.5),
             (0.52, 13.5), (0.55, 10.5), (0.62, 10.0), (0.92, 8.6),
             (0.96, 9.4), (0.98, 9.4), (1.0, 4.5)]
    return [_ring(r, SPREAD * t, HUB_Z * (1.0 - t)) for (t, r) in steps]


def build():
    alu = bkit.pbr("TripodAlu", base=(0.56, 0.57, 0.59), metal=0.85,
                   rough=0.36)
    dark = bkit.pbr("TripodDark", base=(0.085, 0.086, 0.090), rough=0.44)
    rubber = bkit.preset("rubber")

    # ---- three splayed legs, swept about the world origin ----------------
    leg = bkit.loft("TripodLegs", _leg(), mat=alu)
    bkit.array_radial(leg, count=SPEC["legs"], axis="Z")
    bkit.recalc(leg)

    # ---- leg hub, collar clamp and centre column ------------------------
    bkit.cylinder("LegHub", HUB_R, 60.0, segments=48,
                  centre=(0.0, 0.0, HUB_Z + 5.0), mat=dark)
    bkit.cylinder("ColumnClamp", 24.0, 46.0, segments=40,
                  centre=(0.0, 0.0, 1112.0), mat=dark)
    bkit.cylinder("CentreColumn", SPEC["centre_column_diameter"] / 2.0, 240.0,
                  segments=40, centre=(0.0, 0.0, 1210.0), mat=alu)
    bkit.cylinder("ColumnRack", 6.0, 200.0, segments=16,
                  centre=(16.0, 0.0, 1210.0), mat=alu)

    # ---- rubber feet, one per leg, at the 402 mm splay radius ------------
    # Bottom face exactly at z=0 so `sit_on_floor` shifts nothing and the
    # declared overall height is the model's own, not a seated approximation.
    foot = bkit.cylinder("_foot", 13.0, 26.0, segments=24, r2=10.0,
                         centre=(SPREAD, 0.0, 13.0), mat=rubber)
    bkit.array_radial(foot, count=SPEC["legs"], axis="Z")

    # ---- pan head, tilt handle and quick-release plate -------------------
    bkit.cylinder("PanHead", 26.0, 30.0, segments=40,
                  centre=(0.0, 0.0, 1345.0), mat=dark)
    bkit.rounded_box("TiltHandle", 22.0, 90.0, 22.0, r=6.0, segments=3,
                     centre=(0.0, -52.0, 1372.0), mat=dark)
    bkit.rounded_box("QuickReleasePlate", 90.0, 60.0, 12.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 1366.0), mat=alu)
    bkit.rounded_box("PlateLip", 90.0, 60.0, 8.0, r=2.0, segments=2,
                     centre=(0.0, 0.0, 1360.0), mat=dark)

    # ---- leg clamps: one per leg at the 0.47 t station -------------------
    clamp = bkit.box("_clamp", 30.0, 34.0, 26.0,
                     centre=(SPREAD * 0.47, 0.0, HUB_Z * 0.53), mat=dark)
    bkit.array_radial(clamp, count=SPEC["legs"], axis="Z")

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="overall_height", mm=1383.0, tol=2.0, how="bbox_z"),
    dict(name="leg_hub_diameter", mm=76.0, tol=0.6, how="diameter",
         part="LegHub"),
    dict(name="centre_column_diameter", mm=28.0, tol=0.6, how="diameter",
         part="CentreColumn"),
    # top_z is 1030, not 1030 + 15: each loft section is a ring in a horizontal
    # plane, so the leg's topmost vertex is at the hub height itself.
    dict(name="leg_top_height", mm=1030.0, tol=2.0, how="top_z",
         part="TripodLegs"),
    dict(name="quick_release_width", mm=90.0, tol=0.6, how="bbox_x",
         part="QuickReleasePlate"),
]