"""
jigsaw -- 720 W jigsaw, 250 mm over the shoe and 191 mm to the top of the D-handle.

A jigsaw is a shoe, a body that hangs BELOW the handle line, and a blade that
runs down through a slot in the shoe. The number that fixes the silhouette is
the shoe: 178 x 124 mm of pressed steel, and the blade leaves the underside of
the body 8 mm above the shoe's top face so the shoe is what sits on the
material.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    shoe_length=178.0,
    shoe_width=124.0,
    blade_length=102.0,
    blade_width=22.0,
    body_length=198.0,
    handle_height=191.0,
    baseplate_thickness=6.0,
    blade_axis_z=96.0,
)

CHECKS = [
    dict(name="shoe_length", mm=178.0, tol=0.8, how="bbox_x", part="SawShoe"),
    dict(name="shoe_width", mm=124.0, tol=0.8, how="bbox_y", part="SawShoe"),
    dict(name="blade_length", mm=102.0, tol=0.8, how="bbox_x", part="SawBlade"),
    dict(name="blade_width", mm=22.0, tol=0.6, how="bbox_y", part="SawBlade"),
    dict(name="body_length", mm=198.0, tol=0.8, how="bbox_x", part="SawBody"),
    dict(name="handle_height", mm=191.0, tol=2.0, how="top_z",
         part="SawHandle"),
]

BZ = SPEC["blade_axis_z"]


def build():
    teal = bkit.preset("blue_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    grip_mat = bkit.pbr("SawGripRubber", base=(0.07, 0.07, 0.08), rough=0.62)

    # ---- shoe: the floor datum, underside at z = 0 -------------------------
    T.shell("SawShoe", SPEC["shoe_length"], SPEC["shoe_width"],
            SPEC["baseplate_thickness"],
            centre=(0.0, 0.0, SPEC["baseplate_thickness"] / 2.0),
            r=4.0, mat=steel, segments=2)
    bkit.rounded_box("SawShoeSlot", 20.0, 34.0, 5.0, r=2.0, segments=1,
                     centre=(-14.0, 0.0, 5.0), mat=dark)

    # ---- blade: a T-shank stem and a toothed ground blade ------------------
    bkit.rounded_box("SawBlade", 102.0, 22.0, 1.6, r=0.8, segments=1,
                     centre=(-14.0, 0.0, BZ - 66.0), mat=steel)
    teeth = bkit.rounded_box("SawBladeTeeth", 74.0, 24.0, 2.6, r=1.0,
                             segments=1, centre=(-14.0, 0.0, BZ - 66.0),
                             mat=steel)
    T.strut("SawBladeShank", (-14.0, 0.0, BZ - 66.0), (-14.0, 0.0, BZ + 18.0),
            14.0, 20.0, mat=steel, r=1.5)

    # ---- body --------------------------------------------------------------
    T.shell("SawBody", SPEC["body_length"], 78.0, 88.0,
            centre=(-4.0, 0.0, BZ + 6.0), r=15.0, mat=teal)
    T.shell("SawGearcase", 78.0, 72.0, 58.0, centre=(-48.0, 0.0, BZ + 4.0),
            r=14.0, mat=dark)
    T.vent_panel("SawVent", 4, 2, 14.0, 16.0, 3.6, 54.0, 30.0, 5.0,
                 centre=(48.0, 0.0, BZ + 14.0), axis="X", mat=dark)

    # ---- D-handle ----------------------------------------------------------
    bkit.arc_torus("SawHandle", 44.0, 11.0, 4.0, 176.0, centre=(-6.0, 0.0,
                                                                 136.0),
                   plane="XZ", seg_major=30, mat=grip_mat)
    T.strut("SawHandlePost", (-6.0, 0.0, 136.0), (-6.0, 0.0, BZ + 44.0),
            26.0, 30.0, mat=grip_mat)
    T.trigger("SawTrigger", (18.0, 0.0, 128.0), (18.0, 0.0, 112.0),
              26.0, 13.0, mat=dark)

    # ---- pendulum lock + dust port + cord ---------------------------------
    T.shell("SawLockLever", 54.0, 20.0, 18.0, centre=(66.0, 0.0, BZ + 44.0),
            r=6.0, mat=steel)
    bkit.tube("SawDustPort", 30.0, 24.0, 34.0, segments=32,
              centre=(-92.0, 0.0, BZ - 18.0), axis="X", mat=dark)
    T.coiled_cord("SawCord", (-124.0, 0.0, BZ - 40.0), 26.0, 5.0, 20.0, 330.0)

    return dict(spec=SPEC, parts=11)