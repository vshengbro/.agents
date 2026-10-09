"""
moebius_tower -- a 210 mm tapering tower that turns 1.5 times on the way up.

Twenty-four rounded-square sections, each rotated a further 22.5 degrees and
shrunk, lofted into one closed solid. `loft` caps both ends, so the result is
watertight without any further work; the only rule to respect is that every
section must have the SAME vertex count, which is why per_corner is fixed
rather than derived from the tapering width.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height=210.0,
    base_width=46.0,
    tip_width=13.0,
    turns=1.5,             # 540 degrees of twist over the full height
    levels=24,
    width=50.34,           # base section is 46 x 36.8; the twist rotates the
    depth=49.15,           # corners out past the nominal 46 mm
)

LEVELS = SPEC["levels"]

CHECKS = [
    dict(name="height", mm=210.0, tol=0.5, how="bbox_z", part="MoebiusTower"),
    dict(name="width", mm=50.34, tol=0.5, how="bbox_x", part="MoebiusTower"),
    dict(name="depth", mm=49.15, tol=0.5, how="bbox_y", part="MoebiusTower"),
]


def build():
    sections = []
    for k in range(LEVELS + 1):
        t = k / LEVELS
        w = SPEC["base_width"] + (SPEC["tip_width"] - SPEC["base_width"]) * t
        d = w * 0.80
        ang = 2.0 * math.pi * SPEC["turns"] * t
        # Constant point count across every section -- loft raises otherwise.
        ring = bkit.rounded_rect_section(w, d, r=w * 0.16, per_corner=4)
        ca, sa = math.cos(ang), math.sin(ang)
        sections.append([(x * ca - y * sa, x * sa + y * ca,
                          SPEC["height"] * t) for (x, y) in ring])

    mat = bkit.pbr("TowerShell", base=(0.74, 0.74, 0.78), metal=0.20, rough=0.26)
    tower = bkit.loft("MoebiusTower", sections, closed_loop=True,
                      cap_start=True, cap_end=True, mat=mat)

    # A twisted loft arrives with consistent winding but the caps can sit
    # inside-out; recalc() settles the whole shell in one pass.
    bkit.recalc(tower)
    # Flat-shaded on purpose: with smooth shading the twist disappears into a
    # soft vertical gradient and the tower reads as a cone.
    bkit.bevel(tower, width_mm=0.5, segments=2, angle_deg=25)

    return dict(spec=SPEC, parts=1)