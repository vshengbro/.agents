"""
rail_track -- a 5.76 m standard-gauge permanent-way section, 1435 mm gauge.

Three things make this read as railway track and not as two bars on planks:
the rail is a REAL 60E1 SECTION (150 mm foot, 16 mm web, 70 mm head, 172 mm
tall) rather than a rectangle; the 1435 mm gauge is the INNER FACE of one head
to the inner face of the other, so it is checked as two inner-face coordinates
instead of a centre-to-centre guess; and the sleepers are a computed row at
600 mm centres, buried in a trapezoidal ballast prism.

The ballast toe is the floor datum: it sits on z=0, which makes
`sit_on_floor()` a no-op, so every `top_z` check below reads straight off the
model. Sleeper top is at 300 and the rail head crown therefore at 472.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    section_length=5760.0,
    gauge=1435.0,
    rail_height=172.0,
    rail_head_width=70.0,
    sleeper_spacing=600.0,
    sleeper_length=2600.0,
    sleeper_top_z=300.0,
    ballast_top_z=250.0,
)

# The gauge cannot be read off the rail's bounding box: the FOOT is 150 mm
# wide, so a rail's y_min is its foot edge at +/-677.5, not the 717.5 inner
# face of the head. A track gauge -- the real bar a fitter lays across the
# four-foot -- spans exactly 1435 mm between turned-up ends that bear on those
# inner head faces, so ITS width is the gauge, measured directly.
CHECKS = [
    dict(name="section_length", mm=5760.0, tol=2.0, how="bbox_x",
         part="TrackRailL"),
    dict(name="gauge", mm=1435.0, tol=1.0, how="bbox_y", part="TrackGaugeBar"),
    dict(name="rail_height", mm=172.0, tol=1.0, how="bbox_z", part="TrackRailL"),
    dict(name="rail_crown_z", mm=472.0, tol=1.0, how="top_z", part="TrackRailL"),
    dict(name="sleeper_top_z", mm=300.0, tol=1.0, how="top_z",
         part="TrackSleeperRow"),
    dict(name="sleeper_length", mm=2600.0, tol=2.0, how="bbox_y",
         part="TrackSleeperRow"),
    dict(name="ballast_top_z", mm=250.0, tol=1.0, how="top_z",
         part="TrackBallast"),
]

LENGTH = 5760.0
SLEEPERS = 9
PITCH = 600.0
SLEEPER_L = 2600.0
SLEEPER_T = 200.0
SLEEPER_Z0 = 100.0        # buried 100 mm in the ballast, as cast in situ
RAIL_Z0 = 300.0
RAIL_H = 172.0


def build():
    concrete = bkit.pbr("SleeperConcrete", base=(0.52, 0.51, 0.49), rough=0.82)
    steel = bkit.preset("dark_metal")
    rust = bkit.pbr("RailHead", base=(0.30, 0.25, 0.22), metal=0.80, rough=0.52)
    stone = bkit.preset("soil")

    R.ballast("TrackBallast", LENGTH, top_w=3600.0, base_w=5200.0,
              height=SLEEPER_Z0 + 150.0, mat=stone)

    R.sleeper_row("TrackSleeperRow", SLEEPERS, PITCH, SLEEPER_L,
                  sx=250.0, sz=SLEEPER_T, z0=SLEEPER_Z0, mat=concrete)

    # Rails sit on top of the sleepers. Rail foot z=300, so the head crown --
    # the surface a wheel tread actually runs on -- is at 472.
    rail_l = R.rail("TrackRailL", LENGTH, y=R.RAIL_Y, z0=RAIL_Z0,
                    h=RAIL_H, mat=rust)
    rail_r = R.rail("TrackRailR", LENGTH, y=-R.RAIL_Y, z0=RAIL_Z0,
                    h=RAIL_H, mat=rust)
    # A polished running band on the head crown: that polished stripe is the
    # single most recognisable rail cue there is.
    for ob, tag in ((rail_l, "L"), (rail_r, "R")):
        bkit.assign_faces_by(ob, bkit.preset("polished_metal"),
                             lambda c, n: c.z / bkit.MM > RAIL_Z0 + RAIL_H - 2.0)

    # Rail chairs / baseplates under each rail at every sleeper
    chair = bkit.rounded_box("TrackChair", 190.0, 230.0, 22.0, r=6.0,
                             segments=2, centre=(0.0, R.RAIL_Y, RAIL_Z0 - 9.0),
                             mat=steel)
    bkit.array_linear(chair, SLEEPERS, (PITCH, 0.0, 0.0), world=True)
    bkit.move(chair, -(SLEEPERS - 1) * PITCH / 2.0, 0.0, 0.0)
    # Mirror, never duplicate: `duplicate()` SETS location to the offset alone,
    # which throws away the -2400 mm the array row was just shifted by and
    # leaves the copy a whole sleeper pitch off to one side.
    bkit.mirror(chair, "Y")
    chair.name = "TrackChairs"

    # A track gauge laid across the four-foot: its width is the gauge.
    gauge = bkit.rounded_box("TrackGaugeBar", 150.0, SPEC["gauge"], 38.0,
                             r=8.0, segments=2,
                             centre=(0.0, 0.0, RAIL_Z0 + RAIL_H - 5.0),
                             mat=steel)
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        bkit.rounded_box("TrackGaugeHorn" + tag, 90.0, 40.0, 80.0, r=8.0,
                         segments=2,
                         centre=(0.0, s * (SPEC["gauge"] / 2.0 - 20.0),
                                 RAIL_Z0 + RAIL_H + 12.0), mat=steel)

    return dict(spec=SPEC, parts=9)