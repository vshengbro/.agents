"""
bar_stool -- four-leg round bar stool, 350 mm seat diameter, 750 mm seat height.

750 mm is the defining number: a dining chair is 450 mm and this is exactly
300 mm taller, which is why it reads as bar furniture and not as a tall chair.
The foot ring at 250 mm is the second defining number -- without it a 750 mm
stool is just a chair that cannot be sat on comfortably, and with it the leg
frame closes into a recognisable object.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    seat_diameter=350.0,
    seat_height=750.0,      # bar height, 300 mm above a dining seat
    seat_thickness=35.0,
    seat_dish=6.0,
    legs=4,
    foot_circle=360.0,      # circle the feet stand on
    top_circle=250.0,       # circle the legs meet the seat on
    leg_bottom_section=30.0,
    leg_top_section=38.0,
    foot_ring_outer=158.0,
    foot_ring_inner=142.0,
    foot_ring_height=26.0,
    foot_ring_height_above_floor=250.0,
)

SEAT_R = SPEC["seat_diameter"] / 2.0
SEAT_T = SPEC["seat_thickness"]
SEAT_TOP = SPEC["seat_height"]
LEG_H = SEAT_TOP - SEAT_T               # 715
N_LEGS = SPEC["legs"]
FOOT_R = SPEC["foot_circle"] / 2.0      # 180
TOP_R = SPEC["top_circle"] / 2.0        # 125

CHECKS = [
    dict(name="seat_height", mm=750.0, tol=0.3, how="bbox_z"),
    dict(name="seat_diameter", mm=350.0, tol=0.3, how="diameter", part="Seat"),
    dict(name="seat_thickness", mm=35.0, tol=0.3, how="bbox_z", part="Seat"),
    dict(name="leg_height", mm=715.0, tol=0.3, how="bbox_z", part="Leg1"),
    dict(name="foot_ring_outer_diameter", mm=316.0, tol=0.3, how="diameter",
         part="FootRing"),
]


def _splayed_leg(name, angle_deg, mat):
    a = math.radians(angle_deg)
    bot = bkit.rounded_rect_section(SPEC["leg_bottom_section"],
                                    SPEC["leg_bottom_section"], r=3.0,
                                    per_corner=3,
                                    centre=(math.cos(a) * FOOT_R,
                                            math.sin(a) * FOOT_R))
    top = bkit.rounded_rect_section(SPEC["leg_top_section"],
                                    SPEC["leg_top_section"], r=4.0,
                                    per_corner=3,
                                    centre=(math.cos(a) * TOP_R,
                                            math.sin(a) * TOP_R))
    sections = [[(px, py, 0.0) for (px, py) in bot],
                [(px, py, LEG_H) for (px, py) in top]]
    leg = bkit.loft(name, sections, closed_loop=True, cap_start=True,
                    cap_end=True, mat=mat)
    bkit.bevel(leg, width_mm=0.8, segments=2, angle_deg=35)
    return leg


def build():
    wood = bkit.pbr("BarStoolOak", base=(0.42, 0.27, 0.13), metal=0.0, rough=0.36)
    wood_dark = bkit.pbr("BarStoolLeg", base=(0.33, 0.20, 0.09), metal=0.0,
                         rough=0.42)
    iron = bkit.preset("dark_metal")

    d = SPEC["seat_dish"]
    prof = [
        (0.0, 0.0),
        (SEAT_R - 5.0, 0.0),
        (SEAT_R, 3.0),
        (SEAT_R, SEAT_T - 5.0),
        (SEAT_R - 6.0, SEAT_T),
        (100.0, SEAT_T - d),
        (0.0, SEAT_T - d),
    ]
    bkit.lathe("Seat", prof, segments=96, centre=(0, 0, LEG_H), mat=wood)

    for i in range(N_LEGS):
        _splayed_leg("Leg%d" % (i + 1), 45.0 + 360.0 * i / N_LEGS, wood_dark)

    # Leg centreline at 250 mm is 180 - 55*(250/715) = 160.8 mm, so a ring
    # spanning 142..158 mm passes through all four legs.
    bkit.tube("FootRing", SPEC["foot_ring_outer"], SPEC["foot_ring_inner"],
              SPEC["foot_ring_height"], segments=64,
              centre=(0, 0, SPEC["foot_ring_height_above_floor"]), mat=iron)

    return dict(spec=SPEC, parts=6)
