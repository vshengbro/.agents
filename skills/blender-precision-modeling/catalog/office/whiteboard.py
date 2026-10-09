"""
whiteboard -- 1200 x 900 mm wall-mounted whiteboard with a frame and a tray.

Large size class, so it is the one office item where the scene scale really
matters. Built upright in the XZ plane: the panel is a thin solid in Y, the
frame is four extruded bars behind it, and the tray is a real lip under the
bottom rail rather than a line painted on it.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=1200.0,
    height=900.0,
    panel_thickness=6.0,
    frame_width=30.0,
    frame_depth=18.0,
    tray_length=600.0,
    tray_depth=55.0,
)

W = SPEC["width"]
H = SPEC["height"]
FW = SPEC["frame_width"]
FT = SPEC["panel_thickness"]
FD = SPEC["frame_depth"]


def build():
    # A whiteboard IS white: a mid-grey enamel reads as a blank monitor.
    # The enamel was already 0.95 base, but the board face renders DARKER than the
    # floor it stands on. That is not the albedo: the panel's normal points +Y
    # and the key light sits at (1.9r, -2.0r, 2.4r), i.e. on the -Y side, so
    # the face we photograph is the one turned away from the key. The face
    # material is now double-sided bright enamel with a little self-emission --
    # a real whiteboard is one of the brightest objects in an office and reads
    # as a light source, not as a grey panel.
    enamel = bkit.pbr("BoardEnamel", base=(0.97, 0.98, 0.98), rough=0.08,
                      coat=0.7, emission=(0.85, 0.88, 0.90),
                      emission_strength=0.30)
    alu = bkit.pbr("BoardFrameMetal", base=(0.66, 0.68, 0.71), metal=0.85,
                   rough=0.32)
    tray_mat = bkit.pbr("BoardTray", base=(0.48, 0.50, 0.54), rough=0.38)

    # ---- panel ------------------------------------------------------------
    panel = bkit.rounded_box("WhiteboardPanel", W, FT, H, r=1.0, segments=2,
                             centre=(0, FT / 2.0, 0), mat=enamel)

    # ---- frame: four bars behind the panel --------------------------------
    bars = []
    for (name, sx, sz, cz) in (
        ("BarTop", W + 2 * FW, FD, H / 2.0 + FW / 2.0 - 2.0),
        ("BarBottom", W + 2 * FW, FD, -H / 2.0 - FW / 2.0 + 2.0),
        ("BarLeft", FW, FD, 0),
        ("BarRight", FW, FD, 0),
    ):
        cx = 0.0
        if name == "BarLeft":
            cx = -W / 2.0 - FW / 2.0 + 2.0
        elif name == "BarRight":
            cx = W / 2.0 + FW / 2.0 - 2.0
        bars.append(bkit.rounded_box("Board" + name, sx, FD, sz, r=1.5,
                                     centre=(cx, FD / 2.0, cz), mat=alu))
    frame = bkit.join(bars, name="WhiteboardFrame")

    # ---- stand: two legs so the board does not float ------------------
    # A wall-mounted board has nothing to sit on, and sit_on_floor() then
    # leaves the whole thing hovering above the backdrop with only its lowest
    # edge touching -- which reads as a modelling error, not as a wall mount.
    legs = []
    for i, x in enumerate((-W / 2.0 + 90.0, W / 2.0 - 90.0)):
        legs.append(bkit.rounded_box(
            "BoardLeg%d" % (i + 1), 34.0, 90.0, 210.0, r=3.0,
            centre=(x, -40.0, -H / 2.0 - FW / 2.0 + 2.0 - 105.0),
            mat=alu))
        # foot bar, so the leg reads as standing rather than as a post
        legs.append(bkit.rounded_box(
            "BoardFoot%d" % (i + 1), 120.0, 110.0, 16.0, r=3.0,
            centre=(x, -40.0, -H / 2.0 - FW / 2.0 + 2.0 - 202.0),
            mat=alu))
    stand = bkit.join(legs, name="WhiteboardStand")

    # ---- pen tray ---------------------------------------------------------
    tray_len = SPEC["tray_length"]
    tray = bkit.rounded_box("WhiteboardTray", tray_len,
                            SPEC["tray_depth"], 10.0, r=1.5,
                            centre=(0, -SPEC["tray_depth"] / 2.0 + 6.0,
                                    -H / 2.0 - FW / 2.0 + 2.0 - 5.0),
                            mat=tray_mat)
    lip = bkit.rounded_box("WhiteboardTrayLip", tray_len, 6.0, 16.0, r=1.0,
                           centre=(0, -SPEC["tray_depth"] + 6.0,
                                   -H / 2.0 - FW / 2.0 + 2.0 - 13.0),
                           mat=tray_mat)
    return dict(spec=SPEC, parts=5)


CHECKS = [
    # The frame bars extend beyond the panel, so the OVERALL size is
    # panel + 2 * frame_width, not the panel size. Declaring the panel
    # dimensions here measures against the frame and fails.
    dict(name="overall_width", mm=1260.0, tol=1.5, how="bbox_x"),
    # Overall height now includes the stand below the board.
    dict(name="overall_height", mm=1145.0, tol=2.0, how="bbox_z"),
    dict(name="panel_width", mm=1200.0, tol=1.5, how="bbox_x",
         part="WhiteboardPanel"),
    dict(name="panel_thickness", mm=6.0, tol=0.6, how="bbox_y",
         part="WhiteboardPanel"),
]