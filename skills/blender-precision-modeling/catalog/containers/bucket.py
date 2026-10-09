"""
bucket -- 10 litre tapered plastic bucket: a lathed tub with a rolled rim, a
base rib, and a wire bail handle.

The bucket is the clearest test of a lathed vessel that is *not* a cylinder:
the wall tapers about 10 degrees, so if the profile is written as two straight
radii the silhouette is a cone. The inside wall is offset by the real 2.5 mm
thickness, and the bail handle's arc is solved from its two anchors and its
rise rather than guessed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    top_diameter=268.0,
    base_diameter=212.0,
    height=250.0,              # base to the rim
    wall=2.5,
    base_thickness=11.0,
    bail_rise=41.4,            # handle centreline rise above the rim
    overall_height=292.0,
    volume_l=10.0,
)

RT = SPEC["top_diameter"] / 2.0
RB = SPEC["base_diameter"] / 2.0
H = SPEC["height"]
WALL = SPEC["wall"]


def build():
    plastic = bkit.preset("white_plastic")
    plastic_grey = bkit.pbr("BucketGrey", base=(0.55, 0.57, 0.58), rough=0.42)
    wire = bkit.preset("brushed_metal")

    # ---- tub: base -> tapered outside -> rolled rim -> inside -> inner floor -
    prof = [
        (0.0, 0.0),
        (92.0, 0.0),
        (RB, 7.0),                    # base edge
        (RB + 0.5, 20.0),
        (RT, 244.0),                   # the taper, the whole silhouette
        (RT + 3.0, 248.0),
        (RT + 4.0, 250.0),             # rolled rim
        (RT + 1.0, 250.0),
        (RT - 2.0, 246.0),
        (RT - WALL - 1.0, 242.0),
        (RB - WALL - 1.0, 22.0),       # inside wall, offset by the real thickness
        (RB - WALL - 14.0, SPEC["base_thickness"]),
        (0.0, SPEC["base_thickness"]),
    ]
    body = bkit.lathe("BucketBody", prof, segments=96, mat=plastic)

    # ---- a moulded rib near the base, a common anti-creep feature ----------
    rib = bkit.torus("BucketRib", RB + 3.0, 3.5, seg_major=72, seg_minor=16,
                     centre=(0.0, 0.0, 40.0), mat=plastic_grey)

    # ---- wire bail: solve the arc from the two anchors and the rise ---------
    # The arc's ENDS sit at (+-a, rim) and its PEAK is `rise` above the rim.
    # A circle centred k below the rim satisfies
    #     a^2 + k^2 = (rise + k)^2   =>   k = (a^2 - rise^2) / (2 * rise)
    # and the sweep runs phi -> 180-phi so the arc passes over the top.
    # The handle's highest point is rim + rise + tube, so `bail_rise` is read
    # straight off the SPEC without subtracting the tube radius.
    a, rise = RT + 2.0, SPEC["bail_rise"]
    k = (a * a - rise * rise) / (2.0 * rise)
    rmaj = rise + k
    ang = math.degrees(math.atan2(k, a))
    bail = bkit.arc_torus("BucketBail", rmaj, 2.6, ang, 180.0 - ang,
                          centre=(0.0, 0.0, H - 2.0 - k), plane="XZ",
                          seg_major=44, mat=wire, caps=True)

    # ---- the grip sleeve in the middle of the bail -------------------------
    # Centred one radius below the wire so the sleeve's top just meets the arc:
    # a sleeve centred ON the peak pushes the bounding box above the bail and
    # the declared overall height stops matching what was built.
    grip = bkit.cylinder("BucketGrip", 6.0, 90.0, segments=32, axis="X",
                         centre=(0.0, 0.0, H - 2.0 + rise - 6.0),
                         mat=plastic_grey)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="top_diameter", mm=276.0, tol=1.0, how="diameter", part="BucketBody"),
    dict(name="body_height", mm=250.0, tol=1.0, how="bbox_z", part="BucketBody"),
    dict(name="overall_height", mm=292.0, tol=2.0, how="bbox_z"),
]
