"""
tiffin_box -- a two-tier stainless lunch box: a body, a fitted lid with a
clipped rim, and a folding carry handle.

Handle height is *solved* from the anchor spacing rather than guessed, so the
handle always lands on the anchor lugs. A guessed arc that misses by 2 mm
leaves two floating tips -- visually broken even though the mesh is clean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=220.0,             # along X
    width=150.0,              # along Y
    body_height=58.0,
    lid_height=12.0,
    overall_height=70.0,      # closed, before the handle
    handle_reach=52.0,        # rise of the handle above the lid
    corner_radius=12.0,
)

L = SPEC["length"]
W = SPEC["width"]
BH = SPEC["body_height"]
LH = SPEC["lid_height"]
H = SPEC["overall_height"]


def build():
    steel = bkit.pbr("TiffinSteel", base=(0.76, 0.78, 0.80), metal=0.50, rough=0.28)
    # The lid is a broad flat top with nothing bright above it; at metal=1.0 it
    # reflects the dark backdrop and reads as a black slab.
    lid_mat = bkit.pbr("TiffinLid", base=(0.72, 0.74, 0.76), metal=0.45, rough=0.30)
    gasket = bkit.preset("rubber")
    handle_mat = bkit.pbr("TiffinHandle", base=(0.52, 0.54, 0.57), metal=0.45,
                          rough=0.32)

    # ---- body: rounded tub ---------------------------------------------------
    body = bkit.rounded_box("TiffinBody", L, W, BH,
                            r=SPEC["corner_radius"], segments=5,
                            centre=(0.0, 0.0, BH / 2.0), mat=steel)

    # ---- lid ----------------------------------------------------------------
    lid = bkit.rounded_box("TiffinLid", L + 3.0, W + 3.0, LH,
                           r=SPEC["corner_radius"] + 1.5, segments=5,
                           centre=(0.0, 0.0, BH + LH / 2.0 - 1.0), mat=lid_mat)

    # ---- silicone gasket, visible in the parting line -----------------------
    ring = bkit.rounded_box("TiffinGasket", L - 6.0, W - 6.0, 3.0,
                            r=8.0, segments=3,
                            centre=(0.0, 0.0, BH - 0.5), mat=gasket)

    # ---- two side clips -----------------------------------------------------
    for i, sx in enumerate((-1.0, 1.0)):
        bkit.rounded_box("TiffinClip%d" % (i + 1), 6.0, 34.0, 22.0,
                         r=2.5, segments=3,
                         centre=(sx * (L / 2.0 + 1.0), 0.0, BH - 4.0),
                         mat=handle_mat)

    # ---- folding carry handle: solve the arc from the anchors ---------------
    # The arc's ENDS sit at (+-a, lid top) and its PEAK is `rise` above that.
    # A circle centred k below the lid satisfies
    #     a^2 + k^2 = (rise + k)^2   =>   k = (a^2 - rise^2) / (2 * rise)
    # and the sweep runs from phi to 180-phi so it passes over the top.
    a, rise = L / 2.0 - 26.0, SPEC["handle_reach"] - 4.0
    k = (a * a - rise * rise) / (2.0 * rise)
    rmaj = rise + k
    ang = math.degrees(math.atan2(k, a))
    handle = bkit.arc_torus("TiffinHandle", rmaj, 4.0, ang, 180.0 - ang,
                            centre=(0.0, 0.0, H - k), plane="XZ",
                            seg_major=44, mat=handle_mat, caps=True)

    # ---- anchor lugs the handle tips land on -------------------------------
    for i, sx in enumerate((-1.0, 1.0)):
        bkit.rounded_box("TiffinAnchor%d" % (i + 1), 10.0, 20.0, 8.0,
                         r=2.0, segments=2,
                         centre=(sx * a, 0.0, H - 2.0), mat=handle_mat)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="length", mm=220.0, tol=0.5, how="bbox_x", part="TiffinBody"),
    dict(name="width", mm=150.0, tol=0.5, how="bbox_y", part="TiffinBody"),
    dict(name="overall_height", mm=122.0, tol=3.0, how="bbox_z"),
]
