"""pepper_mill -- 182 mm turned hardwood pepper mill with a steel cap.

The silhouette of a pepper mill is all shoulder and taper: a 62 mm base that
steps in to a 53 mm waist, a steep conical head, and a turned finial. Each of
the three parts is its own closed lathe so the wood and the steel read as
different materials without a second shell inside the first.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height=182.0,           # finial top above the table
    base_diameter=62.0,     # widest point, at the foot
    body_diameter=53.0,     # waist above the foot
    body_height=138.0,      # top of the wooden body
    cap_height=162.0,       # top of the steel cap
)

BODY = [
    (0.0, 0.0),
    (22.0, 0.0),
    (28.0, 1.5),
    (31.0, 5.0),            # foot
    (31.0, 14.0),
    (28.0, 24.0),
    (26.5, 40.0),
    (26.5, 105.0),          # waist
    (25.0, 126.0),          # shoulder into the neck
    (21.0, 138.0),
    (0.0, 138.0),
]

CAP = [
    (0.0, 162.0),
    (8.0, 162.0),
    (12.0, 159.0),
    (14.0, 150.0),
    (18.0, 138.0),          # cone down onto the neck
    (20.0, 135.0),
    (0.0, 135.0),
]

FINIAL = [
    (0.0, 182.0),
    (6.0, 181.5),
    (11.0, 178.0),
    (14.0, 172.0),
    (14.0, 165.0),
    (11.0, 161.0),
    (0.0, 160.0),
]


def build():
    wood = bkit.pbr("MillWalnut", base=(0.42, 0.25, 0.13), metal=0.0,
                    rough=0.42)
    steel = bkit.preset("brushed_metal")

    body = bkit.lathe("MillBody", BODY, segments=80, mat=wood)
    cap = bkit.recalc(bkit.lathe("MillCap", CAP, segments=80, mat=steel))
    # CAP and FINIAL are written pole-first (top-down), which winds the revolve
    # inward; recalc makes their signed volume positive.
    finial = bkit.recalc(bkit.lathe("MillFinial", FINIAL, segments=64, mat=wood))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="mill_height", mm=182.0, tol=0.3, how="bbox_z"),
    dict(name="base_diameter", mm=62.0, tol=0.3, how="diameter",
         part="MillBody"),
    dict(name="body_height", mm=138.0, tol=0.3, how="bbox_z", part="MillBody"),
]
