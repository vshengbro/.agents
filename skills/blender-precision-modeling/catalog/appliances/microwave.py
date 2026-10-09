"""
microwave -- 480 x 380 x 290 mm countertop microwave oven: enamelled steel
cabinet on four pads, a dark tinted door with a real recessed window behind a
chrome bezel, a bar handle, a right-hand control panel with a lit display, a
rotary encoder and a 3x3 keypad laid out from one pitch, and top cooling louvres.

The recessed window behind a proud bezel, and the right-hand control stack,
are the two features that separate a microwave from every other white box.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=480.0,
    cabinet_depth=380.0,
    cabinet_height=272.0,
    overall_height=286.0,     # pads to the top of the raised vent louvres
    foot_height=10.0,
    corner_radius=10.0,
    door_width=346.0,
    door_thickness=22.0,
    window_width=250.0,
    window_height=200.0,
    panel_width=120.0,
    key_diameter=26.0,
    key_pitch=34.0,
    key_rows=3,
    key_cols=3,
    encoder_diameter=52.0,
    display_width=86.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
H = SPEC["cabinet_height"]
FOOT = SPEC["foot_height"]
TOP = FOOT + H                              # 282, top of the cabinet
FRONT = -(D / 2.0)                          # -190, front face of the carcass
DOOR_X = -(W / 2.0) + SPEC["door_width"] / 2.0 + 7.0   # -67, leaf centre
DOOR_Y = FRONT - 6.0
DOOR_FACE = DOOR_Y - SPEC["door_thickness"] / 2.0        # -207, leaf front
PANEL_X = W / 2.0 - SPEC["panel_width"] / 2.0            # 180
PANEL_FACE = FRONT - 18.0                                # proud panel face
DOOR_H = H - 16.0


def build():
    enamel = bkit.pbr("MicroEnamel", base=(0.90, 0.90, 0.89),
                      metal=0.0, rough=0.22, coat=0.3)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("black_plastic")
    tint = bkit.pbr("MicroDoorGlass", base=(0.05, 0.05, 0.06), rough=0.08,
                    transmission=0.45, ior=1.5)
    lamp = bkit.pbr("MicroDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.35, 0.85, 0.95), emission_strength=1.5)

    # ---- carcass ----------------------------------------------------------
    body = bkit.rounded_box("MicroCabinet", W, D, H, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, FOOT + H / 2.0),
                            mat=enamel)

    # ---- door leaf, window aperture and chrome bezel ----------------------
    door = bkit.rounded_box("DoorLeaf", SPEC["door_width"],
                            SPEC["door_thickness"], DOOR_H, r=8.0, segments=4,
                            centre=(DOOR_X, DOOR_Y, FOOT + H / 2.0), mat=dark)
    # The blade is deliberately deeper than the leaf is thick, so it exits both
    # faces instead of ending tangent to either of them. bkit.boolean() consumes
    # its cutter, so a fresh blade is built for the bezel below.
    def _window_cutter():
        return bkit.rounded_box(
            "_window_cut", SPEC["window_width"],
            SPEC["door_thickness"] + 24.0, SPEC["window_height"],
            r=5.0, segments=3,
            centre=(DOOR_X, DOOR_Y, FOOT + H / 2.0 + 6.0))

    bkit.boolean(door, _window_cutter(), "DIFFERENCE")
    bkit.recalc(door)
    bkit.health(door)

    bezel = bkit.rounded_box("WindowBezel", SPEC["window_width"] + 18.0, 12.0,
                             SPEC["window_height"] + 18.0, r=6.0, segments=4,
                             centre=(DOOR_X, DOOR_FACE - 1.0,
                                     FOOT + H / 2.0 + 6.0),
                             mat=steel)
    bkit.boolean(bezel, _window_cutter(), "DIFFERENCE")
    bkit.recalc(bezel)
    bkit.health(bezel)

    # Tinted glass sits 3 mm behind the leaf face, so the bezel reads as a real
    # reveal rather than a flush laminate.
    bkit.rounded_box("DoorGlass", SPEC["window_width"] - 4.0, 6.0,
                     SPEC["window_height"] - 4.0, r=4.0, segments=3,
                     centre=(DOOR_X, DOOR_Y + 5.0, FOOT + H / 2.0 + 6.0),
                     mat=tint)
    # Dark cavity behind the glass: without it the window is a hole into the
    # bright inside of the cabinet and the door reads as a cut-out.
    bkit.rounded_box("WaveCavity", SPEC["window_width"] - 16.0, 6.0,
                     SPEC["window_height"] - 16.0, r=4.0, segments=2,
                     centre=(DOOR_X, DOOR_Y + 17.0, FOOT + H / 2.0 + 6.0),
                     mat=dark)

    # ---- door handle ------------------------------------------------------
    bkit.rounded_box("DoorHandle", 26.0, 22.0, 190.0, r=9.0, segments=4,
                     centre=(DOOR_X + SPEC["door_width"] / 2.0 - 18.0,
                             DOOR_FACE - 8.0, FOOT + H / 2.0), mat=steel)

    # ---- control panel ----------------------------------------------------
    bkit.rounded_box("ControlPanel", SPEC["panel_width"], 20.0, DOOR_H, r=7.0,
                     segments=4, centre=(PANEL_X, FRONT - 8.0, FOOT + H / 2.0),
                     mat=steel)
    bkit.rounded_box("ControlBezel", SPEC["panel_width"] - 14.0, 6.0, DOOR_H - 14.0,
                     r=5.0, segments=3,
                     centre=(PANEL_X, PANEL_FACE, FOOT + H / 2.0), mat=dark)
    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 6.0, 34.0, r=3.0,
                     segments=2,
                     centre=(PANEL_X, PANEL_FACE - 4.0, TOP - 58.0), mat=lamp)

    # ---- rotary encoder ---------------------------------------------------
    bkit.cylinder("EncoderKnob", SPEC["encoder_diameter"] / 2.0, 20.0, segments=48,
                  axis="Y", centre=(PANEL_X, PANEL_FACE - 7.0, TOP - 108.0),
                  mat=dark)
    bkit.rounded_box("EncoderPointer", 4.0, 12.0, 14.0, r=1.5, segments=2,
                     centre=(PANEL_X, PANEL_FACE - 19.0, TOP - 96.0), mat=steel)

    # ---- keypad: one pitch, one grid, never hand-placed -------------------
    kd = SPEC["key_diameter"]
    for idx, (dx, dy) in enumerate(
            bkit.grid_positions(cols=SPEC["key_cols"], rows=SPEC["key_rows"],
                                pitch_x=SPEC["key_pitch"],
                                pitch_y=SPEC["key_pitch"])):
        bkit.cylinder("Key_%d" % idx, kd / 2.0, 8.0, segments=28, axis="Y",
                      centre=(PANEL_X + dx, PANEL_FACE - 3.0, 76.0 + dy),
                      mat=dark)

    # ---- top cooling louvres ---------------------------------------------
    n = 13
    pitch = 26.0
    span = (n - 1) * pitch
    louvre = bkit.rounded_box("TopVent", 150.0, 8.0, 5.0, r=2.0, segments=2,
                              centre=(W / 2.0 - 100.0, -span / 2.0, TOP + 1.5),
                              mat=dark)
    bkit.array_linear(louvre, n, (0.0, pitch, 0.0))

    # ---- feet -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 14.0, FOOT, segments=28,
                          centre=(sx * (W / 2.0 - 30.0), sy * (D / 2.0 - 30.0),
                                  FOOT / 2.0),
                          mat=dark)

    return dict(spec=SPEC, parts=19)


CHECKS = [
    dict(name="cabinet_width", mm=480.0, tol=0.5, how="bbox_x", part="MicroCabinet"),
    dict(name="cabinet_depth", mm=380.0, tol=0.5, how="bbox_y", part="MicroCabinet"),
    dict(name="overall_height", mm=286.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=480.0, tol=0.5, how="bbox_x"),
    dict(name="glass_width", mm=246.0, tol=0.5, how="bbox_x", part="DoorGlass"),
    dict(name="glass_height", mm=196.0, tol=0.5, how="bbox_z", part="DoorGlass"),
    dict(name="encoder_diameter", mm=52.0, tol=0.4, how="diameter",
         part="EncoderKnob"),
]