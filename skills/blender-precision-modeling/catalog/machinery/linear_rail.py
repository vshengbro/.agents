"""
linear_rail -- 300 mm profile rail with a 100 mm carriage block.

The cross-section is the object: a 16 mm mounting foot, a shoulder, and a 35 mm
head with a real side groove on each face for the ball circuit. Both the rail
and the carriage are lofted along X from an explicit YZ outline, so no boolean
touches them and the profile is visible in every render. Mounting holes sit on
a 60 mm pitch with counterbores, laid out with grid_positions; the carriage's
four M6 holes and two grease ports are computed the same way.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    rail_length=300.0,
    rail_width=35.0,
    rail_height=28.0,
    foot_width=20.0,          # wider than the counterbore, or the counterbore
                               # is exactly tangent to the foot's side faces
                               # and the boolean answers with non-manifold edges
    groove_depth=3.0,
    groove_height=6.0,
    mounting_pitch=60.0,
    mounting_holes=5,
    mounting_hole_diameter=6.5,
    counterbore_diameter=12.0,
    carriage_length=100.0,
    carriage_width=55.0,
    carriage_height=44.0,       # from the rail base to the carriage top
    carriage_holes=4,
    carriage_hole_diameter=6.6,
    grease_ports=2,
)


def _rail_section(x):
    hw = SPEC["rail_width"] / 2.0
    hf = SPEC["foot_width"] / 2.0
    gd = SPEC["groove_depth"]
    h = SPEC["rail_height"]
    z0 = h - SPEC["groove_height"] - 2.0          # groove lower edge
    z1 = z0 + SPEC["groove_height"]              # groove upper edge
    yz = [(-hf, 0.0), (hf, 0.0),                 # mounting foot
          (hf, 7.0), (hw, 7.0),                  # shoulder out to the head
          (hw, z0), (hw - gd, z0),               # ball groove, lower lip
          (hw - gd, z1), (hw, z1),               # ball groove, upper lip
          (hw, h), (-hw, h),                     # head top
          (-hw, z1), (-hw + gd, z1),             # mirrored groove
          (-hw + gd, z0), (-hw, z0),
          (-hw, 7.0), (-hf, 7.0)]
    return [(x, y, z) for (y, z) in yz]


def _carriage_section(x):
    hw = SPEC["carriage_width"] / 2.0
    cav = SPEC["rail_width"] / 2.0 + 0.5
    top = SPEC["carriage_height"]
    yz = [(-hw, 6.0), (-cav, 6.0), (-cav, SPEC["rail_height"] + 0.6),
          (cav, SPEC["rail_height"] + 0.6), (cav, 6.0), (hw, 6.0),
          (hw, top), (-hw, top)]
    return [(x, y, z) for (y, z) in yz]


def build():
    half = SPEC["rail_length"] / 2.0
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    rail = bkit.loft("Rail", [_rail_section(-half), _rail_section(half)],
                     closed_loop=True, cap_start=True, cap_end=True, mat=steel)
    bkit.recalc(rail)

    # ---- mounting holes: ONE lathe cutter per hole ---------------------
    # The counterbored hole is a single revolved solid, not two joined
    # cylinders: a joined cutter is two interpenetrating shells, and feeding a
    # self-intersecting cutter to the EXACT solver is what produced 589
    # non-manifold edges here. The cutter also reaches 1 mm below the rail's
    # underside so its end cap is never coplanar with the bottom face.
    for (x, _y) in bkit.grid_positions(SPEC["mounting_holes"], 1,
                                       SPEC["mounting_pitch"], 1.0):
        r_h = SPEC["mounting_hole_diameter"] / 2.0
        r_c = SPEC["counterbore_diameter"] / 2.0
        cutter = bkit.lathe("HoleCutter",
                            [(0.0, -9.0), (r_h, -9.0), (r_h, -1.0),
                             (r_c, -1.0), (r_c, 5.0), (0.0, 5.0)],
                            segments=32, centre=(x, 0.0, 0.0))
        bkit.boolean(rail, cutter, "DIFFERENCE")
    bkit.recalc(rail)

    # ---- carriage ------------------------------------------------------
    cl = SPEC["carriage_length"] / 2.0
    carriage = bkit.loft("Carriage", [_carriage_section(-cl), _carriage_section(cl)],
                         closed_loop=True, cap_start=True, cap_end=True, mat=dark)
    bkit.recalc(carriage)

    # four M6 counterbored fixing holes in the carriage top
    for (x, y) in bkit.grid_positions(2, 2, 60.0, 36.0):
        hole = bkit.cylinder("FixHole", SPEC["carriage_hole_diameter"] / 2.0,
                             24.0, segments=32,
                             centre=(x, y, SPEC["carriage_height"] - 2.0))
        bkit.boolean(carriage, hole, "DIFFERENCE")
        cb = bkit.cylinder("FixCbore", 6.0, 6.0, segments=32,
                           centre=(x, y, SPEC["carriage_height"] - 2.0))
        bkit.boolean(carriage, cb, "DIFFERENCE")

    # grease ports, one per side
    for s in (-1.0, 1.0):
        port = bkit.cylinder("GreasePort", 3.0, 8.0, segments=24, axis="Y",
                             centre=(0.0, s * (SPEC["carriage_width"] / 2.0 - 2.0),
                                     SPEC["carriage_height"] - 12.0))
        bkit.boolean(carriage, port, "DIFFERENCE")
    bkit.recalc(carriage)

    # Lie along Y: the studio's side elevation is az=2, i.e. straight down +X,
    # so a 300 mm rail built along X is photographed end-on.
    rail.rotation_euler = (0.0, 0.0, math.radians(90.0))
    carriage.rotation_euler = (0.0, 0.0, math.radians(90.0))
    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="rail_length", mm=300.0, tol=0.6, how="bbox_y", part="Rail"),
    dict(name="rail_width", mm=35.0, tol=0.4, how="bbox_x", part="Rail"),
    dict(name="rail_height", mm=28.0, tol=0.4, how="bbox_z", part="Rail"),
    dict(name="carriage_width", mm=55.0, tol=0.4, how="bbox_x", part="Carriage"),
]
