"""
stove -- 600 x 650 x 900 mm freestanding cooker: enamelled carcass on four
legs, an oven door with a window and a cast handle, a hob with four burner
assemblies on a computed grid, a control panel with four knobs on one pitch and
a display, and a raised back splash.

The burner rings and the knob row are the two repeated features, and both are
laid out from a real pitch so the spacing cannot come out uneven.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=600.0,
    cabinet_depth=600.0,
    leg_height=100.0,
    carcass_height=700.0,
    back_splash_height=100.0,
    overall_height=900.0,
    corner_radius=10.0,
    hob_plate_thickness=12.0,
    burner_count=4,
    burner_pitch_x=270.0,
    burner_pitch_y=250.0,
    burner_cap_diameter=92.0,
    burner_ring_diameter=150.0,
    knob_count=4,
    knob_diameter=42.0,
    knob_pitch=96.0,
    door_thickness=34.0,
    door_height=440.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
LEG = SPEC["leg_height"]
CH = SPEC["carcass_height"]
SPLASH = SPEC["back_splash_height"]
TOP = LEG + CH                            # 800, top of the carcass
FRONT = -(D / 2.0)
DOOR_Y = FRONT - 8.0 + SPEC["door_thickness"] / 2.0
DOOR_H = SPEC["door_height"]
DOOR_Z = LEG + 26.0 + DOOR_H / 2.0
PANEL_Z = LEG + CH - 120.0


def _on_face(t, proud=4.0):
    """Centre y for a part of thickness t moulded onto the carcass front."""
    return FRONT - t / 2.0 + proud


def build():
    enamel = bkit.pbr("StoveEnamel", base=(0.88, 0.88, 0.87),
                      metal=0.0, rough=0.24, coat=0.3)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("black_plastic")
    tint = bkit.pbr("StoveGlass", base=(0.06, 0.06, 0.07), rough=0.07,
                    transmission=0.5, ior=1.5)
    lamp = bkit.pbr("StoveDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.95, 0.62, 0.30), emission_strength=1.6)

    # ---- carcass and back splash ------------------------------------------
    body = bkit.rounded_box("StoveCarcass", W, D, CH, r=SPEC["corner_radius"],
                            segments=5, centre=(0.0, 0.0, LEG + CH / 2.0),
                            mat=enamel)
    bkit.rounded_box("BackSplash", W, 40.0, SPLASH, r=8.0, segments=4,
                     centre=(0.0, D / 2.0 - 14.0, TOP + SPLASH / 2.0), mat=enamel)

    # ---- hob plate and four burner assemblies -----------------------------
    bkit.rounded_box("HobPlate", W - 10.0, D - 60.0, SPEC["hob_plate_thickness"],
                     r=6.0, segments=4,
                     centre=(0.0, -20.0, TOP + SPEC["hob_plate_thickness"] / 2.0),
                     mat=dark)
    # grid_positions gives the four burner centres on one computed pitch, so
    # the hob can never end up with a burner hanging off the plate.
    bx, by = SPEC["burner_pitch_x"], SPEC["burner_pitch_y"]
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=bx, pitch_y=by)):
        bkit.cylinder("BurnerCap%d" % i, SPEC["burner_cap_diameter"] / 2.0, 8.0,
                      segments=48, centre=(x, y, TOP + 24.0), mat=dark)
        bkit.tube("BurnerRing%d" % i, SPEC["burner_ring_diameter"] / 2.0,
                  SPEC["burner_ring_diameter"] / 2.0 - 14.0, 9.0, segments=64,
                  centre=(x, y, TOP + 26.0), mat=dark)
        # Trivet: three bars at 60 deg make a six-spoke pan stand. rounded_box
        # bakes its centre into the vertices and leaves obj.location at the
        # origin, so the bar has to be rotated FIRST and moved afterwards --
        # rotating it after placing would swing it around the world origin.
        for k in range(3):
            bar = bkit.rounded_box("Trivet%d_%d" % (i, k), 132.0, 12.0, 8.0,
                                   r=4.0, segments=2, mat=dark)
            bar.rotation_euler = (0.0, math.radians(60 * k), 0.0)
            bkit.move(bar, x, y, TOP + 16.0)

    # ---- oven door --------------------------------------------------------
    def _door_cut():
        return bkit.rounded_box("_window_cut", 380.0, SPEC["door_thickness"] + 26.0,
                                250.0, r=5.0, segments=3,
                                centre=(0.0, DOOR_Y, DOOR_Z))

    door = bkit.rounded_box("OvenDoor", W - 30.0, SPEC["door_thickness"], DOOR_H,
                            r=8.0, segments=4, centre=(0.0, DOOR_Y, DOOR_Z),
                            mat=steel)
    bkit.boolean(door, _door_cut(), "DIFFERENCE")
    bkit.recalc(door)
    bkit.health(door)

    frame = bkit.rounded_box("DoorFrame", W - 18.0, 14.0, DOOR_H + 12.0, r=8.0,
                             segments=4,
                             centre=(0.0, DOOR_Y - SPEC["door_thickness"] / 2.0
                                     - 3.0, DOOR_Z), mat=steel)
    bkit.boolean(frame, _door_cut(), "DIFFERENCE")
    bkit.recalc(frame)
    bkit.health(frame)

    bkit.rounded_box("DoorGlass", 374.0, 8.0, 244.0, r=4.0, segments=3,
                     centre=(0.0, DOOR_Y + 5.0, DOOR_Z), mat=tint)
    bkit.rounded_box("OvenLiner", 460.0, 10.0, 320.0, r=5.0, segments=2,
                     centre=(0.0, FRONT + 46.0, DOOR_Z), mat=dark)

    # ---- handle, control panel, display -----------------------------------
    bkit.rounded_box("DoorHandle", W - 130.0, 26.0, 30.0, r=11.0, segments=4,
                     centre=(0.0, DOOR_Y - SPEC["door_thickness"] / 2.0 - 12.0,
                             DOOR_Z + DOOR_H / 2.0 - 36.0), mat=steel)

    bkit.rounded_box("ControlPanel", W - 40.0, 26.0, 92.0, r=7.0, segments=4,
                     centre=(0.0, _on_face(26.0, 8.0), PANEL_Z), mat=steel)
    kd = SPEC["knob_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["knob_count"],
                         gap=SPEC["knob_pitch"] - kd, centre=False)):
        bkit.cylinder("ControlKnob%d" % i, kd / 2.0, 22.0, segments=48, axis="Y",
                      centre=(-240.0 + x, _on_face(26.0, 22.0), PANEL_Z),
                      mat=dark)
        bkit.rounded_box("KnobPointer%d" % i, 4.0, 10.0, 14.0, r=1.5,
                         segments=2,
                         centre=(-240.0 + x, _on_face(26.0, 32.0), PANEL_Z + 13.0),
                         mat=steel)
    bkit.rounded_box("ControlDisplay", 110.0, 8.0, 40.0, r=3.0, segments=2,
                     centre=(195.0, _on_face(26.0, 16.0), PANEL_Z), mat=lamp)

    # ---- legs -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.rounded_box("Leg_%d%d" % (ix, iy), 46.0, 46.0, LEG, r=8.0,
                             segments=3,
                             centre=(sx * (W / 2.0 - 60.0),
                                     sy * (D / 2.0 - 60.0), LEG / 2.0),
                             mat=dark)

    return dict(spec=SPEC, parts=24)


CHECKS = [
    dict(name="carcass_width", mm=600.0, tol=0.5, how="bbox_x", part="StoveCarcass"),
    dict(name="carcass_depth", mm=600.0, tol=0.5, how="bbox_y", part="StoveCarcass"),
    dict(name="overall_height", mm=900.0, tol=0.6, how="bbox_z"),
    dict(name="overall_width", mm=600.0, tol=0.5, how="bbox_x"),
    dict(name="door_height", mm=440.0, tol=0.5, how="bbox_z", part="OvenDoor"),
    dict(name="knob_diameter", mm=42.0, tol=0.4, how="diameter",
         part="ControlKnob0"),
    dict(name="burner_cap_diameter", mm=92.0, tol=0.4, how="diameter",
         part="BurnerCap0"),
]