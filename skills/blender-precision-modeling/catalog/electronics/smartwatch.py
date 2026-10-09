"""
smartwatch -- 45 x 38 x 10.7 mm case with 22 mm sport bands, laid flat.

The case is a superellipse loft (n = 4.4, a squircle) rather than a rounded
box: an Apple-style case is a flattened cushion whose corner radius is far
larger than its half-thickness, which is exactly the case a uniform bevel
clamp cannot express. The two bands are one `loft` of three rounded-rect
sections each, so the taper from 24 mm at the lugs down to 20 mm at the tip is
computed, not placed.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    case_length=45.0,
    case_width=38.0,
    case_height=10.7,
    band_length=56.0,
    band_thickness=4.2,
)

CL, CW, CH = SPEC["case_length"], SPEC["case_width"], SPEC["case_height"]


def build():
    alu = bkit.pbr("WatchAlu", base=(0.62, 0.63, 0.66), metal=0.85, rough=0.30)
    glass = bkit.pbr("WatchGlass", base=(0.018, 0.020, 0.026), rough=0.05,
                     coat=0.9)
    band_mat = bkit.pbr("WatchBand", base=(0.13, 0.30, 0.50), rough=0.62)
    crown_mat = bkit.preset("polished_metal")

    # ---- squircle case: loft of superellipse sections --------------------
    secs = []
    for (sx, sy, z) in ((CL - 2.0, CW - 2.0, 0.0), (CL, CW, 1.8),
                        (CL - 0.4, CW - 0.4, 5.2), (CL - 2.6, CW - 2.6, CH - 1.6),
                        (CL - 5.0, CW - 5.0, CH)):
        secs.append([(x, y, z)
                     for (x, y) in bkit.superellipse_section(sx, sy, n=4.4,
                                                            steps=64)])
    case = bkit.loft("WatchCase", secs, mat=alu, smooth=True)

    # ---- display sunk into the top face ---------------------------------
    scr = bkit.extrude_profile(
        "WatchScreen", bkit.rounded_rect_section(CL - 9.0, CW - 9.0, 8.0),
        0.6, centre=(0, 0, CH - 0.6), mat=glass)
    cut = bkit.extrude_profile(
        "_scr", bkit.rounded_rect_section(CL - 8.4, CW - 8.4, 8.0),
        2.0, centre=(0, 0, CH + 0.2))
    bkit.boolean(case, cut, "DIFFERENCE")

    # ---- digital crown + side key on the +X face -------------------------
    # 1 mm of overlap into the case: a crown butted exactly onto the wall is
    # the tangency case that hands the solver 3-10 bad edges.
    bkit.cylinder("WatchCrown", 3.0, 3.2, segments=32, axis="X",
                  centre=(CL / 2.0 + 0.6, 5.0, 5.6), mat=crown_mat)
    bkit.rounded_box("WatchKey", 2.4, 9.0, 2.6, r=0.7, segments=3,
                     centre=(CL / 2.0 + 0.2, -6.0, 5.6), mat=crown_mat)

    # ---- two tapered bands, one loft each --------------------------------
    # Each section is a rounded rect in the band's CROSS-SECTION plane and the
    # loft sweeps it along Y, so the section's second coordinate becomes world
    # Z. Laying the rings out in XY instead -- all at the same height -- makes
    # a zero-thickness ribbon whose signed volume is float noise, and health()
    # reports it as inverted normals.
    #
    # The -Y band reuses the +Y sections mirrored through y, which reverses
    # their winding, so the joined result is recalculated rather than trusted.
    bands = []
    for sign in (1, -1):
        rings = []
        for (sw, y, t) in ((24.0, 15.0, 5.0), (22.0, 40.0, 4.6),
                           (20.0, 62.0, 4.2)):
            ring = bkit.rounded_rect_section(sw, t, 1.8)
            rings.append([(x, sign * y, yy + t / 2.0) for (x, yy) in ring])
        bands.append(bkit.loft("_band%d" % sign, rings, mat=band_mat))
    band = bkit.join(bands, name="WatchBands")
    bkit.recalc(band)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="case_length", mm=45.0, tol=0.5, how="bbox_x", part="WatchCase"),
    dict(name="case_width", mm=38.0, tol=0.5, how="bbox_y", part="WatchCase"),
    dict(name="case_height", mm=10.7, tol=0.5, how="bbox_z", part="WatchCase"),
    dict(name="overall_length", mm=124.0, tol=0.6, how="longest"),
]
