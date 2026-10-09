"""
cylinder_shape -- a 60 mm x 80 mm turned steel billet, flat-ground ends.

`cylinder` with r2=None is the straight case of a truncated cone: this is the
control specimen every other lathe form in the catalog is compared against.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    diameter=60.0,
    height=80.0,
    end_flat=0.4,         # flatness tolerance of the ground ends
    aspect=1.333,         # height / diameter
)

CHECKS = [
    dict(name="diameter", mm=60.0, tol=0.1, how="diameter", part="Cylinder"),
    dict(name="height", mm=80.0, tol=0.1, how="bbox_z", part="Cylinder"),
]


def build():
    r = SPEC["diameter"] / 2.0
    billet = bkit.cylinder("Cylinder", r, SPEC["height"], segments=128,
                           centre=(0, 0, SPEC["height"] / 2.0),
                           mat=bkit.pbr("BilletSteel",
                                        base=(0.72, 0.73, 0.76),
                                        metal=0.30, rough=0.28))
    # A 0.3 mm edge break: a lathe-ground billet never has a razor end, and the
    # break gives the two end circles a bright line that separates them from
    # the backdrop. It does not touch the bounding box.
    bkit.bevel(billet, width_mm=0.3, segments=2, angle_deg=30)

    return dict(spec=SPEC, parts=1)