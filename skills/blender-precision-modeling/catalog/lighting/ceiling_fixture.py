"""
ceiling_fixture -- flush-mount LED ceiling luminaire: a shallow drum can, a wide
opal diffuser and an aluminium bezel.

Modelled hanging DOWNWARD from the origin. run_model calls sit_on_floor(), which
lifts the assembly until its lowest point rests on z = 0, so a ceiling fixture
authored upward would be flipped over and rendered as a floor-standing drum.
Building downward keeps the ceiling face at the top of the bounding box, which
is how the object is actually installed.

Every profile is closed by recalc(): lathe() welds but does not re-orient, and a
profile walked downward comes out with inward normals -- a negative volume that
still renders fine from one side and fails the health check.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    fixture_diameter=292.0,
    can_diameter=286.0,
    overall_height=74.0,
    diffuser_diameter=270.0,
    diffuser_height=44.0,
    bezel_diameter=292.0,
    bezel_height=14.0,
)

H = SPEC["overall_height"]


def _lathe(name, profile, mat, segments=96, centre=(0.0, 0.0, 0.0)):
    """Downward-authored lathe with normals forced outward."""
    ob = bkit.lathe(name, profile, segments=segments, centre=centre, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    alu = bkit.preset("anodized")
    white = bkit.preset("white_plastic")
    frosted = bkit.pbr("OpalDiffuser", base=(0.93, 0.94, 0.95), rough=0.42,
                       emission=(1.0, 0.97, 0.92), emission_strength=2.6)
    glow = bkit.pbr("PanelGlow", base=(1.0, 0.96, 0.88), rough=0.30,
                    emission=(1.0, 0.94, 0.82), emission_strength=4.0)

    can_r = SPEC["can_diameter"] / 2.0
    diff_r = SPEC["diffuser_diameter"] / 2.0
    bez_r = SPEC["bezel_diameter"] / 2.0
    diff_h = SPEC["diffuser_height"]
    bez_h = SPEC["bezel_height"]

    # ---- the can: ceiling face at z = 0, full fixture depth below it ----
    # This part owns overall_height, so the CHECK points at it rather than at
    # the assembly bounding box.
    can = _lathe("CeilingCan", [
        (0.0, 0.0),
        (can_r - 6.0, 0.0),
        (can_r, -6.0),          # steps DOWN from the ceiling face
        (can_r, -H + 10.0),
        (can_r - 8.0, -H),
        (diff_r + 2.0, -H),
        (diff_r + 2.0, -H + 6.0),
        (can_r - 26.0, -H + 6.0),
        (0.0, -H + 6.0),
    ], white)

    # ---- LED board visible in the cavity behind the diffuser -----------
    board = _lathe("CeilingBoard", [
        (0.0, -H + 6.0),
        (diff_r, -H + 6.0),
        (diff_r, -H + 11.0),
        (0.0, -H + 11.0),
    ], glow, segments=72)

    # ---- opal diffuser: a shallow domed lens set into the can ----------
    diffuser = _lathe("CeilingDiffuser", [
        (0.0, -H),
        (70.0, -H + 1.5),
        (118.0, -H + 8.0),
        (diff_r, -H + 18.0),
        (diff_r, -H + diff_h),
        (0.0, -H + diff_h),
    ], frosted)

    # ---- bezel: the rim trim clamping the diffuser ---------------------
    bezel = _lathe("CeilingBezel", [
        (diff_r - 1.0, -H + diff_h - bez_h + 4.0),
        (bez_r, -H + diff_h - bez_h + 4.0),
        (bez_r, -H + diff_h + 4.0),
        (diff_r - 1.0, -H + diff_h + 4.0),
    ], alu)

    # ---- four driver bosses, spaced by measurement ---------------------
    for (x, y) in bkit.grid_positions(cols=2, rows=2, pitch_x=190.0,
                                      pitch_y=190.0):
        boss = bkit.cylinder("CeilingBoss", 15.0, 9.0, segments=24,
                             centre=(x, y, -H + diff_h + 8.0), mat=alu)
        bkit.move(boss, 0.0, 0.0, 0.0)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="can_diameter", mm=286.0, tol=0.6, how="diameter", part="CeilingCan"),
    dict(name="overall_height", mm=74.0, tol=0.5, how="bbox_z", part="CeilingCan"),
    dict(name="diffuser_diameter", mm=270.0, tol=0.6, how="diameter", part="CeilingDiffuser"),
    dict(name="diffuser_height", mm=44.0, tol=0.5, how="bbox_z", part="CeilingDiffuser"),
    dict(name="bezel_diameter", mm=292.0, tol=0.6, how="diameter", part="CeilingBezel"),
]