"""
cufflink -- 14 mm domed face on a 9 mm post with a 16 mm hinged T-bar.

Three separate pieces of metal and a hinge, which is what separates a cufflink
from a shirt stud: the post passes through two buttonholes, so it has to be
long enough to reach the back of the cuff and end in a bar that cannot rotate
out. The face is a revolved dome (not a disc) because a flat face reads as a
washer; the bar is a capsule, a cylinder with a half-round end on each side,
so it has to be a lathe turned about its own axis rather than a plain cylinder
stuck on.
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

FACE_D = 14.0           # face diameter
FACE_H = 2.60           # face thickness at the rim, dome above that
DOME_RISE = 1.10        # how far the centre stands above the rim
POST_D = 2.20          # hinge post diameter
POST_L = 9.0            # post length between face and bar
BAR_D = 2.80            # T-bar diameter
BAR_L = 16.0            # T-bar overall length

FACE_R = FACE_D / 2.0
POST_R = POST_D / 2.0
BAR_R = BAR_D / 2.0

SPEC = dict(face_diameter=FACE_D,
            face_rim_thickness=FACE_H,
            dome_rise=DOME_RISE,
            post_diameter=POST_D,
            post_length=POST_L,
            bar_length=BAR_L,
            overall_height=FACE_H + POST_L)


def build():
    silver = bkit.pbr("CufflinkSilver", base=(0.86, 0.88, 0.91), metal=0.85,
                      rough=0.13)
    onyx = bkit.pbr("CufflinkOnyx", base=(0.05, 0.05, 0.06), metal=0.0, rough=0.08,
                    coat=0.8)

    # ---- face: revolved dome with a chamfered rim --------------------------
    # (r, z) profile: flat underside, domed top, 0.3 rim break.
    face = bkit.lathe(
        "Face",
        [(0.0, 0.0),
         (FACE_R - 0.3, 0.0),
         (FACE_R, 0.3),
         (FACE_R, FACE_H - 0.3),
         (FACE_R - 0.3, FACE_H),
         (FACE_R * 0.62, FACE_H + DOME_RISE * 0.62),
         (FACE_R * 0.30, FACE_H + DOME_RISE * 0.93),
         (0.0, FACE_H + DOME_RISE)],
        segments=80, mat=onyx)

    # ---- hinge post ---------------------------------------------------------
    post = bkit.cylinder("HingePost", POST_R, POST_L + 2.0, segments=32,
                         centre=(0.0, 0.0, FACE_H + POST_L / 2.0), mat=silver)
    # hinge knuckle: a short collar where the post meets the face, the part
    # that actually articulates
    knuckle = bkit.cylinder("HingeKnuckle", POST_R + 0.55, 2.2, segments=32,
                            centre=(0.0, 0.0, FACE_H + 1.1), mat=silver)

    # ---- T-bar: a lathe about X, so both ends are real domes ----------------
    # profile is in (r, z) and is then laid on its side: the bar is a turned
    # part, not a cylinder with two discs on it.
    hl = BAR_L / 2.0
    bar_profile = [
        (0.0, -hl),
        (BAR_R - 0.5, -hl),
        (BAR_R, -hl + 0.5),
        (BAR_R, hl - 0.5),
        (BAR_R - 0.5, hl),
        (0.0, hl),
    ]
    bar = bkit.lathe("TBar", bar_profile, segments=40, mat=silver)
    bar.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(bar, 0.0, 0.0, FACE_H + POST_L)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="face_diameter", mm=14.0, tol=0.05, how="bbox_x", part="Face"),
    dict(name="face_height", mm=3.7, tol=0.05, how="bbox_z", part="Face"),
    dict(name="post_length", mm=11.0, tol=0.05, how="bbox_z", part="HingePost"),
    dict(name="bar_length", mm=16.0, tol=0.05, how="bbox_x", part="TBar")
]