"""
mallet -- 295 mm wooden club mallet, 110 x 60 mm barrel head.

Head down, handle up, so the barrel rests on the floor and the camera gets an
unobstructed view of the handle taper.

The handle is a lathe, not a loft: a mallet handle is genuinely turned on a
lathe, so its circular section with a slow swell reads correctly, and the
lathe welds its own pole at each end of the profile.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=295.0,
    head_length=110.0,
    head_diameter=60.0,
    handle_length=277.0,
    handle_diameter=34.0,
)


def build():
    head_wood = bkit.pbr("MalletHead", base=(0.42, 0.24, 0.10), rough=0.52)
    shaft_wood = bkit.preset("wood")

    head = bkit.cylinder("MalletHead", 30.0, 110.0, segments=64, axis="Y",
                         centre=(0, 0, 30.0), mat=head_wood)

    handle = bkit.lathe("MalletHandle",
                        [(0, 18), (16, 18), (17, 40), (15, 120),
                         (14, 200), (16, 260), (17, 295), (0, 295)],
                        segments=56, mat=shaft_wood)
    bkit.recalc(handle)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="head_length", mm=110.0, tol=0.5, how="bbox_y", part="MalletHead"),
    dict(name="head_diameter", mm=60.0, tol=0.5, how="bbox_x",
         part="MalletHead"),
    dict(name="handle_length", mm=277.0, tol=0.8, how="bbox_z",
         part="MalletHandle"),
    dict(name="overall_length", mm=295.0, tol=1.5, how="bbox_z"),
]