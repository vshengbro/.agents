"""
headphones -- 236 x 50 x 127 mm over-ear pair, standing on their cups.

Laid the way a product shot puts them: cups down, headband arcing over. The
band is a real `arc_torus` with both ends buried inside the earcup shells --
an open-ended sweep is non-manifold even when its tips are hidden, so it is
capped. The ear pads are `tube`s with a genuine 9 mm wall and a 1 mm overlap
onto the cup face, because a pad butted exactly flush with the shell is the
tangency case that hands the solver bad edges.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=236.0,
    depth=50.0,
    height=125.0,
    band_radius=76.0,
    band_tube=7.0,
    cup_diameter=84.0,
    pad_wall=9.0,
)

BAND_R, BAND_T = SPEC["band_radius"], SPEC["band_tube"]
CUP_R = SPEC["cup_diameter"] / 2.0
CUP_X, CUP_Z = BAND_R, 42.0
PAD_H = 14.0


def build():
    band = bkit.pbr("HeadbandShell", base=(0.24, 0.24, 0.27), rough=0.34,
                    coat=0.25)
    pad_mat = bkit.pbr("HeadbandPadMat", base=(0.18, 0.18, 0.21), rough=0.80)
    cushion = bkit.pbr("EarCushion", base=(0.30, 0.30, 0.34), rough=0.86)
    shell = bkit.pbr("EarCupShell", base=(0.42, 0.43, 0.46), rough=0.30,
                     coat=0.3)
    chrome = bkit.preset("polished_metal")

    # ---- headband: capped arc, tips inside the cups ---------------------
    bkit.arc_torus("HeadphonesBand", BAND_R, BAND_T, 0.0, 180.0,
                   centre=(0, 0, CUP_Z), plane="XZ", seg_major=56,
                   mat=band, caps=True)
    # Padded underside, concentric and slightly inboard of the band.
    bkit.arc_torus("HeadphonesPad", BAND_R - 8.0, 10.0, 16.0, 164.0,
                   centre=(0, 0, CUP_Z), plane="XZ", seg_major=44,
                   mat=pad_mat, caps=True)

    cups, pads, hinges = [], [], []
    for sign in (1, -1):
        x = sign * CUP_X
        cups.append(bkit.cylinder("_cup%d" % sign, CUP_R, 24.0, segments=64,
                                  axis="Y", centre=(x, 0, CUP_Z), mat=shell))
        # Pad faces the other cup, so it sits on the inward face only.
        pads.append(bkit.tube("_pad%d" % sign, CUP_R, CUP_R - SPEC["pad_wall"],
                              PAD_H, segments=64, axis="Y",
                              centre=(x, -sign * 18.0, CUP_Z),
                              mat=cushion))
        hinges.append(bkit.cylinder("_hinge%d" % sign, 11.0, 30.0, segments=32,
                                    axis="Y", centre=(x, 0, CUP_Z + 46.0),
                                    mat=chrome))
    bkit.join(cups, name="HeadphonesCups")
    bkit.join(pads, name="HeadphonesEarPads")
    bkit.join(hinges, name="HeadphonesHinges")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="width", mm=236.0, tol=1.0, how="bbox_x", part="HeadphonesCups"),
    dict(name="depth", mm=50.0, tol=1.0, how="bbox_y", part="HeadphonesEarPads"),
    dict(name="height", mm=125.0, tol=1.0, how="bbox_z"),
]
