"""
oven -- 595 x 570 x 600 mm built-in electric oven: enamelled steel carcass, a
drop-down door with a real glass window and a cast bar handle, a control
barrel across the top with two rotary knobs and a lit display, a wire shelf
visible through the glass, and a back-panel vent.

Built-in ovens have no feet and no legs; they hang off a rail, so the model
sits directly on the cabinet floor and reads as an appliance drop into a run.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cabinet_width=595.0,
    cabinet_depth=570.0,
    cabinet_height=600.0,
    overall_height=600.0,
    corner_radius=8.0,
    door_thickness=34.0,
    door_stand_off=8.0,
    door_height=440.0,
    window_width=400.0,
    window_height=260.0,
    knob_diameter=46.0,
    knob_count=2,
    knob_pitch=110.0,
    display_width=140.0,
    shelf_z=280.0,
)

W = SPEC["cabinet_width"]
D = SPEC["cabinet_depth"]
H = SPEC["cabinet_height"]
FRONT = -(D / 2.0)
DOOR_Y = FRONT - SPEC["door_stand_off"] + SPEC["door_thickness"] / 2.0
DOOR_FACE = DOOR_Y - SPEC["door_thickness"] / 2.0
DOOR_H = SPEC["door_height"]
DOOR_Z = 26.0 + DOOR_H / 2.0
BAR_Z = 548.0


def _on_face(t, proud=4.0):
    """Centre y for a part of thickness t moulded onto the carcass front."""
    return FRONT - t / 2.0 + proud


# Every control sits on the CONTROL BARREL's front face, not on the carcass
# front: the barrel already stands 24 mm proud, so measuring from the carcass
# buries the knobs inside the barrel they belong to.
BARREL_FACE = _on_face(34.0, 10.0) - 17.0


def build():
    enamel = bkit.pbr("OvenEnamel", base=(0.88, 0.88, 0.87),
                      metal=0.0, rough=0.24, coat=0.3)
    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("black_plastic")
    tint = bkit.pbr("OvenGlass", base=(0.06, 0.06, 0.07), rough=0.07,
                    transmission=0.5, ior=1.5)
    lamp = bkit.pbr("OvenDisplay", base=(0.02, 0.03, 0.04), rough=0.12,
                    emission=(0.95, 0.55, 0.25), emission_strength=1.6)

    # ---- carcass ----------------------------------------------------------
    body = bkit.rounded_box("OvenCabinet", W, D, H, r=SPEC["corner_radius"],
                            segments=5, centre=(0.0, 0.0, H / 2.0), mat=enamel)

    # Cavity cut, then the door cut: both blades over-run the surface they meet
    # so nothing ends exactly tangent to a skin.
    cavity = bkit.rounded_box("_cavity_cut", W - 90.0, 460.0, 330.0, r=6.0,
                              segments=3,
                              centre=(0.0, FRONT + 226.0, 26.0 + 165.0))
    bkit.boolean(body, cavity, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    # ---- drop-down door with a glass window --------------------------------
    def _door_cut():
        return bkit.rounded_box("_window_cut", SPEC["window_width"],
                                SPEC["door_thickness"] + 26.0,
                                SPEC["window_height"], r=5.0, segments=3,
                                centre=(0.0, DOOR_Y, DOOR_Z))

    door = bkit.rounded_box("OvenDoor", W - 16.0, SPEC["door_thickness"],
                            DOOR_H, r=8.0, segments=4,
                            centre=(0.0, DOOR_Y, DOOR_Z), mat=steel)
    bkit.boolean(door, _door_cut(), "DIFFERENCE")
    bkit.recalc(door)
    bkit.health(door)

    frame = bkit.rounded_box("DoorFrame", W - 4.0, 16.0, DOOR_H + 12.0, r=8.0,
                             segments=4, centre=(0.0, DOOR_FACE - 2.0, DOOR_Z),
                             mat=steel)
    bkit.boolean(frame, _door_cut(), "DIFFERENCE")
    bkit.recalc(frame)
    bkit.health(frame)

    bkit.rounded_box("DoorGlass", SPEC["window_width"] - 6.0, 8.0,
                     SPEC["window_height"] - 6.0, r=4.0, segments=3,
                     centre=(0.0, DOOR_Y + 6.0, DOOR_Z), mat=tint)
    # Dark oven cavity behind the glass so the window is not a hole into the
    # bright inside of the carcass.
    bkit.rounded_box("OvenLiner", W - 110.0, 10.0, 320.0, r=5.0, segments=2,
                     centre=(0.0, FRONT + 40.0, 26.0 + 165.0), mat=dark)

    # ---- wire shelf inside the cavity -------------------------------------
    # Each bar is a full-width rod in X and the array steps them in Y. The
    # offset is applied in the object's LOCAL space, so on an axis="X" cylinder
    # an X offset would walk the rods DOWN in world z instead of across the
    # cavity -- offset along the axis the rods do NOT run.
    bars = 7
    pitch = 44.0
    shelf = bkit.cylinder("ShelfBar", 3.5, 470.0, segments=16, axis="X",
                          centre=(0.0, -190.0, SPEC["shelf_z"]), mat=steel)
    bkit.array_linear(shelf, bars, (0.0, pitch, 0.0))

    # ---- bar handle -------------------------------------------------------
    bkit.rounded_box("DoorHandle", W - 120.0, 26.0, 30.0, r=11.0, segments=4,
                     centre=(0.0, DOOR_FACE - 10.0, DOOR_Z + DOOR_H / 2.0 - 34.0),
                     mat=steel)

    # ---- control barrel ---------------------------------------------------
    bkit.rounded_box("ControlBarrel", W - 8.0, 34.0, 100.0, r=8.0, segments=4,
                     centre=(0.0, _on_face(34.0, 10.0), BAR_Z), mat=steel)
    kd = SPEC["knob_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([kd] * SPEC["knob_count"],
                         gap=SPEC["knob_pitch"] - kd, centre=False)):
        bkit.cylinder("ControlKnob%d" % i, kd / 2.0, 24.0, segments=48, axis="Y",
                      centre=(-150.0 + x, BARREL_FACE - 6.0, BAR_Z), mat=dark)
        bkit.rounded_box("KnobPointer%d" % i, 4.0, 10.0, 15.0, r=1.5,
                         segments=2,
                         centre=(-150.0 + x, BARREL_FACE - 20.0, BAR_Z + 14.0),
                         mat=steel)
    bkit.rounded_box("ControlDisplay", SPEC["display_width"], 8.0, 44.0, r=3.0,
                     segments=2,
                     centre=(130.0, BARREL_FACE - 2.0, BAR_Z), mat=lamp)

    # ---- back-panel vent --------------------------------------------------
    n = 10
    pitch = 44.0
    span = (n - 1) * pitch
    louvre = bkit.rounded_box("RearVent", 30.0, 10.0, 9.0, r=3.0, segments=2,
                              centre=(-span / 2.0, D / 2.0 - 2.0, 60.0), mat=dark)
    bkit.array_linear(louvre, n, (pitch, 0.0, 0.0))

    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="cabinet_width", mm=595.0, tol=0.5, how="bbox_x", part="OvenCabinet"),
    dict(name="cabinet_depth", mm=570.0, tol=0.5, how="bbox_y", part="OvenCabinet"),
    dict(name="overall_height", mm=600.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=595.0, tol=0.5, how="bbox_x"),
    dict(name="door_height", mm=440.0, tol=0.5, how="bbox_z", part="OvenDoor"),
    dict(name="knob_diameter", mm=46.0, tol=0.4, how="diameter",
         part="ControlKnob0"),
]