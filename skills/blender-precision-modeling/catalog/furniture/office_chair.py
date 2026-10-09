"""
office_chair -- five-star task chair, 480 mm seat height, 1020 mm overall.

A task chair is three stacked systems and the silhouette only reads when their
heights are right: a 600 mm castor-to-hub base, a gas column from 70 to 360 mm,
and a seat pan whose top is at 480 mm -- 30 mm above a dining chair, which is
what puts the armrests at a typing height rather than a dining one. The
backrest is lofted from three sections so it flares from 400 mm at the lumbar
to 450 mm at the shoulders.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    overall_height=1020.0,
    seat_height=480.0,
    seat_width=480.0,
    seat_depth=470.0,
    seat_thickness=80.0,
    back_height=480.0,
    back_bottom_width=400.0,
    back_top_width=450.0,
    base_diameter=600.0,
    base_arms=5,
    armrest_height=710.0,
    castor_diameter=52.0,
    column_diameter=80.0,
)

SEAT_W, SEAT_D = SPEC["seat_width"], SPEC["seat_depth"]
SEAT_T = SPEC["seat_thickness"]
SEAT_TOP = SPEC["seat_height"]
SEAT_Z0 = SEAT_TOP - SEAT_T               # 400
MECH_H = 40.0
MECH_Z0 = SEAT_Z0 - MECH_H               # 360
COL_TOP = MECH_Z0                        # 360: the column tops out under the tilt
HUB_Z0 = 70.0
BASE_R = SPEC["base_diameter"] / 2.0     # 300
CASTOR_R = SPEC["castor_diameter"] / 2.0 # 26
N_ARMS = SPEC["base_arms"]

CHECKS = [
    dict(name="overall_height", mm=1020.0, tol=0.5, how="bbox_z"),
    dict(name="seat_width", mm=480.0, tol=0.3, how="bbox_x", part="Seat"),
    dict(name="seat_depth", mm=470.0, tol=0.3, how="bbox_y", part="Seat"),
    dict(name="seat_thickness", mm=80.0, tol=0.3, how="bbox_z", part="Seat"),
    dict(name="back_height", mm=480.0, tol=0.3, how="bbox_z", part="Backrest"),
    dict(name="back_top_width", mm=450.0, tol=0.3, how="bbox_x", part="Backrest"),
]


def _place(obj, x, y, z, rot_deg=(0.0, 0.0, 0.0)):
    """Absolute placement in MILLIMETRES plus an absolute euler in degrees.

    obj.location is metres in Blender, so it must go through bkit.v(); only the
    rotation is raw (Blender wants radians there). The view_layer update is not
    optional -- matrix_world is cached, and run_model measures the bounding box
    before anything forces a depsgraph evaluation.

    `rot_deg` REPLACES the rotation, it does not add to it. cylinder(axis="Y")
    leaves a 90 deg X rotation on the object, and silently dropping it here
    stood every castor on its edge -- which floated the whole chair 14 mm above
    the floor and made the measured overall height 14 mm short.
    """
    obj.location = bkit.v(x, y, z)
    obj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.view_layer.update()
    return obj


def build():
    frame = bkit.pbr("ChairFrame", base=(0.10, 0.10, 0.11), metal=0.0, rough=0.45)
    mesh_fab = bkit.pbr("ChairMesh", base=(0.13, 0.14, 0.16), metal=0.0, rough=0.72)
    chrome = bkit.preset("polished_metal")
    dark = bkit.preset("dark_metal")

    # ---- five-star base + castors -----------------------------------------
    # The arm mesh is authored already offset to +X (a spoke, not a diameter)
    # so that rotating the object about its own origin swings it around the hub
    # instead of about its middle. Authoring five sets of coordinates by hand is
    # exactly the hand-placing the anti-hand-placing rule warns about, and a
    # 72 deg miss on one arm is invisible in the numbers but obvious in the
    # render.
    arm = bkit.rounded_box("BaseArm0", 270.0, 58.0, 40.0, r=10.0, segments=3,
                           centre=(155.0, 0, 0), mat=dark)
    castor = bkit.cylinder("Castor0", CASTOR_R, 24.0, segments=32,
                           centre=(0, 0, 0), axis="Y", mat=dark)
    _place(arm, 0, 0, 62.0)
    # 90 deg X lays the wheel disc flat; centre at its own radius so the tyre
    # touches z=0 and the chair is not left floating for sit_on_floor to fix.
    _place(castor, BASE_R - 10.0, 0, CASTOR_R, rot_deg=(90.0, 0.0, 0.0))
    for i in range(1, N_ARMS):
        ang = 360.0 * i / N_ARMS
        bkit.duplicate(arm, "BaseArm%d" % i, offset_mm=(0, 0, 62.0),
                       rot_deg=(0, 0, ang))
        bkit.duplicate(castor, "Castor%d" % i, offset_mm=(0, 0, CASTOR_R),
                       rot_deg=(90, 0, ang))
    bpy.context.view_layer.update()
    bkit.cylinder("Hub", 52.0, 48.0, segments=40, centre=(0, 0, HUB_Z0 + 24.0),
                  mat=dark)

    # ---- gas column: a wide sleeve over a narrow polished shaft ------------
    bkit.cylinder("ColumnSleeve", SPEC["column_diameter"] / 2.0, 150.0,
                  segments=40, centre=(0, 0, HUB_Z0 + 75.0), mat=dark)
    bkit.cylinder("ColumnShaft", 24.0, COL_TOP - (HUB_Z0 + 150.0), segments=32,
                  centre=(0, 0, (HUB_Z0 + 150.0 + COL_TOP) / 2.0), mat=chrome)

    # ---- seat pan, tilt mechanism, back support ---------------------------
    bkit.rounded_box("TiltMechanism", 230.0, 210.0, MECH_H, r=8.0, segments=3,
                     centre=(0, 0, MECH_Z0 + MECH_H / 2.0), mat=frame)
    bkit.rounded_box("Seat", SEAT_W, SEAT_D, SEAT_T, r=26.0, segments=4,
                     centre=(0, -10.0, SEAT_Z0 + SEAT_T / 2.0), mat=mesh_fab)
    bkit.rounded_box("BackStem", 80.0, 50.0, 170.0, r=8.0, segments=2,
                     centre=(0, 195.0, 470.0), mat=frame)

    # ---- backrest: three lofted sections, flaring toward the shoulders ----
    back_y = 215.0
    back_z0 = 540.0
    back_z1 = back_z0 + SPEC["back_height"]               # 1020
    sections = []
    for (w, d, z) in ((SPEC["back_bottom_width"], 70.0, back_z0),
                      ((SPEC["back_bottom_width"] + SPEC["back_top_width"]) / 2.0,
                       66.0, back_z0 + SPEC["back_height"] * 0.5),
                      (SPEC["back_top_width"], 58.0, back_z1)):
        ring = bkit.rounded_rect_section(w, d, r=24.0, per_corner=4)
        sections.append([(x, y + back_y, z) for (x, y) in ring])
    back = bkit.loft("Backrest", sections, closed_loop=True, cap_start=True,
                     cap_end=True, mat=mesh_fab)
    bkit.recalc(back)
    bkit.bevel(back, width_mm=1.2, segments=2, angle_deg=40)

    # ---- armrests: post + pad, top of pad at 710 mm -----------------------
    for (sx, tag) in ((-1, "Left"), (1, "Right")):
        bkit.rounded_box("ArmPost%s" % tag, 45.0, 60.0, 200.0, r=10.0,
                         segments=3, centre=(sx * 255.0, 60.0, 580.0), mat=frame)
        bkit.rounded_box("ArmPad%s" % tag, 70.0, 240.0, 30.0, r=13.0,
                         segments=3,
                         centre=(sx * 255.0, -20.0, SPEC["armrest_height"] - 15.0),
                         mat=frame)

    return dict(spec=SPEC, parts=19)
