"""
bracelet -- 68.4 mm open bangle, 4.4 mm round section, with a screw clasp.

A bangle is a piece of round wire bent on a mandrel, so it is an arc_torus and
not a closed torus: the 40 degree gap is the whole point, because it is the
part that goes over the wrist. The two arc ends get real domed caps rather than
flat ones, and the clasp is a short collar over one end plus a screw post
through the other -- a bangle photographed with a bare gap reads as a bracelet
that fell apart.

The arc is left OPEN (a0 to a1 across the 40 degree gap) so the silhouette has
a real opening at the bottom of the render, which is the recognisable feature.
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

BANGLE_R = 32.0         # centreline radius
WIRE_R = 2.20           # 4.4 mm round section
GAP_DEG = 40.0          # the opening, centred on the bottom of the ring
CLASP_L = 7.0
SCREW_R = 1.30

A0 = 20.0
A1 = 340.0

SPEC = dict(bangle_outer_diameter=2.0 * (BANGLE_R + WIRE_R),
            wire_diameter=2.0 * WIRE_R,
            opening_degrees=GAP_DEG,
            shank_band_length=7.0)


def build():
    gold = bkit.pbr("BangleGold", base=(1.00, 0.79, 0.40), metal=0.85, rough=0.15)
    steel = bkit.pbr("ClaspSteel", base=(0.82, 0.84, 0.87), metal=0.85, rough=0.20)

    # ---- the bangle: a 320 degree arc of round wire ------------------------
    # plane="XZ" with the sweep in XZ puts the 40 degree opening on the +X
    # side, so the full outside diameter is across Z and the shortened run
    # across X. Both are declared, because neither is "the" diameter.
    bangle = bkit.arc_torus("Bangle", BANGLE_R, WIRE_R, A0, A1, plane="XZ",
                            seg_major=120, seg_minor=24, mat=gold, caps=True)

    # ---- raised shank band at the top of the ring, where the tangent is X --
    top = BANGLE_R
    band = bkit.cylinder("ShankBand", WIRE_R + 1.0, 7.0, segments=36,
                         centre=(0.0, 0.0, top), axis="X", mat=steel)
    knurl = bkit.cylinder("ShankKnurl", WIRE_R + 1.4, 1.8, segments=36,
                          centre=(0.0, 0.0, top), axis="X", mat=steel)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    # the opening is on +X, so the full diameter is the Z extent
    dict(name="bangle_outer_diameter", mm=68.4, tol=0.1, how="bbox_z", part="Bangle"),
    # X extent = full diameter on the -X side plus the 20 deg chord on +X:
    # 34.2 + (32*cos20 + 2.2) = 66.47, less the 2.67 deg arc sampling step
    dict(name="open_length", mm=66.34, tol=0.15, how="bbox_x", part="Bangle"),
    dict(name="wire_diameter", mm=4.4, tol=0.1, how="bbox_y", part="Bangle"),
    dict(name="shank_band_length", mm=7.0, tol=0.1, how="bbox_x", part="ShankBand")
]