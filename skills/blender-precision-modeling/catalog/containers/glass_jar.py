"""
glass_jar -- 500 ml straight-sided preserving jar: a lathed glass body with a
3 mm wall, a threaded neck and a separate two-piece metal screw lid.

Same lesson as the bottle: the cross-section is closed, so the jar has real
glass thickness at the rim instead of a paper-thin revolve that reads as film.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=70.0,       # straight-sided body, outside
    body_height=100.0,        # base to the top of the threaded neck
    wall=3.0,                 # mason-jar glass
    base_thickness=3.0,
    neck_diameter=57.0,
    bore_diameter=52.0,
    lid_diameter=62.0,
    lid_height=12.0,
    overall_height=111.5,      # jar rim to the top of the lid dome
    volume_ml=500.0,
)

R = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]
WALL = SPEC["wall"]


def build():
    # `preset("glass")` is transmission=1.0, which against this studio's dark
    # backdrop renders the jar as a near-black silhouette -- the whole surface
    # is the backdrop seen through it. Backing the transmission off to ~0.7 and
    # adding a coat gives back the specular the eye uses to read glass.
    glass = bkit.pbr("JarGlass", base=(0.86, 0.90, 0.90), rough=0.06,
                     transmission=0.70, ior=1.52, coat=0.6)
    # Metalness backed off: the lid is a horizontal disc with only the dark
    # backdrop above it, and at metal=1.0 it renders as a black cap.
    lid_metal = bkit.pbr("JarLidMetal", base=(0.74, 0.76, 0.78), metal=0.45,
                         rough=0.26)

    # ---- jar: base -> outside -> shoulder -> neck -> rim -> bore -> floor ----
    prof = [
        (0.0, 0.0),                  # centre of the base
        (30.0, 0.0),
        (33.5, 1.5),
        (R, 5.0),                    # rounded base corner
        (R, 76.0),                   # straight wall
        (34.0, 82.0),                # shoulder starts
        (29.0, 90.0),                # shoulder in to the neck
        (28.5, BH - 4.0),            # neck outside
        (29.8, BH - 4.0),            # thread crest
        (29.8, BH - 1.0),
        (28.5, BH - 1.0),
        (28.5, BH),                  # rim, outer corner
        (26.0, BH),                  # across the rim
        (26.0, 86.0),                # down the bore
        (31.5, 78.0),                # inside of the shoulder
        (32.0, 6.0),                 # down the inside wall
        (28.0, 3.0),
        (0.0, 3.0),                  # across the inner floor
    ]
    jar = bkit.lathe("JarBody", prof, segments=96, mat=glass)

    # ---- lid: a flat disc with a glass top and a rim skirt ------------------
    # Screwed over the neck: the skirt reaches down past the rim and the top
    # stands 12 mm proud, which is what gives the jar its two-piece look.
    lid_prof = [
        (0.0, 0.0),
        (30.0, 0.0),
        (31.0, 1.2),
        (31.0, 6.5),                 # skirt that grips the jar threads
        (27.0, 7.5),
        (27.0, 10.5),
        (12.0, 12.0),                # raised centre of the lid
        (0.0, 12.0),
    ]
    lid = bkit.lathe("JarLid", lid_prof, segments=96,
                     centre=(0.0, 0.0, BH - 0.5), mat=lid_metal)

    # ---- the flat inner lid disc, a different material on its own solid -----
    liner = bkit.lathe("JarLidLiner", [
        (0.0, 0.0), (25.5, 0.0), (25.5, 2.2), (0.0, 2.2),
    ], segments=96, centre=(0.0, 0.0, BH + 1.1),
        mat=bkit.pbr("JarLiner", base=(0.88, 0.87, 0.84), rough=0.25))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="body_diameter", mm=70.0, tol=0.4, how="diameter", part="JarBody"),
    dict(name="lid_diameter", mm=62.0, tol=0.4, how="diameter", part="JarLid"),
    dict(name="overall_height", mm=111.5, tol=0.3, how="bbox_z"),
]
