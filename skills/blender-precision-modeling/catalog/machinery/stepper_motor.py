"""
stepper_motor -- NEMA 23 (57 mm) two-phase stepper with a 5 mm D-cut shaft.

NEMA 23 is a standard, so the numbers are the standard's: 57.0 mm across the
flats, mounting holes on the 47.14 mm square, a 38.1 mm pilot boss, and a
22.2 mm long 5 mm shaft with a flat and a keyway. The body, front plate and
rear cap are one fused solid so the rear cap can be black plastic by face
assignment instead of being a second shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    flange_size=57.0,           # across flats
    body_length=76.0,
    body_bolt_pitch=47.14,      # NEMA 23 mounting square
    mounting_holes=4,
    mounting_hole_diameter=5.2,
    front_plate_size=55.0,
    front_plate_thickness=6.0,
    pilot_diameter=38.1,
    pilot_height=2.0,
    rear_cap_size=55.0,
    rear_cap_length=12.0,
    shaft_diameter=5.0,
    shaft_length=30.0,
    shaft_protrusion=20.0,
    shaft_flat_depth=1.5,
    keyway_width=3.0,
    overall_length=89.0,
)


def build():
    F = SPEC["flange_size"]
    L = SPEC["body_length"]
    half = F / 2.0

    alloy = bkit.pbr("anodised", base=(0.52, 0.53, 0.55), metal=0.45, rough=0.40)
    steel = bkit.pbr("bright_steel", base=(0.74, 0.75, 0.78), metal=0.70, rough=0.16)
    cap_mat = bkit.pbr("black_polymer", base=(0.10, 0.10, 0.11), rough=0.35)

    # ---- laminated stator stack ----------------------------------------
    body = bkit.rounded_box("Motor", F, F, L, r=2.5, segments=3,
                            centre=(0.0, 0.0, L / 2.0), mat=alloy)

    # ---- front end plate + pilot boss (both overlap the stack) ----------
    plate = bkit.rounded_box("FrontPlate", SPEC["front_plate_size"],
                             SPEC["front_plate_size"],
                             SPEC["front_plate_thickness"], r=2.0, segments=2,
                             centre=(0.0, 0.0, L - 1.0), mat=alloy)
    bkit.boolean(body, plate, "UNION")
    pilot = bkit.cylinder("Pilot", SPEC["pilot_diameter"] / 2.0,
                          SPEC["pilot_height"] + 2.0, segments=72,
                          centre=(0.0, 0.0, L + SPEC["pilot_height"] / 2.0), mat=alloy)
    bkit.boolean(body, pilot, "UNION")

    # ---- rear cap, overlapping the stack by 2 mm -----------------------
    cap = bkit.rounded_box("RearCap", SPEC["rear_cap_size"], SPEC["rear_cap_size"],
                           SPEC["rear_cap_length"], r=2.0, segments=2,
                           centre=(0.0, 0.0, -SPEC["rear_cap_length"] / 2.0 + 2.0),
                           mat=alloy)
    bkit.boolean(body, cap, "UNION")

    # ---- four mounting holes on the 47.14 square -----------------------
    for (x, y) in bkit.grid_positions(2, 2, SPEC["body_bolt_pitch"],
                                      SPEC["body_bolt_pitch"]):
        hole = bkit.cylinder("MountHole", SPEC["mounting_hole_diameter"] / 2.0,
                             L + 40.0, segments=32, centre=(x, y, L / 2.0))
        bkit.boolean(body, hole, "DIFFERENCE")

    # ---- shaft clearance bore in the front face ------------------------
    seat = bkit.cylinder("ShaftSeat", SPEC["shaft_diameter"] / 2.0 + 0.1, 14.0,
                         segments=64, centre=(0.0, 0.0, L - 1.0))
    bkit.boolean(body, seat, "DIFFERENCE")
    bkit.recalc(body)
    body.name = "Motor"
    bkit.assign_faces_by(body, cap_mat, lambda c, n: c.z < 0.5)

    # ---- shaft: D-flat and keyway --------------------------------------
    z_shaft0 = L - 10.0
    shaft = bkit.cylinder("Shaft", SPEC["shaft_diameter"] / 2.0,
                          SPEC["shaft_length"], segments=64,
                          centre=(0.0, 0.0, z_shaft0 + SPEC["shaft_length"] / 2.0),
                          mat=steel)
    z_flat = z_shaft0 + 24.0
    flat = bkit.box("Flat", 20.0, 10.0, 12.0,
                    centre=(0.0, half * 0 + 4.0 + SPEC["shaft_diameter"] / 4.0, z_flat))
    bkit.boolean(shaft, flat, "DIFFERENCE")
    key = bkit.box("Keyway", SPEC["keyway_width"], 6.0, 10.0,
                   centre=(0.0, SPEC["shaft_diameter"] / 4.0 + 0.4, z_shaft0 + 8.0))
    bkit.boolean(shaft, key, "DIFFERENCE")
    bkit.recalc(shaft)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="flange_size", mm=57.0, tol=0.4, how="bbox_x", part="Motor"),
    dict(name="overall_length", mm=89.0, tol=0.5, how="bbox_z", part="Motor"),
    dict(name="shaft_diameter", mm=5.0, tol=0.3, how="bbox_x", part="Shaft"),
    dict(name="shaft_length", mm=30.0, tol=0.4, how="bbox_z", part="Shaft"),
]
