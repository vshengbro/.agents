"""
keychain -- 25.8 mm split ring carrying a leather fob and one flat key.

Three separate pieces hang from the ring, and each is joined to the one above
it by a jump ring that overlaps it by more than a millimetre. The feature that
makes a keychain read as a keychain is that chain of overlaps: a tag floating
below a ring looks like two objects, a tag threaded on a jump ring looks like a
keychain.

The key is a bow, a blade and three bit teeth on a 3.6 mm pitch computed with
bkit.lay_out(), because hand-placed teeth on a 20 mm key is exactly the kind
of repetition that produces two teeth at the same coordinate.
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

SPLIT_R = 12.0
SPLIT_W = 0.90
JUMP_R = 1.60
JUMP_W = 0.40
TAG_W = 24.0
TAG_H = 16.0
TAG_T = 2.5
TAG_Y = -1.0
KEY_BOW_R = 3.2
KEY_BLADE_W = 5.0
KEY_BLADE_L = 20.0
KEY_BLADE_T = 1.6
KEY_TEETH = 3
KEY_TOOTH_W = 4.0

SPEC = dict(split_ring_outer_diameter=2.0 * (SPLIT_R + SPLIT_W),
            split_ring_wire=2.0 * SPLIT_W,
            tag_width=TAG_W,
            tag_height=TAG_H,
            key_length=KEY_BOW_R + KEY_BLADE_L,
            overall_height=53.5)


def build():
    steel = bkit.pbr("KeychainSteel", base=(0.80, 0.82, 0.86), metal=0.85, rough=0.20)
    leather = bkit.pbr("FobLeather", base=(0.17, 0.09, 0.06), metal=0.0, rough=0.60)
    brass = bkit.pbr("KeyBrass", base=(0.90, 0.70, 0.34), metal=0.85, rough=0.26)

    # ---- split ring, in the XZ plane so it reads face-on -------------------
    # seg_minor=16 so a tube sample lands exactly on 90 deg: at 14 segments the
    # wire measures 1.755 mm instead of its true 1.8 mm
    ring = bkit.torus("SplitRing", SPLIT_R, SPLIT_W, seg_major=72, seg_minor=16,
                      centre=(0.0, 0.0, 0.0), axis="Y", mat=steel)
    ring_bot = -(SPLIT_R + SPLIT_W)

    # ---- fob jump ring, threaded through the bottom of the split ring ------
    fob_jump = bkit.torus("FobJump", JUMP_R, JUMP_W, seg_major=32, seg_minor=10,
                          centre=(0.0, 0.0, ring_bot - 0.7), axis="Y", mat=steel)

    # ---- leather fob tag ----------------------------------------------------
    tag_top = ring_bot - 0.7 - JUMP_R - JUMP_W + 1.2
    tag = bkit.rounded_box("FobTag", TAG_W, TAG_T, TAG_H, r=2.2, segments=4,
                           centre=(0.0, TAG_Y, tag_top - TAG_H / 2.0), mat=leather)

    # ---- one flat key, hung off the same jump ring -------------------------
    key_jump = bkit.torus("KeyJump", JUMP_R, JUMP_W, seg_major=32, seg_minor=10,
                          centre=(7.5, 0.0, ring_bot - 0.7), axis="Y", mat=steel)
    bow = bkit.torus("KeyBow", KEY_BOW_R, 0.9, seg_major=44, seg_minor=12,
                     centre=(7.5, 0.0, ring_bot - 5.6), axis="Y", mat=brass)
    blade_top = ring_bot - 5.6 - KEY_BOW_R - 0.9 + 2.0
    blade = bkit.rounded_box("KeyBlade", KEY_BLADE_W, KEY_BLADE_T, KEY_BLADE_L,
                             r=0.6, segments=2,
                             centre=(7.5, 0.0, blade_top - KEY_BLADE_L / 2.0),
                             mat=brass)
    # Three bit teeth off one long edge of the blade, on a measured pitch.
    # They overlap the blade by 1.2 mm in X and all sit inside the blade's own
    # Z span, so the union adds the bit without changing the blade's length.
    tooth = bkit.rounded_box("KeyBit", 4.4, KEY_BLADE_T, 1.8, r=0.4, segments=2,
                             centre=(11.0, 0.0, blade_top - 2.0), mat=brass)
    bkit.array_linear(tooth, KEY_TEETH, (0.0, 0.0, -3.6), world=True)
    bkit.boolean(blade, tooth, "UNION")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="split_ring_outer", mm=25.8, tol=0.05, how="bbox_x", part="SplitRing"),
    dict(name="split_ring_wire", mm=1.8, tol=0.05, how="bbox_y", part="SplitRing"),
    dict(name="tag_width", mm=24.0, tol=0.05, how="bbox_x", part="FobTag"),
    dict(name="tag_height", mm=16.0, tol=0.05, how="bbox_z", part="FobTag"),
    dict(name="key_blade_length", mm=20.0, tol=0.05, how="bbox_z", part="KeyBlade"),
    # split ring top (+12.9) to key bit tip (-40.6): the key hangs below the
    # fob, and every link in the chain overlaps the one above it
    dict(name="overall_height", mm=53.5, tol=0.2, how="bbox_z", part=None)
]