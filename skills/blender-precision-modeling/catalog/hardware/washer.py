"""
washer -- ISO 7089 M4 flat (plain) washer.

A washer is the least forgiving item in the catalog: at 9 mm across and 0.8 mm
thick it is one millimetre of geometry in every direction, so any drafting
error reads immediately. Everything here is the ISO 7089 M4 row: outside
diameter d2 = 9, inside diameter d1 = 4.3, thickness h = 0.8.

Built as a single revolved cross-section (closed loop, so no end caps are
needed) with the standard raised-chamfer profile rather than a plain tube --
a washer is never a bare cylinder in reality, and the chamfer is what catches
the rim light and makes it read as a stamped part.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND (no shared file is edited). Blender's camera data defaults
# to clip_start = 0.1 m, but bkit.frame() parks the camera at
# radius * 1.18 / tan(vfov/2) -- only ~34 mm from a 9 mm washer. Everything
# nearer than 0.1 m is discarded, so this model renders as an empty backdrop
# and auto_exposure reports "probe unreadable" (the calibration ball is clipped
# too, leaving every probe pixel transparent). Re-binding bkit.camera with a
# near plane derived from the distance the harness itself chose fixes it:
# render_shots() resolves `camera` from bkit's module globals at call time.
# Only models whose bounding radius is under ~13.5 mm need this.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

OUTSIDE_D = 9.0          # d2, ISO 7089 for M4
INSIDE_D = 4.3           # d1
THICKNESS = 0.8          # h
CHAMFER = 0.15           # raised-chamfer on both faces

SPEC = dict(outer_diameter=OUTSIDE_D,
            inner_diameter=INSIDE_D,
            thickness=THICKNESS,
            chamfer=CHAMFER)


def build():
    # metal=0.7 rather than bkit's metal=1.0 presets: a pure metal has no
    # diffuse term and renders black in this dark studio (see recipes/staging).
    steel = bkit.pbr("WasherZinc", base=(0.88, 0.89, 0.91), metal=0.64,
                     rough=0.30)
    ri, ro = INSIDE_D / 2.0, OUTSIDE_D / 2.0
    h, c = THICKNESS / 2.0, CHAMFER

    # closed cross-section in (r, z): flat faces, conical chamfers, bore wall
    profile = [
        (ri, -h),
        (ro, -h),
        (ro, h - c),
        (ro - c, h),
        (ri + c, h),
        (ri, h - c),
        (ri, -h),                      # closes the loop; lathe(cap_ends=False)
    ]
    washer = bkit.lathe("Washer", profile, segments=96, cap_ends=False, mat=steel)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="outer_diameter", mm=9.0, tol=0.02, how="bbox_x", part="Washer"),
    dict(name="outer_diameter_y", mm=9.0, tol=0.02, how="bbox_y", part="Washer"),
    dict(name="thickness", mm=0.8, tol=0.02, how="bbox_z", part="Washer"),
]