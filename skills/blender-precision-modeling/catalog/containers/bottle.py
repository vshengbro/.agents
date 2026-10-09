"""
bottle -- 500 ml PET drinks bottle: lathed body with a real wall, a shoulder,
a 28 mm PCO neck finish and a separate screw cap.

The whole vessel is ONE closed cross-section. Walk order is the whole game:
out along the base, up the outside, over the shoulder and neck, across the
rim, back down the inside, across the inner floor. Stop anywhere else and you
have revolved a single surface, which renders as a zero-thickness ghost.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres ------------------------------------------
SPEC = dict(
    body_diameter=65.0,       # 500 ml bottle body, outside
    body_height=190.0,        # base to the top of the neck finish
    wall=1.2,                 # PET wall; thin, but visible in a closeup
    base_thickness=4.0,
    neck_diameter=29.0,       # 28 mm PCO finish
    cap_diameter=32.0,        # HDPE screw cap
    cap_height=30.0,
    overall_height=210.0,     # base to the top of the cap
    volume_ml=500.0,
)

R = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]
CAP_R = SPEC["cap_diameter"] / 2.0
NECK_R = SPEC["neck_diameter"] / 2.0


def build():
    pet = bkit.pbr("PetBody", base=(0.78, 0.84, 0.88), rough=0.12, coat=0.6,
                   transmission=0.35, ior=1.57)
    cap = bkit.pbr("BottleCap", base=(0.06, 0.20, 0.62), rough=0.30)
    label = bkit.pbr("BottleLabel", base=(0.90, 0.90, 0.88), rough=0.42)

    # ---- body: one closed profile, base -> outside -> neck -> rim -> inside ----
    prof = [
        (0.0, 0.0),                  # centre of the base, outside
        (26.0, 0.0),                 # across the base
        (30.0, 2.0),
        (R, 8.0),                    # full body radius
        (R, 40.0),
        (30.5, 55.0),                # waist in
        (30.5, 76.0),                # waist held
        (R, 92.0),                   # back out
        (R, 122.0),                  # straight body to the shoulder
        (31.0, 132.0),
        (25.0, 150.0),               # shoulder
        (16.5, 165.0),
        (NECK_R, 173.0),             # neck
        (NECK_R, BH - 12.0),
        (15.6, BH - 12.0),           # support ring
        (15.6, BH - 8.0),
        (NECK_R, BH - 8.0),
        (NECK_R, BH),                # finish top, outside
        (11.0, BH),                  # across the rim
        (11.0, BH - 2.0),
        (11.0, 173.0),               # down the bore
        (14.0, 162.0),               # inside of the shoulder
        (23.0, 148.0),
        (28.5, 130.0),
        (29.0, 122.0),
        (29.0, 92.0),
        (29.0, 76.0),
        (29.0, 55.0),
        (29.0, 40.0),
        (28.5, 10.0),
        (24.0, 4.0),
        (0.0, 4.0),                  # across the inner floor
    ]
    body = bkit.lathe("BottleBody", prof, segments=96, mat=pet)

    # A wrap label is a second material on the same solid: a duplicate cylinder
    # would z-fight with the wall and leave two non-manifold objects behind.
    bkit.assign_faces_by(
        body, label,
        lambda c, n: 62.0 < c.z / bkit.MM < 118.0
        and abs(n.x * 0.5 + n.y * 0.5) > 0.0,
    )

    # ---- cap: solid of revolution sitting over the neck ---------------------
    cap_prof = [
        (0.0, 0.0),
        (CAP_R - 1.2, 0.0),
        (CAP_R, 1.6),
        (CAP_R, 22.0),
        (CAP_R - 2.0, 27.0),         # rounded crown
        (12.0, 29.5),
        (0.0, 30.0),                 # across the top
    ]
    # The cap screws OVER the neck, so it straddles the neck top: its skirt
    # reaches down inside the finish and its crown stands proud of it. Placing
    # it wholly above the body leaves a floating disc instead of a cap.
    cap_obj = bkit.lathe("BottleCap", cap_prof, segments=96,
                         centre=(0.0, 0.0, SPEC["overall_height"]
                                 - SPEC["cap_height"]), mat=cap)

    # ---- tamper band: the ring the cap tears off ---------------------------
    band = bkit.tube("BottleTamperBand", CAP_R + 0.7, CAP_R - 0.5, 5.0,
                     segments=96,
                     centre=(0.0, 0.0, SPEC["overall_height"]
                             - SPEC["cap_height"] + 2.0), mat=cap)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_diameter", mm=65.0, tol=0.4, how="diameter", part="BottleBody"),
    dict(name="cap_diameter", mm=32.0, tol=0.4, how="diameter", part="BottleCap"),
    dict(name="overall_height", mm=210.0, tol=0.5, how="bbox_z"),
]
