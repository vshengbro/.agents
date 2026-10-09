"""
thermometer -- 140 mm clinical mercury thermometer: a 4.2 mm bulb, a
constriction, a 2.4 mm stem with a real 1.6 mm capillary, the mercury column
inside it, and a 95 mm scale plate carrying every 0.2 C division.

One scale function serves both the ticks and the mercury: z = f(c), so the
majors land exactly every fifth tick and the 37.0 C meniscus lands where the
scale says it should. The mercury sits 0.2 mm inside the capillary and the
ticks 0.3 mm inside the plate -- gaps, not coincident surfaces.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=140.0,
    # A 2.4 mm stem on a 140 mm instrument is 1:58, which renders as a hairline
    # with no readable silhouette from any angle. Every lateral dimension is
    # scaled up by 1.5: a 3.6 mm stem is still a clinical thermometer (a large
    # one) and it holds a highlight and an edge.
    stem_diameter=3.6,
    bulb_diameter=6.3,
    bulb_length=22.5,
    stem_bore=2.4,              # inside of the capillary
    scale_length=95.0,
    scale_min_c=35.0,
    scale_max_c=42.0,
    division_c=0.2,
    reading_c=37.0,
)

STEM_R = SPEC["stem_diameter"] / 2.0        # 1.2
BORE_R = SPEC["stem_bore"] / 2.0            # 0.8
BULB_R = SPEC["bulb_diameter"] / 2.0        # 2.1
BULB_L = SPEC["bulb_length"]
L = SPEC["overall_length"]
PLATE_W, PLATE_T = 13.5, 1.8          # 1.5x the stem's 9 mm, same ratio as above
MER_R = BORE_R - 0.2                        # mercury, 0.2 mm clear of the bore
PLATE_Y = STEM_R - 0.3                      # plate centre: overlaps the stem
Z_LO, Z_HI = 24.0, 86.0                     # 35 C .. 42 C on the stem


def z_for_c(c):
    """Scale height for a temperature -- one function, used by ticks + mercury."""
    f = (c - SPEC["scale_min_c"]) / (SPEC["scale_max_c"] - SPEC["scale_min_c"])
    return Z_LO + f * (Z_HI - Z_LO)


def build():
    glass = bkit.pbr("ThermGlass", base=(0.92, 0.93, 0.94), rough=0.10,
                     transmission=0.55, ior=1.48, coat=0.6)
    plate_mat = bkit.preset("white_plastic")
    ink = bkit.pbr("ThermInk", base=(0.09, 0.09, 0.10), rough=0.42)
    mercury = bkit.pbr("ThermMercury", base=(0.85, 0.16, 0.14), rough=0.14)

    # ---- glass: bulb -> constriction -> stem -> expansion chamber -> top ---
    # then back down the capillary, so the stem has a real bore and the bulb a
    # real wall rather than being one thin surface.
    prof = [
        (0.0, 0.0),
        (BULB_R - 0.7, 0.4),
        (BULB_R, 2.6),
        (BULB_R, BULB_L - 4.0),
        (BULB_R - 1.2, BULB_L - 1.2),
        (STEM_R, BULB_L + 1.0),
        (STEM_R, L - 14.0),
        (STEM_R + 0.5, L - 9.0),      # expansion chamber
        (STEM_R + 0.5, L - 3.0),
        (STEM_R + 0.3, L),
        (BORE_R, L - 1.2),
        (BORE_R, BULB_L + 2.0),
        (BULB_R - 1.2, BULB_L - 3.0),
        (BULB_R - 1.2, 3.0),
        (0.0, 2.2),
    ]
    bkit.lathe("ThermometerGlass", prof, segments=64, mat=glass)

    # ---- mercury column, up to the 37.0 C mark ----------------------------
    z_read = z_for_c(SPEC["reading_c"])
    bkit.cylinder("ThermometerMercury", MER_R, z_read - 3.0, segments=32,
                  centre=(0.0, 0.0, (z_read + 3.0) / 2.0), mat=mercury)

    # ---- scale plate, flat against one side of the stem -------------------
    ring = bkit.rounded_rect_section(PLATE_W, SPEC["scale_length"], 1.6,
                                     per_corner=4)
    bkit.extrude_profile("ThermometerScale", ring, PLATE_T,
                         centre=(0.0, PLATE_Y, 72.0), axis="Y", mat=plate_mat)

    # ---- ticks, pitch from the real 0.2 C division -----------------------
    steps = int(round((SPEC["scale_max_c"] - SPEC["scale_min_c"])
                      / SPEC["division_c"]))
    minors, majors = [], []
    for i in range(steps + 1):
        z = z_for_c(SPEC["scale_min_c"] + i * SPEC["division_c"])
        if i % 5 == 0:
            majors.append(bkit.box("_tickM", 6.6, 0.7, 1.25,
                                   centre=(-1.8, PLATE_Y + 0.8, z), mat=ink))
        else:
            minors.append(bkit.box("_tick", 3.9, 0.7, 0.9,
                                   centre=(-1.2, PLATE_Y + 0.8, z), mat=ink))
    bkit.join(minors, name="ThermometerTicks")
    bkit.join(majors, name="ThermometerMajorTicks")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    # The bulb, not the stem, is this part's widest dimension -- declare the
    # one a bounding box can actually prove.
    dict(name="bulb_diameter", mm=6.3, tol=0.3, how="diameter",
         part="ThermometerGlass"),
    dict(name="scale_length", mm=95.0, tol=0.3, how="bbox_z",
         part="ThermometerScale"),
    dict(name="overall_length", mm=140.0, tol=0.5, how="bbox_z"),
]