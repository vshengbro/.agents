"""
chandelier -- six-arm candle chandelier: ceiling canopy, a central drop stem,
and six arms radiating at exactly even angles.

The arms are the whole model. A chandelier with five arms, or six at uneven
angles, reads as broken, so the sweep count is a computed value.

DO NOT lathe the repeated parts and sweep them. `bkit.lathe` routes through
`place()`, which sets `obj.location`, and `array_radial` only orbits when the
swept object's own transform is identity -- Blender's object offset is
`empty.matrix_world.inverted() @ obj.matrix_world`, so a part carrying a
location gets a pure-translation offset and the six copies march off in a
straight line instead of orbiting. `revolve()` below bakes the centre into the
mesh vertices so location stays 0 and the sweep is a true orbit. `array_radial`
itself is correct -- it is only unsafe on location-bearing objects.

Per-part CHECKS deliberately measure Z extents and the unswept stem: after a
radial sweep an object's bounding box covers the whole ring, so a cup's
diameter would read as the chandelier's full span.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    arm_count=6,
    arm_angle_deg=60.0,      # 360 / 6: one value, never typed twice
    arm_radius=245.0,        # centre of each candle cup
    canopy_diameter=160.0,
    canopy_height=30.0,
    stem_diameter=60.0,
    drop_length=240.0,
    cup_diameter=96.0,
    cup_height=26.0,
    candle_diameter=26.0,
    candle_height=130.0,
    finial_height=66.0,
    overall_span=536.0,
)

ARM_R = SPEC["arm_radius"]


def revolve(name, profile, centre=(0.0, 0.0, 0.0), segments=48, mat=None):
    """Solid of revolution, MESH-BAKED at `centre` so obj.location stays 0.

    See the module docstring: a swept part must have an identity transform or
    array_radial turns the sweep into a translation.
    """
    secs = []
    for (r, z) in profile:
        if abs(r) < 1e-6:
            secs.append([(centre[0], centre[1], centre[2] + z)] * segments)
        else:
            secs.append([(centre[0] + r * math.cos(2.0 * math.pi * i / segments),
                          centre[1] + r * math.sin(2.0 * math.pi * i / segments),
                          centre[2] + z) for i in range(segments)])
    ob = bkit.loft(name, secs, closed_loop=True,
                   cap_start=abs(profile[0][0]) > 1e-6,
                   cap_end=abs(profile[-1][0]) > 1e-6, mat=mat)
    bkit.weld(ob)
    bkit.recalc(ob)
    return ob


def build():
    brass = bkit.pbr("ChandelierBrass", base=(0.74, 0.58, 0.27), metal=0.85,
                     rough=0.26)
    wax = bkit.pbr("CandleWax", base=(0.91, 0.88, 0.79), rough=0.55)
    flame = bkit.pbr("FlameBulb", base=(1.0, 0.93, 0.75), rough=0.28,
                     emission=(1.0, 0.86, 0.62), emission_strength=9.0)

    n = SPEC["arm_count"]
    step = SPEC["arm_angle_deg"]
    canopy_h = SPEC["canopy_height"]
    drop = SPEC["drop_length"]
    cup_r = SPEC["cup_diameter"] / 2.0
    cup_h = SPEC["cup_height"]
    candle_r = SPEC["candle_diameter"] / 2.0
    candle_h = SPEC["candle_height"]
    finial_h = SPEC["finial_height"]

    # ---- ceiling canopy (never swept, so it may use place() freely) -----
    canopy = bkit.lathe("ChandelierCanopy", [
        (0.0, 0.0),
        (72.0, 0.0),
        (80.0, 3.0),
        (80.0, 18.0),
        (70.0, 25.0),
        (40.0, canopy_h),
        (16.0, canopy_h - 3.0),
        (16.0, canopy_h - 14.0),
        (0.0, canopy_h - 14.0),
    ], segments=72, mat=brass)

    stem_top = canopy_h - 12.0
    stem = bkit.lathe("ChandelierStem", [
        (0.0, 0.0),
        (26.0, 0.0),
        (30.0, 6.0),
        (24.0, 14.0),
        (11.0, 20.0),
        (11.0, drop - 24.0),
        (22.0, drop - 16.0),
        (30.0, drop - 6.0),
        (26.0, drop),
        (0.0, drop),
    ], segments=64, centre=(0.0, 0.0, stem_top - drop), mat=brass)

    hub_z = stem_top - drop + 10.0

    # ---- the six arms: a swept tube curving down and out ---------------
    # A horizontal bar reads as a bracket; the downward curve is what makes
    # the candles sit BELOW the stem, which is the chandelier silhouette.
    stations = [(26.0, 15.0, 0.0), (ARM_R * 0.55, 12.0, -40.0),
                (ARM_R * 0.86, 10.0, -66.0), (ARM_R, 9.0, -78.0)]
    secs = []
    for (x, r, dz) in stations:
        secs.append([(x, r * math.cos(2.0 * math.pi * i / 16),
                      hub_z + dz + r * math.sin(2.0 * math.pi * i / 16))
                     for i in range(16)])
    arm = bkit.loft("ChandelierArm", secs, closed_loop=True,
                    cap_start=True, cap_end=True, mat=brass)
    bkit.recalc(arm)
    bkit.array_radial(arm, n)

    # ---- candle cups, candles and flame bulbs, all mesh-baked + swept ---
    cup_base_z = hub_z - 78.0 - cup_h + 4.0
    cup = revolve("ChandelierCup", [
        (cup_r - 2.0, cup_base_z),
        (cup_r - 2.0, cup_base_z + cup_h),
        (cup_r, cup_base_z + cup_h),
        (cup_r, cup_base_z),
        (0.0, cup_base_z),
    ], centre=(ARM_R, 0.0, 0.0), segments=64, mat=brass)
    bkit.array_radial(cup, n)

    candle = revolve("ChandelierCandle", [
        (0.0, cup_base_z + cup_h),
        (candle_r, cup_base_z + cup_h),
        (candle_r, cup_base_z + cup_h + candle_h - 6.0),
        (candle_r - 3.0, cup_base_z + cup_h + candle_h),
        (0.0, cup_base_z + cup_h + candle_h),
    ], centre=(ARM_R, 0.0, 0.0), segments=48, mat=wax)
    bkit.array_radial(candle, n)

    bulb = revolve("ChandelierBulb", [
        (0.0, cup_base_z + cup_h + candle_h - 14.0),
        (13.0, cup_base_z + cup_h + candle_h - 10.0),
        (17.0, cup_base_z + cup_h + candle_h + 4.0),
        (18.0, cup_base_z + cup_h + candle_h + 22.0),
        (13.0, cup_base_z + cup_h + candle_h + 40.0),
        (6.0, cup_base_z + cup_h + candle_h + 52.0),
        (0.0, cup_base_z + cup_h + candle_h + 56.0),
    ], centre=(ARM_R, 0.0, 0.0), segments=48, mat=flame)
    bkit.array_radial(bulb, n)

    # ---- finial balancing the canopy under the stem --------------------
    finial = revolve("ChandelierFinial", [
        (0.0, -finial_h),
        (30.0, -finial_h + 4.0),
        (34.0, -finial_h + 14.0),
        (22.0, -finial_h + 30.0),
        (26.0, -finial_h + 40.0),
        (14.0, -finial_h + 56.0),
        (0.0, 0.0),
    ], centre=(0.0, 0.0, hub_z), segments=64, mat=brass)

    return dict(spec=SPEC, parts=7, arms=n)


CHECKS = [
    dict(name="canopy_diameter", mm=160.0, tol=0.6, how="diameter", part="ChandelierCanopy"),
    dict(name="drop_length", mm=240.0, tol=0.5, how="bbox_z", part="ChandelierStem"),
    dict(name="cup_height", mm=26.0, tol=0.4, how="bbox_z", part="ChandelierCup"),
    dict(name="candle_height", mm=130.0, tol=0.5, how="bbox_z", part="ChandelierCandle"),
    dict(name="finial_height", mm=66.0, tol=0.4, how="bbox_z", part="ChandelierFinial"),
]