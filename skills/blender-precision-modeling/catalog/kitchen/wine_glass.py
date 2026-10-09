"""wine_glass -- lead crystal stemware: solid glass, one lathe, real foot/stem/bowl.

A 620 ml claret glass, 157 mm tall on an 84 mm foot. Glassware is the awkward
case for a lathe: the wall is thin, but below the bowl the glass is SOLID, so
the profile is a single closed cross-section that runs out along the foot, up
the stem, over the rim and back down the inside to the bowl's inner floor on
the axis. The cavity between that floor and the rim is the wine space; nothing
down there is modelled twice.

`preset("glass")` is a tinted partial-transmission material on purpose: full
transmission has nothing bright behind it in this studio and renders black.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    foot_diameter=84.0,    # widest point of the whole glass
    height=157.0,          # rim above the table
    bowl_diameter=76.0,    # widest point of the bowl
    rim_diameter=70.0,
    stem_diameter=8.0,     # pulled stem, thin waist
    wall=2.2,              # bowl wall thickness at the rim
    bowl_depth=66.0,       # inner floor of the bowl up to the rim
    volume_ml=620.0,
)

FOOT_R = SPEC["foot_diameter"] / 2.0
H = SPEC["height"]
BOWL_R = SPEC["bowl_diameter"] / 2.0
RIM_R = SPEC["rim_diameter"] / 2.0
STEM_R = SPEC["stem_diameter"] / 2.0
WALL = SPEC["wall"]
FLOOR = H - SPEC["bowl_depth"]          # top of the solid stem/bowl junction


def build():
    # preset("glass") carries 0.82 transmission, which this studio has nothing
    # bright behind to refract, so the glass renders charcoal. Same lever the
    # preset's own comment recommends: brighter base, much less transmission.
    glass = bkit.pbr("CrystalBright", base=(0.95, 0.97, 1.0), rough=0.04,
                     transmission=0.22, ior=1.46, coat=0.4)

    prof = [
        # --- foot: underside out to the rim, then back across the top ------
        (0.0, 0.0),
        (FOOT_R - 6.0, 0.0),
        (FOOT_R - 1.5, 0.6),
        (FOOT_R, 2.0),                  # foot edge
        (FOOT_R - 1.0, 3.4),
        (FOOT_R - 6.0, 4.2),            # slightly domed foot top
        (16.0, 5.0),
        (STEM_R + 2.6, 7.2),
        # --- stem ---------------------------------------------------------
        (STEM_R, 16.0),
        (STEM_R - 0.5, 44.0),
        (STEM_R - 0.3, 70.0),
        (STEM_R, 86.0),
        # --- underside of the bowl flaring out of the stem ----------------
        (STEM_R + 1.4, 92.0),
        (12.0, 98.0),
        (26.0, 108.0),
        (BOWL_R - 3.0, 121.0),
        (BOWL_R, 133.0),                # widest point of the bowl
        (BOWL_R - 0.6, 144.0),
        (RIM_R + 1.0, 152.0),
        (RIM_R, H - 1.0),
        (RIM_R - 0.2, H),
        # --- across the rim and back down the inside ----------------------
        (RIM_R - 0.2 - WALL, H),
        (RIM_R - 0.6, H - 2.5),
        (BOWL_R - 0.6 - WALL, 144.0),
        (BOWL_R - WALL, 133.0),
        (BOWL_R - 3.0 - WALL, 122.0),
        (24.0, 110.0),
        (11.0, 100.0),
        (5.0, FLOOR + 2.0),
        (4.2, FLOOR),                   # interior floor, on the way to the axis
        (0.0, FLOOR),                   # pole: closes the solid glass below
    ]
    glass_obj = bkit.lathe("WineGlass", prof, segments=96, mat=glass)
    bkit.recalc(glass_obj)

    return dict(spec=SPEC, parts=1)


# Only envelope dimensions are declared here: `measure()` reads bounding boxes,
# so a stem or wall claim would be checked against something it cannot see.
# Those two live in SPEC as documentation, not as a score.
CHECKS = [
    dict(name="foot_diameter", mm=84.0, tol=0.3, how="diameter", part="WineGlass"),
    dict(name="glass_height", mm=157.0, tol=0.3, how="bbox_z", part="WineGlass"),
    dict(name="overall_height", mm=157.0, tol=0.3, how="bbox_z"),
]
