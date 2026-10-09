"""
rubber_stamp -- self-inking desk stamp, 54 mm tall including the handle.

A stamp has three distinct diameters: the knob you press, the collar, and the
rubber pad that actually stamps. Getting the pad wider than the collar is what
makes the silhouette read as a stamp rather than as a doorstop.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    pad_width=30.0,
    pad_depth=22.0,
    pad_height=4.0,
    body_width=34.0,
    body_height=8.0,
    handle_diameter=26.0,
    total_height=51.0,
)

# The knob fills the height above the body; the profile ends 0.4 mm past
# HANDLE_H to round off the crown, so subtract that to make the declared
# total the measured one.
HANDLE_H = (SPEC["total_height"] - SPEC["pad_height"]
            - SPEC["body_height"] - 0.4)


def build():
    rubber = bkit.pbr("StampRubber", base=(0.14, 0.14, 0.16), rough=0.80)
    body_mat = bkit.pbr("StampBody", base=(0.30, 0.31, 0.34), rough=0.42)
    wood = bkit.pbr("StampWood", base=(0.62, 0.40, 0.21), rough=0.45)

    # ---- rubber pad (the stamping face) -----------------------------------
    pad = bkit.rounded_box("StampPad", SPEC["pad_width"], SPEC["pad_depth"],
                           SPEC["pad_height"], r=1.0,
                           centre=(0, 0, SPEC["pad_height"] / 2.0),
                           mat=rubber)

    # ---- body block -------------------------------------------------------
    body_z = SPEC["pad_height"] + SPEC["body_height"] / 2.0
    body = bkit.rounded_box("StampBody", SPEC["body_width"],
                            SPEC["pad_depth"] + 4.0, SPEC["body_height"],
                            r=2.0, centre=(0, 0, body_z), mat=body_mat)

    # ---- turned wooden knob: one lathed profile ---------------------------
    r = SPEC["handle_diameter"] / 2.0
    z0 = SPEC["pad_height"] + SPEC["body_height"]
    prof = [
        (0.0, z0),
        (r * 0.42, z0),
        (r * 0.40, z0 + HANDLE_H * 0.42),
        (r * 0.50, z0 + HANDLE_H * 0.58),    # waist
        (r * 0.46, z0 + HANDLE_H * 0.74),
        (r * 0.34, z0 + HANDLE_H * 0.92),
        (r * 0.20, z0 + HANDLE_H),
        (0.0, z0 + HANDLE_H + 0.4),
    ]
    handle = bkit.lathe("StampHandle", prof, segments=48, mat=wood)
    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="pad_width", mm=30.0, tol=0.6, how="bbox_x", part="StampPad"),
    dict(name="body_width", mm=34.0, tol=0.6, how="bbox_x", part="StampBody"),
    dict(name="total_height", mm=51.0, tol=1.0, how="bbox_z"),
]