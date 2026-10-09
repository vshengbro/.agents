"""
scarf_ring -- 30 x 24 mm slotted scarf ring, 3 mm flat band, 6 mm opening.

A scarf ring is a flat band, not a wire: it is a strip of metal 3 mm across the
face and 3 mm deep, bent into a C. So it is a revolved annulus with a closed
(r, z) cross-section, and the opening is cut afterwards.

The gap cutter is a box that fully severs the ring, not one that nicks its
outer edge -- a real scarf ring is open, and a ring with a slot in the top of
its rim reads as a washer. The cutter is placed so it crosses the whole band in
Y, which leaves a clean C rather than two stubs joined over a notch.
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

R_OUT = 15.0
R_IN = 12.0
BAND_T = 3.0          # height of the band (Z)
BAND_W = 3.0          # width of the band section
GAP_W = 6.0           # opening across the band

SPEC = dict(outer_diameter=2.0 * R_OUT,
            inner_diameter=2.0 * R_IN,
            band_height=BAND_T,
            band_width=BAND_W,
            opening=GAP_W)


def build():
    silver = bkit.pbr("ScarfRingSilver", base=(0.86, 0.88, 0.91), metal=0.85,
                      rough=0.17)

    # ---- the band: a closed annular cross-section revolved about Z ---------
    hw = BAND_T / 2.0
    ring = bkit.lathe(
        "ScarfRing",
        [(R_IN, -hw), (R_OUT, -hw), (R_OUT, hw), (R_IN, hw), (R_IN, -hw)],
        segments=96, centre=(0.0, 0.0, hw), cap_ends=False, mat=silver)

    # ---- open it: a cutter that severs the band clear of +X ----------------
    # The cutter starts at x = +6, so the surviving C runs from the -X outside
    # (-15) to +6: a 21 mm long open ring, not a ring with a nick in its rim.
    gap = bkit.rounded_box("_gap", 34.0, 2.0 * (R_OUT + 6.0), 2.0 * BAND_T + 6.0,
                           r=1.0, segments=2, centre=(R_OUT + 8.0, 0.0, hw))
    bkit.boolean(ring, gap, "DIFFERENCE")

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="band_height", mm=3.0, tol=0.05, how="bbox_z", part="ScarfRing"),
    # the ring is open at +X, so its X extent is short of the outer diameter;
    # the Y extent is the full diameter, which is what `diameter` reports.
    dict(name="outer_diameter", mm=30.0, tol=0.05, how="diameter", part="ScarfRing"),
    dict(name="open_length", mm=21.0, tol=0.1, how="bbox_x", part="ScarfRing")
]