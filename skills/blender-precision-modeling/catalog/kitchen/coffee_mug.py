"""
coffee_mug -- cylindrical ceramic mug, lathed body with a real wall thickness
and a real swept handle.

Dimensions are a typical 350 ml diner mug. `SPEC` is the contract verify.py
scores against: every value is a real-world millimetre measurement, and the
tolerance there is what "precise" means for this object class.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
sys.path.insert(0, os.path.abspath(__file__))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    body_diameter=84.0,     # outside diameter
    body_height=98.0,       # rim height above the table
    wall=4.0,               # rim thickness
    base_thickness=6.0,
    handle_reach=26.0,      # outer protrusion from the body wall
    handle_tube=5.5,
    volume_ml=340.0,
)

BODY_R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]
WALL = SPEC["wall"]
BASE = SPEC["base_thickness"]
TUBE = SPEC["handle_tube"]


def build():
    ceramic = bkit.preset("ceramic")
    glaze_inside = bkit.pbr("MugGlazeInside", base=(0.90, 0.89, 0.86),
                            rough=0.12, coat=0.4)

    # ---- body: one lathe profile that includes the inner wall ---------------
    # Walking out along the base, up the outside, over the rim, back down the
    # inside is what gives a real wall thickness; a single-surface revolve
    # gives a paper-thin rim that reads as plastic in a closeup.
    prof = [
        (0.0, 0.0),
        (BODY_R - 2.2, 0.0),
        (BODY_R - 0.2, 1.6),          # rounded foot
        (BODY_R, 4.0),
        (BODY_R, H - 3.0),
        (BODY_R - 0.3, H - 0.6),      # slight outer roll at the rim
        (BODY_R - 0.9, H),
        (BODY_R - WALL, H),           # across the rim
        (BODY_R - WALL - 0.6, H - 0.8),
        (BODY_R - WALL, 4.0),         # down the inside
        (BODY_R - WALL - 1.4, BASE),
        (0.0, BASE),                  # across the inside floor
    ]
    body = bkit.lathe("MugBody", prof, segments=96, mat=ceramic)

    # ---- handle: partial torus whose tips are buried in the wall -----------
    # arc from -90 to +90 about +X, centred on the wall plane, so both tips
    # sit at x = BODY_R and half the tube is inside the ceramic. Capped: an
    # open-ended tube is non-manifold, and a buried open end still shows up in
    # every health check for the rest of the catalog.
    reach = SPEC["handle_reach"] - TUBE       # centreline radius
    handle = bkit.arc_torus("MugHandle", reach, TUBE, -86.0, 86.0,
                            centre=(BODY_R - 1.5, 0.0, H * 0.53),
                            plane="XZ", seg_major=40, mat=ceramic, caps=True)

    # ---- interior glaze as a second material, not a second shell ----------
    # A duplicate interior object both z-fights with the real wall and doubles
    # the non-manifold count. Selecting faces by radius keeps one watertight solid.
    glaze_inside = bkit.pbr("MugGlazeInside", base=(0.90, 0.89, 0.86),
                            rough=0.12, coat=0.4)
    bkit.assign_faces_by(
        body, glaze_inside,
        lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM < (BODY_R - WALL + 0.05)
        and c.z / bkit.MM < H - 0.5,
    )

    return dict(spec=SPEC, parts=2)


# How each SPEC dimension is measured. The harness measures; the model only
# declares the intent, so a dimension claim cannot be satisfied by asserting it.

# How each SPEC dimension is measured. The harness measures; the model only
# declares the intent, so a dimension claim cannot be satisfied by asserting it.
CHECKS = [
    dict(name="body_diameter", mm=84.0, tol=0.3, how="diameter", part="MugBody"),
    dict(name="body_height", mm=98.0, tol=0.3, how="bbox_z", part="MugBody"),
    dict(name="overall_height", mm=98.0, tol=0.3, how="bbox_z"),
]
