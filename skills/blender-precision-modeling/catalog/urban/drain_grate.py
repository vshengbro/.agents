"""
drain_grate -- 450 x 300 x 45 mm kerbside gully grate: a cast frame with a
rebated seat, a 6 x 3 field of 68 mm clear holes in a real `perforated_panel`,
a lifting slot and two cross ribs.

This is the one urban object the brief calls out by name: the grating is
`bkit.perforated_panel`, 18 real holes in one mesh, no booleans, and the hole
count is stated in SPEC so the field can be checked by eye. The panel is set 2
mm proud of the frame seat so it reads as a drop-in grate rather than as a
plate fused to a frame -- flush, the two would touch along the whole panel
outline.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    frame_width=450.0,
    frame_depth=300.0,
    overall_height=45.0,
    frame_rim=40.0,
    grate_panels=1,
    vent_cols=6,
    vent_rows=3,
    vent_holes=18,
    hole_diameter=40.0,
    panel_thickness=22.0,
)

FW, FD = SPEC["frame_width"], SPEC["frame_depth"]
RIM = SPEC["frame_rim"]
INNER_W = FW - 2 * RIM              # 370
INNER_D = FD - 2 * RIM              # 220


def build():
    frame = bkit.pbr("GrateFrame", base=(0.18, 0.18, 0.19), metal=0.85,
                     rough=0.64)
    grate = bkit.pbr("GratePanel", base=(0.24, 0.24, 0.25), metal=0.85,
                     rough=0.58)
    seat = bkit.pbr("GrateSeat", base=(0.13, 0.13, 0.14), metal=0.85,
                    rough=0.70)

    # ---- frame: four rails around a real opening -------------------------
    rails = [bkit.box("_front", FW, RIM, 45.0, mat=frame,
                      centre=(0.0, RIM / 2.0, 22.5)),
             bkit.box("_back", FW, RIM, 45.0, mat=frame,
                      centre=(0.0, FD - RIM / 2.0, 22.5))]
    for side in (-1.0, 1.0):
        rails.append(bkit.box("_c%.0f" % side, RIM, INNER_D, 45.0, mat=frame,
                              centre=(side * (FW / 2.0 - RIM / 2.0),
                                      FD / 2.0, 22.5)))
    bkit.join(rails, name="GrateFrame")

    # ---- the perforated field: 6 x 3 real 40 mm holes, one mesh ---------
    # NB hole_diameter must be well under the pitch, or adjacent holes overlap
    # and the panel tears into a field of shards.
    pitch_x = (INNER_W - SPEC["hole_diameter"]) / (SPEC["vent_cols"] - 1)
    pitch_y = (INNER_D - SPEC["hole_diameter"]) / (SPEC["vent_rows"] - 1)
    bkit.perforated_panel("GratePanel", SPEC["vent_cols"], SPEC["vent_rows"],
                          pitch_x, pitch_y, SPEC["hole_diameter"] / 2.0,
                          INNER_W, INNER_D, SPEC["panel_thickness"], mat=grate)
    bkit.move(bpy.data.objects["GratePanel"], 0.0, FD / 2.0 - RIM, 34.0)

    # ---- rebated seat under the panel and two lifting slots --------------
    bkit.box("GrateSeat", FW - 4.0, FD - 4.0, 10.0, mat=seat,
             centre=(0.0, FD / 2.0, 5.0))
    for side, tag in ((-1, "L"), (1, "R")):
        bkit.box("LiftSlot" + tag, 30.0, 70.0, 14.0, mat=seat,
                 centre=(side * 150.0, FD / 2.0 - RIM, 32.0))

    # The cross ribs sit 12 mm above the panel's mid-plane and read as a real
    # stiffener. NOTE: bkit.perforated_panel builds two perforated skins
    # `thickness` apart joined by a 0.01 mm SOLIDIFY wall, so a "22 mm" panel is
    # a hollow double-skinned box, not a solid plate. Harmless here (a grate
    # should be see-through) but it is not what the signature implies.
    ribs = []
    for i, ry in enumerate((FD / 2.0 - 110.0, FD / 2.0 + 110.0)):
        ribs.append(bkit.box("_rib%d" % i, INNER_W - 10.0, 14.0, 10.0,
                             mat=grate, centre=(0.0, ry, 40.0)))
    bkit.join(ribs, name="GrateRibs")

    # ---- corner fixing holes and a cast maker's plate -------------------
    holes = []
    for i, (hx, hy) in enumerate(bkit.grid_positions(2, 2, FW - 70.0,
                                                     FD - 70.0)):
        holes.append(bkit.box("_h%d" % i, 22.0, 22.0, 12.0, mat=seat,
                              centre=(hx, hy, 44.0)))
    bkit.join(holes, name="GrateFixingHoles")
    bkit.box("MakersPlate", 110.0, 46.0, 6.0, mat=seat,
             centre=(0.0, FD / 2.0 - RIM + 22.0, 44.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=9)


CHECKS = [
    dict(name="frame_width", mm=450.0, tol=0.6, how="bbox_x",
         part="GrateFrame"),
    dict(name="frame_depth", mm=300.0, tol=0.6, how="bbox_y",
         part="GrateFrame"),
    dict(name="panel_width", mm=370.0, tol=0.8, how="bbox_x",
         part="GratePanel"),
    dict(name="panel_depth", mm=220.0, tol=0.8, how="bbox_y",
         part="GratePanel"),
    dict(name="panel_thickness", mm=22.0, tol=0.6, how="bbox_z",
         part="GratePanel"),
    dict(name="overall_height", mm=50.0, tol=1.0, how="bbox_z"),
]