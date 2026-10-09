"""
grommet -- flanged rubber grommet for a 6 mm cable, 12 mm flange, 8 mm tall.

The smallest item in this domain, and the one where a wrong number shows
immediately: 12 x 8 mm over a 6 mm bore gives an outside-to-bore ratio of 2 : 1
and a flange that is visibly wider than the waist. It is a single revolved
annulus (closed cross-section, so no end caps) with the waisted barrel that
makes a grommet grip a panel instead of falling out of the hole.

Rubber is the one material in the toolkit that already works at metal = 0, so
this part needs no studio workaround: it renders from its diffuse term alone.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND (no shared file is edited). Blender's camera data defaults
# to clip_start = 0.1 m while bkit.frame() parks the camera at
# radius * 1.18 / tan(vfov/2) -- 49 mm from this 12 mm grommet. Everything
# nearer than 0.1 m is discarded, so the model renders as an empty backdrop
# and auto_exposure reports "probe unreadable" (the calibration ball is
# clipped too). render_shots() resolves `camera` from bkit's module globals at
# call time, so re-binding it with a near plane derived from the harness's own
# distance fixes small subjects. Needed under ~13.5 mm bounding radius.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

BORE_D = 6.0            # cable / hole diameter
FLANGE_D = 12.0
WAIST_D = 9.2
HEIGHT = 8.0
FLANGE_T = 1.8

SPEC = dict(bore_diameter=BORE_D,
            flange_diameter=FLANGE_D,
            waist_diameter=WAIST_D,
            height=HEIGHT,
            flange_thickness=FLANGE_T)


def build():
    # Black rubber, but lifted off the near-black `rubber` preset (0.055):
    # against this dark backdrop a 5 % albedo grommet renders as a silhouette
    # with no readable bore or waist. 0.13 still reads as black rubber.
    rubber = bkit.pbr("GrommetRubber", base=(0.13, 0.13, 0.14), metal=0.0,
                      rough=0.68)
    ri = BORE_D / 2.0
    ro = FLANGE_D / 2.0
    rw = WAIST_D / 2.0
    h, ft = HEIGHT, FLANGE_T

    profile = [
        (ri, 0.0), (ro, 0.0), (ro, ft),                 # bottom flange
        (rw, ft + 0.4), (rw, h - ft - 0.4),           # waisted barrel
        (ro, h - ft), (ro, h),                         # top flange
        (ri, h), (ri, 0.0),                            # bore wall, closes the loop
    ]
    grommet = bkit.lathe("RubberGrommet", profile, segments=80, cap_ends=False,
                         mat=rubber)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="flange_diameter", mm=12.0, tol=0.02, how="bbox_x", part="RubberGrommet"),
    dict(name="flange_diameter_y", mm=12.0, tol=0.02, how="bbox_y", part="RubberGrommet"),
    dict(name="grommet_height", mm=8.0, tol=0.02, how="bbox_z", part="RubberGrommet"),
]