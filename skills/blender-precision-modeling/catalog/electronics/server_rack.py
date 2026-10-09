"""
server_rack -- 42U 19" rack, 600 x 1070 x 2000 mm.

The number that has to be right is 42. One rack unit is 44.45 mm, so the
usable rail height is 42 * 44.45 = 1866.9 mm, and the EIA-310-E mounting
pattern puts three square holes per unit at 15.875 mm pitch -- offsets 3.175,
19.05 and 34.925 mm from each unit boundary, which is where the 12.7 mm
seam between the last hole of one unit and the first of the next falls out.
That is 126 holes per rail, built as one three-hole unit arrayed 42 times and
cut with a single boolean, rather than 126 hand-placed cutters.

The side panels are one `perforated_panel` each (8 x 42 = 336 holes) stood up
into the YZ plane, which needs a compound rotation: a single -90 degree swing
would leave the sheet's normal along Y, i.e. facing the front of the rack.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=600.0,
    depth=1070.0,
    height=2000.0,
    units=42,
    unit_height=44.45,
    rail_holes_per_unit=3,
    side_cols=8,
    side_rows=42,
    servers=3,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
U = SPEC["unit_height"]
UNITS = SPEC["units"]
RAIL_Z0 = 110.0                       # first unit's bottom edge
RAIL_H = UNITS * U                    # 1866.9
RAIL_ZC = RAIL_Z0 + RAIL_H / 2.0
RAIL_X = 240.0                        # 19" mounting flange, 482.6 between
POST = 40.0

# EIA-310-E: 3 holes per unit, 15.875 mm pitch, first at 15.875 above the
# unit floor -- which puts the third one 3.175 mm into the unit above.
HOLE_OFF = (3.175, 19.05, 34.925)
SIDE_PITCH = 45.0
SIDE_R = 12.0
SIDE_W = (SPEC["side_cols"] - 1) * SIDE_PITCH + 2 * SIDE_R
SIDE_H = (SPEC["side_rows"] - 1) * U + 2 * SIDE_R


def build():
    # A 2 m rack is nearly all frame, and a frame at metal=0.85 has no diffuse
    # term to catch the key light -- it renders as a black cage. Real powder
    # coat is barely metallic anyway, so these sit at 0.45 with a lifted base.
    steel = bkit.pbr("RackSteel", base=(0.38, 0.39, 0.41), metal=0.45,
                     rough=0.40)
    dark = bkit.pbr("RackDark", base=(0.20, 0.20, 0.23), rough=0.46)
    mesh = bkit.pbr("RackMesh", base=(0.31, 0.32, 0.34), metal=0.45,
                    rough=0.44)
    face = bkit.pbr("RackServerFace", base=(0.52, 0.53, 0.56), metal=0.45,
                    rough=0.32)
    led = bkit.pbr("RackLed", base=(0.12, 0.60, 0.32), rough=0.20,
                   emission=(0.10, 0.80, 0.40), emission_strength=1.2)

    # ---- plinth and four corner posts -----------------------------------
    bkit.rounded_box("RackPlinth", W, D, 100.0, r=4.0, segments=3,
                     centre=(0, 0, 50.0), mat=steel)
    posts = []
    for i, (x, y) in enumerate(bkit.grid_positions(
            cols=2, rows=2, pitch_x=W - POST, pitch_y=D - POST)):
        posts.append(bkit.extrude_profile(
            "_post%d" % i, bkit.rounded_rect_section(POST, POST, 3.0),
            1880.0, centre=(x, y, 1040.0), mat=steel))
    bkit.join(posts, name="RackPosts")

    # ---- two front rails, 3 holes x 42 units, one arrayed cutter each ---
    rails = []
    for i, x in enumerate((-RAIL_X, RAIL_X)):
        # The flange is 16 mm wide with a 12 mm return flange, standing proud of the
        # front plane by 26 mm, so the square rack holes are visible from
        # outside the cabinet instead of being hidden behind the frame.
        rail = bkit.rounded_box("_rail%d" % i, 44.0, 16.0, RAIL_H, r=2.0,
                                segments=2, centre=(x, -D / 2.0 + 26.0,
                                                    RAIL_ZC), mat=steel)
        unit = []
        for j, off in enumerate(HOLE_OFF):
            # The cutter was 9.5 mm deep in Y but the rail flange is 12 mm
            # thick, so the boolean stopped 2.5 mm short and produced square
            # blind dimples instead of the square through-holes a mounting
            # rail has. Cutting 30 mm through the 12 mm flange leaves a real
            # hole with visible daylight through it.
            unit.append(bkit.box("_h%d_%d" % (i, j), 9.5, 30.0, 9.5,
                                 centre=(x, -D / 2.0 + 26.0,
                                         RAIL_Z0 + off), mat=dark))
        cut = bkit.join(unit, name="_hole_unit%d" % i)
        bkit.array_linear(cut, count=UNITS, offset_mm=(0, 0, U))
        bkit.boolean(rail, cut, "DIFFERENCE")
        rails.append(rail)
    bkit.join(rails, name="RackFrontRails")

    # ---- two perforated side panels, stood into the YZ plane ------------
    # Compound rotation: (90, 0, 90) sends local +X to world +Y, local +Y to
    # world +Z and the sheet normal to world +X. A lone -90 swing leaves the
    # normal along Y, so the panel would sit across the front of the rack.
    panels = []
    for i, x in enumerate((-(W / 2.0 - 1.0), W / 2.0 - 1.0)):
        p = bkit.perforated_panel("RackSidePanel%d" % i, cols=SPEC["side_cols"],
                                  rows=SPEC["side_rows"], pitch_x=SIDE_PITCH,
                                  pitch_y=U, hole_r=SIDE_R,
                                  panel_sx=SIDE_W, panel_sy=SIDE_H,
                                  thickness=1.5, mat=mesh)
        p.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
        bkit.move(p, x, 0.0, RAIL_ZC)
        panels.append(p)
    bkit.join(panels, name="RackSidePanels")

    # ---- top panel with two 120 mm fan apertures ------------------------
    top = bkit.rounded_box("RackTop", W, D, 20.0, r=3.0, segments=3,
                           centre=(0, 0, H - 10.0), mat=steel)
    for i, (x, w) in enumerate(bkit.lay_out([130.0, 130.0], gap=180.0)):
        bkit.bore(top, radius=60.0, depth=40.0,
                  centre=(x, 140.0, H - 10.0), host_segments=64)

    # ---- three populated 1U servers --------------------------------------
    # Five units apart, not adjacent: consecutive 1U servers leave a 2.45 mm
    # gap, which is sub-pixel across a 2 m rack and renders as one grey slab.
    units = []
    for i in range(SPEC["servers"]):
        u = 30 - i * 5                               # U30, U25, U20
        z = RAIL_Z0 + (UNITS - u) * U + U / 2.0
        body = bkit.rounded_box("_srv%d" % i, 448.0, 650.0, 42.0, r=3.0,
                                segments=2, centre=(0, 20.0, z), mat=dark)
        bezel = bkit.rounded_box("_bez%d" % i, 482.0, 12.0, 44.0, r=2.0,
                                 segments=2,
                                 centre=(0, -D / 2.0 + 34.0, z), mat=face)
        bay = bkit.rounded_box("_bay%d" % i, 8.0, 8.0, 26.0, r=1.0,
                               segments=2, centre=(-196.0, -D / 2.0 + 40.0,
                                                  z), mat=face)
        bkit.array_linear(bay, count=8, offset_mm=(28.0, 0, 0))
        units += [body, bezel, bay]
        units.append(bkit.cylinder("_led%d" % i, 2.4, 4.0, segments=20,
                                   axis="Y",
                                   centre=(228.0, -D / 2.0 + 40.0, z),
                                   mat=led))
    bkit.join(units, name="RackServers")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=600.0, tol=1.5, how="bbox_x", part="RackPlinth"),
    dict(name="depth", mm=1070.0, tol=1.5, how="bbox_y", part="RackPlinth"),
    dict(name="overall_height", mm=2000.0, tol=1.5, how="bbox_z"),
]
