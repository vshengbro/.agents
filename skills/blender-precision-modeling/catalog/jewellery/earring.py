"""
earring -- 7.3 mm hoop earring with a 1.15 mm bead drop and a stud post.

Deliberately built at the small end of the range. A hoop earring is the one
jewellery form that genuinely exists at every size from 6 to 60 mm, so this is
a real product (a small everyday hoop) rather than a full-size one shrunk to
fit -- the section, the post gauge and the jump ring are the real ones for this
diameter.

The hoop is a torus because it is a closed ring of constant section; the post
is a short cylinder driven through the top of it, and the jump ring is a second
torus of much smaller major radius. The two torus axes differ (Y for the hoop,
Z for the jump ring) because a jump ring has to hang perpendicular to the hoop
it passes through -- which is the whole reason it exists.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py. At a 7 mm bounding
# radius the camera the harness picks sits ~17 mm out, well inside Blender's
# 0.1 m default near plane, so the model would render as an empty backdrop.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

HOOP_R = 3.20           # hoop centreline radius
HOOP_W = 0.90           # hoop wire diameter
JUMP_R = 0.80           # jump ring centreline radius
JUMP_W = 0.38           # jump ring wire diameter
POST_R = 0.45           # stud post radius
POST_L = 2.60           # stud post length
BEAD_R = 1.15           # drop bead radius

HOOP_TOP = HOOP_R + HOOP_W / 2.0          # 3.65
HOOP_BOT = -(HOOP_R + HOOP_W / 2.0)       # -3.65

SPEC = dict(hoop_diameter=2.0 * HOOP_R + HOOP_W,
            wire_diameter=HOOP_W,
            post_diameter=2.0 * POST_R,
            bead_diameter=2.0 * BEAD_R,
            overall_height=HOOP_TOP + POST_L + BEAD_R)


def build():
    gold = bkit.pbr("EarringGold", base=(0.98, 0.79, 0.40), metal=0.85, rough=0.16)
    pearl = bkit.pbr("EarringPearl", base=(0.90, 0.88, 0.84), metal=0.0, rough=0.14,
                     coat=0.6)

    # ---- hoop: axis along Y, so it reads as a ring from the front ----------
    hoop = bkit.torus("Hoop", HOOP_R, HOOP_W / 2.0, seg_major=72, seg_minor=20,
                      centre=(0.0, 0.0, 0.0), axis="Y", mat=gold)

    # ---- stud post driven through the top of the hoop ----------------------
    post = bkit.cylinder("StudPost", POST_R, POST_L, segments=24,
                         centre=(0.0, -POST_L / 2.0 + HOOP_W / 4.0, HOOP_TOP - 0.15),
                         axis="Y", mat=gold)

    # ---- jump ring through the post, hanging perpendicular -----------------
    jump = bkit.torus("JumpRing", JUMP_R, JUMP_W / 2.0, seg_major=40, seg_minor=12,
                      centre=(0.0, -POST_L + 0.35, HOOP_TOP - 0.55),
                      axis="Z", mat=gold)

    # ---- bead drop at the bottom of the hoop --------------------------------
    # Overlaps the hoop's lower arc by well over 1 mm, so the two solids cross
    # rather than touch tangentially.
    bead = bkit.sphere("Bead", BEAD_R, segments=32, rings=16,
                       centre=(0.0, 0.0, HOOP_BOT + 0.45), mat=pearl)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="hoop_diameter", mm=7.3, tol=0.05, how="bbox_x", part="Hoop"),
    dict(name="hoop_diameter_y", mm=7.3, tol=0.05, how="bbox_z", part="Hoop"),
    dict(name="post_length", mm=2.6, tol=0.05, how="bbox_y", part="StudPost"),
    dict(name="bead_diameter", mm=2.3, tol=0.05, how="diameter", part="Bead")
]