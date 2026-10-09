"""
pendant -- 22 mm teardrop drop on a 4.8 mm bail ring, 12 mm front stone.

A teardrop pendant is a solid of revolution, not a flat cutout: the profile
runs from a point on the axis at the top, out to the belly and back to a point
on the axis at the bottom, so lathe() welds two poles and closes the solid with
no caps and no degenerate faces. That is also why the profile must never have
two consecutive axis points -- a segment from (0, 22) back to (0, 0) would
revolve into a ring of zero-area faces.

The bail is a torus whose plane is perpendicular to the drop, so the chain
passes through it the way it does on a real pendant, and it is set low enough
to bury itself in the neck of the drop rather than touch it tangentially.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

DROP_H = 22.0
DROP_R = 6.0
BAIL_R = 2.40
BAIL_W = 0.60
GEM_R = 1.80
GEM_Y = 5.40         # how far the gem's centre sits out on the belly
GEM_Z = 17.0

SPEC = dict(drop_height=DROP_H,
            drop_diameter=2.0 * DROP_R,
            bail_outer_diameter=2.0 * (BAIL_R + BAIL_W),
            gem_diameter=2.0 * GEM_R,
            overall_height=DROP_H)


def build():
    gold = bkit.pbr("PendantGold", base=(0.99, 0.80, 0.41), metal=0.85, rough=0.14)
    gem = bkit.pbr("PendantGem", base=(0.88, 0.93, 0.98), metal=0.0, rough=0.03,
                   transmission=0.6, ior=2.2)

    # ---- teardrop: axis -> point -> axis, both ends welded into poles -------
    drop = bkit.lathe(
        "Drop",
        [(0.0, 0.0),
         (1.2, 2.2), (2.8, 5.6), (4.4, 9.6), (5.6, 13.6), (DROP_R, 17.0),
         (5.4, 19.8), (3.8, 21.6), (0.0, DROP_H)],
        segments=72, mat=gold)

    # ---- bail: a ring in the YZ plane, buried in the neck of the drop ------
    bail = bkit.torus("Bail", BAIL_R, BAIL_W, seg_major=40, seg_minor=12,
                      centre=(0.0, 0.0, 5.0), axis="X", mat=gold)

    # ---- front stone on the belly -------------------------------------------
    stone = bkit.sphere("FrontStone", GEM_R, segments=32, rings=16,
                        centre=(0.0, GEM_Y, GEM_Z), mat=gem)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="drop_height", mm=22.0, tol=0.05, how="bbox_z", part="Drop"),
    dict(name="drop_diameter", mm=12.0, tol=0.05, how="diameter", part="Drop"),
    dict(name="bail_outer_diameter", mm=6.0, tol=0.05, how="bbox_y", part="Bail"),
    dict(name="gem_diameter", mm=3.6, tol=0.05, how="bbox_y", part="FrontStone"),
    # the bail is set INTO the neck of the drop (z 2 to 8 of a 22 mm drop), so
    # the assembly's height is the drop's own height
    dict(name="overall_height", mm=22.0, tol=0.1, how="bbox_z", part=None)
]