"""
tap -- single-lever basin mixer: lathed body with a base flange, a real
gooseneck spout, a flat lever blade, and an aerator.

The gooseneck is a 180 degree arc whose two ends sit at the SAME height, one
facing up (the riser) and one facing down (the outlet). `arc_torus` puts its
up-facing end at the +X side of the centre and its down-facing end at -X, so
the arc is built pointing backwards and then mirrored in X -- otherwise the
spout arcs over and comes back down BEHIND the body.

Sizes are a typical UK basin mixer: 193 mm overall to the top of the spout,
120 mm forward reach, and a lever that is a blade rather than a knob.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_diameter=48.0,
    base_height=14.0,
    body_diameter=44.0,
    body_height=118.0,      # deck to the top of the body
    spout_reach=120.0,      # body axis to the spout outlet axis
    spout_arc_radius=60.0,  # a 180 degree arc, so reach = 2 x this
    springing_height=120.0, # height of the gooseneck's two ends
    spout_diameter=26.0,
    aerator_diameter=24.0,
    aerator_height=15.0,
    lever_length=78.0,
    lever_height=150.0,     # top of the lever blade
    overall_height=193.0,   # the gooseneck crown is the tallest point
)

BODY_R = SPEC["body_diameter"] / 2.0
BASE_R = SPEC["base_diameter"] / 2.0
REACH = SPEC["spout_reach"]
RARC = SPEC["spout_arc_radius"]
SPR = SPEC["springing_height"]
SP_R = SPEC["spout_diameter"] / 2.0


def build():
    chrome = bkit.preset("polished_metal")
    body_mat = bkit.pbr("TapBody", base=(0.72, 0.73, 0.75), metal=0.85,
                        rough=0.18)

    # ---- base flange + body: one lathe, so the shoulder is continuous -------
    # The flange (48) is the WIDEST part: it covers the 32 mm deck hole, and a
    # body wider than its own flange reads as a bottle standing on a coaster.
    body = bkit.lathe("TapBody", [
        (0.0, 0.0),
        (BASE_R, 0.0),
        (BASE_R, SPEC["base_height"]),
        (BODY_R, SPEC["base_height"] + 8.0),        # step in off the flange
        (BODY_R, SPEC["body_height"] - 24.0),
        (BODY_R - 5.0, SPEC["body_height"] - 8.0),  # shoulder
        (BODY_R - 8.0, SPEC["body_height"]),        # top face
        (0.0, SPEC["body_height"]),
    ], segments=72, mat=body_mat)

    # ---- riser: the vertical leg the gooseneck springs from ---------------
    # It starts BELOW the body's top face so the two solids interlock by
    # 24 mm instead of meeting tangentially on a circle.
    riser = bkit.cylinder("TapRiser", SP_R, SPR - 96.0, segments=48,
                          centre=(0.0, 0.0, (96.0 + SPR) / 2.0), mat=chrome)

    # ---- gooseneck: a 180 degree arc over the top ------------------------
    # Both ends of a semicircular arch point DOWNWARD, which is exactly what a
    # gooseneck needs: the riser rises from the body into the back end at x=0,
    # and the outlet leaves the front end at x=REACH pointing at the basin.
    # Centred at REACH/2 so the arch is centred between them.
    #
    # No `mirror()` here. Mirroring an arc_torus copies its two end caps onto
    # the seam, leaving two coincident cap discs and 24 non-manifold edges --
    # one per segment across the seam.
    spout = bkit.arc_torus("TapSpout", RARC, SP_R, 0.0, 180.0,
                           centre=(REACH / 2.0, 0.0, SPR), plane="XZ",
                           seg_major=48, seg_minor=32, mat=chrome, caps=True)

    # ---- aerator: a real fitting in the outlet, pointing down -------------
    # Raised 7 mm INTO the spout tube. Hanging it exactly tangent to the tube's
    # outer surface leaves a visible air gap in every render, because the
    # surface is curved and only the centreline touches.
    aer = bkit.lathe("TapAerator", [
        (0.0, 0.0), (8.0, 0.0), (12.0, 4.0), (12.0, SPEC["aerator_height"]),
        (8.0, SPEC["aerator_height"]), (8.0, 3.0), (0.0, 3.0),
    ], segments=48, mat=body_mat)
    bkit.move(aer, REACH, 0.0,
              SPR - SP_R - SPEC["aerator_height"] + 7.0)

    # ---- lever: a flat blade on a pivot at the body's top -----------------
    lt = SPEC["lever_length"]
    lever = bkit.rounded_box("TapLever", lt, 20.0, 11.0, r=5.0, segments=3,
                             centre=(0.0, 0.0, SPEC["lever_height"] - 5.5),
                             mat=chrome)
    bkit.move(lever, -lt * 0.42, 0.0, 0.0)
    pivot = bkit.cylinder("TapPivot", 9.0, 26.0, segments=32,
                          centre=(0.0, 0.0, SPEC["lever_height"] - 17.0),
                          axis="Y", mat=chrome)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_diameter", mm=48.0, tol=0.3, how="diameter", part="TapBody"),
    dict(name="body_height", mm=118.0, tol=0.3, how="bbox_z", part="TapBody"),
    dict(name="overall_height", mm=193.0, tol=0.6, how="bbox_z"),
    dict(name="lever_length", mm=78.0, tol=0.4, how="bbox_x", part="TapLever"),
    # The swept envelope across X, not the centreline reach: the tube is 26 mm
    # thick, so bbox_x overshoots the 120 mm centreline reach at both ends.
    dict(name="spout_envelope_x", mm=146.0, tol=0.6, how="bbox_x", part="TapSpout"),
    dict(name="outlet_x", mm=24.0, tol=0.4, how="bbox_x", part="TapAerator"),
]
