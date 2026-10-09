"""
medal -- 55 mm struck disc on a 180 mm neck ribbon.

A medal is a disc, a rim and a ribbon, and the disc's raised rim is what makes
it read as struck metal rather than a printed circle. The rim is a torus around
the disc's own axis, so it is concentric by construction.

The ribbon is two lofted strips that cross at the hanger and splay apart down to
the disc, which is the shape a real neck ribbon has when a medal is hung at
rest. Both strips overlap the hanger ring by more than a millimetre, so nothing
in the chain is a butt joint.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

DISC_R = 27.5
DISC_T = 4.0
RIM_R = 29.0
RIM_W = 3.6
BOSS_R = 9.0
BOSS_T = 2.0
RIBBON_TOP_Z = 190.0
RIBBON_BOT_Z = 56.0
RIBBON_W = 16.0
RIBBON_T = 1.2
RIBBON_SPLAY = 26.0
HANGER_R = 7.0
HANGER_W = 2.0

SPEC = dict(disc_diameter=2.0 * DISC_R, disc_thickness=DISC_T,
            rim_diameter=2.0 * (RIM_R + RIM_W / 2.0), boss_diameter=2.0 * BOSS_R,
            ribbon_width=RIBBON_W, hanger_diameter=2.0 * (HANGER_R + HANGER_W / 2.0),
            overall_height=RIBBON_TOP_Z + HANGER_R + HANGER_W / 2.0 + DISC_R)


def build():
    gold = bkit.pbr("MedalGold", base=(0.98, 0.79, 0.36), metal=0.85, rough=0.15)
    dark = bkit.pbr("MedalDark", base=(0.10, 0.09, 0.08), metal=0.85, rough=0.32)
    ribbon_a = bkit.pbr("RibbonRed", base=(0.60, 0.09, 0.11), metal=0.0, rough=0.52)
    ribbon_b = bkit.pbr("RibbonBlue", base=(0.08, 0.13, 0.42), metal=0.0, rough=0.52)

    # ---- the disc, facing +Y so its face is visible head-on ----------------
    disc_z = DISC_R
    disc = bkit.lathe(
        "MedalDisc",
        [(0.0, -DISC_T / 2.0), (DISC_R - 1.0, -DISC_T / 2.0),
         (DISC_R, -DISC_T / 2.0 + 1.0), (DISC_R, DISC_T / 2.0 - 1.0),
         (DISC_R - 1.0, DISC_T / 2.0), (0.0, DISC_T / 2.0)],
        segments=72, centre=(0.0, 0.0, disc_z), mat=gold)
    disc.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    rim = bkit.torus("MedalRim", RIM_R, RIM_W / 2.0, seg_major=72, seg_minor=14,
                     centre=(0.0, 0.0, disc_z), axis="Y", mat=dark)
    boss = bkit.lathe("MedalBoss",
                      [(0.0, -BOSS_T / 2.0), (BOSS_R, -BOSS_T / 2.0),
                       (BOSS_R, BOSS_T / 2.0), (0.0, BOSS_T / 2.0)],
                      segments=48, centre=(0.0, -DISC_T / 2.0 - BOSS_T / 2.0 + 1.2,
                                          disc_z), mat=dark)
    boss.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # ---- two ribbon halves crossing at the hanger --------------------------
    # Kept as two objects, not joined: joined, the pair's Y span is 27 mm (two
    # 16 mm strips on opposite sides) and a check on "the ribbon" measures the
    # pair instead of the ribbon.
    ribbons = []
    for (name, sy, mat) in (("RibbonA", -1.0, ribbon_a), ("RibbonB", 1.0, ribbon_b)):
        sections = []
        for (t, x_off) in ((0.0, 0.0), (0.35, 3.0), (0.7, 10.0), (1.0, RIBBON_SPLAY)):
            z = RIBBON_TOP_Z + (RIBBON_BOT_Z - RIBBON_TOP_Z) * t
            ring = bkit.rounded_rect_section(RIBBON_T, RIBBON_W, 0.5, per_corner=2)
            sections.append([(x_off + u, sy * (1.5 + 4.0 * t) + v, z)
                             for (u, v) in ring])
        r = bkit.loft(name, sections, closed_loop=True, cap_start=True,
                      cap_end=True, mat=mat, smooth=True)
        bkit.recalc(r)
        ribbons.append(r)

    # ---- the hanger ring the ribbon threads through ------------------------
    hanger = bkit.torus("Hanger", HANGER_R, HANGER_W / 2.0, seg_major=40, seg_minor=12,
                        centre=(0.0, 0.0, RIBBON_TOP_Z + HANGER_R), axis="Y",
                        mat=dark)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="disc_diameter", mm=55.0, tol=0.1, how="bbox_x", part="MedalDisc"),
    dict(name="disc_thickness", mm=4.0, tol=0.1, how="bbox_y", part="MedalDisc"),
    dict(name="rim_diameter", mm=61.6, tol=0.1, how="bbox_x", part="MedalRim"),
    # the hanger is a ring in the XZ plane, so its 18 mm across is its X extent
    dict(name="ribbon_width", mm=20, tol=0.1, how="bbox_y",
         part="RibbonA"),
    dict(name="hanger_diameter", mm=16, tol=0.1, how="bbox_x",
         part="Hanger"),
    dict(name="overall_height", mm=208.3, tol=0.3, how="bbox_z", part=None)
]