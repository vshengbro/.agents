"""
computer_mouse -- 120 x 65 x 38 mm ergonomic mouse.

A superellipse loft (n = 3.0) is the whole shape: eight sections up the palm
rest, the last one small enough that the end cap closes the crown smoothly
instead of leaving a flat lid. Two cuts make it read as a mouse rather than a
pebble -- the wheel slot and the L/R button split -- and both are cut with
rounded-box cutters that pass fully through the local surface, never ending
exactly on it.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=120.0,
    width=65.0,
    height=38.0,
    wheel_diameter=10.0,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]


def build():
    shell = bkit.pbr("MouseShell", base=(0.30, 0.31, 0.34), rough=0.30,
                     coat=0.35)
    seam = bkit.pbr("MouseSeam", base=(0.11, 0.11, 0.13), rough=0.55)
    wheel_mat = bkit.pbr("MouseWheel", base=(0.16, 0.16, 0.18), rough=0.48)

    # ---- palm body: one superellipse loft, widest at z = 10 mm ----------
    profile = ((100.0, 62.0, 0.0), (112.0, 64.0, 3.0), (L, W, 10.0),
               (118.0, 64.0, 18.0), (104.0, 56.0, 26.0), (78.0, 44.0, 32.0),
               (44.0, 28.0, 36.0), (16.0, 12.0, H))
    secs = [[(x, y, z) for (x, y) in bkit.superellipse_section(sx, sy, n=3.0,
                                                                steps=64)]
            for (sx, sy, z) in profile]
    body = bkit.loft("MouseBody", secs, mat=shell, smooth=True)

    # ---- scroll-wheel slot: narrow in X, long in Y, cut through the top --
    slot = bkit.rounded_box("_slot", 7.0, 18.0, 10.0, r=1.6, segments=3,
                            centre=(0, -7.0, 34.0), mat=seam)
    bkit.boolean(body, slot, "DIFFERENCE")

    # ---- L/R button split, a 1.4 mm groove down the front ----------------
    split = bkit.rounded_box("_split", 1.4, 30.0, 14.0, r=0.6, segments=2,
                             centre=(0, 24.0, 33.0), mat=seam)
    bkit.boolean(body, split, "DIFFERENCE")

    # ---- the wheel itself, axle along X, flush with the crown -------------
    bkit.cylinder("MouseWheel", SPEC["wheel_diameter"] / 2.0, 6.0,
                  segments=40, axis="X", centre=(0, -7.0, 33.0),
                  mat=wheel_mat)

    # ---- two thumb buttons on the -X flank, one computed row -------------
    keys = []
    for i, (y, ln) in enumerate(bkit.lay_out([9.0, 9.0], gap=5.0)):
        keys.append(bkit.rounded_box(
            "_k%d" % i, 2.0, ln, 3.2, r=0.8, segments=3,
            centre=(-58.0, y, 15.0), mat=seam))
    bkit.join(keys, name="MouseButtons")

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="length", mm=120.0, tol=0.6, how="bbox_x", part="MouseBody"),
    dict(name="width", mm=65.0, tol=0.6, how="bbox_y", part="MouseBody"),
    dict(name="height", mm=38.0, tol=0.6, how="bbox_z", part="MouseBody"),
]
