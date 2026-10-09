"""
hole_punch -- 2-hole punch, 100 mm long.

The two things that make a punch recognisable are the round punch pin and the
lever arm above it, so both are separate solids with the pin protruding through
a real hole cut in the base. Paper guides are two low ribs, laid out with
grid_positions so nothing is hand-placed.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=100.0,
    depth=50.0,
    overall_height=58.5,
    punch_diameter=6.0,
    hole_spacing=64.0,
)

BASE_H = 14.0
PILLAR_H = 34.0
LEVER_H = 11.0


def build():
    # A near-black shell against a 0.19 backdrop reads as a silhouette blob with
    # no form. Mid-grey with a satin finish keeps the edges legible.
    shell = bkit.pbr("PunchShell", base=(0.42, 0.44, 0.48), rough=0.34,
                     coat=0.25)
    dark = bkit.pbr("PunchDark", base=(0.16, 0.17, 0.20), rough=0.42)
    steel = bkit.preset("polished_metal")

    base = bkit.rounded_box("PunchBase", SPEC["length"], SPEC["depth"],
                            BASE_H, r=3.0, centre=(0, 0, BASE_H / 2.0),
                            mat=shell)

    # Two real punch holes, spaced by the declared hole_spacing.
    holes = []
    for (x, _w) in bkit.lay_out([8.0, 8.0], gap=SPEC["hole_spacing"] - 8.0):
        cutter = bkit.cylinder("hole_cut", SPEC["punch_diameter"] / 2.0,
                               BASE_H * 2.0, segments=32, centre=(x, 0, 6.0),
                               mat=None)
        bkit.boolean(base, cutter, "DIFFERENCE")
    # the punch itself, standing in the left hole
    pin = bkit.cylinder("PunchPin", SPEC["punch_diameter"] / 2.0, 22.0,
                        segments=32, centre=(-(SPEC["hole_spacing"] / 2.0),
                                            0, BASE_H + 5.0), mat=steel)
    pin2 = bkit.cylinder("PunchPin2", SPEC["punch_diameter"] / 2.0, 22.0,
                         segments=32,
                         centre=(SPEC["hole_spacing"] / 2.0, 0, BASE_H + 5.0),
                         mat=steel)

    # side pillars carrying the lever, set in from the base ends
    pillars = []
    for (x, _w) in bkit.lay_out([16.0, 16.0], gap=54.0):
        pillars.append(bkit.rounded_box("PunchPillar", 16.0, 46.0, PILLAR_H,
                                        r=2.5,
                                        centre=(x, 0, BASE_H + PILLAR_H / 2.0),
                                        mat=shell))
    pillar = bkit.join(pillars, name="PunchPillars")

    # lever arm spanning the pillars
    lever = bkit.rounded_box("PunchLever", SPEC["length"], 44.0, LEVER_H,
                             r=3.0,
                             centre=(0, 0, BASE_H + PILLAR_H + LEVER_H / 2.0 - 1.0),
                             mat=shell)

    # chip tray at the back, low enough that the punch pins stay visible above
    # it -- a full-height tray hides the pins and the model stops reading.
    tray = bkit.rounded_box("PunchTray", 56.0, 40.0, 8.0, r=2.0,
                            centre=(-6.0, 0, BASE_H + 4.0), mat=dark)

    return dict(spec=SPEC, parts=8, holes=holes)


CHECKS = [
    dict(name="length", mm=100.0, tol=0.5, how="bbox_x", part="PunchBase"),
    dict(name="depth", mm=50.0, tol=0.5, how="bbox_y", part="PunchBase"),
    dict(name="overall_height", mm=58.5, tol=0.6, how="bbox_z"),
    dict(name="punch_diameter", mm=6.0, tol=0.4, how="bbox_x", part="PunchPin"),
]