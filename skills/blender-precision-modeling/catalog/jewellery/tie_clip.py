"""
tie_clip -- 55 mm slide tie bar with a bowed spring blade and two end lips.

A tie clip is a bowed strip, and a bow is a cross-section that changes along a
path -- which is what loft() is for. The bar is a run of rounded-rectangle
sections along X whose centres ride an arc, so it curves rather than sitting
flat; the blade behind it is the same construction with a deeper arc, which is
the spring that grips the tie.

The blade's arc is the number that matters: it has to bow far enough to clear
the tie (12 mm of clearance at the middle) and then come back to the bar at
both ends, which is why the blade is built over 25 stations rather than as two
straight arms and a curve. Both lofts are capped at both ends, so each is a
closed solid.
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

BAR_L = 55.0
BAR_W = 9.0           # across the tie (Y)
BAR_T = 2.6           # front-to-back thickness of the bar section (Z)
BAR_BOW = 1.6         # how far the bar's centre rises at mid-span
BAR_STATIONS = 13

BLADE_L = 40.0
BLADE_H = 8.4         # the blade's height (Z)
BLADE_T = 1.3
BLADE_GAP = 4.6       # clearance between blade and bar at the ends
BLADE_BOW = 12.0      # extra clearance at mid-span
BLADE_STATIONS = 21
LIP_L = 4.0

SPEC = dict(bar_length=BAR_L,
            bar_width=BAR_W,
            bar_thickness=BAR_T,
            blade_height=BLADE_H,
            blade_thickness=BLADE_T,
            blade_clearance=BLADE_GAP + BLADE_BOW,
            overall_depth=25.3)


def build():
    steel = bkit.pbr("TieClipSteel", base=(0.84, 0.86, 0.89), metal=0.85, rough=0.14)
    dark = bkit.pbr("TieClipLacquer", base=(0.10, 0.10, 0.12), metal=0.0, rough=0.18,
                    coat=0.6)

    # ---- the bar: rounded-rect sections riding an arc along X --------------
    sections = []
    for i in range(BAR_STATIONS):
        t = i / float(BAR_STATIONS - 1)
        x = -BAR_L / 2.0 + BAR_L * t
        # the bar is deepest at mid-span and thins toward the tips
        taper = 1.0 - 0.25 * (2.0 * t - 1.0) ** 2
        z = BAR_BOW * (1.0 - (2.0 * t - 1.0) ** 2)
        ring = bkit.rounded_rect_section(BAR_W, BAR_T * taper, BAR_T * taper / 2.2,
                                         per_corner=5)
        sections.append([(x, u, z + v) for (u, v) in ring])
    bkit.loft("ClipBar", sections, closed_loop=True, cap_start=True,
              cap_end=True, mat=dark, smooth=True)

    # ---- the blade: the same construction with a much deeper bow ----------
    sections = []
    for i in range(BLADE_STATIONS):
        t = i / float(BLADE_STATIONS - 1)
        x = -BLADE_L / 2.0 + BLADE_L * t
        u = 2.0 * t - 1.0
        # end lips: the last and first stations come back to the bar
        y = BLADE_GAP + BLADE_BOW * (1.0 - u * u) - BLADE_BOW * (u ** 8)
        h = BLADE_H * (1.0 - 0.30 * u * u)
        ring = bkit.rounded_rect_section(BLADE_T, h, BLADE_T / 2.0, per_corner=4)
        sections.append([(x, y + p, q) for (p, q) in ring])
    bkit.loft("ClipBlade", sections, closed_loop=True, cap_start=True,
              cap_end=True, mat=steel, smooth=True)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="bar_length", mm=55.0, tol=0.15, how="bbox_x", part="ClipBar"),
    dict(name="bar_width", mm=9.0, tol=0.1, how="bbox_y", part="ClipBar"),
    # a BOWED bar's Z extent is the section plus the bow, not the section
    # alone: 1.6 mm of bow above the crown line and 0.975 mm below the tips
    dict(name="bar_crown_to_tip", mm=3.875, tol=0.05, how="bbox_z", part="ClipBar"),
    dict(name="blade_length", mm=40.0, tol=0.15, how="bbox_x", part="ClipBlade"),
    dict(name="blade_height", mm=8.4, tol=0.1, how="bbox_z", part="ClipBlade"),
    dict(name="overall_depth", mm=25.3, tol=0.3, how="bbox_y", part=None)
]