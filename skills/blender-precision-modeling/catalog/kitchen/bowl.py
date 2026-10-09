"""bowl -- wide ceramic cereal bowl, one lathe profile with a real foot ring.

A 165 mm breakfast bowl: shallow enough to read as tableware rather than a
mixing basin, with the underside sprung so it stands on a 100 mm foot ring
instead of rocking on its base.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    bowl_diameter=165.0,   # outside diameter at the rim
    bowl_height=70.0,      # rim height above the table
    wall=5.0,              # rim thickness
    base_thickness=9.0,
    foot_diameter=100.0,   # ring the bowl actually stands on
    volume_ml=1100.0,
)

R = SPEC["bowl_diameter"] / 2.0
H = SPEC["bowl_height"]
WALL = SPEC["wall"]
FOOT = SPEC["foot_diameter"] / 2.0
BASE = SPEC["base_thickness"]


def build():
    ceramic = bkit.preset("ceramic")

    # Out along the underside, over the foot ring, up the outside, over the rim,
    # back down the inside and across the inside floor. Both ends of the profile
    # sit on the axis, so the revolve closes on itself with two poles and the
    # result is one watertight solid with a real cavity.
    prof = [
        (0.0, 0.0),
        (FOOT - 6.0, 0.0),          # underside flat
        (FOOT, 3.0),                 # foot ring chamfer
        (FOOT, 7.0),                 # foot ring wall
        (FOOT + 4.0, 9.0),
        (R - 4.0, 20.0),             # underside springs out to the wall
        (R, 34.0),
        (R, H - 6.0),
        (R - 0.4, H - 1.0),          # soft outer roll at the rim
        (R - 2.6, H),
        (R - WALL - 2.6, H),         # across the rim
        (R - WALL - 1.4, H - 3.0),
        (R - WALL, H - 10.0),        # down the inside
        (R - WALL - 5.0, 26.0),
        (46.0, 15.0),
        (30.0, BASE + 1.0),
        (0.0, BASE),                 # across the inside floor
    ]
    body = bkit.lathe("BowlBody", prof, segments=96, mat=ceramic)

    # Glazed interior as a second material on the same solid: a duplicate
    # interior shell would z-fight with the wall and double the non-manifold
    # count for no visual gain.
    glaze = bkit.pbr("BowlGlazeInside", base=(0.90, 0.89, 0.85), rough=0.12,
                     coat=0.4)
    bkit.assign_faces_by(
        body, glaze,
        lambda c, n: ((c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM < (R - WALL + 0.05)
                      and c.z / bkit.MM < H - 1.0),
    )

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="bowl_diameter", mm=165.0, tol=0.3, how="diameter", part="BowlBody"),
    dict(name="bowl_height", mm=70.0, tol=0.3, how="bbox_z", part="BowlBody"),
    dict(name="overall_height", mm=70.0, tol=0.3, how="bbox_z"),
]
