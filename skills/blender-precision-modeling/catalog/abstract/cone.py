"""
cone -- a 64 mm base, 64 mm tall moulded cone (a traffic-cone study solid).

Built with `lathe` rather than `cylinder(r2=0)`: the cylinder recipe emits
`segments` separate vertices at the apex, which is exactly the coincident-
vertex tangle that `lathe`'s weld step exists to collapse.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    base_diameter=64.0,
    height=64.0,
    wall=0.0,             # solid of revolution, not a shell
    slant_ratio=1.0,      # height : base radius
)

BASE_R = SPEC["base_diameter"] / 2.0

CHECKS = [
    dict(name="base_diameter", mm=64.0, tol=0.1, how="diameter", part="Cone"),
    dict(name="height", mm=64.0, tol=0.1, how="bbox_z", part="Cone"),
]


def build():
    mat = bkit.pbr("ConeShell", base=(0.80, 0.30, 0.03), metal=0.0, rough=0.30,
                   coat=0.25)

    # A three-point profile revolved on Z is a closed solid: the pole vertices
    # at r=0 are welded into proper fans by lathe(), and cap_ends correctly
    # adds nothing because both ends already sit on the axis.
    prof = [
        (0.0, 0.0),                 # apex of the base fan
        (BASE_R, 0.0),              # out across the flat base
        (0.0, SPEC["height"]),      # up the flank and in to the tip
    ]
    cone = bkit.lathe("Cone", prof, segments=128, mat=mat)

    return dict(spec=SPEC, parts=1)