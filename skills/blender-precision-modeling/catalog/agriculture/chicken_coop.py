"""
chicken_coop -- a 1.8 x 1.2 m timber chicken coop on legs, with a run and a ramp.

The run is `perforated_panel`, not a wall with holes cut in it: chicken wire is
built as one perforated sheet, which keeps it watertight and fast. Note what
`panel_sx`/`panel_sy` are NOT: the panel's real extent is
`(cols - 1) * pitch + 2 * hole_r`, so the size is chosen by picking the pitch
and the column count and letting the grid set the dimension.

The house sits 400 mm clear of the ground so the flock can get under it, which
is why every leg is exactly the stand height and the floor is at z=400 rather
than resting on the soil.

Real small coop: 1800 x 1200 mm house on a 400 mm stand, 1000 x 1800 mm run,
680 mm mono-pitch roof falling forward, 300 mm pop hole with a 30 deg ramp.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _agri as A

SPEC = dict(
    house_length=1800.0,
    house_width=1200.0,
    stand_height=400.0,
    wall_height=900.0,
    roof_depth=680.0,
    roof_rise=650.0,
    run_length=1000.4,
    run_height=888.0,
    ramp_angle_deg=30.0,
    ramp_length=700.0,
    perch_length=900.0,
)

HL = SPEC["house_length"]
HW = SPEC["house_width"]
SH = SPEC["stand_height"]
WH = SPEC["wall_height"]
RUN = SPEC["run_length"]
RUNH = SPEC["run_height"]
RY = HW / 2.0 + RUN / 2.0
TOP = SH + 40.0 + WH

CHECKS = [
    dict(name="house_length", mm=1800.0, tol=4.0, how="bbox_x",
         part="CoopFloor"),
    dict(name="house_width", mm=1200.0, tol=4.0, how="bbox_y",
         part="CoopFloor"),
    dict(name="stand_height", mm=400.0, tol=3.0, how="z_min", part="CoopFloor"),
    dict(name="wall_height", mm=900.0, tol=4.0, how="bbox_z",
         part="CoopWall0"),
    dict(name="roof_top", mm=2020.0, tol=8.0, how="top_z", part="CoopRoof"),
    dict(name="run_height", mm=888.0, tol=5.0, how="bbox_z",
         part="CoopRunMesh0"),
    dict(name="perch_length", mm=900.0, tol=4.0, how="bbox_x",
         part="CoopPerch"),
    dict(name="leg_on_floor", mm=0.0, tol=2.0, how="z_min", part="CoopLeg0"),
]


def build():
    board = bkit.pbr("CoopBoard", base=(0.58, 0.44, 0.26), rough=0.72)
    trim = bkit.pbr("CoopTrim", base=(0.44, 0.33, 0.19), rough=0.68)
    felt = bkit.pbr("CoopFelt", base=(0.24, 0.24, 0.25), rough=0.86)
    wire = bkit.pbr("CoopWire", base=(0.42, 0.44, 0.46), metal=0.85, rough=0.42)
    soil = bkit.preset("soil")

    # ---- six legs, each exactly the stand height ----------------------
    for i, (x, y) in enumerate(bkit.grid_positions(3, 2, HL - 300.0,
                                                   HW - 200.0)):
        bkit.rounded_box("CoopLeg%d" % i, 90.0, 90.0, SH, r=6.0, segments=2,
                         centre=(x, y, SH / 2.0), mat=trim)

    # ---- the house: floor, three solid walls, a low fourth ------------
    bkit.rounded_box("CoopFloor", HL, HW, 40.0, r=6.0, segments=2,
                     centre=(0.0, 0.0, SH + 20.0), mat=board)
    for i, (x, y, sx, sy) in enumerate((
            (0.0, -HW / 2.0 + 15.0, HL, 30.0),
            (-HL / 2.0 + 15.0, 0.0, 30.0, HW),
            (HL / 2.0 - 15.0, 0.0, 30.0, HW))):
        bkit.rounded_box("CoopWall%d" % i, sx, sy, WH, r=4.0, segments=2,
                         centre=(x, y, SH + 40.0 + WH / 2.0), mat=board)
    bkit.rounded_box("CoopLowWall", HL, 30.0, 260.0, r=4.0, segments=2,
                     centre=(0.0, HW / 2.0 - 15.0, SH + 40.0 + 130.0),
                     mat=board)

    # ---- the run: two side panels and a front, all chicken wire -------
    # `perforated_panel` builds a flat sheet in XY; a run wall has to be
    # STOOD UP, so the panel is rotated 90 deg about X and only then placed.
    for i, x in enumerate((-HL / 2.0 + 10.0, HL / 2.0 - 10.0)):
        # the run's long dimension must end up along Y (the run direction),
        # so the flat sheet is stood up AND swung: Rx(90) then Rz(90).
        p = bkit.perforated_panel("CoopRunMesh%d" % i, 17, 16, 61.4, 58.0,
                                  9.0, RUN, RUNH, 4.0, mat=wire)
        p.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
        p.location = bkit.v(x, RY, SH + 20.0 + RUNH / 2.0)
    front = bkit.perforated_panel("CoopRunMesh2", 29, 16, 63.6, 58.0, 9.0,
                                  HL, RUNH, 4.0, mat=wire)
    front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    front.location = bkit.v(0.0, HW / 2.0 + RUN, SH + 20.0 + RUNH / 2.0)

    # ---- the mono-pitch roof ------------------------------------------
    # `extrude_profile(..., axis="Y")` stands the polygon up with local +Y
    # mapping to world +Z, so the wedge is written positive-y: written
    # negative it builds the roof downwards, inside the house, and still
    # measures 680 mm.
    d = SPEC["roof_depth"]
    bkit.extrude_profile("CoopRoof",
                         [(-HL / 2.0 - 90.0, 0.0), (HL / 2.0 + 90.0, 0.0),
                          (HL / 2.0 + 90.0, 30.0),
                          (-HL / 2.0 - 90.0, d)],
                         HW + 220.0, centre=(0.0, 0.0, TOP), axis="Y", mat=felt)

    # ---- the pop hole, the ramp and the roost -------------------------
    bkit.rounded_box("CoopPopHole", 300.0, 40.0, 400.0, r=6.0, segments=2,
                     centre=(0.0, -HW / 2.0 - 4.0, SH + 290.0), mat=trim)
    a = math.radians(SPEC["ramp_angle_deg"])
    A.bar_between("CoopRamp", (0.0, -HW / 2.0 - 20.0, SH + 40.0),
                  (0.0, -HW / 2.0 - 20.0 - SPEC["ramp_length"] * math.cos(a),
                   20.0), 300.0, 24.0, mat=board, r=6.0)
    bkit.cylinder("CoopPerch", 22.0, SPEC["perch_length"], segments=20,
                  axis="X", centre=(0.0, 120.0, TOP - 180.0), mat=trim)

    A.make_ground("Ground", HL + RUN + 700.0, HW + RUN + 700.0, 30.0,
                  mat=soil)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6 + 5 + 3 + 1 + 3 + 1)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
