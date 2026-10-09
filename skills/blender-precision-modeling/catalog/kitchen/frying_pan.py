"""frying_pan -- 260 mm skillet: sprung base, flared rim, welded stay-cool handle.

The pan is one lathe profile with a real 4 mm wall; the handle is a tapered
cylinder lying on the rim axis, so it rests on the same line the pan sits on
and every declared dimension is a plain bounding-box measurement.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    pan_diameter=261.0,    # outside diameter at the rim
    pan_depth=52.0,        # rim height above the table
    handle_length=210.0,   # outside reach of the handle from its root
    handle_diameter=26.0,  # at the root, tapering to 19 at the hang hole
    wall=4.0,
    base_thickness=3.5,
    capacity_ml=2400.0,
)

R = SPEC["pan_diameter"] / 2.0
D = SPEC["pan_depth"]


def build():
    # preset("dark_metal") is base 0.22, which against this dark studio leaves
    # no surface to read at all; cast iron needs to be dark, not invisible.
    iron = bkit.pbr("PanCastIron", base=(0.31, 0.32, 0.34), metal=1.0,
                    rough=0.33)

    prof = [
        (0.0, 0.0),
        (86.0, 0.0),            # flat cooking base
        (104.0, 1.0),
        (118.0, 4.0),
        (126.0, 12.0),          # the base springs out to the wall
        (R - 0.5, 24.0),
        (R - 0.5, 48.0),
        (R, 51.0),              # slight rim flare
        (R - 2.0, D),           # rim, outside
        (R - 5.0, D),           # across the rim
        (R - 4.0, 47.0),        # down the inside
        (R - 4.5, 26.0),
        (122.0, 15.0),
        (114.0, 8.0),
        (100.0, 4.5),
        (86.0, SPEC["base_thickness"]),
        (0.0, SPEC["base_thickness"]),
    ]
    body = bkit.lathe("FryingPanBody", prof, segments=96, mat=iron)

    # Handle root sits inside the wall (the rim inner face is at R-4 = 126.5 at
    # this height) so there is no seam or coincident face where they meet.
    handle = bkit.cylinder("FryingPanHandle", 13.0, SPEC["handle_length"],
                           segments=48, centre=(0.0, 0.0, 0.0), axis="Y",
                           r2=9.5, mat=iron)
    bkit.move(handle, 0.0, 126.0 + SPEC["handle_length"] / 2.0, 42.0)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="pan_diameter", mm=261.0, tol=0.3, how="diameter",
         part="FryingPanBody"),
    dict(name="pan_depth", mm=52.0, tol=0.3, how="bbox_z", part="FryingPanBody"),
    dict(name="handle_length", mm=210.0, tol=0.3, how="bbox_y",
         part="FryingPanHandle"),
]
