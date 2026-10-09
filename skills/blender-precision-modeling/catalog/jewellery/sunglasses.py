"""
sunglasses -- 142 mm acetate front, two rims, real tinted lenses, folded temples.

The rims are annular lofts, not tori: a rim's cross-section is a thin rectangle
whose outer boundary is a rounded rectangle 58 x 46 and whose inner boundary is
a second rounded rectangle 50 x 38. loft() bridges four corner sections and
the fifth repeats the first, so the surface closes on itself -- cap both ends
and you seal the front of the rim, which is the trap here. The lens is then a
separate thin extrusion of the inner outline, tinted dark and set back 0.6 mm
inside the rim so the frame reads as holding it.

Temples hinge at the outer top corners, sweep back and break down at the ear,
which is the shape that makes a pair of sunglasses read as sunglasses in side
view instead of as a flat mask.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

RIM_W = 58.0           # outer width of one rim
RIM_H = 46.0           # outer height of one rim
RIM_R = 14.0           # corner radius
BAND = 4.0             # frame material width
DEPTH = 5.0            # front-to-back depth of the frame
LENS_SAG = 0.6         # lens set back inside the rim
RIM_CX = 39.0          # rim centre offset from the bridge, +/- in X
TEMPLE_L = 132.0
TEMPLE_W = 6.0
TEMPLE_T = 4.0

LENS_W = RIM_W - 2.0 * BAND
LENS_H = RIM_H - 2.0 * BAND

SPEC = dict(frame_width=2.0 * (RIM_CX + RIM_W / 2.0),
            rim_width=RIM_W,
            rim_height=RIM_H,
            frame_band=BAND,
            lens_width=LENS_W,
            temple_length=TEMPLE_L,
            overall_depth=TEMPLE_L)

def _rim(name, cx, mat):
    """One rim: a rounded-rect prism with a rounded-rect hole cut through it.

    NOT a five-section loft swept four sides and welded. That construction puts
    four faces on every interior vertex of the seam ring, which is non-manifold
    by definition -- the closing band and the opening band share an edge that
    only exists because the first and last sections were welded together. A
    solid prism minus an oversized through-cut is the same part, is watertight,
    and has no seam to fail.
    """
    outer = bkit.rounded_rect_section(RIM_W, RIM_H, RIM_R, per_corner=7,
                                      centre=(cx, 0.0))
    rim = bkit.extrude_profile(name, outer, DEPTH, axis="Y", mat=mat)
    inner = bkit.rounded_rect_section(LENS_W, LENS_H, RIM_R - BAND / 2.0,
                                      per_corner=7, centre=(cx, 0.0))
    # the cutter is 6 mm taller than the rim, so it passes clear through both
    # faces instead of ending flush with them (flush = tangency = bad edges)
    hole = bkit.extrude_profile("_rim_hole", inner, DEPTH + 6.0, axis="Y")
    bkit.boolean(rim, hole, "DIFFERENCE")
    return rim


def build():
    acetate = bkit.pbr("Acetate", base=(0.10, 0.09, 0.11), metal=0.0, rough=0.16,
                      coat=0.5)
    tint = bkit.pbr("SunTint", base=(0.06, 0.09, 0.12), metal=0.0, rough=0.06,
                    transmission=0.25, ior=1.52)
    metal = bkit.pbr("TempleMetal", base=(0.83, 0.85, 0.88), metal=0.85, rough=0.24)

    rims = []
    for sx in (-1.0, 1.0):
        rims.append(_rim("Rim", sx * RIM_CX, acetate))
    frame = bkit.join(rims, name="FrameFront")

    # bridge and top bar span the two rims
    bridge = bkit.rounded_box("Bridge", 2.0 * RIM_CX - LENS_W - BAND * 2.0,
                              9.0, 4.2, r=1.6, segments=3,
                              centre=(0.0, 0.0, 9.0), mat=acetate)
    brow = bkit.rounded_box("BrowBar", 2.0 * (RIM_CX + RIM_W / 2.0) - 6.0,
                            5.0, 3.0, r=1.2, segments=3,
                            centre=(0.0, 0.0, RIM_H / 2.0 - 3.0), mat=acetate)

    # ---- lenses ------------------------------------------------------------
    lenses = []
    for sx in (-1.0, 1.0):
        poly = bkit.rounded_rect_section(LENS_W - 0.6, LENS_H - 0.6,
                                         RIM_R - BAND / 2.0, per_corner=7,
                                         centre=(sx * RIM_CX, 0.0))
        lenses.append(bkit.extrude_profile("Lens", poly, 1.8, axis="Y", mat=tint))
    bkit.join(lenses, name="Lenses")

    # ---- temples: lofted, swept back and broken down at the ear -------------
    temples = []
    for sx in (-1.0, 1.0):
        x = sx * (RIM_CX + RIM_W / 2.0 - 2.0)
        stations = [(0.0, 1.0, 0.0), (30.0, 0.95, -1.0), (80.0, 0.85, -3.5),
                    (TEMPLE_L - 26.0, 0.75, -6.5), (TEMPLE_L - 8.0, 0.68, -9.0),
                    (TEMPLE_L, 0.55, -12.5)]
        sections = []
        for (y, taper, dz) in stations:
            ring = bkit.rounded_rect_section(TEMPLE_W * taper, TEMPLE_T * taper,
                                             TEMPLE_W * taper / 2.4,
                                             per_corner=4)
            sections.append([(x + u, y, 18.0 + v + dz) for (u, v) in ring])
        temples.append(bkit.loft("Temple", sections, closed_loop=True,
                                 cap_start=True, cap_end=True, mat=metal,
                                 smooth=True))
    bkit.join(temples, name="Temples")
    # loft() does not call recalc(), and these two shells come out of the
    # sweep with inverted normals -- a multi-shell mesh whose signed volume is
    # negative, which is exactly what health() reports as an inverted object.
    bkit.recalc(bpy.data.objects["Temples"])

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="frame_width", mm=136.0, tol=0.2, how="bbox_x", part="FrameFront"),
    dict(name="frame_height", mm=46.0, tol=0.2, how="bbox_z", part="FrameFront"),
    dict(name="frame_depth", mm=5.0, tol=0.2, how="bbox_y", part="FrameFront"),
    # both lenses: 2 x (RIM_CX + (LENS_W - 0.6)/2)
    dict(name="lens_pair_width", mm=127.4, tol=0.1, how="bbox_x", part="Lenses"),
    dict(name="temple_length", mm=132.0, tol=0.3, how="bbox_y", part="Temples")
]