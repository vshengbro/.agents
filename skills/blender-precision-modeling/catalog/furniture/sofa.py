"""
sofa -- three-seat sofa, 2100 mm long, 850 mm high, 430 mm seat height.

A three-seater is three 560 mm seats inside 2100 mm of outside width: the two
180 mm arms and the 1740 mm clear span are not round numbers, they are what
remains after the seat bank is divided. All six cushions are laid out with
bkit.lay_out from their real widths plus a 30 mm gap, so the seat bank and the
back bank are guaranteed to align -- the single most visible error on a sofa
is a back cushion that does not line up with the seat cushion under it.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=2100.0,
    depth=900.0,
    height=850.0,
    foot_height=90.0,
    foot_diameter=64.0,
    base_height=170.0,
    seat_height=430.0,
    arm_width=180.0,
    arm_top=640.0,
    seat_cushion_count=3,
    seat_cushion_width=560.0,
    seat_cushion_depth=700.0,
    seat_cushion_thickness=170.0,
    cushion_gap=30.0,
    back_cushion_height=400.0,
    back_cushion_thickness=180.0,
)

L, D, H = SPEC["length"], SPEC["depth"], SPEC["height"]
FOOT_H = SPEC["foot_height"]
BASE_H = SPEC["base_height"]
BASE_Z0 = FOOT_H                              # 90
BASE_CZ = BASE_Z0 + BASE_H / 2.0              # 175
BASE_Z1 = BASE_Z0 + BASE_H                   # 260
SEAT_TOP = SPEC["seat_height"]                # 430
CUSH_W = SPEC["seat_cushion_width"]
CUSH_D = SPEC["seat_cushion_depth"]
CUSH_T = SPEC["seat_cushion_thickness"]
GAP = SPEC["cushion_gap"]
ARM_W = SPEC["arm_width"]
BACK_T = SPEC["back_cushion_thickness"]
BACK_H = SPEC["back_cushion_height"]

CHECKS = [
    dict(name="overall_length", mm=2100.0, tol=0.5, how="bbox_x"),
    dict(name="overall_height", mm=850.0, tol=0.5, how="bbox_z"),
    dict(name="overall_depth", mm=900.0, tol=0.5, how="bbox_y"),
    dict(name="seat_cushion_width", mm=560.0, tol=0.3, how="bbox_x",
         part="SeatCushion0"),
    dict(name="seat_cushion_thickness", mm=170.0, tol=0.3, how="bbox_z",
         part="SeatCushion0"),
    dict(name="arm_width", mm=180.0, tol=0.3, how="bbox_x", part="ArmLeft"),
    dict(name="back_panel_width", mm=2060.0, tol=0.4, how="bbox_x",
         part="BackPanel"),
]


def build():
    cloth = bkit.pbr("SofaLinen", base=(0.52, 0.50, 0.46), metal=0.0, rough=0.86)
    cloth_dk = bkit.pbr("SofaCushion", base=(0.44, 0.42, 0.38), metal=0.0,
                        rough=0.88)
    wood = bkit.pbr("SofaFoot", base=(0.28, 0.17, 0.08), metal=0.0, rough=0.42)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            bkit.cylinder("Foot%s%s" % (yn, xn), SPEC["foot_diameter"] / 2.0,
                          FOOT_H, segments=24,
                          centre=(sx * (L / 2.0 - 150.0), sy * (D / 2.0 - 100.0),
                                  FOOT_H / 2.0),
                          mat=wood)

    bkit.rounded_box("Base", L, D, BASE_H, r=16.0, segments=4,
                     centre=(0, 0, BASE_CZ), mat=cloth)

    # Back panel fills the rear third and carries the 850 mm overall height.
    # 20 mm narrower than the 2100 mm outside width: the arms' outer faces are
    # at x = +/-1050, and a full-width panel would share that plane with them
    # over the whole arm height -- z-fighting, which health() cannot see and
    # which renders as a black patch on the arm.
    panel_t = 200.0
    bkit.rounded_box("BackPanel", L - 40.0, panel_t, H - BASE_Z1, r=16.0,
                     segments=4,
                     centre=(0, D / 2.0 - panel_t / 2.0, (BASE_Z1 + H) / 2.0),
                     mat=cloth)

    arm_x = L / 2.0 - ARM_W / 2.0
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Arm%s" % tag, ARM_W, D, SPEC["arm_top"] - BASE_Z1,
                         r=18.0, segments=4,
                         centre=(sx * arm_x, 0, (BASE_Z1 + SPEC["arm_top"]) / 2.0),
                         mat=cloth)

    # ---- cushion banks: one lay_out each, so the two banks align ----------
    cols = bkit.lay_out([CUSH_W] * SPEC["seat_cushion_count"], gap=GAP)
    for i, (cx, _w) in enumerate(cols):
        bkit.rounded_box("SeatCushion%d" % i, CUSH_W, CUSH_D, CUSH_T, r=34.0,
                         segments=4, centre=(cx, -60.0, SEAT_TOP - CUSH_T / 2.0),
                         mat=cloth_dk)
    back_z1 = H - 20.0
    for i, (cx, _w) in enumerate(cols):
        bkit.rounded_box("BackCushion%d" % i, CUSH_W, BACK_T, BACK_H, r=40.0,
                         segments=4,
                         centre=(cx, D / 2.0 - panel_t - BACK_T / 2.0 + 10.0,
                                 back_z1 - BACK_H / 2.0),
                         mat=cloth_dk)

    return dict(spec=SPEC, parts=14)
