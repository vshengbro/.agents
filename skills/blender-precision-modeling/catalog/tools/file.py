"""
file -- 200 mm flat mill file with a turned handle.

The body is a plain tapered plate, which is the silhouette that identifies a
file; the tooth field is a single raised band on one face rather than ~100
modelled teeth, which would be sub-pixel at every angle this studio shoots.
A 3 mm proud band in a rougher material reads as the cut surface.

The ferrule is a real TUBE: the blade passes through its bore, so the
junction shows a wall thickness instead of two solids z-fighting.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BODY_POLY = [(-10.5, 0.0), (10.5, 0.0), (10.0, 60.0), (9.0, 130.0),
             (5.0, 175.0), (0.5, 196.0), (-5.0, 175.0), (-9.0, 130.0),
             (-10.0, 60.0)]
BODY_T = 6.0

SPEC = dict(
    overall_length=202.0,
    file_length=196.0,
    file_width=21.0,
    handle_grip_width=34.0,
    body_thickness=BODY_T,
)


def build():
    wood = bkit.preset("wood")
    file_mat = bkit.pbr("FileSteel", base=(0.60, 0.62, 0.66), metal=0.30,
                        rough=0.42)
    cut_mat = bkit.pbr("FileCut", base=(0.40, 0.41, 0.44), metal=0.15,
                       rough=0.66)
    steel = bkit.pbr("FerruleSteel", base=(0.70, 0.72, 0.76), metal=0.30,
                     rough=0.26)

    body = bkit.extrude_profile("FileBody", BODY_POLY, BODY_T, axis="Y",
                                mat=file_mat)
    bkit.recalc(body)
    bkit.bevel(body, width_mm=0.6, segments=2, angle_deg=32)

    # ---- raised tooth band on the +Y face, tapered with the body ----------
    cut_poly = [(-8.6, 58.0), (8.6, 58.0), (7.0, 170.0), (-7.0, 170.0)]
    cut = bkit.extrude_profile("FileCutBand", cut_poly, 0.8,
                               centre=(0, BODY_T / 2.0 + 0.05, 0), axis="Y",
                               mat=cut_mat)
    bkit.recalc(cut)

    # ---- turned handle ----------------------------------------------------
    grip = ((-6.0, 30.0, 26.0, 6.0), (12.0, 34.0, 28.0, 7.0),
            (46.0, 30.0, 25.0, 7.0), (80.0, 26.0, 22.0, 6.0))
    sections = [[(x, y, z) for (x, y) in
                 bkit.rounded_rect_section(sx, sy, r)] for (z, sx, sy, r) in grip]
    handle = bkit.loft("FileHandle", sections, mat=wood)
    bkit.recalc(handle)

    ferrule = bkit.tube("FileFerrule", 14.0, 12.6, 14.0, segments=48,
                        centre=(0, 0, 86.0), mat=steel)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="file_length", mm=196.0, tol=0.5, how="bbox_z", part="FileBody"),
    dict(name="file_width", mm=21.0, tol=0.4, how="bbox_x", part="FileBody"),
    dict(name="handle_grip_width", mm=34.0, tol=0.5, how="diameter",
         part="FileHandle"),
    dict(name="overall_length", mm=202.0, tol=1.5, how="bbox_z"),
]