"""
stool -- three-leg round wooden stool, 290 mm seat diameter, 280 mm seat height.

Low enough to be a step stool / dressing stool, which is what makes it a
*small* object rather than a second chair: at 280 mm it is 170 mm below a
dining seat, and the three splayed legs land on a 250 mm foot circle against a
290 mm seat, so the seat overhangs the feet the way a real stool does.

The splay is built into the geometry rather than applied as a rotation: each
leg is a loft between a foot ring and a top ring at different radii. Rotating a
straight leg would need an object transform, and a transform would also make
the measured bounding box lie about how far the feet actually reach.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    seat_diameter=290.0,
    seat_height=280.0,      # low step/dressing stool, well under a 450 seat
    seat_thickness=20.0,
    seat_dish=4.0,          # centre of the seat sits below the rim
    legs=3,
    foot_circle=250.0,      # circle the feet stand on
    top_circle=180.0,       # circle the legs meet the seat on
    leg_bottom_section=24.0,
    leg_top_section=30.0,
    stretcher_ring_outer=118.0,
    stretcher_ring_inner=104.0,
    stretcher_height=22.0,
    stretcher_height_above_floor=110.0,
)

SEAT_R = SPEC["seat_diameter"] / 2.0
SEAT_T = SPEC["seat_thickness"]
SEAT_TOP = SPEC["seat_height"]
LEG_H = SEAT_TOP - SEAT_T               # 260: legs stop under the seat
N_LEGS = SPEC["legs"]
FOOT_R = SPEC["foot_circle"] / 2.0      # 125
TOP_R = SPEC["top_circle"] / 2.0        # 90

CHECKS = [
    dict(name="seat_height", mm=280.0, tol=0.3, how="bbox_z"),
    dict(name="seat_diameter", mm=290.0, tol=0.3, how="diameter", part="Seat"),
    dict(name="seat_thickness", mm=20.0, tol=0.3, how="bbox_z", part="Seat"),
    dict(name="leg_height", mm=260.0, tol=0.3, how="bbox_z", part="Leg1"),
]


def _splayed_leg(name, angle_deg, mat):
    """One leg: a rounded square prism whose top is offset inboard of its foot."""
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
    bkit.bevel(leg, width_mm=0.7, segments=2, angle_deg=35)
    return leg


def build():
    wood = bkit.pbr("StoolBeech", base=(0.55, 0.37, 0.20), metal=0.0, rough=0.36)
    wood_dark = bkit.pbr("StoolLeg", base=(0.45, 0.29, 0.15), metal=0.0,
                         rough=0.42)
    iron = bkit.preset("dark_metal")

    # ---- seat: a lathed dish, not a disc ----------------------------------
    # Profile runs axis -> bottom -> up the outside -> back in along the dished
    # top. Both end radii are 0, so lathe emits no cap faces and the solid
    # closes on its own axis.
    d = SPEC["seat_dish"]
    prof = [
        (0.0, 0.0),
        (SEAT_R - 4.0, 0.0),
        (SEAT_R, 2.5),
        (SEAT_R, SEAT_T - 3.0),
        (SEAT_R - 4.0, SEAT_T),
        (80.0, SEAT_T - d),
        (0.0, SEAT_T - d),
    ]
    bkit.lathe("Seat", prof, segments=96, centre=(0, 0, LEG_H), mat=wood)

    for i in range(N_LEGS):
        _splayed_leg("Leg%d" % (i + 1), 90.0 + 360.0 * i / N_LEGS, wood_dark)

    # ---- foot ring, sized to pass through the legs at z = 110 -------------
    # The leg centreline runs linearly from 125 mm at the floor to 90 mm at the
    # seat, so at 110 mm it sits at 125 - 35*(110/260) = 110.2 mm: the ring
    # spans 104..118 and straddles that.
    bkit.tube("FootRing", SPEC["stretcher_ring_outer"],
              SPEC["stretcher_ring_inner"], SPEC["stretcher_height"],
              segments=64, centre=(0, 0, SPEC["stretcher_height_above_floor"]),
              mat=iron)

    return dict(spec=SPEC, parts=5)
