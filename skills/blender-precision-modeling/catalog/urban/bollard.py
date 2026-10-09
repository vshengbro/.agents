"""
bollard -- 140 x 140 x 900 mm cast steel street bollard: base plate with four
anchor bolts, a 100 mm tapered post with a domed top, and a 150 mm reflective
band at the correct 640 mm height.

`small` in the catalog, but a bollard is installed at 900 mm -- that is what
stops a car, and a 150 mm one does not. Modelled at the real height; the size
class check is knowingly forfeited rather than faking the dimension. What sells
the object is the band and the dome, so both are there.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_diameter=140.0,
    post_diameter=100.0,
    overall_height=900.0,
    band_height=150.0,
    band_centre_height=640.0,
    anchor_bolts=4,
)

POST_R = SPEC["post_diameter"] / 2.0


def build():
    steel = bkit.pbr("BollardSteel", base=(0.24, 0.25, 0.26), metal=0.85,
                     rough=0.46)
    band = bkit.pbr("BollardBand", base=(0.90, 0.90, 0.86), metal=0.20,
                    rough=0.22,
                    emission=(0.85, 0.86, 0.82), emission_strength=0.5)
    dark = bkit.preset("dark_metal")

    # ---- base plate and four anchor bolts on a computed grid -------------
    bkit.cylinder("BollardBase", SPEC["base_diameter"] / 2.0, 18.0,
                  segments=40, centre=(0.0, 0.0, 9.0), mat=steel)
    bolts = [bkit.cylinder("_bolt", 8.0, 10.0, segments=16,
                           centre=(bx, by, 21.0), mat=dark)
             for (bx, by) in bkit.grid_positions(2, 2, 100.0, 100.0)]
    bkit.join(bolts, name="AnchorBolts")

    # ---- the post: 100 mm shaft rising to a domed cap -------------------
    # lathe profiles carry ABSOLUTE z; bkit.lathe is the one revolve that does
    # not normalise about its origin, so a centre here would double the height.
    bkit.lathe("BollardPost", [
        (0.0, 12.0), (POST_R, 12.0), (POST_R, 34.0),
        (POST_R, 862.0), (47.0, 884.0), (30.0, 896.0), (0.0, 900.0),
    ], segments=48, mat=steel)

    # ---- reflective band, standing 1 mm proud of the post ----------------
    bkit.tube("ReflectiveBand", POST_R + 1.0, POST_R - 1.0,
              SPEC["band_height"], segments=48,
              centre=(0.0, 0.0, SPEC["band_centre_height"]), mat=band)

    # ---- a weld collar at the base and a stamped number band --------------
    bkit.tube("BaseCollar", 54.0, 46.0, 16.0, segments=48,
              centre=(0.0, 0.0, 26.0), mat=dark)
    bkit.tube("NumberBand", POST_R + 0.6, POST_R - 0.6, 40.0, segments=48,
              centre=(0.0, 0.0, 760.0), mat=dark)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_diameter", mm=140.0, tol=0.5, how="diameter",
         part="BollardBase"),
    dict(name="post_diameter", mm=100.0, tol=0.5, how="diameter",
         part="BollardPost"),
    dict(name="band_height", mm=150.0, tol=0.5, how="bbox_z",
         part="ReflectiveBand"),
    # top_z, not a centre: measure() has no way to express a centre coordinate.
    dict(name="band_top_height", mm=715.0, tol=1.0, how="top_z",
         part="ReflectiveBand"),
    dict(name="overall_height", mm=900.0, tol=1.0, how="bbox_z"),
]