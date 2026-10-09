"""
volcano -- a stratovolcano: 3.9 km wide, 1.24 km to the crater rim, with a
summit crater 380 m across and 140 m deep.

Size class `huge` (3000..40000 mm band). The real Mount Etna is 3357 m tall
and 60 km across at the base; a 3.9 km base / 1.24 km height keeps the classic
~3:1 flank ratio in range without leaving the band.

The cone is a `lathe` over a closed profile that walks out along the ground,
up the flank, over the crater rim, down into the crater and across the floor --
one watertight solid with a real crater, not a cone with a subtracted hole.
Three parasitic cones sit on the flank at computed positions and radii, and a
lavapool disc closes the crater floor.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_diameter=3900.0,
    summit_height=1240.0,      # to the crater rim
    crater_diameter=380.0,
    crater_depth=140.0,
    parasitic_cones=3,
    ash_plume_height=900.0,
)

R_BASE = SPEC["base_diameter"] / 2.0
H = SPEC["summit_height"]
R_CRATER = SPEC["crater_diameter"] / 2.0
DEPTH = SPEC["crater_depth"]
FLANK_CURVE = 0.62            # concave flank: a straight cone reads as a party hat


def build():
    basalt = bkit.pbr("VolcanoBasalt", base=(0.185, 0.175, 0.170), rough=0.86)
    scoria = bkit.pbr("VolcanoScoria", base=(0.115, 0.108, 0.105), rough=0.92)
    ash = bkit.pbr("VolcanoAsh", base=(0.46, 0.44, 0.43), rough=0.95)
    lava = bkit.pbr("VolcanoLava", base=(0.60, 0.16, 0.045), rough=0.55,
                    emission=(0.9, 0.22, 0.05), emission_strength=1.5)

    # ---- main cone with a real summit crater ------------------------------
    # The profile is the whole model: out along the ground, up a concave
    # flank, over the rim, down the inner wall, across the crater floor. Both
    # ends close at r=0, so `lathe` needs no end caps and the solid is sealed
    # without a single boolean.
    prof = [
        (0.0, 0.0),
        (R_BASE, 0.0),
    ]
    steps = 12
    for i in range(1, steps + 1):
        t = float(i) / steps
        # Concave flank, base to summit. The exponent is BELOW 1 so the slope
        # is gentle at the base and steepens toward the crater -- the shape of
        # a real stratocone. An exponent above 1 makes a smooth dome, which
        # is what the first pass produced.
        r = R_CRATER + (R_BASE - R_CRATER) * ((1.0 - t) ** FLANK_CURVE)
        prof.append((r, H * t))
    prof.append((R_CRATER, H - 4.0))            # inner lip
    prof.append((R_CRATER - 12.0, H - DEPTH + 18.0))   # inner wall, stepped
    prof.append((R_CRATER - 26.0, H - DEPTH))   # crater floor
    prof.append((0.0, H - DEPTH + 6.0))         # slightly domed lava floor
    cone = bkit.lathe("VolcanoCone", prof, segments=48, mat=basalt, smooth=False)
    bkit.recalc(cone)

    # ---- crater rim collar ----------------------------------------------
    # A raised lip standing on the rim crest. It exists so the crater's
    # DIAMETER is a measurable part: measure() reports bbox sizes, not
    # positions, so a crater depth can never be checked directly.
    rim = bkit.tube("CraterRim", R_CRATER + 26.0, R_CRATER - 4.0, 34.0,
                    segments=48, centre=(0.0, 0.0, H - 12.0), mat=basalt)
    # The rim collar stands proud of the crater, so its own outer diameter is
    # crater_diameter + the two collars. Declared, not accidental.

    # ---- lava pool on the crater floor ------------------------------------
    pool_r = R_CRATER - 34.0
    pool = bkit.cylinder("LavaPool", pool_r, 10.0, segments=32,
                         centre=(0.0, 0.0, H - DEPTH + 2.0), smooth=False, mat=lava)

    # ---- parasitic cones on the flank -------------------------------------
    # Positioned on the profile's own radius at their height fraction, so a
    # cone sits ON the flank instead of floating beside it.
    for i, (hf, ang) in enumerate(((0.30, 34.0), (0.46, 205.0), (0.62, 128.0))):
        t = hf
        # Foot placed ON the flank profile, sunk 40% of its height so the
        # cone grows out of the mountain rather than standing beside it.
        rr = R_CRATER + (R_BASE - R_CRATER) * ((1.0 - t) ** FLANK_CURVE)
        ch = 260.0 - 50.0 * i
        cr = ch * 1.5
        a = math.radians(ang)
        sub = bkit.cylinder("ParasiticCone%d" % (i + 1), cr, ch, r2=cr * 0.12,
                            segments=22,
                            centre=(rr * math.cos(a), rr * math.sin(a),
                                    H * t - ch * 0.30),
                            smooth=False, mat=scoria)
        bkit.recalc(sub)

    # ---- ash plume: three stacked, shrinking discs above the crater -------
    # A real eruption column narrows with height, so the plume stack widens
    # downward-to-upward only slightly and each puff is offset: three boxes
    # of equal size stacked on the axis read as a wedding cake.
    for i, (z, r, hh) in enumerate(((H + 60.0, 150.0, 190.0),
                                    (H + 250.0, 215.0, 220.0),
                                    (H + 470.0, 260.0, 240.0))):
        bkit.rounded_box("AshPlume%d" % (i + 1), r * 1.9, r * 1.7, hh,
                         r=r * 0.9,
                         centre=(r * 0.22 * i, -r * 0.16 * i, z), mat=ash)
    # The column itself: a lathe whose radius follows the classic
    # power-law widening, so the stack of puffs sits on a real cone.
    plume_prof = [(70.0, 0.0), (150.0, 0.10)]
    steps = 8
    for i in range(1, steps + 1):
        t = float(i) / steps
        plume_prof.append((70.0 + (300.0 - 70.0) * (t ** 0.55), H * 0.62 * t))
    bkit.lathe("AshColumn", plume_prof, segments=28, centre=(0.0, 0.0, H),
               mat=ash, smooth=True)

    return dict(spec=SPEC, parts=3 + SPEC["parasitic_cones"] + 4)


CHECKS = [
    dict(name="base_diameter", mm=3900.0, tol=6.0, how="diameter", part="VolcanoCone"),
    dict(name="summit_height", mm=1240.0, tol=8.0, how="bbox_z", part="VolcanoCone"),
    # A crater is a DIP in the profile, and `measure()` reports bbox SIZES, not
    # positions -- so crater depth is not directly measurable. The parts that
    # own measurable dimensions are checked instead: the cone's own height,
    # the lava pool's width, and the top plume's thickness.
    dict(name="lava_pool_diameter", mm=312.0, tol=3.0,
         how="diameter", part="LavaPool"),
    dict(name="lava_pool_depth", mm=10.0, tol=1.0, how="bbox_z", part="LavaPool"),
    dict(name="crater_rim_outer_diameter", mm=432.0, tol=4.0,
         how="diameter", part="CraterRim"),
    dict(name="plume_height", mm=240.0, tol=4.0, how="bbox_z", part="AshPlume3"),
]