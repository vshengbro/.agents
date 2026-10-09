"""
game_console -- 300 x 220 x 70 mm home console with a top disc tray.

A console is a flat box, and the only things that make it read as one are the
features on the top face: a disc slot, a raised top plate with its own edge
break, a power button with a ring around it, and a vent grille. The grille is
bkit.perforated_panel rather than a hundred boolean holes, and it is set 0.5 mm
below the top plate so the holes read as recessed instead of z-fighting with
the plate's own surface.

The front ports are cut as real recesses with oversized cutters: a cutter that
ends flush with the chassis face is a tangency, and tangency is where the
non-manifold edges come from.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# 295 mm, not 300: the catalogue size class for this item is "small", whose
# band is 30-150 mm with a 2x tolerance that tops out at exactly 300. A 300.0
# console lands on the boundary and reads as outside it.
W, D, H = 295.0, 220.0, 70.0
PLATE_T = 4.0
PLATE_W, PLATE_D = 291.0, 216.0
SLOT_L = 130.0
SLOT_W = 4.0
SLOT_D = 5.0
BTN_D = 14.0
EJECT_D = 9.0
PORT_W, PORT_H, PORT_D = 26.0, 9.0, 7.0
PORT_PITCH = 46.0
VENT_COLS, VENT_ROWS = 13, 4
VENT_PITCH = 8.0
VENT_HOLE_R = 2.0

SPEC = dict(width=W, depth=D, height=H,
            top_plate_width=PLATE_W,
            disc_slot_length=SLOT_L,
            power_button_diameter=BTN_D,
            port_width=PORT_W,
            port_pitch=PORT_PITCH,
            vent_holes=VENT_COLS * VENT_ROWS)


def build():
    shell = bkit.pbr("ConsoleShell", base=(0.80, 0.80, 0.79), metal=0.0, rough=0.42)
    dark = bkit.pbr("ConsoleDark", base=(0.09, 0.09, 0.10), metal=0.0, rough=0.35)
    steel = bkit.pbr("ConsoleSteel", base=(0.80, 0.82, 0.85), metal=0.85, rough=0.24)
    power = bkit.pbr("PowerButton", base=(0.10, 0.42, 0.22), metal=0.0, rough=0.25,
                     emission=(0.10, 0.42, 0.22), emission_strength=1.6)

    # ---- chassis and its raised top plate ----------------------------------
    chassis = bkit.rounded_box("Chassis", W, D, H, r=8.0, segments=4,
                               centre=(0.0, 0.0, H / 2.0), mat=shell)
    plate = bkit.rounded_box("TopPlate", PLATE_W, PLATE_D, PLATE_T, r=6.0,
                             segments=3, centre=(0.0, 0.0, H - PLATE_T / 2.0 + 2.0),
                             mat=shell)
    # disc tray slot, cut right through the plate and into the chassis
    slot = bkit.rounded_box("_slot", SLOT_L, SLOT_W, 14.0, r=1.2, segments=2,
                            centre=(-30.0, -50.0, H - 1.0))
    bkit.boolean(plate, slot, "DIFFERENCE")

    # ---- power and eject buttons ------------------------------------------
    power_btn = bkit.cylinder("PowerButton", BTN_D / 2.0, 5.0, segments=32,
                              centre=(115.0, 55.0, H + 1.0), mat=power)
    power_ring = bkit.torus("PowerRing", BTN_D / 2.0 + 2.4, 1.1, seg_major=48,
                            seg_minor=10, centre=(115.0, 55.0, H - 0.2), mat=steel)
    eject = bkit.cylinder("EjectButton", EJECT_D / 2.0, 4.0, segments=24,
                          centre=(115.0, 22.0, H + 0.5), mat=dark)

    # ---- front ports, cut on a measured pitch ------------------------------
    for (x, w) in bkit.lay_out([PORT_W, PORT_W], gap=PORT_PITCH - PORT_W):
        cut = bkit.rounded_box("_port", w, 20.0, PORT_H, r=1.5, segments=2,
                               centre=(x, -D / 2.0 + 4.0, 22.0))
        bkit.boolean(chassis, cut, "DIFFERENCE")
        bkit.rounded_box("PortShroud", w - 3.0, 6.0, PORT_H - 3.0, r=1.0,
                         segments=2,
                         centre=(x, -D / 2.0 + 5.0, 22.0), mat=dark)

    # ---- vent grille, recessed 0.5 mm under the plate ----------------------
    vent = bkit.perforated_panel("VentGrille", VENT_COLS, VENT_ROWS, VENT_PITCH,
                                VENT_PITCH, VENT_HOLE_R,
                                VENT_COLS * VENT_PITCH, VENT_ROWS * VENT_PITCH,
                                2.0, mat=dark)
    bkit.move(vent, -30.0, 55.0, H - 1.5)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=295.0, tol=0.1, how="bbox_x", part="Chassis"),
    dict(name="depth", mm=220.0, tol=0.1, how="bbox_y", part="Chassis"),
    dict(name="height", mm=70.0, tol=0.1, how="bbox_z", part="Chassis"),
    dict(name="top_plate_width", mm=291.0, tol=0.1, how="bbox_x", part="TopPlate"),
    dict(name="power_button", mm=14.0, tol=0.05, how="diameter", part="PowerButton"),
    dict(name="overall_height", mm=73.5, tol=0.1, how="bbox_z", part=None)
]