"""
armchair -- upholstered occasional armchair, 800 mm wide, 800 mm high.

The numbers that make an armchair an armchair rather than a chair with padding:
an 800 mm outside width, 440 mm seat height, and 620 mm arm tops -- the arms
have to be low enough to reach across and high enough to support a forearm.
The 120 mm turned legs are what stop an upholstered mass from reading as a
block sitting on the floor.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width=800.0,
    depth=820.0,
    height=800.0,
    leg_height=120.0,
    leg_section=50.0,
    base_height=200.0,       # upholstered box the seat cushion sits on
    seat_height=440.0,
    seat_cushion_width=560.0,
    seat_cushion_depth=640.0,
    seat_cushion_thickness=120.0,
    back_panel_thickness=200.0,
    back_panel_width=780.0,  # 20 mm narrower than the outside width, see build
    arm_width=120.0,
    arm_height=300.0,        # arm panel height, sitting on the 320 mm base
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
LEG_H = SPEC["leg_height"]
LEG = SPEC["leg_section"]
BASE_H = SPEC["base_height"]
BASE_Z0 = LEG_H                                  # 120
BASE_CZ = BASE_Z0 + BASE_H / 2.0                 # 220
SEAT_TOP = SPEC["seat_height"]                   # 440
CUSH_T = SPEC["seat_cushion_thickness"]          # 120
CUSH_CZ = SEAT_TOP - CUSH_T / 2.0               # 380
ARM_W = SPEC["arm_width"]
# Arms sit on top of the upholstered base, so their top lands at
# 120 + 200 + 300 = 620 mm -- forearm height above a 440 mm seat.
ARM_TOP = BASE_Z0 + BASE_H + SPEC["arm_height"]
ARM_CZ = (BASE_Z0 + BASE_H + ARM_TOP) / 2.0

CHECKS = [
    dict(name="overall_width", mm=800.0, tol=0.3, how="bbox_x"),
    dict(name="overall_height", mm=800.0, tol=0.3, how="bbox_z"),
    dict(name="overall_depth", mm=820.0, tol=0.3, how="bbox_y"),
    dict(name="seat_cushion_width", mm=560.0, tol=0.3, how="bbox_x",
         part="SeatCushion"),
    dict(name="seat_cushion_thickness", mm=120.0, tol=0.3, how="bbox_z",
         part="SeatCushion"),
    dict(name="seat_cushion_depth", mm=640.0, tol=0.3, how="bbox_y",
         part="SeatCushion"),
    dict(name="arm_width", mm=120.0, tol=0.3, how="bbox_x", part="ArmLeft"),
    dict(name="back_panel_width", mm=780.0, tol=0.3, how="bbox_x",
         part="BackPanel"),
]


def build():
    # Mid-tone, not navy. An 0.14-albedo upholstery inside a 560 mm well
    # between two arms gets no light at all and renders as a black hole with
    # hard edges, which reads as missing geometry rather than as shadow.
    cloth = bkit.pbr("UpholsterySlate", base=(0.44, 0.49, 0.58), metal=0.0,
                     rough=0.85)
    cloth_dk = bkit.pbr("UpholsteryShadow", base=(0.35, 0.40, 0.49), metal=0.0,
                        rough=0.88)
    wood = bkit.pbr("ArmchairWalnut", base=(0.30, 0.18, 0.09), metal=0.0,
                    rough=0.40)

    for (sx, xn) in ((-1, "Left"), (1, "Right")):
        for (sy, yn) in ((-1, "Front"), (1, "Back")):
            bkit.rounded_box("Leg%s%s" % (yn, xn), LEG, LEG, LEG_H, r=5.0,
                             segments=2,
                             centre=(sx * (W / 2.0 - 60.0), sy * (D / 2.0 - 60.0),
                                     LEG_H / 2.0),
                             mat=wood)

    bkit.rounded_box("Base", W, D, BASE_H, r=18.0, segments=4,
                     centre=(0, 0, BASE_CZ), mat=cloth)

    # Back panel sits flush with the rear of the base, so the 820 mm depth is
    # owned by the base and the back does not push the silhouette further out.
    #
    # It is 20 mm NARROWER than the 800 mm outside width on purpose. The arms'
    # outer faces are at x = +/-400, so a full-width back panel puts two large
    # flat faces in exactly the same plane over y 210..410 / z 320..620. That
    # is not a mesh defect -- both parts stay watertight and health() reports
    # zero non-manifold edges -- it is z-fighting, and it renders as a hard
    # black rectangle punched into the side of the chair.
    back_t = SPEC["back_panel_thickness"]
    back_w = W - 20.0
    bkit.rounded_box("BackPanel", back_w, back_t, H - BASE_Z0 - BASE_H, r=20.0,
                     segments=4,
                     centre=(0, D / 2.0 - back_t / 2.0,
                             (BASE_Z0 + BASE_H + H) / 2.0),
                     mat=cloth)
    bkit.rounded_box("BackCushion", 560.0, 150.0, 380.0, r=45.0, segments=4,
                     centre=(0, D / 2.0 - back_t - 55.0, 590.0), mat=cloth_dk)

    # Arms: outer face lands exactly on the 800 mm width, inner face exactly on
    # the 560 mm seat cushion, so the cushion spans the clear width with no gap.
    arm_x = W / 2.0 - ARM_W / 2.0
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("Arm%s" % tag, ARM_W, D, ARM_TOP - (BASE_Z0 + BASE_H),
                         r=20.0, segments=4, centre=(sx * arm_x, 0, ARM_CZ),
                         mat=cloth)

    # The cushion has to fill the well between the arms all the way back to the
    # back panel. A 560 mm cushion on an 820 mm base leaves a bare shelf in
    # front of it and a 180 mm deep void behind, and that void is what renders
    # black. 640 mm deep leaves a 20 mm front ledge and tucks under the back.
    bkit.rounded_box("SeatCushion", SPEC["seat_cushion_width"],
                     SPEC["seat_cushion_depth"], CUSH_T, r=32.0, segments=4,
                     centre=(0, -70.0, CUSH_CZ), mat=cloth_dk)

    return dict(spec=SPEC, parts=10)
