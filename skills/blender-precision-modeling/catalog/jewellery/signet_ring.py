"""
signet_ring -- 19.8 mm band carrying an 11 x 9 mm oval signet face.

The band is a torus whose axis lies along Y, so the ring stands upright and the
signet sits on top -- the way a signet ring is worn, and the only orientation
in which the face is visible at all. The face itself is a squircle (superellipse
n = 2.6), which is what a cast signet actually is: an oval with flattened
flanks, not a plain ellipse.

The face is built in two pieces -- a shoulder that flares out of the band and
a face plate on top of it -- because the shoulder is what carries the load into
the band. The two overlap by 0.5 mm rather than meeting flush.
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

BAND_R = 8.90          # centreline radius, so 17.8 mm inside diameter
BAND_W = 2.00          # 1.0 mm wire -> 2.0 mm round band
SHOULDER_W = 8.50
SHOULDER_H = 7.00
SHOULDER_T = 4.00
SHOULDER_Z = 8.00
FACE_W = 11.00
FACE_H = 9.00
FACE_T = 2.80
FACE_Z = 10.90

SPEC = dict(band_outer_diameter=2.0 * (BAND_R + BAND_W / 2.0),
            band_wire_diameter=BAND_W,
            face_width=FACE_W,
            face_height=FACE_H,
            face_thickness=FACE_T,
            overall_height=25.3)


def build():
    gold = bkit.pbr("SignetGold", base=(1.00, 0.79, 0.39), metal=0.85, rough=0.15)
    onyx = bkit.pbr("SignetOnyx", base=(0.05, 0.05, 0.06), metal=0.0, rough=0.07,
                    coat=0.9)

    # ---- band: a torus in the XZ plane, axis along Y -----------------------
    band = bkit.torus("Band", BAND_R, BAND_W / 2.0, seg_major=80, seg_minor=20,
                      centre=(0.0, 0.0, 0.0), axis="Y", mat=gold)

    # ---- shoulder: a squircle prism rising out of the band -----------------
    shoulder_poly = bkit.superellipse_section(SHOULDER_W, SHOULDER_H, n=2.6,
                                              steps=64)
    shoulder = bkit.extrude_profile("Shoulder", shoulder_poly, SHOULDER_T,
                                    axis="Y", centre=(0.0, 0.0, SHOULDER_Z),
                                    mat=gold)
    bkit.bevel(shoulder, 0.4, segments=2)

    # ---- signet face on top of the shoulder --------------------------------
    face_poly = bkit.superellipse_section(FACE_W, FACE_H, n=2.6, steps=64)
    face = bkit.extrude_profile("SignetFace", face_poly, FACE_T, axis="Y",
                                centre=(0.0, 0.0, FACE_Z), mat=onyx)
    bkit.bevel(face, 0.35, segments=2)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="band_outer_diameter", mm=19.8, tol=0.05, how="diameter", part="Band"),
    dict(name="band_wire_diameter", mm=2.0, tol=0.05, how="bbox_y", part="Band"),
    dict(name="face_width", mm=11.0, tol=0.08, how="bbox_x", part="SignetFace"),
    dict(name="face_height", mm=9.0, tol=0.08, how="bbox_z", part="SignetFace"),
    # the face plate's outline is 9 mm tall in Z and its centre rides 10.9 mm up
    # the band, so the top is at 15.4 against a band bottom of -9.9
    dict(name="overall_height", mm=25.3, tol=0.15, how="bbox_z", part=None)
]